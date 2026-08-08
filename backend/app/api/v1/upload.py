"""LabLens AI - Upload & Processing API"""
import os
import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models.report import Report, ReportStatus, TestResult
from app.models.user import User
from app.schemas.report import UploadResponse
from app.api.v1.auth import get_current_active_user
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import decrypt_file_data
from app.services.document.processor import DocumentProcessor
from app.services.extraction.service import ExtractionService
from app.services.validation.service import ValidationService
from app.services.security.storage import StorageService
from app.services.ai.service import AIService

logger = get_logger(__name__)
router = APIRouter(tags=["Upload"])
settings = get_settings()


@router.post("", response_model=UploadResponse)
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    report_date: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    file_bytes = await file.read()
    if len(file_bytes) > settings.max_upload_size:
        raise HTTPException(status_code=413, detail="File too large")
    is_valid, errors = DocumentProcessor.validate_file(file_bytes, file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation failed: {', '.join(errors)}")
    storage = StorageService()
    storage_path, secure_name = await storage.save_file(file_bytes, file.filename, encrypt=True)
    mime = file.content_type or "application/octet-stream"
    page_count = DocumentProcessor.get_page_count(file_bytes, mime)
    report = Report(
        user_id=current_user.id, filename=file.filename, storage_path=storage_path,
        file_size=len(file_bytes), mime_type=mime, page_count=page_count,
        status=ReportStatus.PROCESSING, report_date=report_date,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    background_tasks.add_task(process_report_task, report.id, current_user.id)
    logger.info("Report uploaded", report_id=report.id, filename=file.filename)
    return UploadResponse(report_id=report.id, filename=file.filename, status=ReportStatus.PROCESSING, message="Report uploaded and is being processed. Check back shortly.")


async def process_report_task(report_id: int, user_id: int):
    from app.db import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Report).where(Report.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            logger.error("Report not found for processing", report_id=report_id)
            return
        try:
            storage = StorageService()
            file_bytes = await storage.get_file(report.storage_path)
            try:
                file_bytes = decrypt_file_data(file_bytes)
            except Exception:
                pass

            # Extract
            extractor = ExtractionService()
            extraction = await extractor.extract_from_document(file_bytes, report.mime_type)
            report.ocr_confidence_avg = extraction.get("ocr_confidence")
            report.extraction_quality_score = extraction.get("ocr_confidence")
            quality_issues = extraction.get("quality_issues", [])
            if quality_issues:
                report.validation_errors = quality_issues
            patient_info = extraction.get("patient_info", {})
            if not report.patient_name and patient_info.get("name"):
                report.patient_name = patient_info["name"]
            if not report.patient_age and patient_info.get("age"):
                report.patient_age = patient_info["age"]
            if not report.patient_gender and patient_info.get("gender"):
                report.patient_gender = patient_info["gender"]

            # Validate
            validator = ValidationService()
            validated_results = validator.validate_results(extraction["test_results"], report.patient_gender, report.patient_age)
            for r in validated_results:
                test = TestResult(
                    report_id=report.id, test_name=r["test_name"], normalized_test_name=r.get("normalized_test_name"),
                    category=r.get("category", "other"), result=r.get("result"), result_text=r.get("result_text"),
                    unit=r.get("unit"), reference_low=r.get("reference_low"), reference_high=r.get("reference_high"),
                    reference_text=r.get("reference_text"), lab_flag=r.get("lab_flag"), status=r.get("status", "unknown"),
                    report_date=report.report_date, source_page=r.get("source_page"), source_text=r.get("source_text"),
                    ocr_confidence=r.get("ocr_confidence", 0.0), interpretation_confidence=r.get("interpretation_confidence", 0.0),
                    notes=r.get("notes", ""),
                )
                db.add(test)
            categories = set(r.get("category", "other") for r in validated_results)
            if len(categories) > 3:
                from app.models.report import ReportType
                report.report_type = ReportType.MULTI_PANEL

            # AI Analysis (concurrent for all languages)
            ai_service = AIService()
            test_results = [{"test_name": r["test_name"], "normalized_test_name": r.get("normalized_test_name"), "result": r.get("result"), "result_text": r.get("result_text"), "unit": r.get("unit"), "reference_text": r.get("reference_text"), "status": r.get("status"), "notes": r.get("notes")} for r in validated_results]
            patient_info = {"name": report.patient_name, "age": report.patient_age, "gender": report.patient_gender}
            summary_en, summary_hi, summary_hinglish = await asyncio.gather(
                ai_service.generate_summary(test_results, patient_info, "en"),
                ai_service.generate_summary(test_results, patient_info, "hi"),
                ai_service.generate_summary(test_results, patient_info, "hinglish"),
            )
            report.ai_summary = summary_en
            report.ai_summary_hi = summary_hi
            report.ai_summary_hinglish = summary_hinglish
            report.status = ReportStatus.COMPLETED
            await db.commit()
            logger.info("Report processing completed", report_id=report_id)
        except Exception as e:
            logger.error("Report processing failed", report_id=report_id, error=str(e))
            report.status = ReportStatus.FAILED
            report.processing_notes = str(e)
            await db.commit()

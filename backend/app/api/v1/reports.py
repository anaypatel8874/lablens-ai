"""LabLens AI - Reports API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.report import Report, ReportStatus, ReportType
from app.models.user import User
from app.schemas.report import (
    ReportResponse, ReportListResponse, ReportUpdate, ReportDashboard,
    UploadResponse, AISummary
)
from app.api.v1.auth import get_current_active_user
from app.core.logging import get_logger
from app.services.ai.service import AIService
from app.services.trends.service import TrendAnalysisService
from app.services.pdf.service import PDFReportService

logger = get_logger(__name__)
router = APIRouter(tags=["Reports"])


@router.get("", response_model=List[ReportListResponse])
async def list_reports(
    status: Optional[ReportStatus] = None,
    report_type: Optional[ReportType] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Report).where(Report.user_id == current_user.id)
    if status:
        query = query.where(Report.status == status)
    if report_type:
        query = query.where(Report.report_type == report_type)
    query = query.order_by(desc(Report.created_at)).offset(offset).limit(limit)
    query = query.options(selectinload(Report.test_results))
    result = await db.execute(query)
    reports = result.scalars().all()
    response = []
    for r in reports:
        abnormal_count = sum(1 for t in r.test_results if t.status not in ["normal", "unknown", "missing"])
        response.append(ReportListResponse(
            id=r.id, filename=r.filename, report_type=r.report_type,
            status=r.status, report_date=r.report_date, lab_name=r.lab_name,
            created_at=r.created_at, result_count=len(r.test_results),
            abnormal_count=abnormal_count,
        ))
    return response


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.user_id == current_user.id).options(selectinload(Report.test_results)))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/dashboard", response_model=ReportDashboard)
async def get_dashboard(report_id: int, language: str = Query("en", regex="^(en|hi|hinglish)$"), current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.user_id == current_user.id).options(selectinload(Report.test_results)))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != ReportStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report processing not complete")
    ai_service = AIService()
    summary_data = None
    if language == "hi" and report.ai_summary_hi:
        summary_data = report.ai_summary_hi
    elif language == "hinglish" and report.ai_summary_hinglish:
        summary_data = report.ai_summary_hinglish
    elif report.ai_summary:
        summary_data = report.ai_summary
    else:
        test_results = [{"test_name": t.test_name, "normalized_test_name": t.normalized_test_name, "result": t.result, "result_text": t.result_text, "unit": t.unit, "reference_text": t.reference_text, "status": t.status, "notes": t.notes} for t in report.test_results]
        patient_info = {"name": report.patient_name, "age": report.patient_age, "gender": report.patient_gender}
        summary_data = await ai_service.generate_summary(test_results, patient_info, language)
        if language == "hi":
            report.ai_summary_hi = summary_data
        elif language == "hinglish":
            report.ai_summary_hinglish = summary_data
        else:
            report.ai_summary = summary_data
        await db.commit()
    category_counts = {}
    status_counts = {}
    for t in report.test_results:
        cat = t.category or "other"
        category_counts[cat] = category_counts.get(cat, 0) + 1
        status_counts[t.status] = status_counts.get(t.status, 0) + 1
    return ReportDashboard(report=report, summary=AISummary(**summary_data), category_counts=category_counts, status_counts=status_counts, trend_data=None)


@router.get("/{report_id}/download")
async def download_pdf(report_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.user_id == current_user.id).options(selectinload(Report.test_results)))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    pdf_service = PDFReportService()
    report_data = {
        "patient_info": {"name": report.patient_name, "age": report.patient_age, "gender": report.patient_gender},
        "report_date": report.report_date, "lab_name": report.lab_name,
        "test_results": [{"test_name": t.test_name, "result": t.result, "result_text": t.result_text, "unit": t.unit, "reference_text": t.reference_text, "status": t.status} for t in report.test_results],
    }
    summary = report.ai_summary or {}
    pdf_bytes = pdf_service.generate_summary_pdf(report_data, summary)
    from fastapi.responses import Response
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=lablens-report-{report_id}.pdf"})


@router.delete("/{report_id}", status_code=204)
async def delete_report(report_id: int, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id, Report.user_id == current_user.id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    from app.services.security.storage import StorageService
    storage = StorageService()
    background_tasks.add_task(storage.delete_file, report.storage_path)
    await db.delete(report)
    await db.commit()
    logger.info("Report deleted", report_id=report_id, user_id=current_user.id)
    return None

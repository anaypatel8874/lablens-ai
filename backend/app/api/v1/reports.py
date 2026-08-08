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
from app.services.deep_explain_engine import deep_explain_engine
from app.services.knowledge_engine import knowledge_engine

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
async def download_pdf(
    report_id: int,
    include_deep_explain: bool = Query(True),
    language: str = Query("en"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Download professional PDF report with optional Deep Explain."""
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.user_id == current_user.id).options(selectinload(Report.test_results))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report_data = {
        "filename": report.filename,
        "patient_info": {"name": report.patient_name, "age": report.patient_age, "gender": report.patient_gender},
        "report_date": report.report_date, "lab_name": report.lab_name,
        "test_results": [{"test_name": t.test_name, "result": t.result, "result_text": t.result_text, "unit": t.unit, "reference_text": t.reference_text, "status": t.status, "source_page": t.source_page} for t in report.test_results],
    }

    summary = report.ai_summary or {}

    # Collect deep explain data for attention findings
    deep_explain_data = []
    if include_deep_explain:
        for test in report.test_results:
            if test.status not in ['normal', 'unknown', 'missing']:
                de = {
                    "test_name": test.test_name,
                    "result": str(test.result) if test.result is not None else test.result_text,
                    "unit": test.unit or "",
                    "reference_range": test.reference_text or "N/A",
                    "status": test.status,
                    "priority": "🔴 HIGH PRIORITY" if test.status.startswith("critically") else "🟡 ATTENTION",
                    "what_it_mean": f"{test.test_name} is a laboratory parameter evaluated in this report.",
                    "why_flagged": f"This result ({test.result} {test.unit}) is outside the laboratory reference range ({test.reference_text}).",
                    "why_it_matters": "This parameter provides information about your health status.",
                    "what_it_does_not_prove": [f"One abnormal {test.test_name} result does not establish a specific diagnosis."],
                    "missing_information": ["Clinical history", "Current symptoms", "Related tests"],
                    "possible_symptoms": ["Symptoms vary depending on the underlying cause"],
                    "pattern_analysis": "Related laboratory parameters should be considered together for interpretation.",
                }
                deep_explain_data.append(de)

    # Generate professional PDF
    from app.services.pdf.service import pdf_service
    options = {
        "include_deep_explain": include_deep_explain,
        "language": language,
    }
    pdf_bytes = pdf_service.generate_professional_pdf(report_data, summary, deep_explain_data, options)

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=lablens-report-{report_id}.pdf"},
    )


@router.get("/{report_id}/deep-explain/{test_id}")
async def get_deep_explain(
    report_id: int,
    test_id: int,
    language: str = Query("en", regex="^(en|hi|hinglish)$"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get evidence-grounded deep explanation for a specific test result."""
    from app.services.deep_explanation import DeepExplanationBuilder
    from app.services.validation_engine import ClinicalValidator
    from app.services.evidence_engine import evidence_engine

    result = await db.execute(
        select(Report)
        .where(Report.id == report_id, Report.user_id == current_user.id)
        .options(selectinload(Report.test_results))
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Find the specific test
    test = None
    for t in report.test_results:
        if t.id == test_id:
            test = t
            break

    if not test:
        raise HTTPException(status_code=404, detail="Test result not found")

    # Get all related tests
    related_report_tests = [
        {
            "test_name": t.test_name,
            "result": t.result,
            "result_text": t.result_text,
            "unit": t.unit,
            "reference_text": t.reference_text,
            "status": t.status,
        }
        for t in report.test_results if t.id != test_id
    ]

    # Build test data
    test_data = {
        "test_name": test.test_name,
        "result": test.result,
        "result_text": test.result_text,
        "unit": test.unit,
        "reference_text": test.reference_text,
        "status": test.status,
        "source_page": "Page 1",
    }

    # Use Evidence Grounded Engine
    evidence_result = evidence_engine.generate_explanation(
        test_data=test_data,
        related_tests=related_report_tests,
        language=language,
    )

    # Validate final response
    is_safe, warnings = evidence_engine.validate_final_response(evidence_result)
    if not is_safe:
        logger.warning(f"Deep explain safety violations: {warnings}")

    # Build deep explanation (legacy fields for frontend compatibility)
    builder = DeepExplanationBuilder()
    explanation = builder.build_attention_explanation(
        test_name=test.test_name,
        value=test.result if test.result is not None else test.result_text,
        unit=test.unit or "",
        reference_range=test.reference_text or "N/A",
        status=test.status,
        language=language,
    )

    # Build related tests info
    related_test_names = {
        "hemoglobin": ["MCV", "MCH", "MCHC", "RDW", "Ferritin", "Serum Iron", "TIBC", "Vitamin B12", "Folate", "Reticulocyte Count"],
        "fasting_blood_sugar": ["HbA1c", "Postprandial Glucose", "Random Glucose", "Insulin", "C-Peptide"],
        "tsh": ["Free T4", "Free T3", "Anti-TPO", "Anti-Thyroglobulin", "Total T3", "Total T4"],
        "total_cholesterol": ["LDL", "HDL", "VLDL", "Triglycerides", "Non-HDL Cholesterol"],
        "creatinine": ["BUN", "Urea", "Uric Acid", "eGFR", "Sodium", "Potassium"],
        "alt": ["AST", "ALP", "GGT", "Bilirubin", "Albumin", "Total Protein"],
    }

    related_tests = []
    normalized_name = test.normalized_test_name or test.test_name.lower()

    for key, related_names in related_test_names.items():
        if key in normalized_name or normalized_name in key:
            for name in related_names:
                found = False
                for report_test in report.test_results:
                    if report_test.id != test.id and name.lower() in report_test.test_name.lower():
                        related_tests.append({
                            "name": report_test.test_name,
                            "why_relevant": f"Commonly interpreted alongside {test.test_name}",
                            "current_value": str(report_test.result) if report_test.result is not None else report_test.result_text,
                            "status": report_test.status,
                            "available": True,
                        })
                        found = True
                        break
                if not found:
                    related_tests.append({
                        "name": name,
                        "why_relevant": f"Commonly interpreted alongside {test.test_name}",
                        "current_value": None,
                        "status": None,
                        "available": False,
                    })
            break

    # Determine priority
    if test.status.startswith("critically"):
        priority = "🔴 HIGH PRIORITY"
    elif test.status in ["low", "high"]:
        priority = "🟠 MODERATE ATTENTION"
    elif test.status == "borderline":
        priority = "🟡 ATTENTION"
    else:
        priority = "🟡 ATTENTION"

    # Build comprehensive response
    deep_explain = {
        "test_name": test.test_name,
        "result": str(test.result) if test.result is not None else test.result_text,
        "unit": test.unit or "",
        "reference_range": test.reference_text or "N/A",
        "status": test.status,
        "priority": priority,
        "confidence": explanation.confidence,
        "what_it_mean": explanation.what_it_mean,
        "why_it_matters": explanation.why_it_matters,
        "why_flagged": f"This result has been flagged because its value ({test.result} {test.unit}) is outside the laboratory reference range ({test.reference_text}).",
        "medical_explanation": explanation.what_it_mean,
        "simple_explanation": explanation.what_it_mean,
        "possible_associations": [
            {
                "condition": assoc,
                "what_it_is": assoc,
                "why_associated": f"This condition can be associated with {test.status} {test.test_name}",
                "supporting_findings": [f"{test.test_name}: {test.result}"],
                "missing_info": ["Clinical history", "Symptoms", "Additional tests"],
                "confidence": "LOW",
            }
            for assoc in explanation.possible_associations
        ],
        "common_causes": explanation.possible_associations[:3],
        "other_causes": explanation.possible_associations[3:],
        "less_common_causes": [],
        "pattern_analysis": f"This finding should be interpreted alongside related laboratory parameters for a more complete understanding.",
        "related_tests": related_tests,
        "possible_symptoms": explanation.possible_symptoms,
        "what_it_does_not_prove": explanation.what_it_does_not_prove,
        "trend": None,
        "missing_information": evidence_result.get("sections", [{}])[2].get("items", [{}])[0].get("statement", "").replace("Missing information: ", "") if len(evidence_result.get("sections", [])) > 2 else "Clinical history, current symptoms",
        "doctor_questions": explanation.doctor_questions,
        "next_steps": [
            "Discuss this result with a qualified healthcare professional",
            "Keep previous reports available for comparison",
            "Follow any existing medical advice",
            "Bring a complete list of current medications to your appointment",
        ],
        "safety_warning": None,
        "source_page": "Page 1",
        "ai_confidence": evidence_result.get("overall_confidence", explanation.confidence),
        "evidence_based": evidence_result,
        "safety_status": "passed" if is_safe else "warnings",
        "disease_associations": [],
    }

    # Add disease associations from knowledge engine
    available_test_names = [t.test_name for t in report.test_results]
    disease_associations = knowledge_engine.find_associated_diseases(
        test_name=test.test_name,
        result_status=test.status,
        available_tests=available_test_names,
    )
    deep_explain["disease_associations"] = disease_associations[:3]  # Top 3

    # Generate evidence-grounded explanation using new engine
    test_data = {
        "test_name": test.test_name,
        "result": test.result,
        "unit": test.unit,
        "reference_text": test.reference_text,
        "status": test.status,
        "source_page": "Page 1",
    }
    related_data = [
        {
            "test_name": t.test_name,
            "result": t.result,
            "unit": t.unit,
            "reference_text": t.reference_text,
            "status": t.status,
        }
        for t in report.test_results if t.id != test_id
    ]

    evidence_explanation = deep_explain_engine.generate(
        test_data=test_data,
        related_tests=related_data,
        language=language,
    )
    deep_explain["evidence_grounded"] = evidence_explanation

    return deep_explain


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

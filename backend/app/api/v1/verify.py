"""LabLens AI - Verification and Correction API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models.report import Report, ReportStatus, TestResult
from app.models.user import User
from app.api.v1.auth import get_current_active_user
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/verify", tags=["Verification"])


class ValueVerificationRequest(BaseModel):
    test_result_id: int
    is_correct: bool
    corrected_value: Optional[float] = None
    corrected_unit: Optional[str] = None
    corrected_reference: Optional[str] = None


class BatchVerificationRequest(BaseModel):
    report_id: int
    verifications: List[ValueVerificationRequest]


class CorrectionResponse(BaseModel):
    success: bool
    message: str
    recalculated: bool = False


@router.post("/value", response_model=CorrectionResponse)
async def verify_value(
    request: ValueVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify or correct a single extracted value."""
    result = await db.execute(
        select(TestResult).where(
            TestResult.id == request.test_result_id,
            TestResult.report_id == Report.id,
            Report.user_id == current_user.id,
        )
    )
    test = result.scalar_one_or_none()

    if not test:
        raise HTTPException(status_code=404, detail="Test result not found")

    if request.is_correct:
        logger.info(f"User confirmed value for {test.test_name}: {test.result}")
        return CorrectionResponse(success=True, message="Value confirmed", recalculated=False)

    # Apply correction
    old_value = test.result
    if request.corrected_value is not None:
        test.result = request.corrected_value
    if request.corrected_unit is not None:
        test.unit = request.corrected_unit
    if request.corrected_reference is not None:
        test.reference_text = request.corrected_reference

    # Re-validate the corrected value
    from app.services.validation_engine import ClinicalValidator
    validator = ClinicalValidator()

    if test.result is not None and test.reference_text:
        ref_low, ref_high, _ = validator.validate_reference_range(
            test.reference_text, test.test_name
        )
        if ref_low is not None or ref_high is not None:
            status, _ = validator.classify_result(
                test.result, ref_low, ref_high
            )
            test.status = status
            test.reference_low = ref_low
            test.reference_high = ref_high

    # Mark report for re-analysis
    report = await db.execute(
        select(Report).where(Report.id == test.report_id)
    )
    report = report.scalar_one()
    report.status = ReportStatus.COMPLETED  # Will trigger re-analysis if needed

    await db.commit()

    logger.info(
        f"User corrected {test.test_name}: {old_value} -> {test.result}"
    )

    return CorrectionResponse(
        success=True,
        message="Value corrected and analysis updated",
        recalculated=True,
    )


@router.post("/batch", response_model=CorrectionResponse)
async def batch_verify(
    request: BatchVerificationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify or correct multiple values at once."""
    report = await db.execute(
        select(Report).where(
            Report.id == request.report_id,
            Report.user_id == current_user.id,
        )
    )
    report = report.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    corrected_count = 0
    for verification in request.verifications:
        result = await db.execute(
            select(TestResult).where(
                TestResult.id == verification.test_result_id,
                TestResult.report_id == report.id,
            )
        )
        test = result.scalar_one_or_none()
        if not test:
            continue

        if verification.is_correct:
            continue

        # Apply correction
        if verification.corrected_value is not None:
            test.result = verification.corrected_value
        if verification.corrected_unit is not None:
            test.unit = verification.corrected_unit
        if verification.corrected_reference is not None:
            test.reference_text = verification.corrected_reference
        corrected_count += 1

    await db.commit()

    logger.info(
        f"User batch corrected {corrected_count} values in report {report.id}"
    )

    return CorrectionResponse(
        success=True,
        message=f"{corrected_count} values corrected",
        recalculated=corrected_count > 0,
    )


@router.get("/report/{report_id}")
async def get_verification_data(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get extracted data with confidence scores for user verification."""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Report)
        .where(Report.id == report_id, Report.user_id == current_user.id)
        .options(selectinload(Report.test_results))
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    verification_data = {
        "report_id": report.id,
        "filename": report.filename,
        "status": report.status,
        "tests": [],
    }

    for test in report.test_results:
        verification_data["tests"].append({
            "id": test.id,
            "test_name": test.test_name,
            "result": test.result,
            "unit": test.unit,
            "reference_text": test.reference_text,
            "status": test.status,
            "source_page": test.source_page,
            "needs_verification": test.status in ["unknown", "borderline"],
        })

    return verification_data

"""LabLens AI - Trends API"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.report import Report, ReportStatus
from app.models.user import User
from app.api.v1.auth import get_current_active_user
from app.services.trends.service import TrendAnalysisService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Trends"])


@router.get("/{parameter}")
async def get_parameter_trend(parameter: str, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.user_id == current_user.id, Report.status == ReportStatus.COMPLETED).order_by(desc(Report.report_date)).options(selectinload(Report.test_results)).limit(10))
    reports = result.scalars().all()
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    trend_service = TrendAnalysisService()
    trend = trend_service.analyze_trends([{"report_date": r.report_date, "test_results": [{"normalized_test_name": t.normalized_test_name, "test_name": t.test_name, "result": t.result, "unit": t.unit, "status": t.status, "reference_low": t.reference_low, "reference_high": t.reference_high} for t in r.test_results]} for r in reports], parameter)
    return trend


@router.get("/compare/{report_id_1}/{report_id_2}")
async def compare_two_reports(report_id_1: int, report_id_2: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id.in_([report_id_1, report_id_2]), Report.user_id == current_user.id).options(selectinload(Report.test_results)))
    reports = result.scalars().all()
    if len(reports) != 2:
        raise HTTPException(status_code=404, detail="One or both reports not found")
    r1, r2 = reports
    trend_service = TrendAnalysisService()
    comparison = trend_service.compare_reports(
        {"test_results": [{"normalized_test_name": t.normalized_test_name, "test_name": t.test_name, "result": t.result, "unit": t.unit, "status": t.status} for t in r1.test_results]},
        {"test_results": [{"normalized_test_name": t.normalized_test_name, "test_name": t.test_name, "result": t.result, "unit": t.unit, "status": t.status} for t in r2.test_results]},
    )
    return {"comparison": comparison}

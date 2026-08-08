"""LabLens AI - Chatbot API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models.report import Report
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.v1.auth import get_current_active_user
from app.services.ai.service import AIService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Chatbot"])


@router.post("/ask", response_model=ChatResponse)
async def ask_report(request: ChatRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == request.report_id, Report.user_id == current_user.id).options(selectinload(Report.test_results)))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report_data = [{"test_name": t.test_name, "normalized_test_name": t.normalized_test_name, "result": t.result, "result_text": t.result_text, "unit": t.unit, "reference_text": t.reference_text, "status": t.status} for t in report.test_results]
    ai_service = AIService()
    response = await ai_service.chat_response(request.message, report_data, [h.model_dump() for h in request.history], request.language)
    return ChatResponse(**response)

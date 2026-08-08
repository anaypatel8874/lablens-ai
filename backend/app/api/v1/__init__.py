from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.reports import router as reports_router
from app.api.v1.upload import router as upload_router
from app.api.v1.chat import router as chat_router
from app.api.v1.trends import router as trends_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(reports_router, prefix="/reports")
api_router.include_router(upload_router, prefix="/upload")
api_router.include_router(chat_router, prefix="/chat")
api_router.include_router(trends_router, prefix="/trends")

"""LabLens AI - Chatbot Schemas"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    cited_tests: Optional[List[str]] = None


class ChatRequest(BaseModel):
    report_id: int
    message: str
    language: str = "en"  # en, hi, hinglish
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    message: str
    cited_tests: Optional[List[str]] = None
    confidence: Optional[float] = None
    is_medical_advice: bool = False
    disclaimer: Optional[str] = None

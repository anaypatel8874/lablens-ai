"""LabLens AI - Audit Logging System"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum
import json
import logging

from app.db import Base

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    UPLOAD = "upload"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    ANALYSIS = "analysis"
    USER_CORRECTION = "user_correction"
    VERIFICATION = "verification"
    DOWNLOAD = "download"
    VIEW = "view"
    DELETE = "delete"


class AuditLog(Base):
    __tablename__ = "audit_logs_enhanced"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    report = relationship("Report", back_populates="audit_logs_enhanced")
    user = relationship("User", back_populates="audit_logs_enhanced")


class AuditLogger:
    """Structured audit logging for medical report processing."""

    @staticmethod
    async def log_action(
        db,
        report_id: int,
        user_id: int,
        action: AuditAction,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an auditable action."""
        log_entry = AuditLog(
            report_id=report_id,
            user_id=user_id,
            action=action.value,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(log_entry)
        await db.commit()
        return log_entry

    @staticmethod
    async def log_extraction(
        db,
        report_id: int,
        user_id: int,
        extraction_results: List[Dict],
        confidence_scores: Dict[str, float],
    ):
        """Log extraction results with confidence scores."""
        return await AuditLogger.log_action(
            db, report_id, user_id, AuditAction.EXTRACTION,
            details={
                "extraction_count": len(extraction_results),
                "confidence_scores": confidence_scores,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @staticmethod
    async def log_validation(
        db,
        report_id: int,
        user_id: int,
        validation_results: Dict[str, Any],
    ):
        """Log validation results."""
        return await AuditLogger.log_action(
            db, report_id, user_id, AuditAction.VALIDATION,
            details={
                "validation": validation_results,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @staticmethod
    async def log_user_correction(
        db,
        report_id: int,
        user_id: int,
        field: str,
        old_value: Any,
        new_value: Any,
    ):
        """Log user corrections to extracted data."""
        return await AuditLogger.log_action(
            db, report_id, user_id, AuditAction.USER_CORRECTION,
            details={
                "field": field,
                "old_value": str(old_value) if old_value else None,
                "new_value": str(new_value) if new_value else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


# Add relationships to existing models (will be imported in models update)

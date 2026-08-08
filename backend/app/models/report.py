"""LabLens AI - Report & Test Result Models"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.db import Base


class ReportStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class ReportType(str, enum.Enum):
    CBC = "cbc"
    LFT = "lft"
    KFT = "kft"
    LIPID = "lipid"
    THYROID = "thyroid"
    GLUCOSE = "glucose"
    HBA1C = "hba1c"
    VITAMIN = "vitamin"
    IRON = "iron"
    URINE = "urine"
    HORMONE = "hormone"
    COAGULATION = "coagulation"
    CARDIAC = "cardiac"
    MICROBIOLOGY = "microbiology"
    SEROLOGY = "serology"
    MOLECULAR = "molecular"
    HISTOPATHOLOGY = "histopathology"
    CYTOLOGY = "cytology"
    STOOL = "stool"
    BODY_FLUID = "body_fluid"
    TUMOR_MARKER = "tumor_marker"
    AUTOIMMUNE = "autoimmune"
    ALLERGY = "allergy"
    SEMEN = "semen"
    GYNECOLOGY = "gynecology"
    ELECTROLYTE = "electrolyte"
    OTHER = "other"
    MULTI_PANEL = "multi_panel"


class TestResultStatus(str, enum.Enum):
    NORMAL = "normal"
    BORDERLINE = "borderline"
    LOW = "low"
    HIGH = "high"
    CRITICALLY_LOW = "critically_low"
    CRITICALLY_HIGH = "critically_high"
    UNREADABLE = "unreadable"
    MISSING = "missing"
    UNKNOWN = "unknown"


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    page_count = Column(Integer, default=1)

    report_type = Column(Enum(ReportType), default=ReportType.OTHER)
    status = Column(Enum(ReportStatus), default=ReportStatus.UPLOADED)

    # Patient info extracted from report
    patient_name = Column(String(255), nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), nullable=True)
    report_date = Column(DateTime, nullable=True)
    lab_name = Column(String(255), nullable=True)
    lab_reference = Column(String(255), nullable=True)

    # Processing metadata
    ocr_confidence_avg = Column(Float, nullable=True)
    extraction_quality_score = Column(Float, nullable=True)
    validation_errors = Column(JSON, default=list)
    processing_notes = Column(Text, nullable=True)

    # AI Summary
    ai_summary = Column(JSON, nullable=True)
    ai_summary_hi = Column(JSON, nullable=True)
    ai_summary_hinglish = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="reports")
    test_results = relationship("TestResult", back_populates="report", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="report", cascade="all, delete-orphan")


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)

    test_name = Column(String(255), nullable=False)
    normalized_test_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)

    result = Column(Float, nullable=True)
    result_text = Column(Text, nullable=True)
    unit = Column(String(100), nullable=True)

    reference_low = Column(Float, nullable=True)
    reference_high = Column(Float, nullable=True)
    reference_text = Column(String(500), nullable=True)

    lab_flag = Column(String(50), nullable=True)
    status = Column(Enum(TestResultStatus), default=TestResultStatus.UNKNOWN)

    report_date = Column(DateTime, nullable=True)
    source_page = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)

    ocr_confidence = Column(Float, default=0.0)
    interpretation_confidence = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="test_results")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    report = relationship("Report", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")


# Add relationships to User
from app.models.user import User
User.reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
User.audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

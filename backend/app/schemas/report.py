"""LabLens AI - Report & Test Result Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TestResultStatus(str, Enum):
    NORMAL = "normal"
    BORDERLINE = "borderline"
    LOW = "low"
    HIGH = "high"
    CRITICALLY_LOW = "critically_low"
    CRITICALLY_HIGH = "critically_high"
    UNREADABLE = "unreadable"
    MISSING = "missing"
    UNKNOWN = "unknown"


class TestResultBase(BaseModel):
    test_name: str
    normalized_test_name: Optional[str] = None
    category: Optional[str] = None
    result: Optional[float] = None
    result_text: Optional[str] = None
    unit: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    reference_text: Optional[str] = None
    lab_flag: Optional[str] = None
    status: TestResultStatus = TestResultStatus.UNKNOWN
    report_date: Optional[datetime] = None
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    ocr_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    interpretation_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: Optional[str] = None


class TestResultCreate(TestResultBase):
    report_id: int


class TestResultResponse(TestResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReportStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"
    QUARANTINED = "quarantined"


class ReportType(str, Enum):
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


class ReportBase(BaseModel):
    filename: str
    file_size: int
    mime_type: str
    page_count: int = 1
    report_type: ReportType = ReportType.OTHER
    status: ReportStatus = ReportStatus.UPLOADED
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    report_date: Optional[datetime] = None
    lab_name: Optional[str] = None
    lab_reference: Optional[str] = None


class ReportCreate(ReportBase):
    user_id: int
    storage_path: str


class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    report_type: Optional[ReportType] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    report_date: Optional[datetime] = None
    lab_name: Optional[str] = None
    ocr_confidence_avg: Optional[float] = None
    extraction_quality_score: Optional[float] = None
    validation_errors: Optional[List[str]] = None
    processing_notes: Optional[str] = None
    ai_summary: Optional[Dict[str, Any]] = None
    ai_summary_hi: Optional[Dict[str, Any]] = None
    ai_summary_hinglish: Optional[Dict[str, Any]] = None


class ReportResponse(ReportBase):
    id: int
    user_id: int
    storage_path: str
    ocr_confidence_avg: Optional[float] = None
    extraction_quality_score: Optional[float] = None
    validation_errors: List[str] = []
    processing_notes: Optional[str] = None
    ai_summary: Optional[Dict[str, Any]] = None
    ai_summary_hi: Optional[Dict[str, Any]] = None
    ai_summary_hinglish: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    test_results: List[TestResultResponse] = []

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    id: int
    filename: str
    report_type: ReportType
    status: ReportStatus
    report_date: Optional[datetime] = None
    lab_name: Optional[str] = None
    created_at: datetime
    result_count: int = 0
    abnormal_count: int = 0

    class Config:
        from_attributes = True


class UploadResponse(BaseModel):
    report_id: int
    filename: str
    status: ReportStatus
    message: str


class AISummary(BaseModel):
    overall_summary: str
    normal_findings: List[str]
    attention_findings: List[str]
    high_priority_findings: List[str]
    parameter_explanations: List[Dict[str, str]]
    comparison_with_previous: Optional[str] = None
    doctor_questions: List[str]
    health_education: List[str]
    data_quality_warnings: List[str]
    safety_disclaimer: Optional[str] = None


class ReportDashboard(BaseModel):
    report: ReportResponse
    summary: AISummary
    category_counts: Dict[str, int]
    status_counts: Dict[str, int]
    trend_data: Optional[List[Dict[str, Any]]] = None

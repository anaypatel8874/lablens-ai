"""LabLens AI - Zero-Hallucination Medical Data Pipeline"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNREADABLE = "unreadable"


class ValidationStatus(str, Enum):
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    CONFLICTING = "conflicting"
    UNREADABLE = "unreadable"
    MISSING = "missing"


@dataclass
class ExtractedValue:
    test_name: str
    original_test_name: str
    normalized_test_name: Optional[str]
    value: Optional[float]
    value_text: Optional[str]
    unit: Optional[str]
    reference_range: Optional[str]
    reference_low: Optional[float]
    reference_high: Optional[float]
    reference_source: str = "report"
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    validation_status: ValidationStatus = ValidationStatus.VALID
    ocr_confidence: float = 0.0
    source_page: Optional[int] = None
    source_region: Optional[str] = None
    flags: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    is_valid: bool
    status: ValidationStatus
    confidence: ConfidenceLevel
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    safety_flags: List[str] = field(default_factory=list)


# Unit conversion factors (to standard unit)
UNIT_CONVERSIONS = {
    "glucose": {
        "mg/dL": 1.0,
        "mmol/L": 18.018,
        "g/L": 1000.0,
    },
    "cholesterol": {
        "mg/dL": 1.0,
        "mmol/L": 38.67,
    },
    "creatinine": {
        "mg/dL": 1.0,
        "µmol/L": 0.0113,
        "umol/L": 0.0113,
    },
    "hemoglobin": {
        "g/dL": 1.0,
        "g/L": 0.1,
        "mmol/L": 0.6206,
    },
}

# Standard units for each test category
STANDARD_UNITS = {
    "hemoglobin": "g/dL",
    "rbc_count": "millions/µL",
    "wbc_count": "10³/µL",
    "platelet_count": "10³/µL",
    "hematocrit": "%",
    "mcv": "fL",
    "mch": "pg",
    "fasting_blood_sugar": "mg/dL",
    "total_cholesterol": "mg/dL",
    "hdl_cholesterol": "mg/dL",
    "ldl_cholesterol": "mg/dL",
    "triglycerides": "mg/dL",
    "creatinine": "mg/dL",
    "tsh": "µIU/mL",
}


# Numeric plausibility ranges (absolute min/max for human survival)
PLAUSIBILITY_RANGES = {
    "hemoglobin": (1.0, 25.0),  # g/dL
    "rbc_count": (0.5, 10.0),  # millions/µL
    "wbc_count": (200.0, 50000.0),  # /µL (raw count)
    "platelet_count": (5.0, 2000.0),  # x10³/µL (5000-2000000 /µL)
    "hematocrit": (5.0, 70.0),  # %
    "fasting_blood_sugar": (10.0, 1000.0),  # mg/dL
    "total_cholesterol": (20.0, 600.0),  # mg/dL
    "creatinine": (0.1, 30.0),  # mg/dL
    "tsh": (0.001, 500.0),  # µIU/mL
}


# Test name normalization mapping
TEST_NAME_NORMALIZATION = {
    "sgot": "ast",
    "sgpt": "alt",
    "tlc": "wbc_count",
    "total leukocyte count": "wbc_count",
    "total wbc count": "wbc_count",
    "hb": "hemoglobin",
    "haemoglobin": "hemoglobin",
    "rbc": "rbc_count",
    "red blood cell count": "rbc_count",
    "red blood cells": "rbc_count",
    "pcv": "hematocrit",
    "packed cell volume": "hematocrit",
    "hct": "hematocrit",
    "plt": "platelet_count",
    "platelets": "platelet_count",
    "fbs": "fasting_blood_sugar",
    "fasting glucose": "fasting_blood_sugar",
    "fasting plasma glucose": "fasting_blood_sugar",
    "ppbs": "postprandial_blood_sugar",
    "postprandial glucose": "postprandial_blood_sugar",
    "rbs": "random_blood_sugar",
    "random glucose": "random_blood_sugar",
    "hba1c": "hba1c",
    "glycated hemoglobin": "hba1c",
    "a1c": "hba1c",
    "sgot/ast": "ast",
    "sgpt/alt": "alt",
    "alkaline phosphatase": "alp",
    "gamma gt": "ggt",
    "gamma glutamyl transferase": "ggt",
    "total bilirubin": "total_bilirubin",
    "direct bilirubin": "direct_bilirubin",
    "indirect bilirubin": "indirect_bilirubin",
    "serum creatinine": "creatinine",
    "blood urea": "blood_urea",
    "blood urea nitrogen": "bun",
    "uric acid": "uric_acid",
    "total protein": "total_protein",
    "serum albumin": "albumin",
    "serum globulin": "globulin",
    "a/g ratio": "ag_ratio",
    "albumin globulin ratio": "ag_ratio",
    "total cholesterol": "total_cholesterol",
    "hdl": "hdl_cholesterol",
    "hdl-c": "hdl_cholesterol",
    "ldl": "ldl_cholesterol",
    "ldl-c": "ldl_cholesterol",
    "vldl": "vldl",
    "serum triglycerides": "triglycerides",
    "thyroid stimulating hormone": "tsh",
    "free t3": "free_t3",
    "ft3": "free_t3",
    "free t4": "free_t4",
    "ft4": "free_t4",
    "total t3": "total_t3",
    "tt3": "total_t3",
    "total t4": "total_t4",
    "tt4": "total_t4",
    "vitamin d": "vitamin_d",
    "25-oh vitamin d": "vitamin_d",
    "25 hydroxy vitamin d": "vitamin_d",
    "vitamin d3": "vitamin_d",
    "vitamin b12": "vitamin_b12",
    "b12": "vitamin_b12",
    "cyanocobalamin": "vitamin_b12",
    "folic acid": "folate",
    "s. folate": "folate",
    "serum iron": "serum_iron",
    "s. iron": "serum_iron",
    "total iron binding capacity": "tibc",
    "serum ferritin": "ferritin",
    "s. ferritin": "ferritin",
    "calcium": "calcium",
    "s. calcium": "calcium",
    "serum sodium": "sodium",
    "s. sodium": "sodium",
    "serum potassium": "potassium",
    "s. potassium": "potassium",
    "serum chloride": "chloride",
    "s. chloride": "chloride",
}


class ClinicalValidator:
    """Deterministic clinical rule engine for laboratory value validation."""

    @staticmethod
    def normalize_test_name(raw_name: str) -> Tuple[str, Optional[str]]:
        """Normalize test name to standard form. Returns (original, normalized)."""
        raw_lower = raw_name.lower().strip()
        normalized = TEST_NAME_NORMALIZATION.get(raw_lower)
        return raw_lower, normalized

    @staticmethod
    def validate_numeric_plausibility(
        test_name: str, value: float, unit: str
    ) -> ValidationResult:
        """Check if a numeric value is physiologically plausible."""
        warnings = []
        errors = []
        safety_flags = []

        # Get plausibility range
        range_key = None
        for key in PLAUSIBILITY_RANGES:
            if key in test_name.lower():
                range_key = key
                break

        if range_key:
            low, high = PLAUSIBILITY_RANGES[range_key]
            if value < low:
                errors.append(f"Value {value} is below physiological minimum ({low})")
                safety_flags.append("SUSPICIOUS_VALUE")
            elif value > high:
                errors.append(f"Value {value} is above physiological maximum ({high})")
                safety_flags.append("SUSPICIOUS_VALUE")

        # Check for negative values where impossible
        if value < 0:
            errors.append("Negative value detected for a test that cannot be negative")
            safety_flags.append("IMPOSSIBLE_VALUE")

        # Check for likely decimal errors (e.g., 112 instead of 11.2)
        if value > 1000 and range_key in ["hemoglobin", "hematocrit"]:
            warnings.append("Value may contain decimal error (e.g., 112 instead of 11.2)")
            safety_flags.append("POSSIBLE_DECIMAL_ERROR")

        # Determine confidence
        if errors:
            confidence = ConfidenceLevel.LOW
            status = ValidationStatus.SUSPICIOUS
            is_valid = False
        elif warnings:
            confidence = ConfidenceLevel.MEDIUM
            status = ValidationStatus.VALID
            is_valid = True
        else:
            confidence = ConfidenceLevel.HIGH
            status = ValidationStatus.VALID
            is_valid = True

        return ValidationResult(
            is_valid=is_valid,
            status=status,
            confidence=confidence,
            warnings=warnings,
            errors=errors,
            safety_flags=safety_flags,
        )

    @staticmethod
    def validate_unit(
        test_name: str, unit: str
    ) -> Tuple[bool, List[str]]:
        """Validate that the unit is appropriate for the test."""
        warnings = []
        unit_lower = (unit or "").lower().strip()

        # Check against expected standard unit
        for key, standard in STANDARD_UNITS.items():
            if key in test_name.lower():
                standard_lower = standard.lower()
                if unit_lower != standard_lower:
                    # Check if it's a known convertible unit
                    convertible = False
                    for category, conversions in UNIT_CONVERSIONS.items():
                        if category in test_name.lower():
                            if unit_lower in [u.lower() for u in conversions]:
                                convertible = True
                                break
                    if not convertible and unit_lower not in ["", "n/a"]:
                        warnings.append(
                            f"Unit '{unit}' differs from expected '{standard}'"
                        )
                break

        is_valid = len(warnings) == 0
        return is_valid, warnings

    @staticmethod
    def classify_result(
        value: float,
        reference_low: Optional[float],
        reference_high: Optional[float],
        lab_flags: List[str] = None,
    ) -> Tuple[str, ConfidenceLevel]:
        """Deterministically classify a result against reference range."""
        if reference_low is None and reference_high is None:
            return "unknown", ConfidenceLevel.LOW

        # Check for critical lab flags
        if lab_flags:
            for flag in lab_flags:
                if flag.lower() in ["critical", "panic", "alert"]:
                    return "critical", ConfidenceLevel.HIGH

        # Classify based on reference range
        if reference_low is not None and value < reference_low:
            # Check borderline (within 10%)
            if value >= reference_low * 0.9:
                return "borderline", ConfidenceLevel.HIGH
            return "low", ConfidenceLevel.HIGH

        if reference_high is not None and value > reference_high:
            # Check borderline (within 10%)
            if value <= reference_high * 1.1:
                return "borderline", ConfidenceLevel.HIGH
            return "high", ConfidenceLevel.HIGH

        return "normal", ConfidenceLevel.HIGH

    @staticmethod
    def validate_reference_range(
        reference_text: str,
        test_name: str,
    ) -> Tuple[Optional[float], Optional[float], List[str]]:
        """Parse and validate reference range from report text."""
        warnings = []
        ref_low = None
        ref_high = None

        if not reference_text:
            return None, None, ["No reference range provided"]

        # Common patterns
        patterns = [
            r"(\d+\.?\d*)\s*[-–]\s*(\d+\.?\d*)",  # "12.0 - 15.5"
            r"(\d+\.?\d*)\s*to\s*(\d+\.?\d*)",  # "12.0 to 15.5"
            r"(\d+\.?\d*)\s*±\s*(\d+\.?\d*)",  # "13.5 ± 2.0"
            r"<\s*(\d+\.?\d*)",  # "< 200"
            r">\s*(\d+\.?\d*)",  # "> 40"
            r"up to\s*(\d+\.?\d*)",  # "up to 140"
        ]

        for pattern in patterns:
            match = re.search(pattern, reference_text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    if "±" in reference_text:
                        center = float(groups[0])
                        spread = float(groups[1])
                        ref_low = center - spread
                        ref_high = center + spread
                    else:
                        ref_low = float(groups[0])
                        ref_high = float(groups[1])
                elif len(groups) == 1:
                    if ">" in reference_text or "≥" in reference_text:
                        ref_low = float(groups[0])
                    else:
                        ref_high = float(groups[0])
                break

        if ref_low is None and ref_high is None:
            warnings.append(f"Could not parse reference range: '{reference_text}'")

        return ref_low, ref_high, warnings


class HallucinationDetector:
    """Detect and prevent AI hallucinations in medical context."""

    # Patterns that suggest AI is fabricating data
    HALLUCINATION_PATTERNS = [
        r"\b(likely|probably|certainly|definitely|must be)\b.*\b(disease|condition|disorder)\b",
        r"\b(you have|you are suffering from)\b",
        r"\b(take|prescribe|use)\b.*\b(mg|ml|tablet|capsule)\b",
        r"\b(stop|discontinue|reduce|increase)\b.*\b(medication|medicine|drug)\b",
    ]

    @classmethod
    def check_response(cls, response: str, source_data: Dict) -> Tuple[bool, List[str]]:
        """Check if AI response contains potential hallucinations."""
        warnings = []

        # Check for hallucination patterns
        for pattern in cls.HALLUCINATION_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                warnings.append(f"Potential hallucination detected: pattern '{pattern}'")

        # Check if values mentioned in response match source data
        source_values = set()
        for test in source_data.get("test_results", []):
            if test.get("result") is not None:
                source_values.add(str(test["result"]))
            if test.get("result_text"):
                source_values.add(test["result_text"])

        # Extract numbers from response
        response_numbers = set(re.findall(r"\d+\.?\d*", response))
        for num in response_numbers:
            if num not in source_values and len(num) > 1:
                # Check if this number could be fabricated
                if float(num) > 0 and num not in ["0", "1"]:  # Skip common small numbers
                    warnings.append(
                        f"Value '{num}' in response not found in source data - possible hallucination"
                    )

        is_safe = len(warnings) == 0
        return is_safe, warnings

    @classmethod
    def sanitize_response(cls, response: str) -> str:
        """Remove potentially dangerous content from AI response."""
        # Replace diagnostic language
        replacements = [
            (r"\byou have\b", "The result may be associated with"),
            (r"\byou are suffering from\b", "The findings could be related to"),
            (r"\btake\b\s+\d+\s*(mg|ml)", "[Consult your doctor for dosage]"),
            (r"\bstop\b\s+(taking|your)", "[Do not stop without consulting your doctor]"),
        ]

        sanitized = response
        for pattern, replacement in replacements:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized


class PromptInjectionProtection:
    """Protect against prompt injection in uploaded documents."""

    INJECTION_PATTERNS = [
        r"ignore\s+(previous|all|above)\s+instructions?",
        r"forget\s+(everything|all|previous)",
        r"you\s+are\s+now",
        r"new\s+instructions?:",
        r"system\s+prompt:",
        r"act\s+as\s+(if|a)",
        r"pretend\s+(to\s+be|you\s+are)",
        r"jailbreak",
        r"DAN\s+mode",
        r"developer\s+mode",
    ]

    @classmethod
    def scan_text(cls, text: str) -> Tuple[bool, List[str]]:
        """Scan text for potential prompt injection attempts."""
        warnings = []
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                warnings.append(f"Potential prompt injection pattern detected: '{pattern}'")

        is_safe = len(warnings) == 0
        return is_safe, warnings

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize input to prevent prompt injection."""
        # Wrap document content in clear delimiters
        sanitized = f"[DOCUMENT_CONTENT_START]\n{text}\n[DOCUMENT_CONTENT_END]"
        return sanitized

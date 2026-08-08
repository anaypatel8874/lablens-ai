"""LabLens AI - Validation & Abnormality Detection Service"""
from typing import List, Dict, Any, Optional, Tuple
from app.core.logging import get_logger
from app.schemas.report import TestResultStatus
from app.services.extraction.service import TestDictionary

logger = get_logger(__name__)


class ReferenceRangeDB:
    """Fallback reference ranges when lab range is unavailable.
    These are general population ranges and should NOT override lab-specific ranges."""

    RANGES = {
        "hemoglobin": {"male": (13.5, 17.5), "female": (12.0, 15.5), "unit": "g/dL"},
        "rbc_count": {"male": (4.5, 5.5), "female": (4.0, 5.0), "unit": "millions/µL"},
        "wbc_count": {"default": (4.0, 11.0), "unit": "10^3/µL"},
        "platelet_count": {"default": (150, 450), "unit": "10^3/µL"},
        "hematocrit": {"male": (38.3, 48.6), "female": (35.5, 44.9), "unit": "%"},
        "mcv": {"default": (80.0, 100.0), "unit": "fL"},
        "mch": {"default": (27.0, 33.0), "unit": "pg"},
        "mchc": {"default": (32.0, 36.0), "unit": "g/dL"},
        "rdw": {"default": (11.5, 14.5), "unit": "%"},
        "mpv": {"default": (7.5, 12.5), "unit": "fL"},
        "esr": {"male": (0, 15), "female": (0, 20), "unit": "mm/hr"},

        "fasting_blood_sugar": {"default": (70, 100), "unit": "mg/dL"},
        "random_blood_sugar": {"default": (70, 140), "unit": "mg/dL"},
        "postprandial_blood_sugar": {"default": (70, 140), "unit": "mg/dL"},
        "hba1c": {"default": (4.0, 5.6), "unit": "%"},

        "creatinine": {"male": (0.7, 1.3), "female": (0.6, 1.1), "unit": "mg/dL"},
        "blood_urea": {"default": (7, 20), "unit": "mg/dL"},
        "bun": {"default": (7, 20), "unit": "mg/dL"},
        "uric_acid": {"male": (3.5, 7.2), "female": (2.6, 6.0), "unit": "mg/dL"},
        "egfr": {"default": (90, 120), "unit": "mL/min/1.73m2"},

        "total_bilirubin": {"default": (0.1, 1.2), "unit": "mg/dL"},
        "direct_bilirubin": {"default": (0.0, 0.3), "unit": "mg/dL"},
        "indirect_bilirubin": {"default": (0.1, 0.9), "unit": "mg/dL"},
        "ast": {"default": (10, 40), "unit": "U/L"},
        "alt": {"default": (7, 56), "unit": "U/L"},
        "alp": {"default": (44, 147), "unit": "U/L"},
        "ggt": {"male": (10, 71), "female": (6, 42), "unit": "U/L"},
        "total_protein": {"default": (6.0, 8.3), "unit": "g/dL"},
        "albumin": {"default": (3.5, 5.0), "unit": "g/dL"},
        "globulin": {"default": (2.0, 3.5), "unit": "g/dL"},
        "ag_ratio": {"default": (1.0, 2.2), "unit": "ratio"},

        "total_cholesterol": {"default": (0, 200), "unit": "mg/dL"},
        "hdl_cholesterol": {"male": (40, 100), "female": (50, 100), "unit": "mg/dL"},
        "ldl_cholesterol": {"default": (0, 100), "unit": "mg/dL"},
        "vldl": {"default": (5, 40), "unit": "mg/dL"},
        "triglycerides": {"default": (0, 150), "unit": "mg/dL"},

        "tsh": {"default": (0.4, 4.0), "unit": "µIU/mL"},
        "free_t3": {"default": (2.3, 4.2), "unit": "pg/mL"},
        "free_t4": {"default": (0.8, 1.8), "unit": "ng/dL"},
        "total_t3": {"default": (80, 200), "unit": "ng/dL"},
        "total_t4": {"default": (5.0, 12.0), "unit": "µg/dL"},

        "vitamin_d": {"default": (30, 100), "unit": "ng/mL"},
        "vitamin_b12": {"default": (200, 900), "unit": "pg/mL"},
        "folate": {"default": (3.0, 20.0), "unit": "ng/mL"},

        "serum_iron": {"male": (65, 176), "female": (50, 170), "unit": "µg/dL"},
        "ferritin": {"male": (20, 300), "female": (10, 120), "unit": "ng/mL"},
        "tibc": {"default": (250, 450), "unit": "µg/dL"},
        "transferrin": {"default": (200, 400), "unit": "mg/dL"},
        "transferrin_saturation": {"default": (20, 50), "unit": "%"},

        "sodium": {"default": (135, 145), "unit": "mEq/L"},
        "potassium": {"default": (3.5, 5.0), "unit": "mEq/L"},
        "chloride": {"default": (98, 106), "unit": "mEq/L"},
        "bicarbonate": {"default": (22, 28), "unit": "mEq/L"},
        "calcium": {"default": (8.5, 10.5), "unit": "mg/dL"},

        "pt": {"default": (11, 13.5), "unit": "seconds"},
        "inr": {"default": (0.8, 1.2), "unit": "ratio"},
        "aptt": {"default": (25, 35), "unit": "seconds"},

        "troponin_i": {"default": (0, 0.04), "unit": "ng/L"},
        "troponin_t": {"default": (0, 0.01), "unit": "ng/L"},
        "ck_mb": {"default": (0, 6), "unit": "U/L"},
        "bnp": {"default": (0, 100), "unit": "pg/mL"},
        "nt_probnp": {"default": (0, 300), "unit": "pg/mL"},

        "psa": {"default": (0, 4.0), "unit": "ng/mL"},
        "cea": {"default": (0, 3.0), "unit": "ng/mL"},
        "afp": {"default": (0, 10), "unit": "ng/mL"},
        "ca_125": {"default": (0, 35), "unit": "U/mL"},
        "ca_199": {"default": (0, 37), "unit": "U/mL"},
    }

    CRITICAL_THRESHOLDS = {
        "hemoglobin": {"critically_low": 7.0, "critically_high": 20.0},
        "wbc_count": {"critically_low": 2.0, "critically_high": 30.0},
        "platelet_count": {"critically_low": 50, "critically_high": 1000},
        "fasting_blood_sugar": {"critically_low": 40, "critically_high": 400},
        "random_blood_sugar": {"critically_low": 40, "critically_high": 500},
        "creatinine": {"critically_low": 0.2, "critically_high": 10.0},
        "sodium": {"critically_low": 120, "critically_high": 160},
        "potassium": {"critically_low": 2.5, "critically_high": 6.5},
        "calcium": {"critically_low": 6.0, "critically_high": 13.0},
    }

    @classmethod
    def get_range(
        cls, test_name: str, gender: Optional[str] = None, age: Optional[int] = None
    ) -> Tuple[Optional[float], Optional[float], str]:
        meta = cls.RANGES.get(test_name)
        if not meta:
            return None, None, ""

        unit = meta.get("unit", "")

        # Try gender-specific
        if gender:
            g = gender.lower()
            if g in ["male", "m"] and "male" in meta:
                low, high = meta["male"]
                return low, high, f"{low} - {high} {unit}"
            elif g in ["female", "f"] and "female" in meta:
                low, high = meta["female"]
                return low, high, f"{low} - {high} {unit}"

        # Default
        if "default" in meta:
            low, high = meta["default"]
            return low, high, f"{low} - {high} {unit}"

        return None, None, ""

    @classmethod
    def get_critical_thresholds(cls, test_name: str) -> Dict[str, float]:
        return cls.CRITICAL_THRESHOLDS.get(test_name, {})


class ValidationService:
    def validate_results(
        self,
        results: List[Dict[str, Any]],
        patient_gender: Optional[str] = None,
        patient_age: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Validate and classify extracted results."""
        validated = []

        for result in results:
            validated_result = self._validate_single(result, patient_gender, patient_age)
            validated.append(validated_result)

        return validated

    def _validate_single(
        self,
        result: Dict[str, Any],
        gender: Optional[str],
        age: Optional[int],
    ) -> Dict[str, Any]:
        """Validate a single test result."""
        norm_name = result.get("normalized_test_name")
        value = result.get("result")
        unit = result.get("unit")

        # If no numeric value, check text result
        if value is None and result.get("result_text"):
            result["status"] = self._classify_text_result(result["result_text"])
            return result

        if value is None:
            result["status"] = TestResultStatus.MISSING.value
            result["notes"] = "No readable value found"
            return result

        # Use lab reference range if available
        ref_low = result.get("reference_low")
        ref_high = result.get("reference_high")

        # Fallback to our DB only if lab range missing
        if ref_low is None and ref_high is None and norm_name and norm_name != "UNKNOWN_TEST_REQUIRES_REVIEW":
            ref_low, ref_high, ref_text = ReferenceRangeDB.get_range(norm_name, gender, age)
            if ref_low is not None or ref_high is not None:
                result["reference_low"] = ref_low
                result["reference_high"] = ref_high
                result["reference_text"] = ref_text
                result["notes"] = (result.get("notes") or "") + " [Used general reference range - lab range unavailable]"

        # Classify status
        if norm_name and norm_name != "UNKNOWN_TEST_REQUIRES_REVIEW":
            result["status"] = self._classify_numeric(value, ref_low, ref_high, norm_name, unit)
        else:
            result["status"] = TestResultStatus.UNKNOWN.value

        return result

    def _normalize_value_for_threshold(self, value: float, unit: Optional[str], test_name: str) -> float:
        """Normalize value to match critical threshold units."""
        unit = (unit or "").lower().strip()
        # Thresholds are in 10^3/µL for cell counts
        if test_name in ("wbc_count", "rbc_count", "platelet_count"):
            if unit in ("/cmm", "/mm3", "cells/µl", "cells/cmm"):
                return value / 1000.0
            if unit in ("lakhs/µl",):
                return value * 100.0
        if test_name == "hemoglobin":
            if unit in ("gm%", "gm/dl", "g%"):
                return value  # already in g/dL
        return value

    def _classify_numeric(
        self,
        value: float,
        ref_low: Optional[float],
        ref_high: Optional[float],
        test_name: str,
        unit: Optional[str] = None,
    ) -> str:
        """Classify numeric result against reference range."""
        # Check critical thresholds first (with unit normalization)
        crit = ReferenceRangeDB.get_critical_thresholds(test_name)
        if crit:
            normalized = self._normalize_value_for_threshold(value, unit, test_name)
            if "critically_low" in crit and normalized < crit["critically_low"]:
                return TestResultStatus.CRITICALLY_LOW.value
            if "critically_high" in crit and normalized > crit["critically_high"]:
                return TestResultStatus.CRITICALLY_HIGH.value

        # No reference range available
        if ref_low is None and ref_high is None:
            return TestResultStatus.UNKNOWN.value

        # Check against range
        is_low = ref_low is not None and value < ref_low
        is_high = ref_high is not None and value > ref_high

        if is_low and is_high:
            # Edge case
            return TestResultStatus.UNKNOWN.value

        if is_low:
            # Check borderline (within 10% of lower limit)
            if ref_low and value >= ref_low * 0.9:
                return TestResultStatus.BORDERLINE.value
            return TestResultStatus.LOW.value

        if is_high:
            # Check borderline (within 10% of upper limit)
            if ref_high and value <= ref_high * 1.1:
                return TestResultStatus.BORDERLINE.value
            return TestResultStatus.HIGH.value

        return TestResultStatus.NORMAL.value

    def _classify_text_result(self, text: str) -> str:
        """Classify text-based results."""
        text_lower = text.lower()

        positive_indicators = ["positive", "detected", "reactive", "present", "growth", "abnormal"]
        negative_indicators = ["negative", "not detected", "non-reactive", "absent", "no growth", "normal"]

        if any(p in text_lower for p in positive_indicators):
            # For screening tests, positive is "attention" not "high"
            return TestResultStatus.HIGH.value

        if any(n in text_lower for n in negative_indicators):
            return TestResultStatus.NORMAL.value

        if "equivocal" in text_lower or "borderline" in text_lower:
            return TestResultStatus.BORDERLINE.value

        return TestResultStatus.UNKNOWN.value

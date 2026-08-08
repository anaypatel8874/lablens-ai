"""LabLens AI - Integrated Validation Pipeline"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

from app.services.validation_engine import (
    ClinicalValidator,
    ConfidenceLevel,
    ValidationStatus,
    ExtractedValue,
    HallucinationDetector,
    PromptInjectionProtection,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of the full validation pipeline."""
    success: bool
    extracted_values: List[ExtractedValue]
    validation_summary: Dict[str, Any]
    safety_status: str  # "safe", "warning", "unsafe"
    confidence_overall: ConfidenceLevel
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    ai_safe_response: Optional[str] = None


class MedicalValidationPipeline:
    """
    Zero-hallucination medical data pipeline.
    
    Flow:
    RAW_EXTRACTION → VALUE_VALIDATION → UNIT_VALIDATION → 
    REFERENCE_VALIDATION → CLINICAL_RULES → SAFETY_FILTER → OUTPUT
    """

    def __init__(self):
        self.validator = ClinicalValidator()
        self.hallucination_detector = HallucinationDetector()
        self.injection_protection = PromptInjectionProtection()

    async def process_extraction(
        self,
        raw_extractions: List[Dict[str, Any]],
        report_text: str = "",
        patient_info: Optional[Dict] = None,
    ) -> PipelineResult:
        """Run the full validation pipeline on extracted data."""
        all_warnings = []
        all_errors = []
        extracted_values = []

        # Step 1: Check for prompt injection in raw text
        injection_safe, injection_warnings = self.injection_protection.scan_text(report_text)
        if not injection_safe:
            all_warnings.extend(injection_warnings)
            logger.warning(f"Potential prompt injection detected: {injection_warnings}")

        # Step 2: Validate each extracted value
        high_confidence_count = 0
        low_confidence_count = 0

        for raw in raw_extractions:
            extracted = await self._validate_single_value(raw, patient_info)
            extracted_values.append(extracted)

            if extracted.confidence == ConfidenceLevel.HIGH:
                high_confidence_count += 1
            elif extracted.confidence in (ConfidenceLevel.LOW, ConfidenceLevel.UNREADABLE):
                low_confidence_count += 1

        # Step 3: Cross-validate related tests
        cross_validation_warnings = self._cross_validate(extracted_values)
        all_warnings.extend(cross_validation_warnings)

        # Step 4: Determine overall confidence
        total = len(extracted_values)
        if total == 0:
            overall_confidence = ConfidenceLevel.UNREADABLE
        elif low_confidence_count > total * 0.5:
            overall_confidence = ConfidenceLevel.LOW
        elif high_confidence_count >= total * 0.7:
            overall_confidence = ConfidenceLevel.HIGH
        else:
            overall_confidence = ConfidenceLevel.MEDIUM

        # Step 5: Determine safety status
        if overall_confidence == ConfidenceLevel.LOW:
            safety_status = "warning"
        elif any(v.validation_status == ValidationStatus.CONFLICTING for v in extracted_values):
            safety_status = "unsafe"
        else:
            safety_status = "safe"

        # Build validation summary
        validation_summary = {
            "total_tests": total,
            "high_confidence": high_confidence_count,
            "medium_confidence": total - high_confidence_count - low_confidence_count,
            "low_confidence": low_confidence_count,
            "suspicious_values": [
                v.test_name for v in extracted_values 
                if v.validation_status == ValidationStatus.SUSPICIOUS
            ],
            "conflicting_values": [
                v.test_name for v in extracted_values 
                if v.validation_status == ValidationStatus.CONFLICTING
            ],
        }

        success = overall_confidence != ConfidenceLevel.UNREADABLE

        return PipelineResult(
            success=success,
            extracted_values=extracted_values,
            validation_summary=validation_summary,
            safety_status=safety_status,
            confidence_overall=overall_confidence,
            warnings=all_warnings,
            errors=all_errors,
        )

    async def _validate_single_value(
        self,
        raw: Dict[str, Any],
        patient_info: Optional[Dict] = None,
    ) -> ExtractedValue:
        """Validate a single extracted value through all pipeline stages."""
        warnings = []
        flags = []

        # Extract fields
        test_name = raw.get("test_name", "Unknown")
        original_name = test_name
        value = raw.get("result")
        value_text = raw.get("result_text")
        unit = raw.get("unit")
        ref_text = raw.get("reference_text", "")
        ocr_confidence = raw.get("ocr_confidence", 0.85)

        # Step 1: Normalize test name
        _, normalized = self.validator.normalize_test_name(test_name)

        # Step 2: Parse and validate reference range
        ref_low, ref_high, ref_warnings = self.validator.validate_reference_range(
            ref_text, test_name
        )
        warnings.extend(ref_warnings)

        # Step 3: If we have numeric value, run numeric validations
        validation_result = None
        if value is not None:
            # Numeric plausibility check
            validation_result = self.validator.validate_numeric_plausibility(
                normalized or test_name, value, unit or ""
            )
            warnings.extend(validation_result.warnings)
            flags.extend(validation_result.safety_flags)

            # Unit validation
            unit_valid, unit_warnings = self.validator.validate_unit(
                normalized or test_name, unit or ""
            )
            warnings.extend(unit_warnings)

            # Classify result
            if ref_low is not None or ref_high is not None:
                status, _ = self.validator.classify_result(
                    value, ref_low, ref_high, raw.get("lab_flags", [])
                )
                if status == "critical":
                    flags.append("CRITICAL_VALUE")

        # Determine confidence
        if validation_result:
            confidence = validation_result.confidence
            validation_status = validation_result.status
        elif value is None and value_text:
            confidence = ConfidenceLevel.MEDIUM
            validation_status = ValidationStatus.VALID
        else:
            confidence = ConfidenceLevel.HIGH if ocr_confidence > 0.8 else ConfidenceLevel.MEDIUM
            validation_status = ValidationStatus.VALID

        # Downgrade confidence if unit validation failed
        if warnings and confidence == ConfidenceLevel.HIGH:
            confidence = ConfidenceLevel.MEDIUM

        return ExtractedValue(
            test_name=original_name,
            original_test_name=original_name,
            normalized_test_name=normalized,
            value=value,
            value_text=value_text,
            unit=unit,
            reference_range=ref_text,
            reference_low=ref_low,
            reference_high=ref_high,
            reference_source="report" if ref_text else "missing",
            confidence=confidence,
            validation_status=validation_status,
            ocr_confidence=ocr_confidence,
            source_page=raw.get("source_page"),
            flags=flags,
            warnings=warnings,
        )

    def _cross_validate(self, values: List[ExtractedValue]) -> List[str]:
        """Cross-validate related tests for consistency."""
        warnings = []

        # Build lookup by normalized name
        lookup = {}
        for v in values:
            if v.normalized_test_name:
                lookup[v.normalized_test_name] = v

        # Check CBC consistency
        if "hemoglobin" in lookup and "hematocrit" in lookup:
            hb = lookup["hemoglobin"].value
            hct = lookup["hematocrit"].value
            if hb and hct:
                # HCT should be roughly 3x Hb
                expected_hct = hb * 3
                if abs(hct - expected_hct) > 5:
                    warnings.append(
                        f"Hemoglobin ({hb}) and Hematocrit ({hct}) relationship appears inconsistent"
                    )

        # Check WBC differential sum
        diff_sum = 0
        has_diffs = False
        for diff_name in ["neutrophils", "lymphocytes", "monocytes", "eosinophils", "basophils"]:
            if diff_name in lookup:
                val = lookup[diff_name].value
                if val is not None:
                    diff_sum += val
                    has_diffs = True

        if has_diffs and (diff_sum < 90 or diff_sum > 110):
            warnings.append(
                f"Differential count sum ({diff_sum}%) is outside expected range (90-110%)"
            )

        return warnings

    def validate_ai_response(
        self, response: str, source_data: Dict[str, Any]
    ) -> Tuple[bool, List[str], Optional[str]]:
        """Validate AI-generated response before sending to user."""
        # Run hallucination check
        is_safe, warnings = self.hallucination_detector.check_response(
            response, source_data
        )

        # Sanitize if needed
        if not is_safe:
            sanitized = self.hallucination_detector.sanitize_response(response)
            return False, warnings, sanitized

        return True, [], response


# Singleton instance
pipeline = MedicalValidationPipeline()

"""LabLens AI - Medical Report Extraction Service"""
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.report import TestResultCreate, TestResultStatus
from app.services.ocr.service import OCRService
from app.services.document.processor import DocumentProcessor

logger = get_logger(__name__)
settings = get_settings()


class TestDictionary:
    """Centralized laboratory test dictionary with synonyms and metadata."""

    TESTS = {
        # Hematology
        "hemoglobin": {
            "synonyms": ["hb", "hgb", "haemoglobin"],
            "category": "hematology",
            "units": ["g/dL", "g/dl", "gm/dL", "gm%", "g%"],
        },
        "rbc_count": {
            "synonyms": ["rbc", "red blood cell count", "erythrocyte count"],
            "category": "hematology",
            "units": ["millions/µL", "x10^6/µL", "10^6/µL"],
        },
        "wbc_count": {
            "synonyms": ["wbc", "tlc", "total leukocyte count", "white blood cell count"],
            "category": "hematology",
            "units": ["10^3/µL", "x10^3/µL", "cells/µL", "/cmm", "/mm3"],
        },
        "platelet_count": {
            "synonyms": ["plt", "platelets"],
            "category": "hematology",
            "units": ["10^3/µL", "x10^3/µL", "lakhs/µL"],
        },
        "hematocrit": {
            "synonyms": ["hct", "pcv", "packed cell volume"],
            "category": "hematology",
            "units": ["%", "vol%"],
        },
        "mcv": {
            "synonyms": ["mean corpuscular volume"],
            "category": "hematology",
            "units": ["fL", "fl"],
        },
        "mch": {
            "synonyms": ["mean corpuscular hemoglobin"],
            "category": "hematology",
            "units": ["pg", "pico grams"],
        },
        "mchc": {
            "synonyms": ["mean corpuscular hemoglobin concentration"],
            "category": "hematology",
            "units": ["g/dL", "g/dl"],
        },
        "rdw": {
            "synonyms": ["red cell distribution width"],
            "category": "hematology",
            "units": ["%", "fL"],
        },
        "mpv": {
            "synonyms": ["mean platelet volume"],
            "category": "hematology",
            "units": ["fL", "fl"],
        },
        "esr": {
            "synonyms": ["erythrocyte sedimentation rate"],
            "category": "hematology",
            "units": ["mm/hr", "mm/hour", "mm/1st hour"],
        },
        # Biochemistry - Glucose
        "fasting_blood_sugar": {
            "synonyms": ["fbs", "fasting glucose", "fasting blood sugar", "fasting plasma glucose"],
            "category": "diabetes",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "random_blood_sugar": {
            "synonyms": ["rbs", "random glucose", "random blood sugar"],
            "category": "diabetes",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "postprandial_blood_sugar": {
            "synonyms": ["ppbs", "pp glucose", "postprandial glucose"],
            "category": "diabetes",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "hba1c": {
            "synonyms": ["glycated hemoglobin", "a1c", "hb a1c"],
            "category": "diabetes",
            "units": ["%", "mmol/mol"],
        },
        # Renal
        "creatinine": {
            "synonyms": ["serum creatinine", "s. creatinine"],
            "category": "kidney",
            "units": ["mg/dL", "mg/dl", "µmol/L", "umol/L"],
        },
        "blood_urea": {
            "synonyms": ["urea", "s. urea", "serum urea"],
            "category": "kidney",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "bun": {
            "synonyms": ["blood urea nitrogen"],
            "category": "kidney",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "uric_acid": {
            "synonyms": ["s. uric acid", "serum uric acid"],
            "category": "kidney",
            "units": ["mg/dL", "mg/dl", "µmol/L", "umol/L"],
        },
        "egfr": {
            "synonyms": ["estimated gfr", "gfr"],
            "category": "kidney",
            "units": ["mL/min/1.73m2", "ml/min"],
        },
        # Liver
        "total_bilirubin": {
            "synonyms": ["t. bilirubin", "serum bilirubin total"],
            "category": "liver",
            "units": ["mg/dL", "mg/dl", "µmol/L"],
        },
        "direct_bilirubin": {
            "synonyms": ["d. bilirubin", "conjugated bilirubin"],
            "category": "liver",
            "units": ["mg/dL", "mg/dl", "µmol/L"],
        },
        "indirect_bilirubin": {
            "synonyms": ["i. bilirubin", "unconjugated bilirubin"],
            "category": "liver",
            "units": ["mg/dL", "mg/dl", "µmol/L"],
        },
        "ast": {
            "synonyms": ["sgot", "aspartate aminotransferase", "s. got"],
            "category": "liver",
            "units": ["U/L", "u/l", "IU/L"],
        },
        "alt": {
            "synonyms": ["sgpt", "alanine aminotransferase", "s. gpt"],
            "category": "liver",
            "units": ["U/L", "u/l", "IU/L"],
        },
        "alp": {
            "synonyms": ["alkaline phosphatase", "s. alkaline phosphatase"],
            "category": "liver",
            "units": ["U/L", "u/l", "IU/L"],
        },
        "ggt": {
            "synonyms": ["gamma gt", "gamma glutamyl transferase", "sggt"],
            "category": "liver",
            "units": ["U/L", "u/l", "IU/L"],
        },
        "total_protein": {
            "synonyms": ["t. protein", "serum total protein"],
            "category": "liver",
            "units": ["g/dL", "g/dl", "g/L"],
        },
        "albumin": {
            "synonyms": ["serum albumin", "s. albumin"],
            "category": "liver",
            "units": ["g/dL", "g/dl", "g/L"],
        },
        "globulin": {
            "synonyms": ["serum globulin"],
            "category": "liver",
            "units": ["g/dL", "g/dl", "g/L"],
        },
        "ag_ratio": {
            "synonyms": ["a/g ratio", "albumin globulin ratio"],
            "category": "liver",
            "units": ["ratio", ":1"],
        },
        # Lipid
        "total_cholesterol": {
            "synonyms": ["t. cholesterol", "serum cholesterol", "cholesterol total"],
            "category": "lipid",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "hdl_cholesterol": {
            "synonyms": ["hdl", "hdl-c", "good cholesterol"],
            "category": "lipid",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "ldl_cholesterol": {
            "synonyms": ["ldl", "ldl-c", "bad cholesterol"],
            "category": "lipid",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "vldl": {
            "synonyms": ["vldl cholesterol"],
            "category": "lipid",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "triglycerides": {
            "synonyms": ["tg", "serum triglycerides"],
            "category": "lipid",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        # Thyroid
        "tsh": {
            "synonyms": ["thyroid stimulating hormone", "s. tsh"],
            "category": "thyroid",
            "units": ["µIU/mL", "uiu/ml", "mIU/L", "miu/l"],
        },
        "free_t3": {
            "synonyms": ["ft3", "t3 free"],
            "category": "thyroid",
            "units": ["pg/mL", "pg/ml", "pmol/L"],
        },
        "free_t4": {
            "synonyms": ["ft4", "t4 free"],
            "category": "thyroid",
            "units": ["ng/dL", "ng/dl", "pmol/L"],
        },
        "total_t3": {
            "synonyms": ["tt3", "t3 total"],
            "category": "thyroid",
            "units": ["ng/dL", "ng/dl", "nmol/L"],
        },
        "total_t4": {
            "synonyms": ["tt4", "t4 total"],
            "category": "thyroid",
            "units": ["µg/dL", "ug/dl", "nmol/L"],
        },
        # Vitamins
        "vitamin_d": {
            "synonyms": ["25-oh vitamin d", "25 hydroxy vitamin d", "vit d", "vitamin d3", "vitamin d2"],
            "category": "vitamin",
            "units": ["ng/mL", "ng/ml", "nmol/L"],
        },
        "vitamin_b12": {
            "synonyms": ["b12", "cyanocobalamin", "s. b12"],
            "category": "vitamin",
            "units": ["pg/mL", "pg/ml", "pmol/L"],
        },
        "folate": {
            "synonyms": ["folic acid", "s. folate", "vitamin b9"],
            "category": "vitamin",
            "units": ["ng/mL", "ng/ml", "nmol/L"],
        },
        # Iron
        "serum_iron": {
            "synonyms": ["iron", "s. iron", "serum iron"],
            "category": "iron",
            "units": ["µg/dL", "ug/dl", "µmol/L", "umol/L"],
        },
        "ferritin": {
            "synonyms": ["serum ferritin", "s. ferritin"],
            "category": "iron",
            "units": ["ng/mL", "ng/ml", "µg/L"],
        },
        "tibc": {
            "synonyms": ["total iron binding capacity"],
            "category": "iron",
            "units": ["µg/dL", "ug/dl", "µmol/L"],
        },
        "transferrin": {
            "synonyms": ["s. transferrin"],
            "category": "iron",
            "units": ["mg/dL", "mg/dl", "g/L"],
        },
        "transferrin_saturation": {
            "synonyms": ["tsat", "iron saturation"],
            "category": "iron",
            "units": ["%"],
        },
        # Electrolytes
        "sodium": {
            "synonyms": ["na+", "serum sodium", "s. sodium", "na"],
            "category": "electrolyte",
            "units": ["mEq/L", "meq/l", "mmol/L"],
        },
        "potassium": {
            "synonyms": ["k+", "serum potassium", "s. potassium", "k"],
            "category": "electrolyte",
            "units": ["mEq/L", "meq/l", "mmol/L"],
        },
        "chloride": {
            "synonyms": ["cl-", "serum chloride", "s. chloride", "cl"],
            "category": "electrolyte",
            "units": ["mEq/L", "meq/l", "mmol/L"],
        },
        "bicarbonate": {
            "synonyms": ["hco3", "co2", "total co2"],
            "category": "electrolyte",
            "units": ["mEq/L", "meq/l", "mmol/L"],
        },
        "calcium": {
            "synonyms": ["serum calcium", "s. calcium", "ca"],
            "category": "electrolyte",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        # Urine
        "urine_protein": {
            "synonyms": ["urine albumin", "urinary protein"],
            "category": "urine",
            "units": ["mg/dL", "mg/dl", "g/L", "mg/24h"],
        },
        "urine_glucose": {
            "synonyms": ["urinary glucose", "sugar in urine"],
            "category": "urine",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        "urine_ketones": {
            "synonyms": ["ketone bodies", "urinary ketones"],
            "category": "urine",
            "units": ["mg/dL", "mg/dl", "mmol/L"],
        },
        # Coagulation
        "pt": {
            "synonyms": ["prothrombin time"],
            "category": "coagulation",
            "units": ["seconds", "sec", "s"],
        },
        "inr": {
            "synonyms": ["international normalized ratio"],
            "category": "coagulation",
            "units": ["ratio"],
        },
        "aptt": {
            "synonyms": ["ptt", "activated partial thromboplastin time"],
            "category": "coagulation",
            "units": ["seconds", "sec", "s"],
        },
        # Cardiac
        "troponin_i": {
            "synonyms": ["ctni", "cardiac troponin i"],
            "category": "cardiac",
            "units": ["ng/L", "ng/ml", "µg/L"],
        },
        "troponin_t": {
            "synonyms": ["ctnt", "cardiac troponin t"],
            "category": "cardiac",
            "units": ["ng/L", "ng/ml", "µg/L"],
        },
        "ck_mb": {
            "synonyms": ["creatine kinase mb", "cpk mb"],
            "category": "cardiac",
            "units": ["U/L", "u/l", "IU/L", "ng/mL"],
        },
        "bnp": {
            "synonyms": ["b-type natriuretic peptide"],
            "category": "cardiac",
            "units": ["pg/mL", "pg/ml", "pmol/L"],
        },
        "nt_probnp": {
            "synonyms": ["n-terminal probnp"],
            "category": "cardiac",
            "units": ["pg/mL", "pg/ml", "pmol/L"],
        },
        # Tumor Markers
        "psa": {
            "synonyms": ["prostate specific antigen", "total psa"],
            "category": "tumor_marker",
            "units": ["ng/mL", "ng/ml", "µg/L"],
        },
        "cea": {
            "synonyms": ["carcinoembryonic antigen"],
            "category": "tumor_marker",
            "units": ["ng/mL", "ng/ml", "µg/L"],
        },
        "afp": {
            "synonyms": ["alpha fetoprotein", "alpha-fetoprotein"],
            "category": "tumor_marker",
            "units": ["ng/mL", "ng/ml", "µg/L", "IU/mL"],
        },
        "ca_125": {
            "synonyms": ["cancer antigen 125", "ca125"],
            "category": "tumor_marker",
            "units": ["U/mL", "u/ml", "kU/L"],
        },
        "ca_199": {
            "synonyms": ["cancer antigen 19-9", "ca19-9"],
            "category": "tumor_marker",
            "units": ["U/mL", "u/ml", "kU/L"],
        },
    }

    @classmethod
    def normalize_name(cls, raw_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Normalize a test name. Returns (normalized_name, category)."""
        raw_lower = raw_name.lower().strip()

        for normalized, meta in cls.TESTS.items():
            if raw_lower == normalized.replace("_", " "):
                return normalized, meta["category"]
            for syn in meta["synonyms"]:
                if raw_lower == syn.lower() or raw_lower in syn.lower():
                    return normalized, meta["category"]

        return None, None

    @classmethod
    def get_category(cls, normalized_name: str) -> Optional[str]:
        meta = cls.TESTS.get(normalized_name)
        return meta["category"] if meta else None


class ExtractionService:
    def __init__(self):
        self.ocr_service = OCRService()
        self.doc_processor = DocumentProcessor()

    async def extract_from_document(
        self, file_bytes: bytes, mime_type: str
    ) -> Dict[str, Any]:
        """Main extraction pipeline."""
        logger.info("Starting document extraction", mime_type=mime_type)

        extraction_data = {
            "patient_info": {},
            "test_results": [],
            "report_metadata": {},
            "quality_issues": [],
            "ocr_confidence": 0.0,
        }

        if mime_type == "application/pdf":
            # Try text extraction first
            text_pages = self.doc_processor.extract_pdf_text(file_bytes)
            if text_pages and any(text for _, text in text_pages):
                for page_num, text in text_pages:
                    page_results = self._parse_text_page(text, page_num)
                    extraction_data["test_results"].extend(page_results)
                extraction_data["ocr_confidence"] = 0.95  # High confidence for native PDF text
            else:
                # Fallback to OCR
                images = self.doc_processor.convert_pdf_to_images(file_bytes)
                conf = 0.0
                for page_num, img_bytes in images:
                    preprocessed = self.doc_processor.preprocess_image(img_bytes)
                    text, page_conf = self.ocr_service.extract_text(preprocessed)
                    page_results = self._parse_text_page(text, page_num)
                    extraction_data["test_results"].extend(page_results)
                    conf = max(conf, page_conf)
                extraction_data["ocr_confidence"] = conf
        else:
            # Image file
            preprocessed = self.doc_processor.preprocess_image(file_bytes)

            # Quality checks
            is_blurry, blur_score = self.doc_processor.detect_blur(preprocessed)
            if is_blurry:
                extraction_data["quality_issues"].append(
                    f"Image appears blurry (score: {blur_score:.1f}). Please upload a clearer image."
                )

            is_cropped, crop_msg = self.doc_processor.detect_cropped_report(preprocessed)
            if is_cropped:
                extraction_data["quality_issues"].append(crop_msg)

            text, conf = self.ocr_service.extract_text(preprocessed)
            extraction_data["ocr_confidence"] = conf

            if conf < 0.5:
                extraction_data["quality_issues"].append(
                    "Low OCR confidence. Some values may be unreadable."
                )

            page_results = self._parse_text_page(text, 1)
            extraction_data["test_results"].extend(page_results)

        # Normalize and validate
        for result in extraction_data["test_results"]:
            norm_name, category = TestDictionary.normalize_name(result["test_name"])
            if norm_name:
                result["normalized_test_name"] = norm_name
                result["category"] = category or result.get("category", "other")
            else:
                result["normalized_test_name"] = "UNKNOWN_TEST_REQUIRES_REVIEW"
                result["category"] = "other"

        logger.info(
            "Extraction complete",
            result_count=len(extraction_data["test_results"]),
            confidence=extraction_data["ocr_confidence"],
        )

        return extraction_data

    def _parse_text_page(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """Parse extracted text into structured test results."""
        results = []
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # Known table header patterns to skip
        skip_patterns = [
            "^test$", "^result$", "^unit$", "^reference$", "^reference range$",
            "^normal range$", "^range$", "^units$",
        ]
        skip_pattern = re.compile("|".join(skip_patterns), re.IGNORECASE)

        # Known section headers (not test names)
        section_headers = [
            "complete blood count", "cbc", "lipid profile", "liver function",
            "kidney function", "thyroid", "glucose", "hba1c", "vitamin",
            "iron", "urine", "coagulation", "cardiac", "electrolyte",
        ]

        i = 0
        while i < len(lines):
            line = lines[i]

            # Skip table headers and section headers
            if skip_pattern.match(line) or line.lower().strip() in section_headers:
                i += 1
                continue

            # Try single-line parse first
            parsed = self._parse_test_line(line)
            if parsed:
                parsed["source_page"] = page_num
                parsed["source_text"] = line
                results.append(parsed)
                i += 1
                continue

            # Try multi-line table format: Test Name \n Value \n Unit \n RefRange
            if i + 1 < len(lines) and self._looks_like_test_name(line):
                # Combine next few lines
                combined_parts = [line]
                j = i + 1
                while j < len(lines) and j < i + 5:
                    next_line = lines[j]
                    if skip_pattern.match(next_line) or self._looks_like_test_name(next_line):
                        break
                    combined_parts.append(next_line)
                    j += 1

                combined = " ".join(combined_parts)
                parsed = self._parse_test_line(combined)
                if parsed:
                    parsed["source_page"] = page_num
                    parsed["source_text"] = combined
                    results.append(parsed)
                    i = j
                    continue

            i += 1

        return results

    def _looks_like_test_name(self, line: str) -> bool:
        """Check if a line looks like it could be a test name (not a number/unit)."""
        line = line.strip()
        if not line or len(line) < 2:
            return False
        # Skip pure numbers
        if re.match(r"^[-]?\d+\.?\d*$", line):
            return False
        # Skip pure units
        unit_only = re.compile(r"^(gm%|gm/dL|mg/dL|g/dL|U/L|IU/L|mEq/L|mmol/L|ng/mL|pg/mL|fL|%|ratio|seconds|mm/hr|/cmm|/mm3|millions/µL|x10\^3/µL|10\^3/µL|mL/min|cells/µL|cells/cmm)$", re.IGNORECASE)
        if unit_only.match(line):
            return False
        # Skip reference ranges
        if re.match(r"^[\(\[]?\s*\d+\.?\d*\s*[-–]\s*\d+\.?\d*\s*[\)\]]?$", line):
            return False
        return True

    def _parse_test_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single line into test result components."""
        # Common patterns for lab reports
        # Pattern: Test Name ... Value Unit RefRange
        # Handles various formats

        # Remove extra spaces
        line = " ".join(line.split())

        # Try to find numeric value
        number_pattern = r"([-]?\d+\.?\d*)\s*(gm%|gm/dL|gm/dl|g%|mg/dL|mg/dl|g/dL|g/dl|U/L|u/l|IU/L|mEq/L|meq/l|mmol/L|ng/mL|ng/ml|pg/mL|pg/ml|µIU/mL|uiu/ml|mIU/L|miu/l|fL|fl|pg|%|ratio|seconds|sec|mm/hr|mm/hour|10\^3/µL|x10\^3/µL|millions/µL|x10\^6/µL|/cmm|/mm3|lakhs/µL|µmol/L|umol/L|nmol/L|pmol/L|µg/dL|ug/dl|µg/L|ng/L|g/L|kU/L|U/mL|u/ml|mL/min|mL/min/1\.73m2|cells/µL|cells/cmm|million/cmm|thousand/cmm|yrs|years|mg|µg|ng|ml|dL|L)"

        match = re.search(number_pattern, line, re.IGNORECASE)
        if not match:
            # Try to detect text-only results (Positive/Negative/Detected/etc)
            text_result = self._extract_text_result(line)
            if text_result:
                return text_result
            return None

        value_str = match.group(1)
        unit = match.group(2)

        try:
            value = float(value_str)
        except ValueError:
            value = None

        # Split line around the value to get test name and reference range
        value_pos = match.start()
        test_name_part = line[:value_pos].strip()
        remainder = line[match.end():].strip()

        # Clean test name
        test_name = self._clean_test_name(test_name_part)
        if not test_name or len(test_name) < 2:
            return None

        # Extract reference range from remainder
        ref_low, ref_high, ref_text = self._extract_reference_range(remainder)

        # Extract lab flag
        lab_flag = self._extract_lab_flag(remainder)

        return {
            "test_name": test_name,
            "normalized_test_name": None,
            "category": "other",
            "result": value,
            "result_text": value_str if value is None else None,
            "unit": unit,
            "reference_low": ref_low,
            "reference_high": ref_high,
            "reference_text": ref_text,
            "lab_flag": lab_flag,
            "status": "unknown",
            "report_date": None,
            "source_page": None,
            "source_text": line,
            "ocr_confidence": 0.0,
            "interpretation_confidence": 0.0,
            "notes": "",
        }

    def _extract_text_result(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract non-numeric results like Positive/Negative/Detected."""
        text_results = ["positive", "negative", "detected", "not detected", 
                        "reactive", "non-reactive", "equivocal", "borderline",
                        "normal", "abnormal", "present", "absent", "growth", "no growth"]

        line_lower = line.lower()
        for tr in text_results:
            if tr in line_lower:
                # Find test name (text before the result)
                pos = line_lower.find(tr)
                test_name = self._clean_test_name(line[:pos].strip())
                if test_name:
                    return {
                        "test_name": test_name,
                        "normalized_test_name": None,
                        "category": "other",
                        "result": None,
                        "result_text": tr.upper(),
                        "unit": "",
                        "reference_low": None,
                        "reference_high": None,
                        "reference_text": "",
                        "lab_flag": "",
                        "status": "unknown",
                        "report_date": None,
                        "source_page": None,
                        "source_text": line,
                        "ocr_confidence": 0.0,
                        "interpretation_confidence": 0.0,
                        "notes": "",
                    }
        return None

    def _clean_test_name(self, text: str) -> str:
        """Clean and normalize test name from extracted text."""
        # Remove common artifacts
        text = re.sub(r"^[^a-zA-Z]*", "", text)
        text = re.sub(r"[:\-\.]+$", "", text)
        text = text.strip()

        # Remove common prefixes that are not part of name
        prefixes = ["test", "investigation", "parameter", "result"]
        for prefix in prefixes:
            if text.lower().startswith(prefix):
                text = text[len(prefix):].strip()

        return text

    def _extract_reference_range(self, text: str) -> Tuple[Optional[float], Optional[float], str]:
        """Extract reference range from text."""
        patterns = [
            (r"[\(\[]?\s*([0-9.]+)\s*[-–]\s*([0-9.]+)\s*[\)\]]?", "range"),
            (r"ref[\s\.:]*[\(\[]?\s*([0-9.]+)\s*[-–]\s*([0-9.]+)\s*[\)\]]?", "range"),
            (r"reference[\s\.:]*[\(\[]?\s*([0-9.]+)\s*[-–]\s*([0-9.]+)\s*[\)\]]?", "range"),
            (r"normal[\s\.:]*[\(\[]?\s*([0-9.]+)\s*[-–]\s*([0-9.]+)\s*[\)\]]?", "range"),
            (r"up to[\s\.:]*([0-9.]+)", "max"),
            (r"<\s*([0-9.]+)\s*[HL]?", "max"),
            (r"≤\s*([0-9.]+)", "max"),
            (r">\s*([0-9.]+)\s*[HL]?", "min"),
            (r"≥\s*([0-9.]+)", "min"),
        ]

        for pattern, kind in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if kind == "range" and len(groups) == 2:
                    try:
                        low = float(groups[0])
                        high = float(groups[1])
                        return low, high, f"{low} - {high}"
                    except ValueError:
                        continue
                elif kind == "max":
                    try:
                        val = float(groups[0])
                        return None, val, f"< {val}"
                    except ValueError:
                        continue
                elif kind == "min":
                    try:
                        val = float(groups[0])
                        return val, None, f"> {val}"
                    except ValueError:
                        continue

        return None, None, ""

    def _extract_lab_flag(self, text: str) -> str:
        """Extract lab flag (H, L, *, etc)."""
        flags = ["high", "low", "h", "l", "*", "**", "***", "abnormal", "critical"]
        text_lower = text.lower()
        for flag in flags:
            if flag in text_lower:
                return flag.upper()
        return ""

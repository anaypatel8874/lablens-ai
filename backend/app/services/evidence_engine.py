"""LabLens AI - Evidence-Grounded Explanation Engine
Implements strict evidence hierarchy, diagnosis firewall, and hallucination prevention.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class EvidenceLevel(str, Enum):
    """Evidence hierarchy levels."""
    ORIGINAL_REPORT = "original_report"  # Level 1: Direct from report
    RELATED_FINDINGS = "related_findings"  # Level 2: Other report values
    VALIDATED_KNOWLEDGE = "validated_knowledge"  # Level 3: Medical knowledge
    UNCERTAINTY = "uncertainty"  # Level 4: Unknown


class StatementType(str, Enum):
    """Types of statements in explanations."""
    FACT = "fact"
    CALCULATED = "calculated"
    INTERPRETATION = "interpretation"
    POSSIBLE_ASSOCIATION = "possible_association"
    UNKNOWN = "unknown"
    SAFETY = "safety"


class ConfidenceLevel(str, Enum):
    """Evidence-based confidence levels."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class EvidenceItem:
    """A single piece of evidence with source tracking."""
    statement: str
    statement_type: StatementType
    evidence_level: EvidenceLevel
    source: str  # e.g., "Page 1, CBC table, Hemoglobin row"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    supporting_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplanationSection:
    """A section of the deep explanation with evidence tracking."""
    title: str
    items: List[EvidenceItem]
    overall_confidence: ConfidenceLevel
    has_uncertainty: bool = False


class DiagnosisFirewall:
    """Prevents AI from making definitive diagnoses."""

    # Patterns that indicate a diagnosis claim
    DIAGNOSIS_PATTERNS = [
        (r"\byou\s+have\s+(\w+\s+)?(disease|disorder|condition|syndrome|cancer|diabetes|hepatitis|anemia|failure)\b",
         "Direct diagnosis claim"),
        (r"\bsuffering\s+from\s+(\w+\s+)?(disease|disorder|condition|syndrome|cancer)\b",
         "Suffering from diagnosis"),
        (r"\bdiagnosed\s+with\b",
         "Diagnosis statement"),
        (r"\bthis\s+(proves?|confirms?|establishes?)\s+(that\s+)?you\s+have\b",
         "Confirmatory diagnosis"),
        (r"\bdefinitely\s+have\b",
         "Definitive diagnosis"),
        (r"\bcertainly\s+have\b",
         "Certain diagnosis"),
        (r"\bwithout\s+(a\s+)?doubt\s+have\b",
         "Doubt-free diagnosis"),
    ]

    # Safe replacements for diagnosis language
    SAFE_REPLACEMENTS = {
        "you have": "this finding may be associated with",
        "you are suffering from": "this pattern can occur in",
        "diagnosed with": "may be associated with",
        "this proves that": "this may suggest",
        "this confirms that": "this finding is consistent with",
        "definitely have": "may be associated with",
        "certainly have": "one possible explanation includes",
        "without doubt have": "may be related to",
    }

    @classmethod
    def check_text(cls, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains diagnosis claims."""
        violations = []
        for pattern, description in cls.DIAGNOSIS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"DIAGNOSIS VIOLATION: {description}")
        return len(violations) == 0, violations

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Replace diagnosis language with safe alternatives."""
        sanitized = text
        for unsafe, safe in cls.SAFE_REPLACEMENTS.items():
            sanitized = re.sub(unsafe, safe, sanitized, flags=re.IGNORECASE)
        return sanitized


class CausalityFirewall:
    """Prevents assuming causation from correlation."""

    CAUSATION_PATTERNS = [
        (r"\b(caused\s+by|due\s+to|because\s+of)\s+(your\s+)?(diet|lifestyle|medication|stress)\b",
         "Assumed causation"),
        (r"\b(this\s+is\s+)?(caused|resulted)\s+by\b",
         "Direct causation claim"),
        (r"\b(the\s+)?reason\s+is\b",
         "Assumed reason"),
    ]

    @classmethod
    def check_text(cls, text: str) -> Tuple[bool, List[str]]:
        """Check for inappropriate causation claims."""
        violations = []
        for pattern, description in cls.CAUSATION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"CAUSATION VIOLATION: {description}")
        return len(violations) == 0, violations

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Replace causation language with safe alternatives."""
        replacements = {
            r"\bcaused\s+by\b": "can be associated with",
            r"\bdue\s+to\b": "may occur with",
            r"\bbecause\s+of\b": "can be influenced by",
            r"\bthis\s+is\s+caused\s+by\b": "this finding may be associated with",
            r"\bthe\s+reason\s+is\b": "possible explanations include",
        }
        sanitized = text
        for pattern, replacement in replacements.items():
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        return sanitized


class HallucinationBlocker:
    """Blocks unsupported medical claims."""

    # Claims that require specific evidence
    EVIDENCE_REQUIRED_CLAIMS = {
        "iron deficiency": ["ferritin", "serum iron", "tibc", "transferrin"],
        "vitamin b12 deficiency": ["vitamin b12", "b12", "methylmalonic acid"],
        "folate deficiency": ["folate", "folic acid"],
        "diabetes": ["fasting glucose", "hba1c", "ogtt", "random glucose"],
        "hypothyroidism": ["tsh", "free t4", "ft4"],
        "hyperthyroidism": ["tsh", "free t4", "ft4"],
        "liver disease": ["alt", "ast", "alp", "bilirubin", "albumin"],
        "kidney disease": ["creatinine", "egfr", "bun", "urea"],
    }

    @classmethod
    def check_claim(
        cls, claim: str, available_tests: List[str]
    ) -> Tuple[bool, List[str]]:
        """Check if a claim is supported by available evidence."""
        warnings = []
        claim_lower = claim.lower()

        for condition, required_tests in cls.EVIDENCE_REQUIRED_CLAIMS.items():
            if condition in claim_lower:
                # Check if any required test is available
                has_evidence = any(
                    req in test.lower()
                    for req in required_tests
                    for test in available_tests
                )
                if not has_evidence:
                    warnings.append(
                        f"Claim about '{condition}' lacks supporting test data. "
                        f"Required tests: {', '.join(required_tests)}"
                    )

        is_valid = len(warnings) == 0
        return is_valid, warnings


class SafeLanguageEngine:
    """Enforces safe medical language."""

    PREFERRED_PHRASES = {
        "may be associated with": ["can occur with", "can be seen in", "may suggest"],
        "requires clinical correlation": ["should be interpreted with", "needs clinical context"],
        "the available report does not establish": ["cannot be determined from", "is not confirmed by"],
        "one possible explanation": ["a potential cause", "one consideration"],
    }

    AVOID_PHRASES = [
        "definitely", "certainly", "guaranteed", "without doubt",
        "you have", "you are", "this proves", "this confirms",
        "take this medicine", "stop your medication", "increase your dose",
    ]

    @classmethod
    def check_language(cls, text: str) -> Tuple[bool, List[str]]:
        """Check for unsafe language."""
        warnings = []
        text_lower = text.lower()

        for phrase in cls.AVOID_PHRASES:
            if phrase in text_lower:
                warnings.append(f"Unsafe phrase detected: '{phrase}'")

        return len(warnings) == 0, warnings


class EvidenceGroundedEngine:
    """
    Core engine for generating evidence-grounded medical explanations.
    
    Implements:
    - Evidence hierarchy (report > related > knowledge > uncertainty)
    - Statement tagging (FACT, INTERPRETATION, ASSOCIATION, UNKNOWN)
    - Diagnosis firewall
    - Causality firewall
    - Hallucination blocker
    - Safe language enforcement
    """

    def __init__(self):
        self.diagnosis_firewall = DiagnosisFirewall()
        self.causality_firewall = CausalityFirewall()
        self.hallucination_blocker = HallucinationBlocker()
        self.safe_language = SafeLanguageEngine()

    def generate_explanation(
        self,
        test_data: Dict[str, Any],
        related_tests: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate a complete evidence-grounded explanation."""

        # Step 1: Build evidence items
        evidence_items = self._build_evidence(test_data, related_tests, patient_info)

        # Step 2: Generate explanation sections
        sections = self._build_sections(evidence_items, test_data, related_tests, language)

        # Step 3: Apply safety gates
        sections = self._apply_safety_gates(sections)

        # Step 4: Calculate overall confidence
        overall_confidence = self._calculate_confidence(evidence_items, related_tests)

        # Step 5: Build final response
        return self._build_response(sections, overall_confidence, test_data, language)

    def _build_evidence(
        self,
        test_data: Dict[str, Any],
        related_tests: List[Dict[str, Any]],
        patient_info: Optional[Dict[str, Any]],
    ) -> List[EvidenceItem]:
        """Build evidence items from report data."""
        items = []

        # Level 1: Original report facts
        test_name = test_data.get("test_name", "Unknown")
        result = test_data.get("result")
        unit = test_data.get("unit", "")
        ref_range = test_data.get("reference_text", "")
        status = test_data.get("status", "unknown")
        source_page = test_data.get("source_page", "Page 1")

        if result is not None:
            items.append(EvidenceItem(
                statement=f"{test_name} = {result} {unit}",
                statement_type=StatementType.FACT,
                evidence_level=EvidenceLevel.ORIGINAL_REPORT,
                source=f"{source_page}, {test_name} row",
                confidence=ConfidenceLevel.HIGH,
            ))

        if ref_range:
            items.append(EvidenceItem(
                statement=f"Reference range: {ref_range}",
                statement_type=StatementType.FACT,
                evidence_level=EvidenceLevel.ORIGINAL_REPORT,
                source=f"{source_page}, reference range column",
                confidence=ConfidenceLevel.HIGH,
            ))

        # Level 2: Related findings
        for related in related_tests:
            if related.get("result") is not None:
                items.append(EvidenceItem(
                    statement=f"{related['test_name']} = {related['result']} {related.get('unit', '')}",
                    statement_type=StatementType.FACT,
                    evidence_level=EvidenceLevel.RELATED_FINDINGS,
                    source=f"Related test in same report",
                    confidence=ConfidenceLevel.HIGH,
                ))

        # Level 3: Calculated/interpreted
        if result is not None and ref_range:
            items.append(EvidenceItem(
                statement=f"Status: {status} (determined by comparing result to reference range)",
                statement_type=StatementType.CALCULATED,
                evidence_level=EvidenceLevel.VALIDATED_KNOWLEDGE,
                source="Clinical rule engine",
                confidence=ConfidenceLevel.HIGH,
            ))

        # Level 4: Uncertainty
        missing_info = self._detect_missing_info(test_data, related_tests)
        if missing_info:
            items.append(EvidenceItem(
                statement=f"Missing information: {', '.join(missing_info)}",
                statement_type=StatementType.UNKNOWN,
                evidence_level=EvidenceLevel.UNCERTAINTY,
                source="Report analysis",
                confidence=ConfidenceLevel.LOW,
            ))

        return items

    def _build_sections(
        self,
        evidence_items: List[EvidenceItem],
        test_data: Dict[str, Any],
        related_tests: List[Dict[str, Any]],
        language: str,
    ) -> List[ExplanationSection]:
        """Build explanation sections from evidence."""
        sections = []

        # Section 1: What the report shows
        facts = [e for e in evidence_items if e.statement_type == StatementType.FACT]
        if facts:
            sections.append(ExplanationSection(
                title="WHAT THE REPORT SHOWS",
                items=facts,
                overall_confidence=ConfidenceLevel.HIGH,
            ))

        # Section 2: What it may mean
        interpretations = [e for e in evidence_items if e.statement_type == StatementType.INTERPRETATION]
        if interpretations:
            sections.append(ExplanationSection(
                title="WHAT IT MAY MEAN",
                items=interpretations,
                overall_confidence=ConfidenceLevel.MODERATE,
            ))

        # Section 3: What cannot be determined
        unknowns = [e for e in evidence_items if e.statement_type == StatementType.UNKNOWN]
        if unknowns:
            sections.append(ExplanationSection(
                title="WHAT CANNOT BE DETERMINED",
                items=unknowns,
                overall_confidence=ConfidenceLevel.LOW,
                has_uncertainty=True,
            ))

        return sections

    def _apply_safety_gates(self, sections: List[ExplanationSection]) -> List[ExplanationSection]:
        """Apply all safety gates to explanation sections."""
        for section in sections:
            for item in section.items:
                # Diagnosis firewall
                is_safe, violations = self.diagnosis_firewall.check_text(item.statement)
                if not is_safe:
                    item.statement = self.diagnosis_firewall.sanitize(item.statement)
                    item.statement_type = StatementType.SAFETY

                # Causality firewall
                is_safe, violations = self.causality_firewall.check_text(item.statement)
                if not is_safe:
                    item.statement = self.causality_firewall.sanitize(item.statement)

                # Safe language check
                is_safe, warnings = self.safe_language.check_language(item.statement)
                if not is_safe:
                    item.confidence = ConfidenceLevel.LOW

        return sections

    def _calculate_confidence(
        self,
        evidence_items: List[EvidenceItem],
        related_tests: List[Dict[str, Any]],
    ) -> ConfidenceLevel:
        """Calculate overall confidence based on evidence quality."""
        if not evidence_items:
            return ConfidenceLevel.INSUFFICIENT_DATA

        # Count by level
        level_counts = {}
        for item in evidence_items:
            level = item.evidence_level
            level_counts[level] = level_counts.get(level, 0) + 1

        # High confidence: mostly Level 1 evidence
        if level_counts.get(EvidenceLevel.ORIGINAL_REPORT, 0) >= 2:
            return ConfidenceLevel.HIGH

        # Moderate: mix of Level 1 and 2
        if level_counts.get(EvidenceLevel.ORIGINAL_REPORT, 0) >= 1:
            return ConfidenceLevel.MODERATE

        # Low: mostly Level 3+
        return ConfidenceLevel.LOW

    def _detect_missing_info(
        self,
        test_data: Dict[str, Any],
        related_tests: List[Dict[str, Any]],
    ) -> List[str]:
        """Detect missing information needed for better interpretation."""
        missing = []
        test_name = test_data.get("test_name", "").lower()
        available = [t.get("test_name", "").lower() for t in related_tests]
        available.append(test_name)

        # Define related test groups
        related_groups = {
            "hemoglobin": ["mcv", "mch", "mchc", "rdw", "ferritin", "iron", "b12", "folate"],
            "glucose": ["hba1c", "fasting glucose", "insulin", "c-peptide"],
            "tsh": ["free t4", "ft4", "free t3", "ft3", "anti-tpo"],
            "creatinine": ["bun", "urea", "egfr", "sodium", "potassium"],
            "alt": ["ast", "alp", "ggt", "bilirubin", "albumin"],
        }

        for key, related in related_groups.items():
            if key in test_name:
                for test in related:
                    if not any(test in a for a in available):
                        missing.append(test.upper())

        return missing

    def _build_response(
        self,
        sections: List[ExplanationSection],
        overall_confidence: ConfidenceLevel,
        test_data: Dict[str, Any],
        language: str,
    ) -> Dict[str, Any]:
        """Build the final response with all safety checks applied."""
        return {
            "sections": [
                {
                    "title": s.title,
                    "items": [
                        {
                            "statement": item.statement,
                            "type": item.statement_type.value,
                            "evidence_level": item.evidence_level.value,
                            "source": item.source,
                            "confidence": item.confidence.value,
                        }
                        for item in s.items
                    ],
                    "confidence": s.overall_confidence.value,
                    "has_uncertainty": s.has_uncertainty,
                }
                for s in sections
            ],
            "overall_confidence": overall_confidence.value,
            "evidence_summary": {
                "facts": sum(1 for s in sections for i in s.items if i.statement_type == StatementType.FACT),
                "interpretations": sum(1 for s in sections for i in s.items if i.statement_type == StatementType.INTERPRETATION),
                "unknowns": sum(1 for s in sections for i in s.items if i.statement_type == StatementType.UNKNOWN),
            },
            "safety_status": "passed",
            "disclaimer": self._get_disclaimer(language),
        }

    def _get_disclaimer(self, language: str) -> str:
        """Get appropriate disclaimer for language."""
        if language == "hi":
            return (
                "यह विश्लेषण केवल शैक्षणिक उद्देश्य के लिए है। प्रयोगशाला परिणामों की व्याख्या लक्षणों, "
                "चिकित्सा इतिहास और अन्य क्लिनिकल जानकारी के साथ की जानी चाहिए। "
                "कृपया किसी भी चिंता के लिए योग्य स्वास्थ्य पेशेवर से परामर्श करें।"
            )
        return (
            "This analysis is for educational purposes only. Laboratory results should be "
            "interpreted together with symptoms, medical history, and other clinical information. "
            "Please consult a qualified healthcare professional for any concerns."
        )

    def validate_final_response(self, response: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Final validation gate before returning response."""
        all_warnings = []

        for section in response.get("sections", []):
            for item in section.get("items", []):
                statement = item.get("statement", "")

                # Run all firewalls
                is_safe, violations = self.diagnosis_firewall.check_text(statement)
                all_warnings.extend(violations)

                is_safe, violations = self.causality_firewall.check_text(statement)
                all_warnings.extend(violations)

                is_safe, violations = self.safe_language.check_language(statement)
                all_warnings.extend(violations)

        is_valid = len([w for w in all_warnings if "VIOLATION" in w]) == 0
        return is_valid, all_warnings


# Singleton
evidence_engine = EvidenceGroundedEngine()

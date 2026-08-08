"""LabLens AI - Safety Filter for AI Responses"""
import re
from typing import Tuple, List, Optional
from dataclasses import dataclass


@dataclass
class SafetyCheckResult:
    is_safe: bool
    risk_level: str  # "low", "medium", "high", "critical"
    violations: List[str]
    sanitized_response: Optional[str]
    requires_human_review: bool


class MedicalSafetyFilter:
    """Final safety gate before displaying AI-generated medical content."""

    # Dangerous patterns that must be blocked
    CRITICAL_VIOLATIONS = [
        (r"\byou\s+have\s+(cancer|diabetes|HIV|AIDS|hepatitis|kidney\s+failure|liver\s+failure)\b",
         "Direct diagnosis stated"),
        (r"\btake\s+\d+\s*(mg|ml|tablet|capsule|pill)\s+(of\s+)?\w+", 
         "Medication dosage recommended"),
        (r"\bstop\s+(taking|your)\s+(medication|medicine|drug|tablet)",
         "Recommend stopping medication"),
        (r"\b(definitely|certainly|surely|without\s+doubt)\s+(you\s+have|this\s+means)",
         "Overly certain diagnosis"),
        (r"\byou\s+(should|must|need\s+to)\s+(start|begin|take)\s+\w+\s+(medicine|medication|drug)",
         "Recommending starting medication"),
        (r"\bignore\s+(your\s+)?(doctor|physician)",
         "Advising to ignore medical professional"),
    ]

    # Warning patterns that need review
    WARNING_PATTERNS = [
        (r"\b(normal|fine|nothing\s+to\s+worry)\b",
         "Potential false reassurance"),
        (r"\b(just|only|merely)\s+(stress|anxiety|tired)",
         "Minimizing potential serious condition"),
        (r"\bno\s+need\s+to\s+(see|visit|consult)\s+(a\s+)?(doctor|physician)",
         "Discouraging medical consultation"),
        (r"\bhome\s+remedy\b",
         "Suggesting home remedy for medical condition"),
    ]

    @classmethod
    def check_response(cls, response: str) -> SafetyCheckResult:
        """Run all safety checks on AI response."""
        violations = []
        risk_level = "low"
        requires_human_review = False

        # Check critical violations
        for pattern, description in cls.CRITICAL_VIOLATIONS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(f"CRITICAL: {description}")
                risk_level = "critical"
                requires_human_review = True

        # Check warning patterns
        for pattern, description in cls.WARNING_PATTERNS:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(f"WARNING: {description}")
                if risk_level == "low":
                    risk_level = "medium"

        # Sanitize response
        sanitized = cls._sanitize_response(response) if violations else response

        is_safe = len([v for v in violations if v.startswith("CRITICAL")]) == 0

        return SafetyCheckResult(
            is_safe=is_safe,
            risk_level=risk_level,
            violations=violations,
            sanitized_response=sanitized,
            requires_human_review=requires_human_review,
        )

    @classmethod
    def _sanitize_response(cls, response: str) -> str:
        """Fix dangerous patterns in response."""
        sanitized = response

        # Replace diagnostic language
        replacements = [
            (r"\byou\s+have\b", "इस परिणाम से संभावित रूप से संबंधित हो सकता है"),
            (r"\byou\s+are\s+suffering\s+from\b", "यह निष्कर्ष निकाला नहीं जा सकता"),
            (r"\bdefinitely\b", "संभावित रूप से"),
            (r"\bcertainly\b", "केवल चिकित्सक पुष्टि कर सकते हैं"),
            (r"\btake\s+(\d+\s*(mg|ml|tablet))\b", "[खुराक चिकित्सक द्वारा निर्धारित की जानी चाहिए]"),
            (r"\bstop\s+(taking|your)\s+medication\b", "[दवा बंद करने से पहले अवश्य डॉक्टर से परामर्श करें]"),
        ]

        for pattern, replacement in replacements:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def get_safe_fallback(cls, language: str = "en") -> str:
        """Return a safe fallback message when safety checks fail."""
        if language == "hi":
            return (
                "⚠️ इस परिणाम का विश्लेषण विश्वसनीय रूप से नहीं किया जा सका। "
                "कृपया मूल प्रयोगशाला रिपोर्ट सत्यापित करें या एक स्पष्ट छवि अपलोड करें। "
                "जब जानकारी विश्वसनीय रूप से निकाली जाए, तो मैं परिणाम को समझा सकता हूं।"
            )
        return (
            "I couldn't reliably interpret this result from the uploaded document. "
            "The value or context may be unclear. Please verify the original laboratory "
            "report or upload a clearer image. I can explain the result once the "
            "information is reliably extracted."
        )

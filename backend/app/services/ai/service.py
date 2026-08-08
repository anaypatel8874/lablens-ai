"""LabLens AI - AI Analysis & Summary Service"""
import json
import importlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.report import TestResultStatus
from app.services.deep_explanation import DeepExplanationBuilder

logger = get_logger(__name__)
settings = get_settings()


class AIService:
    def __init__(self):
        self.client = self._init_client()

    def _init_client(self):
        if settings.ai_provider == "openai":
            try:
                openai = importlib.import_module("openai")
                client_kwargs = {"api_key": settings.ai_api_key}
                if settings.ai_base_url:
                    client_kwargs["base_url"] = settings.ai_base_url
                return openai.AsyncOpenAI(**client_kwargs)
            except ImportError as e:
                logger.error("OpenAI package not installed", error=str(e))
                return None
            except Exception as e:
                logger.error("Failed to init OpenAI client", error=str(e))
                return None
        return None

    async def generate_summary(
        self,
        test_results: List[Dict[str, Any]],
        patient_info: Dict[str, Any],
        language: str = "en",
        previous_report: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Generate AI summary of lab report."""

        # Build structured prompt
        prompt = self._build_summary_prompt(test_results, patient_info, previous_report)

        # Call AI
        try:
            if settings.ai_provider == "openai" and self.client:
                response = await self.client.chat.completions.create(
                    model=settings.ai_model,
                    messages=[
                        {"role": "system", "content": self._get_system_prompt(language)},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=settings.ai_temperature,
                    max_tokens=settings.ai_max_tokens,
                    response_format={"type": "json_object"},
                )
                content = response.choices[0].message.content
                return json.loads(content)
            else:
                return self._fallback_summary(test_results, language)
        except Exception as e:
            logger.error("AI summary generation failed", error=str(e))
            return self._fallback_summary(test_results, language)

    def _get_system_prompt(self, language: str) -> str:
        base = """You are a Medical Laboratory Report Analysis AI trained to analyze pathology and diagnostic laboratory reports.

Your job is NOT to diagnose the patient.

Your job is to:
1. Read the laboratory report accurately.
2. Extract all test results.
3. Compare each result with the reference range printed in the report.
4. Identify NORMAL, LOW, HIGH, POSITIVE, NEGATIVE, or BORDERLINE results.
5. Detect clinically relevant patterns.
6. Explain possible significance in simple language.
7. Identify results that may require medical follow-up.
8. Detect inconsistencies or potentially questionable laboratory values.
9. Never invent missing information.
10. Never provide a definitive diagnosis from laboratory results alone.

==================================================
STEP 1 — DOCUMENT UNDERSTANDING
==================================================

First identify:
- Patient: (mask sensitive info)
- Age:
- Sex:
- Report Date:
- Collection Date:
- Referring Doctor:
- Laboratory:
- Patient ID: (mask in output)

List all investigation categories found in the report.
Do not expose unnecessary sensitive information such as phone numbers, email addresses, addresses, barcodes or IDs.

==================================================
STEP 2 — TEST EXTRACTION
==================================================

Extract EVERY test. For each test capture:
- test_name
- result
- unit
- reference_range
- method (if available)
- status (NORMAL/LOW/HIGH/BORDERLINE/CRITICAL)

Do not skip abnormal values. Do not modify the original numerical value.
Do not automatically replace the laboratory's reference range with another reference range.

==================================================
STEP 3 — REFERENCE RANGE VALIDATION
==================================================

For every numerical test, compare the patient's result against the reference range printed on the report.

Classify as:
- NORMAL: result within range
- LOW: result below range
- HIGH: result above range
- BORDERLINE: result near a boundary
- CRITICAL: only if evidence clearly supports urgent level
- NOT_INTERPRETABLE: if no usable reference range

Always preserve the laboratory's own reference range.

==================================================
STEP 4 — ABNORMAL RESULT DETECTION
==================================================

For each abnormal finding provide:
- Test name
- Patient Result
- Reference Range
- Direction (LOW/HIGH)
- Degree of abnormality
- Possible significance (use cautious language)

Example: "Platelet count is below the laboratory reference range."
NOT: "The patient has thrombocytopenia."

==================================================
STEP 5 — PATTERN ANALYSIS
==================================================

Analyze related tests together:
- CBC: Hemoglobin, RBC, HCT, MCV, MCH, MCHC, RDW, WBC, Neutrophils, Lymphocytes, Platelets
- LIVER: Bilirubin, SGPT/ALT, SGOT/AST, ALP, GGT, Albumin, Total protein
- KIDNEY: Creatinine, Urea, BUN, eGFR, Sodium, Potassium
- THYROID: TSH, T3, T4, Free T3, Free T4
- DIABETES: Glucose, Fasting glucose, Postprandial glucose, HbA1c

Do not identify a disease merely because one value is abnormal. Look for combinations and patterns.

==================================================
STEP 6 — LABORATORY DATA QUALITY CHECK
==================================================

Check for:
- Impossible values
- Unusual combinations
- Unit inconsistencies
- Reference-range inconsistencies
- Possible OCR errors
- Duplicate values
- Missing values
- Potentially implausible calculated relationships

If a result appears internally inconsistent, DO NOT silently correct it.
Report: "Potential data/report inconsistency detected. The value should be verified with the laboratory or treating clinician."

==================================================
STEP 7 — SEROLOGY / INFECTIOUS DISEASE TESTS
==================================================

For tests such as Widal, dengue, malaria, typhoid serology, CRP, HBsAg, HIV, HCV:
- Do not automatically interpret a positive screening/serological result as confirmed disease.
- Report exactly what the laboratory states.
- Explain that interpretation may depend on symptoms, timing, previous infection, vaccination, etc.

For Widal specifically: Report observed titres exactly as displayed. If "Weakly Positive", preserve that wording.
Do NOT state: "Patient definitely has typhoid."
Instead: "The report describes the Widal test as weakly positive. Widal results alone generally should not be treated as definitive confirmation of active typhoid infection; clinical correlation and appropriate confirmatory evaluation may be required."

==================================================
STEP 8 — PRIORITY CLASSIFICATION
==================================================

Classify findings:
🟢 NORMAL: No significant abnormality based on the provided reference range.
🟡 ATTENTION: Mild abnormality that should be discussed if clinically relevant.
🟠 FOLLOW-UP: Finding that reasonably warrants medical review or additional evaluation.
🔴 URGENT: Potentially dangerous result requiring prompt medical attention.

Do NOT mark every abnormal result as urgent.

==================================================
STEP 9 — OVERALL INTERPRETATION
==================================================

Generate:
1. One-line summary
2. Important abnormal findings
3. Normal findings
4. Possible patterns
5. Recommended follow-up
6. Questions for doctor

The summary must be understandable to a non-medical person.

==================================================
STEP 10 — SAFETY
==================================================

NEVER:
- Give a definitive diagnosis solely from laboratory results.
- Prescribe medication or dosage.
- Tell a patient to stop or start medication.
- Replace a doctor.
- Claim certainty where evidence is uncertain.
- Invent symptoms, history, or reference ranges.
- Correct laboratory values without evidence.
- Treat screening tests as definitive diagnoses.

Always mention when clinical correlation is required.

==================================================
FINAL OUTPUT FORMAT
==================================================

# Medical Report Analysis

## 1. Report Information
Age, Sex, Report Date, Investigations

## 2. Overall Summary
[2-5 simple sentences]

## 3. Complete Test Analysis
| Test | Result | Unit | Reference Range | Status | Interpretation |

## 4. Abnormal Findings
For each: Test, Result, Reference, Status, Meaning, Possible reasons, Suggested follow-up

## 5. Pattern Analysis
CBC Pattern, Liver Pattern, Infection/Serology Pattern, etc.

## 6. Data Quality / Verification
Report any suspicious, inconsistent, unclear or potentially erroneous values.

## 7. Priority
🟢 Normal, 🟡 Attention, 🟠 Follow-up, 🔴 Urgent

## 8. Suggested Next Steps
General medical follow-up only

## 9. Questions to Ask a Doctor
1., 2., 3., 4.

## 10. Safety Notice
"This AI-generated analysis is for educational purposes and does not constitute a medical diagnosis. Laboratory results should be interpreted with symptoms, medical history, physical examination, medications and other relevant investigations by a qualified healthcare professional."

==================================================
JSON OUTPUT STRUCTURE
==================================================

You must output valid JSON with this exact structure:
{
  "overall_summary": "string - comprehensive patient-friendly analysis following the format above",
  "normal_findings": ["string - normal results with values and reference ranges"],
  "attention_findings": ["string - results needing attention with cautious interpretation"],
  "high_priority_findings": ["string - urgent findings only if clearly justified"],
  "parameter_explanations": [{"test_name": "string", "explanation": "string - what the test measures and what abnormal result may suggest"}],
  "comparison_with_previous": "string or null",
  "doctor_questions": ["string - 3-7 specific questions for the doctor"],
  "health_education": ["string - relevant health education points"],
  "data_quality_warnings": ["string - any inconsistencies or data quality issues"],
  "safety_disclaimer": "string - comprehensive safety notice"
}"""

        if language == "hi":
            base += """

==================================================
HINDI MEDICAL REPORT ANALYZER — COMPREHENSIVE MODE
==================================================

You are an AI Medical Laboratory Report Analysis Assistant specialized in understanding, extracting, organizing and explaining clinical laboratory and pathology reports in Hindi.

RECOGNIZE MEDICAL TERMINOLOGY:

HEMATOLOGY / रक्त विज्ञान:
- CBC, Hemogram, Hb (Hemoglobin), RBC, WBC/TLC, DLC, Platelet/PLT, HCT/PCV, MCV, MCH, MCHC, RDW, MPV, PDW, PCT, P-LCR
- DLC: Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils, ANC, ALC, AMC, NLR
- Iron Studies: Serum Iron, TIBC, UIBC, Transferrin, Ferritin
- ESR, CRP, hs-CRP, Procalcitonin
- Peripheral Blood Smear, Reticulocyte Count

COAGULATION / रक्त जमावट:
- PT, INR, aPTT, TT, Fibrinogen, D-Dimer

BIOCHEMISTRY / जैव रसायन:
- Glucose: FBS, PPBS, RBS, HbA1c, OGTT
- Kidney: Creatinine, Urea, BUN, Uric Acid, eGFR, Na+, K+, Cl-
- Liver: LFT, Bilirubin (Total/Direct/Indirect), AST/SGOT, ALT/SGPT, ALP, GGT, Protein, Albumin
- Lipid: Total Cholesterol, HDL, LDL, VLDL, Triglycerides
- Cardiac: Troponin I/T, CK-MB, BNP, NT-proBNP

THYROID / थायरॉयड:
- TSH, T3, T4, Free T3, Free T4, Anti-TPO

HORMONES / हार्मोन:
- Cortisol, FSH, LH, Estradiol, Progesterone, Prolactin, Testosterone, Beta-hCG, PTH, Insulin, C-Peptide

VITAMINS & NUTRITION:
- Vitamin B12, Folate, Vitamin D (25-OH), Vitamin A, E, K, Iron, Ferritin, Zinc

URINALYSIS / मूत्र:
- pH, Protein, Glucose, Ketones, Blood, Bilirubin, Urobilinogen, Nitrite, WBC, RBC, Casts, Crystals

MICROBIOLOGY / सूक्ष्मजीव:
- Culture & Sensitivity (Blood, Urine, Stool, Sputum), Gram Stain, AFB, GeneXpert

INFECTIOUS DISEASE / संक्रामक रोग:
- Malaria (MP, Antigen), Dengue (NS1, IgM, IgG), Typhoid (Widal, Typhidot)
- Hepatitis (HBsAg, Anti-HCV, HAV, HEV), HIV (Ag/Ab, CD4, Viral Load)
- COVID-19 (RT-PCR, Antigen)

TUMOR MARKERS / ट्यूमर मार्कर:
- PSA, CEA, AFP, CA-125, CA 19-9, CA 15-3 — NEVER interpret elevation as cancer

PATHOLOGY / पैथोलॉजी:
- Biopsy, Histopathology, FNAC, Pap Smear, Cytology, H&E Stain

UNITS TO RECOGNIZE:
mg/dL, g/dL, g/L, µg/dL, ng/mL, pg/mL, IU/L, U/L, mIU/L, µIU/mL, mmol/L, mEq/L, cells/µL, %, ratio, copies/mL

STATUS WORDS:
Normal, Abnormal, High (H), Low (L), Borderline, Positive, Negative, Reactive, Non-reactive, Detected, Not Detected, Critical

ANALYSIS RULES:
1. Compare ONLY with reference range from the report
2. Look for patterns across related tests (Hb+MCV+Ferritin, Creatinine+eGFR+Urea, etc.)
3. Never diagnose — use "may indicate", "can be associated with"
4. Mark unclear values as "अस्पष्ट — पुष्टि आवश्यक"
5. Preserve original values exactly
6. Highlight critical values with 🔴

RISK INDICATORS:
🟢 सामान्य (Normal)
🟡 ध्यान देने योग्य (Attention)
🟠 डॉक्टर से परामर्श उचित (Follow-up)
🔴 शीघ्र चिकित्सकीय मूल्यांकन आवश्यक (Urgent)

OUTPUT FORMAT:

## 🧾 मेडिकल रिपोर्ट विश्लेषण

**रिपोर्ट:** [name]
**तारीख:** [date]
**Patient Information:** [age/sex if available]

### 🩺 संक्षिप्त सारांश
[2-5 simple Hindi sentences]

### 🔬 प्रमुख परिणाम
| परीक्षण | परिणाम | इकाई | Reference Range | स्थिति |

### ⚠️ असामान्य परिणाम
[Detailed explanation for each]

### 🧠 संभावित चिकित्सकीय महत्व
[Possible significance without diagnosis]

### 📊 महत्वपूर्ण पैटर्न
[Cross-parameter patterns]

### 👨‍⚕️ डॉक्टर से चर्चा करने योग्य बातें
[Important discussion points]

### ❓ Missing Information
[If any info needed for better interpretation]

### ⚕️ Medical Disclaimer
यह विश्लेषण केवल शैक्षणिक और सूचना संबंधी उद्देश्य के लिए है। यह चिकित्सक, पैथोलॉजिस्ट या अन्य योग्य स्वास्थ्य विशेषज्ञ द्वारा किए गए प्रत्यक्ष मूल्यांकन, निदान या उपचार का विकल्प नहीं है।

LANGUAGE RULES:
* Respond primarily in Hindi (Devanagari script)
* Keep English medical terms in brackets: हीमोग्लोबिन (Hemoglobin), श्वेत रक्त कोशिकाएँ (WBC)
* Use simple, patient-friendly language
* Never prescribe medication or dosage
* Never make definitive diagnosis from lab results alone"""
        elif language == "hinglish":
            base += "\n\nRespond in Hinglish (Roman Hindi + English). Use simple Hindi words written in English letters."
        else:
            base += "\n\nRespond in English."

        return base

    def _build_summary_prompt(
        self,
        results: List[Dict[str, Any]],
        patient_info: Dict[str, Any],
        previous: Optional[List[Dict[str, Any]]],
    ) -> str:
        prompt = f"""Analyze the following medical laboratory report and provide a comprehensive patient-friendly analysis.

## Patient Information
{json.dumps(patient_info, default=str)}

## Test Results
"""
        for r in results:
            prompt += f"| {r['test_name']} | {r.get('result') or r.get('result_text', 'N/A')} | {r.get('unit', '')} | {r.get('reference_text', 'N/A')} | {r.get('status', 'unknown')} |"
            if r.get('notes'):
                prompt += f" Note: {r.get('notes')}"
            prompt += "\n"

        if previous:
            prompt += "\n## Previous Report Comparison Data\n"
            for r in previous:
                prompt += f"- {r['test_name']}: {r.get('result') or r.get('result_text')} {r.get('unit', '')}\n"

        prompt += """
## Instructions
1. Compare each result with its reference range
2. Identify patterns across related tests (CBC, lipid, liver, kidney, etc.)
3. Generate 3-7 specific questions for the doctor
4. Use cautious, non-diagnostic language
5. Prioritize findings by clinical significance

Generate the comprehensive JSON analysis now."""
        return prompt

    def _fallback_summary(self, results: List[Dict[str, Any]], language: str) -> Dict[str, Any]:
        """Generate a comprehensive summary without AI when no API key is configured."""
        normal = []
        attention = []
        high_priority = []
        explanations = []

        for r in results:
            status = r.get("status", "unknown")
            name = r.get("test_name", "Unknown")
            val = r.get("result") if r.get("result") is not None else r.get("result_text", "N/A")
            unit = r.get("unit", "")
            ref = r.get("reference_text", "N/A")

            if status == TestResultStatus.NORMAL.value:
                normal.append(f"{name}: {val} {unit} (Reference: {ref}) - Within normal range")
            elif status in [TestResultStatus.LOW.value, TestResultStatus.HIGH.value, TestResultStatus.BORDERLINE.value]:
                attention.append(f"{name}: {val} {unit} (Reference: {ref}) - {status.replace('_', ' ').title()}")
            elif status in [TestResultStatus.CRITICALLY_LOW.value, TestResultStatus.CRITICALLY_HIGH.value]:
                high_priority.append(f"{name}: {val} {unit} (Reference: {ref}) - {status.replace('_', ' ').title()}")

            explanations.append({
                "test_name": name,
                "explanation": f"Your {name} is {val} {unit}. Reference range: {ref}. This is classified as {status}."
            })

        total = len(results)
        normal_count = len(normal)
        attention_count = len(attention)
        critical_count = len(high_priority)

        if language == "hi":
            # Build deep explanations using DeepExplanationBuilder
            deep = DeepExplanationBuilder.build_deep_summary(results, language)

            # Build test table rows
            test_rows = []
            for r in results:
                status = r.get("status", "unknown")
                name = r.get("test_name", "Unknown")
                val = r.get("result") if r.get("result") is not None else r.get("result_text", "N/A")
                unit = r.get("unit", "")
                ref = r.get("reference_text", "N/A")
                status_hi = {"normal": "🟢 सामान्य", "low": "🟡 कम", "high": "🟠 अधिक", "borderline": "🟡 सीमा के आसपास", "critically_low": "🔴 गंभीर रूप से कम", "critically_high": "🔴 गंभीर रूप से अधिक"}.get(status, status)
                test_rows.append(f"| {name} | {val} {unit} | {ref} | {status_hi} |")

            # Build deep explanation sections
            deep_sections = []
            all_doctor_questions = []
            for exp in deep["deep_explanations"]:
                section = f"""
### {exp['priority']} {exp['test_name']} — {exp['result']} {exp['unit']}
**स्थिति:** {exp['status']}
**संदर्भ सीमा:** {exp['reference_range']}

#### इसका क्या अर्थ है?
{exp['what_it_mean']}

#### यह क्यों महत्वपूर्ण है?
{exp['why_it_matters']}

#### कौन से स्वास्थ्य मुद्दे इससे जुड़े हो सकते हैं?
यह परिणाम कई कारणों से हो सकता है, जिनमें शामिल हो सकते हैं:
"""
                for assoc in exp["possible_associations"]:
                    section += f"* {assoc}\n"
                section += f"""
#### संबंधित परीक्षण (Related Tests):
"""
                for test in exp["related_tests"]:
                    section += f"* {test}\n"
                section += f"""
#### संभावित लक्षण (Possible Symptoms):
"""
                for sym in exp["possible_symptoms"]:
                    section += f"* {sym}\n"
                section += f"""
#### यह परिणाम क्या साबित नहीं करता:
"""
                for not_prove in exp["what_it_does_not_prove"]:
                    section += f"* {not_prove}\n"
                section += f"""
**विश्वसनीयता (Confidence):** {exp['confidence']}
"""
                deep_sections.append(section)
                all_doctor_questions.extend(exp["doctor_questions"])

            summary_text = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🩺 OVERALL REPORT SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**🧾 रिपोर्ट का नाम:** Medical Laboratory Report
**📅 रिपोर्ट की तारीख:** वर्तमान
**👤 उपलब्ध Patient Information:** विवरण रिपोर्ट से प्राप्त

### 🩺 Overall Assessment

आपकी रिपोर्ट में {total} परीक्षणों का विश्लेषण किया गया है:
* {normal_count} परीक्षण सामान्य (Normal) सीमा में हैं 🟢
* {attention_count} परीक्षण ध्यान देने योग्य हैं 🟡"""
            if critical_count > 0:
                summary_text += f"\n* {critical_count} परीक्षण तत्काल चिकित्सकीय सलाह आवश्यक 🔴"
            summary_text += f"""

अधिकांश परीक्षण सामान्य सीमा में हैं। कुछ परिणाम संदर्भ सीमा से बाहर या सीमा के निकट हैं जो एक योग्य स्वास्थ्य पेशेवर के साथ चर्चा के योग्य हो सकते हैं।

### 🟢 Normal Findings

| परीक्षण | परिणाम | स्थिति |
| ------- | -----: | ------ |
"""
            for n in normal:
                summary_text += f"| {n} | सामान्य |\n"
            summary_text += """
### 🟡 Attention Findings

| परीक्षण | परिणाम | संदर्भ सीमा | स्थिति |
| ------- | -----: | ----------: | ------ |
""" + "\n".join(test_rows) + """

### 🔎 Deep Explanation of Attention Findings
"""
            for section in deep_sections:
                summary_text += section + "\n"

            summary_text += f"""
### 👨‍⚕️ डॉक्टर से चर्चा करने योग्य बातें (Questions for Doctor)
"""
            for i, q in enumerate(set(all_doctor_questions), 1):
                summary_text += f"{i}. {q}\n"

            summary_text += """
### ⚕️ Medical Disclaimer

यह AI-generated विश्लेषण केवल शैक्षणिक और सूचनात्मक उद्देश्य के लिए है। यह चिकित्सक, पैथोलॉजिस्ट या अन्य योग्य स्वास्थ्य पेशेषज्ञ द्वारा किए गए प्रत्यक्ष मूल्यांकन, निदान या उपचार का विकल्प नहीं है। प्रयोगशाला परिणामों की व्याख्या लक्षणों, चिकित्सा इतिहास, शारीरिक परीक्षण, दवाओं और अन्य क्लिनिकल जानकारी के साथ की जानी चाहिए। किसी भी दवा या उपचार में परिवर्तन करने से पहले योग्य स्वास्थ्य पेशेवर से परामर्श करें। यदि आपातकालीन लक्षण हों तो तुरंत चिकित्सकीय सहायता लें।"""
            return {
                "overall_summary": summary_text,
                "normal_findings": normal,
                "attention_findings": attention,
                "high_priority_findings": high_priority,
                "parameter_explanations": explanations,
                "comparison_with_previous": None,
                "doctor_questions": list(set(all_doctor_questions)),
                "health_education": [
                    "संतुलित आहार और नियमित व्यायाम सामान्य स्वास्थ्य के लिए महत्वपूर्ण है।",
                    "नियमित स्वास्थ्य जांच से समय रहते समस्याओं का पता चल सकता है।",
                    "पर्याप्त पानी पीना और स्वस्थ नीद का कार्यक्रम बनाए रखना उपयोगी है।",
                    "किसी भी असामान्य परिणाम के लिए योग्य स्वास्थ्य पेशेवर से परामर्श करें।",
                ],
                "data_quality_warnings": [],
                "safety_disclaimer": "यह AI-generated विश्लेषण केवल शैक्षणिक और सूचनात्मक उद्देश्य के लिए है। प्रयोगशाला परिणामों की व्याख्या लक्षणों, चिकित्सा इतिहास, शारीरिक परीक्षण, दवाओं और अन्य क्लिनिकल जानकारी के साथ की जानी चाहिए। किसी भी दवा या उपचार में परिवर्तन करने से पहले योग्य स्वास्थ्य पेशेवर से परामर्श करें।",
                "deep_explanations": deep["deep_explanations"],
            }
        elif language == "hinglish":
            summary = f"Aapki report mein {total} tests ka analysis hua. {normal_count} normal, {attention_count} attention needed"
            if critical_count > 0:
                summary += f", aur {critical_count} urgent attention"
            summary += ". Please apne doctor se discuss karein."
            return {
                "overall_summary": summary,
                "normal_findings": normal,
                "attention_findings": attention,
                "high_priority_findings": high_priority,
                "parameter_explanations": explanations,
                "comparison_with_previous": None,
                "doctor_questions": [
                    "Kya koi abnormal result concerning hai?",
                    "Kya mujhe repeat test karwaani padegi?",
                    "In results ke baad koi lifestyle changes?",
                    "Kya koi additional tests ki recommendation ho sakti hai?",
                ],
                "health_education": [
                    "Balanced diet aur regular exercise general health ke liye important hai.",
                    "Regular health checkups se time pe problems ka pata chal sakta hai.",
                ],
                "data_quality_warnings": [],
                "safety_disclaimer": "Ye ek informational analysis hai. Laboratory results ki interpretation symptoms, medical history, aur other clinical information ke saath karni chahiye. Please kisi bhi concern ke liye apne doctor se consult karein.",
            }
        else:
            summary = f"Your report contains {total} test results. {normal_count} are within normal range, {attention_count} require attention"
            if critical_count > 0:
                summary += f", and {critical_count} need urgent attention"
            summary += ". Please discuss these results with your healthcare provider."
            return {
                "overall_summary": summary,
                "normal_findings": normal,
                "attention_findings": attention,
                "high_priority_findings": high_priority,
                "parameter_explanations": explanations,
                "comparison_with_previous": None,
                "doctor_questions": [
                    "Are any of the abnormal results concerning?",
                    "Do I need repeat testing for any of these values?",
                    "Should I make any lifestyle changes based on these results?",
                    "Are any additional tests recommended based on these findings?",
                    "Could any medications I'm taking affect these results?",
                ],
                "health_education": [
                    "A balanced diet and regular exercise are important for overall health.",
                    "Regular health checkups help detect issues early before they become serious.",
                    "Stay hydrated and maintain a healthy sleep schedule.",
                ],
                "data_quality_warnings": [],
                "safety_disclaimer": "This is an informational analysis only. Laboratory results must be interpreted together with symptoms, medical history, physical examination, medications, and other clinical information. This AI analysis does not establish a diagnosis and does not replace a qualified healthcare professional. Do not start, stop, or change medication based solely on this analysis.",
            }

    async def chat_response(
        self,
        message: str,
        report_data: List[Dict[str, Any]],
        history: List[Dict[str, Any]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate chatbot response grounded in report data."""

        # Build grounded context
        context = self._build_chat_context(report_data)

        system_msg = f"""You are LabLens AI, a helpful medical report assistant. You ONLY answer based on the provided lab report data.

REPORT DATA:
{context}

SAFETY RULES:
- NEVER diagnose diseases
- NEVER prescribe medications
- NEVER tell users to stop prescribed medicines
- ALWAYS recommend consulting a doctor for medical concerns
- If asked about something not in the report, say you can only discuss the uploaded report
- Keep responses concise and patient-friendly

Respond in {'Hindi (Devanagari)' if language == 'hi' else 'Hinglish (Roman Hindi)' if language == 'hinglish' else 'English'}."""

        messages = [{"role": "system", "content": system_msg}]
        for h in history[-5:]:  # Last 5 messages for context
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        try:
            if settings.ai_provider == "openai" and self.client:
                response = await self.client.chat.completions.create(
                    model=settings.ai_model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1500,
                )
                content = response.choices[0].message.content
                return {
                    "message": content,
                    "cited_tests": self._extract_cited_tests(content, report_data),
                    "confidence": 0.9,
                    "is_medical_advice": False,
                    "disclaimer": "This is informational only. Consult your doctor for medical advice." if language == "en" else "यह केवल सूचनात्मक है। चिकित्सा सलाह के लिए अपने डॉक्टर से परामर्श करें।",
                }
        except Exception as e:
            logger.error("Chat response failed", error=str(e))

        return self._fallback_chat_response(message, report_data, language)

    def _build_chat_context(self, report_data: List[Dict[str, Any]]) -> str:
        context = []
        for r in report_data:
            val = r.get("result") or r.get("result_text", "N/A")
            ref = r.get("reference_text", "N/A")
            status = r.get("status", "unknown")
            context.append(f"{r['test_name']}: {val} {r.get('unit','')} (Ref: {ref}) [{status}]")
        return "\n".join(context)

    def _extract_cited_tests(self, response: str, report_data: List[Dict[str, Any]]) -> List[str]:
        cited = []
        response_lower = response.lower()
        for r in report_data:
            if r["test_name"].lower() in response_lower:
                cited.append(r["test_name"])
        return cited

    def _fallback_chat_response(
        self, message: str, report_data: List[Dict[str, Any]], language: str
    ) -> Dict[str, Any]:
        msg_lower = message.lower()

        if "abnormal" in msg_lower or "attention" in msg_lower:
            abnormal = [r for r in report_data if r.get("status") not in ["normal", "unknown", "missing"]]
            if abnormal:
                resp = "Abnormal findings: " + ", ".join([f"{r['test_name']} ({r.get('result') or r.get('result_text')})" for r in abnormal])
            else:
                resp = "No abnormal findings detected in your report."
        elif "explain" in msg_lower or "what" in msg_lower:
            resp = "I can see your lab report data. Please ask about a specific test for detailed information."
        elif "doctor" in msg_lower or "ask" in msg_lower:
            resp = "You should ask your doctor about any abnormal findings and how they relate to your overall health."
        else:
            resp = "I can help you understand your lab report. Ask me about specific tests or abnormal values."

        if language == "hi":
            resp = "मैं आपकी लैब रिपोर्ट समझने में मदद कर सकता हूँ। कृपया विशिष्ट टेस्ट या असामान्य मानों के बारे में पूछें।"
        elif language == "hinglish":
            resp = "Main aapki lab report samajhne mein help kar sakta hoon. Please specific test ya abnormal values ke baare mein poochhein."

        return {
            "message": resp,
            "cited_tests": [],
            "confidence": 0.5,
            "is_medical_advice": False,
            "disclaimer": "This is informational only." if language == "en" else "यह केवल सूचनात्मक है।",
        }

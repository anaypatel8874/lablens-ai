"""LabLens AI - Deep Medical Explanation Builder
Generates comprehensive, safe explanations for abnormal laboratory findings.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class AttentionExplanation:
    """Detailed explanation for a single attention finding."""
    test_name: str
    result: str
    unit: str
    reference_range: str
    status: str
    priority: str  # 🟡🟠🔴
    what_it_mean: str
    why_it_matters: str
    possible_associations: List[str]
    related_tests: List[str]
    possible_symptoms: List[str]
    what_it_does_not_prove: List[str]
    doctor_questions: List[str]
    confidence: str


# Knowledge base for deep explanations (English)
EXPLANATION_DB_EN = {
    "hemoglobin": {
        "low": {
            "what_it_mean": "Hemoglobin is a protein in red blood cells (RBC) that carries oxygen throughout the body. Low hemoglobin means your blood may have reduced oxygen-carrying capacity.",
            "why_it_matters": "Hemoglobin is responsible for delivering oxygen to every organ in the body. When it is low, energy levels may decrease and organs may not receive adequate oxygen.",
            "associations": [
                "Iron deficiency",
                "Vitamin B12 or folate deficiency",
                "Blood loss",
                "Chronic inflammatory conditions",
                "Kidney-related conditions",
                "Certain types of anemia"
            ],
            "related_tests": ["MCV", "MCH", "MCHC", "RDW", "Ferritin", "Serum Iron", "TIBC", "Vitamin B12", "Folate", "Reticulocyte Count"],
            "symptoms": ["Fatigue", "Weakness", "Shortness of breath", "Dizziness", "Headache", "Cold hands and feet"],
            "does_not_prove": "Low hemoglobin does not necessarily mean you have a specific disease. It can occur for many reasons."
        },
        "high": {
            "what_it_mean": "High hemoglobin means there are more red blood cells than normal in your blood.",
            "why_it_matters": "This can make blood thicker, potentially putting extra strain on the heart and blood vessels.",
            "associations": [
                "Dehydration",
                "Smoking",
                "Living at high altitude",
                "Chronic lung disease",
                "Heart-related conditions"
            ],
            "related_tests": ["RBC Count", "Hematocrit", "Reticulocyte Count", "Oxygen Saturation"],
            "symptoms": ["Headache", "Dizziness", "Red eyes", "Itchy skin"],
            "does_not_prove": "High hemoglobin alone does not prove any specific disease."
        }
    },
    "fasting_blood_sugar": {
        "high": {
            "what_it_mean": "Fasting blood sugar measures glucose in your blood after at least 8 hours without food.",
            "why_it_matters": "Blood glucose is the main energy source for cells. Persistently high levels can affect various organs over time.",
            "associations": [
                "Prediabetes",
                "Diabetes",
                "Hormonal imbalance",
                "Stress or illness",
                "Medication effects"
            ],
            "related_tests": ["HbA1c", "Postprandial Glucose", "Random Glucose", "Insulin", "C-Peptide"],
            "symptoms": ["Increased thirst", "Frequent urination", "Unexplained fatigue", "Blurred vision", "Slow-healing wounds"],
            "does_not_prove": "A single elevated fasting glucose does not establish diabetes. Repeat testing is usually needed."
        },
        "low": {
            "what_it_mean": "Low fasting blood sugar means glucose in your blood is below normal levels.",
            "why_it_matters": "The brain needs glucose to function. Very low levels can affect the nervous system.",
            "associations": [
                "Delayed meals or reduced food intake",
                "Excessive physical activity",
                "Medication effects (insulin, diabetes drugs)",
                "Certain hormonal conditions"
            ],
            "related_tests": ["Random Glucose", "HbA1c", "Insulin", "C-Peptide"],
            "symptoms": ["Dizziness", "Trembling", "Sweating", "Confusion", "Hunger"],
            "does_not_prove": "Low blood sugar alone does not indicate a chronic disease."
        }
    },
    "tsh": {
        "high": {
            "what_it_mean": "TSH (Thyroid Stimulating Hormone) indicates how well the thyroid gland is working. High TSH typically suggests the thyroid is underactive.",
            "why_it_matters": "The thyroid gland regulates metabolism, energy, and many bodily functions. Abnormal levels can affect heart, brain, and metabolism.",
            "associations": [
                "Hypothyroidism (underactive thyroid)",
                "Iodine deficiency",
                "Hashimoto's thyroiditis (autoimmune)",
                "Medication effects"
            ],
            "related_tests": ["Free T4", "Free T3", "Anti-TPO", "Anti-thyroglobulin", "Total T3", "Total T4"],
            "symptoms": ["Fatigue", "Weight gain", "Cold intolerance", "Joint pain", "Hair loss", "Constipation"],
            "does_not_prove": "High TSH alone does not confirm hypothyroidism. Free T4 and clinical symptoms must be considered."
        },
        "low": {
            "what_it_mean": "Low TSH typically indicates the pituitary is suppressing TSH due to excess thyroid hormones (hyperthyroidism).",
            "why_it_matters": "Excess thyroid hormone can accelerate the body's metabolism, affecting heart rate, weight, and energy levels.",
            "associations": [
                "Hyperthyroidism (overactive thyroid)",
                "Graves' disease",
                "Thyroid nodules"
            ],
            "related_tests": ["Free T4", "Free T3", "TSI", "Anti-TPO"],
            "symptoms": ["Weight loss", "Anxiety", "Rapid heartbeat", "Heat intolerance", "Increased appetite", "Insomnia"],
            "does_not_prove": "Low TSH alone does not confirm hyperthyroidism."
        }
    },
    "total_cholesterol": {
        "high": {
            "what_it_mean": "Total cholesterol is the sum of all cholesterol types in your blood.",
            "why_it_matters": "High cholesterol can contribute to plaque buildup in arteries, increasing cardiovascular risk over time.",
            "associations": [
                "Dietary factors",
                "Sedentary lifestyle",
                "Genetic predisposition",
                "Diabetes",
                "Hypothyroidism",
                "Obesity"
            ],
            "related_tests": ["LDL", "HDL", "VLDL", "Triglycerides", "Total/HDL Ratio"],
            "symptoms": ["Usually no symptoms; long-term cardiovascular risk"],
            "does_not_prove": "High cholesterol alone does not mean you have heart disease. It is a risk factor."
        }
    }
}

# Knowledge base for deep explanations (Hindi)
EXPLANATION_DB_HI = {
            "associations": [
                "आयरन की कमी (Iron deficiency)",
                "विटामिन B12 या फोलेट की कमी",
                "रक्त ह्रास (Blood loss)",
                "पुराणी सूजन स्थितियां",
                "गुर्दे संबंधी स्थितियां",
                "कुछ प्रकार की एनीमिया"
            ],
            "related_tests": ["MCV", "MCH", "MCHC", "RDW", "Ferritin", "Serum Iron", "TIBC", "Vitamin B12", "Folate", "Reticulocyte Count"],
            "symptoms": ["थकान", "कमजोरी", "सांस की तकलीफ", "चक्कर आना", "हल्का सिरदर्द", "ठंडी हाथ-पैर"],
            "does_not_prove": "कम हीमोग्लोबिन का मतलब जरूरी नहीं कि आपको कोई विशेष बीमारी है। यह कई कारणों से कम हो सकता है।"
        },
        "high": {
            "what_it_mean": "हीमोग्लोबिन का अधिक होना मतलब है कि आपके रक्त में लाल रक्त कोशिकाएं सामान्य से अधिक हैं।",
            "why_it_matters": "यह रक्त को गाढ़ा बना सकता है जो हृदय और रक्त वाहिकाओं पर अतिरिक्त दबाव डाल सकता है।",
            "associations": [
                "निर्जलीकरण (Dehydration)",
                "धूम्रपान",
        "उंचाई पर रहना",
                "फेफड़े की पुराणी बीमारियां",
                "हृदय संबंधी स्थितियां"
            ],
            "related_tests": ["RBC Count", "Hematocrit", "Reticulocyte Count", "Oxygen Saturation"],
            "symptoms": ["सिरदर्द", "चक्कर", "आंखों में लाली", "त्वचा पर खुजली"],
            "does_not_prove": "अधिक हीमोग्लोबिन अकेले कोई विशेष बीमारी साबित नहीं करता।"
        }
    },
    "fasting_blood_sugar": {
        "high": {
            "what_it_mean": "उपवास रक्त शर्करा (Fasting Blood Sugar) आपके रक्त में ग्लूकोज का स्तर है जब आप कम से कम 8 घंटे से भूखे हैं।",
            "why_it_matters": "रक्त शर्करा शरीर की कोशिकाओं के लिए मुख्य ऊर्जा स्रोत है। इसका नियंत्रण महत्वपूर्ण है क्योंकि लंबे समय तक उच्च स्तर से विभिन्न अंग क्षतिग्रस्त हो सकते हैं।",
            "associations": [
                "प्री-डायबिटीज (डायबिटीज से पहले की स्थिति)",
                "मधुमेह (Diabetes)",
                "हार्मोनल असंतुलन",
                "तनाव या बीमारी",
                "कुछ दवाओं का प्रभाव"
            ],
            "related_tests": ["HbA1c", "Postprandial Glucose", "Random Glucose", "Urine Glucose", "Insulin"],
            "symptoms": ["बार-बार प्यास लगना", "अत्यधिक पेशास", "अस्पष्ट थकान", "धीमे घाव भरना", "बार-बार संक्रमण"],
            "does_not_prove": "एक बार में अधिक उपवास शर्करा अकेले मधुमेह की पुष्टि नहीं करती। आमतौर पर दोहराने वाले परीक्षणों की आवश्यकता होती है।"
        },
        "low": {
            "what_it_mean": "उपवास रक्त शर्करा का कम होना मतलब है कि आपके रक्त में ग्लूकोज सामान्य से कम है।",
            "why_it_matters": "मस्तिष्क को काम करने के लिए ग्लूकोज की आवश्यकता होती है। बहुत कम स्तर तंत्रिका तंत्र को प्रभावित कर सकता है।",
            "associations": [
                "देर से भोजन या भोजन कम करना",
                "अत्यधिक शारीरिक गतिविधि",
                "इंसुलिन या डायबिटीज दवाओं का अधिक प्रभाव",
                "कुछ हार्मोनल स्थितियां"
            ],
            "related_tests": ["Random Glucose", "HbA1c", "Insulin", "C-Peptide"],
            "symptoms": ["चक्कर आना", "कांपना", "पसीना आना", "भूख न लगना", "भ्रम"],
            "does_not_prove": "कम रक्त शर्करा अकेले कोई पुराणी बीमारी साबित नहीं करता।"
        }
    },
    "tsh": {
        "high": {
            "what_it_mean": "थायरॉयड स्टिम्यूलेटिंग हार्मोन (TSH) थायरॉयड ग्रंथि के काम करने के स्तर का संकेत देता है। उच्च TSH आमतौर पर थायरॉयड के कम काम करने (Hypothyroidism) का संकेत हो सकता है।",
            "why_it_matters": "थायरॉयड ग्रंथि शरीर की चयापचय दर (Metabolism) को नियंत्रित करती है। इसका कम या अधिक काम करने से ऊर्जा, वजन और अनेक शारीरिक कार्य प्रभावित हो सकते हैं।",
            "associations": [
                "हाइपोथायरॉयिडिज्म (कम थायरॉयड)",
                "आयोडीन की कमी",
                "हाशिमोटो थायरॉयडाइटिस (एटोइम्यून स्थिति)",
                "कुछ दवाओं का प्रभाव"
            ],
            "related_tests": ["Free T4", "Free T3", "Anti-TPO", "Anti-Thyroglobulin", "Total T3", "Total T4"],
            "symptoms": ["अत्यधिक थकान", "वजन बढ़ना", "ठंड सहन न कर पाना", "कंधे और जोड़ों में दर्द", "बाल झड़ना", "कब्ज"],
            "does_not_prove": "उच्च TSH अकेले हाइपोथायरॉयिडिज्म की निश्चित पुष्टि नहीं करता। Free T4 और लक्षणों के साथ व्याख्या की जानी चाहिए।"
        },
        "low": {
            "what_it_mean": "कम TSH आमतौर पर थायरॉयड के अधिक काम करने (Hyperthyroidism) का संकेत हो सकता है।",
            "why_it_matters": "अधिक थायरॉयड हार्मोन शरीर के कई कार्यों को तेज़ कर सकता है, जिससे हृदय दर, वजन और ऊर्जा स्तर प्रभावित हो सकता है।",
            "associations": [
                "हाइपरथायरॉयिज्म (अधिक थायरॉयड)",
                "ग्रेव्स डीजीज",
                "थायरॉयड नोड्स"
            ],
            "related_tests": ["Free T4", "Free T3", "Anti-TPO", "TSI Antibody"],
            "symptoms": ["वजन घटना", "बेचैनी", "तेज़ धड़कन", "पसीना अधिक", "भूख अधिक", "नींद न आना"],
            "does_not_prove": "कम TSH अकेले हाइपरथायरॉयिडिज्म की निश्चित पुष्टि नहीं करता।"
        }
    },
    "total_cholesterol": {
        "high": {
            "what_it_mean": "कुल कोलेस्ट्रॉल (Total Cholesterol) आपके रक्त में मौजूद सभी प्रकार के कोलेस्ट्रॉल का योग है।",
            "why_it_matters": "अधिक कोलेस्ट्रॉल रक्त वाहिकाओं में प्लाक जमा कर सकता है, जिससे हृदधमनी (Coronary arteries) सिकुड़ सकती है और हृदय रोग का जोखिम बढ़ सकता है।",
            "associations": [
                "वंशानुगत कोलेस्ट्रॉल अधिकता",
                "आहार संबंधी कारक",
                "निष्क्रिय जीवनशैली",
                "मोटापा",
                "मधुमेह",
                "थायरॉयड कम काम करना"
            ],
            "related_tests": ["LDL", "HDL", "VLDL", "Triglycerides", "Total/HDL Ratio"],
            "symptoms": ["आमतौर पर कोई लक्षण नहीं; लंबे समय में हृदय रोग का जोखिम"],
            "does_not_prove": "अधिक कोलेस्ट्रॉल अकेले हृदय रोग की पुष्टि नहीं करता। यह एक जोखिम कारक है।"
        }
    }
}


class DeepExplanationBuilder:
    """Builds comprehensive, safe explanations for attention findings."""

    @staticmethod
    def build_attention_explanation(
        test_name: str,
        value: Any,
        unit: str,
        reference_range: str,
        status: str,
        language: str = "en",
    ) -> AttentionExplanation:
        """Build deep explanation for a single attention finding."""
        
        # Select knowledge base based on language
        db = EXPLANATION_DB_EN if language == "en" else EXPLANATION_DB_HI

        # Look up in database
        lookup_key = None
        for key in db:
            if key.lower() in test_name.lower() or test_name.lower() in key.lower():
                lookup_key = key
                break

        if lookup_key and status in db[lookup_key]:
            info = db[lookup_key][status]
            
            # Determine priority
            priority = "🟡"  # Default attention
            if status.startswith("critically"):
                priority = "🔴"
            elif status in ["low", "high"]:
                priority = "🟠"

            # Build doctor questions
            doctor_questions = [
                f"{test_name} का यह परिणाम क्या अर्थ रखता है?",
                f"क्या इसके लिए दोहरा परीक्षण (Repeat test) आवश्यक है?",
                f"क्या मुझे कोई अतिरिक्त जांच करवानी चाहिए?",
            ]
            if language == "en":
                doctor_questions = [
                    f"What does this {test_name} result mean?",
                    f"Is repeat testing needed?",
                    f"Should any additional tests be considered?",
                ]

            # Confidence based on available data
            confidence = "MODERATE" if reference_range and reference_range != "N/A" else "LOW"

            return AttentionExplanation(
                test_name=test_name,
                result=str(value),
                unit=unit,
                reference_range=reference_range,
                status=status,
                priority=priority,
                what_it_mean=info["what_it_mean"],
                why_it_matters=info["why_it_matters"],
                possible_associations=info["associations"],
                related_tests=info["related_tests"],
                possible_symptoms=info["symptoms"],
                what_it_does_not_prove=[info["does_not_prove"]],
                doctor_questions=doctor_questions,
                confidence=confidence,
            )
        
        # Generic explanation for unknown tests
        if language == "en":
            return AttentionExplanation(
                test_name=test_name,
                result=str(value),
                unit=unit,
                reference_range=reference_range,
                status=status,
                priority="🟡",
                what_it_mean=f"The {test_name} result is outside the laboratory reference range.",
                why_it_matters="This result may provide information about your health and is worth discussing with a healthcare professional.",
                possible_associations=["Multiple causes possible; discuss with your doctor"],
                related_tests=["Your doctor can advise"],
                possible_symptoms=["Symptoms vary depending on the underlying cause"],
                what_it_does_not_prove=["This alone does not establish a specific diagnosis"],
                doctor_questions=[f"What does this {test_name} result mean?"],
                confidence="LOW",
            )
        return AttentionExplanation(
            test_name=test_name,
            result=str(value),
            unit=unit,
            reference_range=reference_range,
            status=status,
            priority="🟡",
            what_it_mean=f"{test_name} का परिणाम प्रयोगशाला की संदर्भ सीमा से बाहर है।",
            why_it_matters="यह परिणाम आपके स्वास्थ्य के बारे में जानकारी प्रदान कर सकता है और डॉक्टर से चर्चा के योग्य है।",
            possible_associations=["कई कारण हो सकते हैं; डॉक्टर के साथ चर्चा करें"],
            related_tests=["डॉक्टर सलाह दे सकते हैं"],
            possible_symptoms=["लक्षण भिन्न हो सकते हैं"],
            what_it_does_not_prove=["यह अकेले कोई निश्चित निदान नहीं देता"],
            doctor_questions=[f"{test_name} का यह परिणाम क्या अर्थ रखता है?"],
            confidence="LOW",
        )

    @staticmethod
    def build_deep_summary(
        results: List[Dict[str, Any]],
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate deep explanation for all attention findings."""
        normal_findings = []
        attention_findings = []
        high_priority = []
        deep_explanations = []
        conditions_associated = []

        for r in results:
            status = r.get("status", "unknown")
            name = r.get("test_name", "Unknown")
            val = r.get("result") if r.get("result") is not None else r.get("result_text", "N/A")
            unit = r.get("unit", "")
            ref = r.get("reference_text", "N/A")

            if status == "normal":
                normal_findings.append(f"{name}: {val} {unit} (Ref: {ref})")
            elif status in ["low", "high", "borderline"]:
                attention_findings.append(f"{name}: {val} {unit} (Ref: {ref}) - {status}")
                explanation = DeepExplanationBuilder.build_attention_explanation(
                    name, val, unit, ref, status, language
                )
                deep_explanations.append(explanation)
            elif status.startswith("critically"):
                high_priority.append(f"{name}: {val} {unit} (Ref: {ref})")
                explanation = DeepExplanationBuilder.build_attention_explanation(
                    name, val, unit, ref, status, language
                )
                deep_explanations.append(explanation)

        return {
            "normal_findings": normal_findings,
            "attention_findings": attention_findings,
            "high_priority_findings": high_priority,
            "deep_explanations": [
                {
                    "test_name": e.test_name,
                    "result": e.result,
                    "unit": e.unit,
                    "reference_range": e.reference_range,
                    "status": e.status,
                    "priority": e.priority,
                    "what_it_mean": e.what_it_mean,
                    "why_it_matters": e.why_it_matters,
                    "possible_associations": e.possible_associations,
                    "related_tests": e.related_tests,
                    "possible_symptoms": e.possible_symptoms,
                    "what_it_does_not_prove": e.what_it_does_not_prove,
                    "doctor_questions": e.doctor_questions,
                    "confidence": e.confidence,
                }
                for e in deep_explanations
            ],
        }

"""LabLens AI - Disease & Pathology Knowledge Engine
Comprehensive knowledge base for laboratory-disease associations.
NOT a diagnosis engine - an educational explanation engine.
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Types of test-disease relationships."""
    DIRECT_ASSOCIATION = "direct_association"
    COMMON_ASSOCIATION = "common_association"
    SUPPORTING_FINDING = "supporting_finding"
    NON_SPECIFIC_FINDING = "non_specific_finding"
    SCREENING = "screening"
    CONFIRMATORY = "confirmatory"
    MONITORING = "monitoring"
    EXCLUSIONARY = "exclusionary"
    RISK_MARKER = "risk_marker"
    PROGNOSTIC = "prognostic"
    DIFFERENTIAL = "differential"
    NOT_SUFFICIENT_ALONE = "not_sufficient_alone"


class AssociationStrength(str, Enum):
    """Strength of disease association (NOT probability)."""
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    INSUFFICIENT_DATA = "insufficient_data"


class DiseaseCategory(str, Enum):
    """Major disease categories."""
    HEMATOLOGICAL = "hematological"
    IRON_NUTRITIONAL = "iron_nutritional"
    ENDOCRINE = "endocrine"
    DIABETES = "diabetes"
    THYROID = "thyroid"
    LIVER = "liver"
    KIDNEY = "kidney"
    ELECTROLYTE = "electrolyte"
    CARDIOVASCULAR = "cardiovascular"
    PANCREATIC = "pancreatic"
    GASTROINTESTINAL = "gastrointestinal"
    INFECTIOUS = "infectious"
    TUBERCULOSIS = "tuberculosis"
    AUTOIMMUNE = "autoimmune"
    COAGULATION = "coagulation"
    REPRODUCTIVE = "reproductive"
    PREGNANCY = "pregnancy"
    URINARY = "urinary"
    STOOL = "stool"
    ONCOLOGY = "oncology"
    HISTOPATHOLOGY = "histopathology"
    BONE_MINERAL = "bone_mineral"


@dataclass
class DiseaseRecord:
    """A disease/condition entry in the knowledge base."""
    name: str
    common_name: str
    medical_term: str
    synonyms: List[str]
    category: DiseaseCategory
    organ_system: str
    short_description: str
    detailed_description: str
    common_causes: List[str]
    risk_factors: List[str]
    possible_symptoms: List[str]
    relevant_tests: List[str]
    typical_patterns: List[Dict[str, str]]  # [{"test": "Hb", "pattern": "low"}]
    supporting_findings: List[str]
    contradictory_findings: List[str]
    differential: List[str]
    confirmatory_evaluation: List[str]
    severity_considerations: str = ""
    emergency_considerations: str = ""
    age_sex_considerations: str = ""
    pregnancy_considerations: str = ""
    limitations: str = ""
    # Hindi translations
    name_hi: str = ""
    short_description_hi: str = ""


@dataclass
class TestDiseaseMapping:
    """Maps a test result pattern to possible disease associations."""
    test_name: str
    result_pattern: str  # "low", "high", "positive", "negative"
    disease_name: str
    relationship: RelationshipType
    association_strength: AssociationStrength
    explanation: str
    explanation_hi: str = ""


class DiseaseKnowledgeEngine:
    """Core engine for disease-laboratory test knowledge."""

    def __init__(self):
        self.diseases: Dict[str, DiseaseRecord] = {}
        self.mappings: List[TestDiseaseMapping] = []
        self._populate_knowledge_base()

    def _populate_knowledge_base(self):
        """Populate the disease knowledge database."""
        self._populate_hematology()
        self._populate_iron_nutrition()
        self._populate_diabetes()
        self._populate_thyroid()
        self._populate_liver()
        self._populate_kidney()
        self._populate_cardiovascular()
        self._populate_coagulation()

    def _populate_hematology(self):
        """Hematological disorders."""
        self.diseases["iron_deficiency_anemia"] = DiseaseRecord(
            name="Iron-Deficiency Anemia",
            common_name="Iron Deficiency",
            medical_term="Iron-Deficiency Anemia",
            synonyms=["iron deficiency", "microcytic anemia", "hypochromic anemia"],
            category=DiseaseCategory.HEMATOLOGICAL,
            organ_system="Blood / Hematopoietic",
            short_description="A condition where the body lacks sufficient iron to produce hemoglobin.",
            detailed_description=(
                "Iron-deficiency anemia occurs when the body does not have enough iron to produce "
                "adequate hemoglobin. Hemoglobin is the protein in red blood cells that carries oxygen. "
                "Without sufficient iron, the body cannot produce enough hemoglobin for red blood cells, "
                "leading to reduced oxygen delivery to tissues."
            ),
            common_causes=[
                "Inadequate dietary iron intake",
                "Chronic blood loss (menstruation, gastrointestinal bleeding)",
                "Poor iron absorption (celiac disease, gastric surgery)",
                "Increased iron requirements (pregnancy, growth)",
            ],
            risk_factors=[
                "Vegetarian/vegan diet without supplementation",
                "Heavy menstrual periods",
                "Frequent blood donation",
                "Infancy and adolescence",
                "Pregnancy",
            ],
            possible_symptoms=[
                "Fatigue and weakness",
                "Pale skin",
                "Shortness of breath during activity",
                "Dizziness or lightheadedness",
                "Cold hands and feet",
                "Brittle nails",
                "Poor concentration",
            ],
            relevant_tests=[
                "Hemoglobin", "MCV", "MCH", "MCHC", "RDW",
                "Ferritin", "Serum Iron", "TIBC", "Transferrin Saturation",
                "Peripheral Blood Smear", "Reticulocyte Count"
            ],
            typical_patterns=[
                {"test": "Hemoglobin", "pattern": "low"},
                {"test": "MCV", "pattern": "low"},
                {"test": "MCH", "pattern": "low"},
                {"test": "Ferritin", "pattern": "low"},
            ],
            supporting_findings=["low hemoglobin", "low MCV", "low MCH", "low ferritin", "high RDW"],
            contradictory_findings=["normal ferritin", "high MCV"],
            differential=[
                "Thalassemia trait",
                "Anemia of chronic disease",
                "Sideroblastic anemia",
            ],
            confirmatory_evaluation=[
                "Iron studies (ferritin, serum iron, TIBC)",
                "Peripheral blood smear",
                "Hemoglobin electrophoresis if indicated",
                "Evaluation for source of blood loss",
            ],
            severity_considerations=(
                "Severity depends on the degree of anemia and the underlying cause. "
                "Mild cases may be asymptomatic, while severe cases may require urgent intervention."
            ),
            emergency_considerations=(
                "Seek immediate medical attention if experiencing chest pain, severe shortness of breath, "
                "or signs of acute blood loss."
            ),
            age_sex_considerations="More common in women of reproductive age due to menstruation.",
            pregnancy_considerations=(
                "Iron needs increase significantly during pregnancy. "
                "Untreated iron deficiency in pregnancy can affect both mother and baby."
            ),
            limitations=(
                "Low hemoglobin alone cannot establish iron deficiency as the cause. "
                "Iron studies and clinical evaluation are needed."
            ),
            name_hi="आयरन की कमी से होने वाला एनीमिया",
            short_description_hi="ऐसी स्थिति जिसमें शरीर में पर्याप्त आयरन न होने के कारण हीमोग्लोबिन कम बनता है।",
        )

        self.diseases["vitamin_b12_deficiency"] = DiseaseRecord(
            name="Vitamin B12 Deficiency",
            common_name="B12 Deficiency",
            medical_term="Cobalamin Deficiency",
            synonyms=["b12 deficiency", "cobalamin deficiency", "macrocytic anemia"],
            category=DiseaseCategory.HEMATOLOGICAL,
            organ_system="Blood / Nervous System",
            short_description="A condition where the body lacks sufficient vitamin B12.",
            detailed_description=(
                "Vitamin B12 is essential for red blood cell production, neurological function, "
                "and DNA synthesis. Deficiency can lead to megaloblastic anemia and neurological problems."
            ),
            common_causes=[
                "Inadequate dietary intake (strict vegan diet)",
                "Pernicious anemia (autoimmune absorption problem)",
                "Malabsorption (Crohn's disease, celiac disease)",
                "Gastric bypass surgery",
                "Certain medications (metformin, PPIs)",
            ],
            risk_factors=[
                "Strict vegan diet without supplementation",
                "Older age",
                "Autoimmune conditions",
                "Gastrointestinal surgery",
            ],
            possible_symptoms=[
                "Fatigue and weakness",
                "Tingling or numbness in hands/feet",
                "Difficulty walking",
                "Memory problems",
                "Glossitis (smooth, red tongue)",
                "Mood changes",
            ],
            relevant_tests=[
                "Vitamin B12", "Methylmalonic Acid", "Homocysteine",
                "CBC", "MCV", "Peripheral Smear", "Anti-intrinsic factor antibodies"
            ],
            typical_patterns=[
                {"test": "Vitamin B12", "pattern": "low"},
                {"test": "MCV", "pattern": "high"},
                {"test": "Hemoglobin", "pattern": "low"},
            ],
            supporting_findings=["low vitamin b12", "high MCV", "low hemoglobin"],
            contradictory_findings=["normal MCV", "normal B12"],
            differential=[
                "Folate deficiency",
                "Myelodysplastic syndrome",
                "Liver disease",
                "Hypothyroidism",
            ],
            confirmatory_evaluation=[
                "Serum B12 level",
                "Methylmalonic acid (MMA)",
                "Homocysteine",
                "Anti-intrinsic factor antibodies",
                "Peripheral blood smear",
            ],
            name_hi="विटामिन B12 की कमी",
            short_description_hi="ऐसी स्थिति जिसमें शरीर में पर्याप्त विटामिन B12 उपलब्ध न हो।",
        )

        # Add mappings for hematology
        self.mappings.extend([
            TestDiseaseMapping(
                test_name="hemoglobin", result_pattern="low",
                disease_name="iron_deficiency_anemia",
                relationship=RelationshipType.COMMON_ASSOCIATION,
                association_strength=AssociationStrength.MODERATE,
                explanation="Low hemoglobin is commonly associated with iron-deficiency anemia, but many other causes are possible.",
                explanation_hi="कम हीमोग्लोबिन अक्सर आयरन की कमी से जुड़ा होता है, लेकिन कई अन्य कारण भी हो सकते हैं।",
            ),
            TestDiseaseMapping(
                test_name="mcv", result_pattern="low",
                disease_name="iron_deficiency_anemia",
                relationship=RelationshipType.SUPPORTING_FINDING,
                association_strength=AssociationStrength.HIGH,
                explanation="Low MCV (microcytosis) is a common finding in iron-deficiency anemia, but also occurs in thalassemia trait.",
                explanation_hi="कम MCV आयरन की कमी में आम है, लेकिin थैलेसीमिया ट्रेट में भी हो सकता है।",
            ),
            TestDiseaseMapping(
                test_name="vitamin_b12", result_pattern="low",
                disease_name="vitamin_b12_deficiency",
                relationship=RelationshipType.DIRECT_ASSOCIATION,
                association_strength=AssociationStrength.HIGH,
                explanation="Low vitamin B12 directly indicates B12 deficiency, which can cause megaloblastic anemia and neurological problems.",
                explanation_hi="कम विटामिन B12 सीधे B12 की कमी को दर्शाता है।",
            ),
        ])

    def _populate_iron_nutrition(self):
        """Iron and nutritional disorders."""
        self.diseases["iron_deficiency"] = DiseaseRecord(
            name="Iron Deficiency",
            common_name="Low Iron",
            medical_term="Iron Deficiency (without anemia)",
            synonyms=["low iron", "low ferritin", "iron depletion"],
            category=DiseaseCategory.IRON_NUTRITIONAL,
            organ_system="Blood / Nutrition",
            short_description="A condition where iron stores are low but hemoglobin may still be normal.",
            detailed_description=(
                "Iron deficiency occurs when the body's iron stores are depleted. "
                "This may occur with or without anemia. Low ferritin is the most common laboratory indicator."
            ),
            common_causes=[
                "Inadequate dietary iron",
                "Chronic blood loss",
                "Poor absorption",
                "Increased demand (pregnancy, growth)",
            ],
            risk_factors=["Vegetarian diet", "Heavy menstruation", "Frequent blood donation"],
            possible_symptoms=[
                "Fatigue",
                "Poor concentration",
                "Hair loss",
                "Restless legs",
                "Brittle nails",
            ],
            relevant_tests=["Ferritin", "Serum Iron", "TIBC", "Transferrin Saturation", "CBC"],
            typical_patterns=[
                {"test": "Ferritin", "pattern": "low"},
                {"test": "Serum Iron", "pattern": "low"},
                {"test": "TIBC", "pattern": "high"},
            ],
            supporting_findings=["low ferritin", "low serum iron", "high TIBC"],
            contradictory_findings=["normal ferritin"],
            differential=["Anemia of chronic disease", "Thalassemia"],
            confirmatory_evaluation=["Complete iron studies", "CBC", "Evaluation for blood loss"],
            name_hi="आयरन की कमी",
            short_description_hi="ऐसी स्थिति जिसमें शरीर में आयरन भंडार कम हो जाता है।",
        )

    def _populate_diabetes(self):
        """Diabetes and glucose disorders."""
        self.diseases["type_2_diabetes"] = DiseaseRecord(
            name="Type 2 Diabetes Mellitus",
            common_name="Type 2 Diabetes",
            medical_term="Type 2 Diabetes Mellitus",
            synonyms=["type 2 diabetes", "adult-onset diabetes", "T2DM"],
            category=DiseaseCategory.DIABETES,
            organ_system="Endocrine / Metabolic",
            short_description="A metabolic disorder characterized by insulin resistance and elevated blood glucose.",
            detailed_description=(
                "Type 2 diabetes is a chronic metabolic condition where the body becomes resistant to insulin "
                "or does not produce enough insulin. This leads to elevated blood glucose levels. "
                "Diagnosis requires specific laboratory criteria and clinical evaluation."
            ),
            common_causes=[
                "Insulin resistance",
                "Genetic predisposition",
                "Obesity and sedentary lifestyle",
                "Age-related metabolic changes",
            ],
            risk_factors=[
                "Overweight or obesity",
                "Family history of diabetes",
                "Physical inactivity",
                "Age over 45",
                "History of gestational diabetes",
                "Polycystic ovary syndrome",
            ],
            possible_symptoms=[
                "Increased thirst",
                "Frequent urination",
                "Unexplained weight loss",
                "Fatigue",
                "Blurred vision",
                "Slow-healing wounds",
                "Tingling in hands or feet",
            ],
            relevant_tests=[
                "Fasting Glucose", "HbA1c", "OGTT", "Random Glucose",
                "Insulin", "C-Peptide", "Urine Glucose", "Ketones"
            ],
            typical_patterns=[
                {"test": "Fasting Glucose", "pattern": "high"},
                {"test": "HbA1c", "pattern": "high"},
                {"test": "Random Glucose", "pattern": "high"},
            ],
            supporting_findings=["high fasting glucose", "high hba1c", "high random glucose"],
            contradictory_findings=["normal fasting glucose", "normal hba1c"],
            differential=[
                "Type 1 diabetes",
                "Prediabetes",
                "Stress hyperglycemia",
                "Steroid-induced hyperglycemia",
                "Cushing syndrome",
            ],
            confirmatory_evaluation=[
                "Fasting plasma glucose on two occasions",
                "HbA1c",
                "Oral glucose tolerance test",
                "Clinical assessment of symptoms",
            ],
            severity_considerations=(
                "Requires ongoing management. Poorly controlled diabetes can lead to complications "
                "affecting eyes, kidneys, nerves, and cardiovascular system."
            ),
            emergency_considerations=(
                "Seek immediate care for very high glucose with symptoms like confusion, "
                "fruity breath, nausea, or vomiting."
            ),
            limitations=(
                "A single elevated glucose value does not establish diabetes. "
                "Diagnostic criteria require specific thresholds on repeat testing or with symptoms."
            ),
            name_hi="टाइप 2 मधुमेह",
            short_description_hi="एक चर्म रोग जिसमें शरीर में इंसुलिन के प्रति प्रतिरोध होता है और रक्त शर्करा बढ़ जाती है।",
        )

        self.diseases["prediabetes"] = DiseaseRecord(
            name="Prediabetes",
            common_name="Borderline Diabetes",
            medical_term="Prediabetes / Impaired Glucose Regulation",
            synonyms=["borderline diabetes", "impaired fasting glucose", "impaired glucose tolerance"],
            category=DiseaseCategory.DIABETES,
            organ_system="Endocrine / Metabolic",
            short_description="A condition where blood glucose is elevated but not high enough for diabetes diagnosis.",
            detailed_description=(
                "Prediabetes means blood glucose levels are higher than normal but not yet high enough "
                "to be diagnosed as diabetes. Lifestyle changes can often prevent progression to diabetes."
            ),
            common_causes=[
                "Insulin resistance developing",
                "Weight gain",
                "Reduced physical activity",
                "Aging",
            ],
            risk_factors=["Overweight", "Family history", "Sedentary lifestyle", "Age"],
            possible_symptoms=[
                "Often no symptoms",
                "Slightly increased thirst",
                "Mild fatigue",
            ],
            relevant_tests=["Fasting Glucose", "HbA1c", "OGTT"],
            typical_patterns=[
                {"test": "Fasting Glucose", "pattern": "borderline"},
                {"test": "HbA1c", "pattern": "borderline"},
            ],
            supporting_findings=["borderline fasting glucose", "borderline hba1c"],
            contradictory_findings=["normal glucose"],
            differential=["Normal variation", "Stress hyperglycemia"],
            confirmatory_evaluation=["Repeat testing", "OGTT", "Clinical assessment"],
            name_hi="प्री-डायबिटीज (डायबिटीज से पहले की स्थिति)",
            short_description_hi="ऐसी स्थिति जिसमें रक्त शर्करा सामान्य से अधिक है लेकिन मधुमेह के स्तर तक नहीं पहुंची है।",
        )

        self.mappings.extend([
            TestDiseaseMapping(
                test_name="fasting_blood_sugar", result_pattern="high",
                disease_name="type_2_diabetes",
                relationship=RelationshipType.SCREENING,
                association_strength=AssociationStrength.MODERATE,
                explanation="Elevated fasting glucose can be associated with diabetes, but requires repeat testing and clinical evaluation for diagnosis.",
                explanation_hi="उच्च उपवास शर्करा मधुमेह से जुड़ी हो सकती है, लेकिन निदान के लिए दोहराव परीक्षण आवश्यक है।",
            ),
            TestDiseaseMapping(
                test_name="hba1c", result_pattern="high",
                disease_name="type_2_diabetes",
                relationship=RelationshipType.SCREENING,
                association_strength=AssociationStrength.HIGH,
                explanation="HbA1c reflects average blood glucose over 2-3 months and is used in diabetes diagnosis according to established criteria.",
                explanation_hi="HbA1c 2-3 महीनों की औसत शर्करा को दर्शाता है और मधुमेह निदान में उपयोग किया जाता है।",
            ),
        ])

    def _populate_thyroid(self):
        """Thyroid disorders."""
        self.diseases["hypothyroidism"] = DiseaseRecord(
            name="Hypothyroidism",
            common_name="Underactive Thyroid",
            medical_term="Primary Hypothyroidism",
            synonyms=["underactive thyroid", "low thyroid", "thyroid deficiency"],
            category=DiseaseCategory.THYROID,
            organ_system="Endocrine / Thyroid",
            short_description="A condition where the thyroid gland does not produce enough thyroid hormones.",
            detailed_description=(
                "Hypothyroidism means the thyroid gland is underactive and does not produce sufficient "
                "thyroid hormones (T4 and T3). These hormones regulate metabolism, energy, and many "
                "bodily functions. Primary hypothyroidism is indicated by elevated TSH with low free T4."
            ),
            common_causes=[
                "Hashimoto's thyroiditis (autoimmune)",
                "Iodine deficiency",
                "Thyroid surgery or radiation",
                "Certain medications",
                "Pituitary disorders (secondary)",
            ],
            risk_factors=["Female sex", "Age over 60", "Autoimmune disease history", "Family history"],
            possible_symptoms=[
                "Fatigue and sluggishness",
                "Weight gain",
                "Cold intolerance",
                "Dry skin and hair",
                "Constipation",
                "Depression",
                "Muscle aches",
                "Heavy menstrual periods",
                "Slowed thinking",
            ],
            relevant_tests=["TSH", "Free T4", "Free T3", "Total T4", "Anti-TPO", "Anti-thyroglobulin"],
            typical_patterns=[
                {"test": "TSH", "pattern": "high"},
                {"test": "Free T4", "pattern": "low"},
            ],
            supporting_findings=["high TSH", "low free T4"],
            contradictory_findings=["normal TSH", "normal free T4"],
            differential=["Subclinical hypothyroidism", "Euthyroid sick syndrome", "Central hypothyroidism"],
            confirmatory_evaluation=["TSH and free T4", "Anti-TPO antibodies", "Clinical assessment"],
            severity_considerations="Untreated hypothyroidism can affect heart, brain, and metabolism.",
            emergency_considerations="Myxedema coma is a rare but life-threatening emergency in severe untreated hypothyroidism.",
            pregnancy_considerations="Thyroid requirements change during pregnancy. Proper monitoring is essential.",
            name_hi="हाइपोथायरॉयिडिज्म (कम थायरॉयड)",
            short_description_hi="ऐसी स्थिति जिसमें थायरॉयड ग्रंथि पर्याप्त थायरॉयड हार्मोन उत्पन्न नहीं कर पाती।",
        )

        self.diseases["hyperthyroidism"] = DiseaseRecord(
            name="Hyperthyroidism",
            common_name="Overactive Thyroid",
            medical_term="Hyperthyroidism / Thyrotoxicosis",
            synonyms=["overactive thyroid", "thyrotoxicosis", "thyroid overactivity"],
            category=DiseaseCategory.THYROID,
            organ_system="Endocrine / Thyroid",
            short_description="A condition where the thyroid gland produces too much thyroid hormone.",
            detailed_description=(
                "Hyperthyroidism means the thyroid is overactive, producing excess thyroid hormones. "
                "This accelerates the body's metabolism. Laboratory findings typically show "
                "low TSH with elevated free T4 and/or free T3."
            ),
            common_causes=[
                "Graves' disease (autoimmune)",
                "Toxic nodular goiter",
                "Thyroiditis (temporary)",
                "Excessive iodine intake",
            ],
            risk_factors=["Female sex", "Family history", "Autoimmune disease", "Stress"],
            possible_symptoms=[
                "Weight loss despite increased appetite",
                "Rapid or irregular heartbeat",
                "Heat intolerance and sweating",
                "Tremor",
                "Anxiety and irritability",
                "Frequent bowel movements",
                "Difficulty sleeping",
                "Enlarged thyroid (goiter)",
            ],
            relevant_tests=["TSH", "Free T4", "Free T3", "Total T3", "TSI", "Anti-TPO"],
            typical_patterns=[
                {"test": "TSH", "pattern": "low"},
                {"test": "Free T4", "pattern": "high"},
            ],
            supporting_findings=["low TSH", "high free T4", "high free T3"],
            contradictory_findings=["normal TSH"],
            differential=["Thyroiditis", "Exogenous thyroid hormone", "Toxic nodule"],
            confirmatory_evaluation=["TSH, free T4, free T3", "TSI antibodies", "Thyroid ultrasound", "Radioactive iodine uptake"],
            name_hi="हाइपरथायरॉयिडिज्म (अधिक थायरॉयड)",
            short_description_hi="ऐसी स्थिति जिसमें थायरॉयड ग्रंथि अत्यधिक थायरॉयड हार्मोन उत्पन्न करती है।",
        )

        self.mappings.extend([
            TestDiseaseMapping(
                test_name="tsh", result_pattern="high",
                disease_name="hypothyroidism",
                relationship=RelationshipType.DIRECT_ASSOCIATION,
                association_strength=AssociationStrength.HIGH,
                explanation="Elevated TSH typically indicates the pituitary is trying to stimulate an underactive thyroid (primary hypothyroidism).",
                explanation_hi="उच्च TSH आमतौर पर पिट्यूटरी ग्रंथि के थायरॉयड को उत्तेजित करने का प्रयास कर रही है।",
            ),
            TestDiseaseMapping(
                test_name="tsh", result_pattern="low",
                disease_name="hyperthyroidism",
                relationship=RelationshipType.DIRECT_ASSOCIATION,
                association_strength=AssociationStrength.HIGH,
                explanation="Low TSH typically indicates the pituitary is suppressing TSH due to excess thyroid hormones.",
                explanation_hi="कम TSH अत्यधिक थायरॉयड हार्मोन के कारण पिट्यूटरी ग्रंथि द्वारा दबाव है।",
            ),
        ])

    def _populate_liver(self):
        """Liver and hepatobiliary conditions."""
        self.diseases["nafld"] = DiseaseRecord(
            name="Non-Alcoholic Fatty Liver Disease",
            common_name="Fatty Liver",
            medical_term="Non-Alcoholic Fatty Liver Disease (NAFLD)",
            synonyms=["fatty liver", "hepatic steatosis", "NAFLD", "MASLD"],
            category=DiseaseCategory.LIVER,
            organ_system="Hepatobiliary",
            short_description="Accumulation of excess fat in the liver not caused by alcohol.",
            detailed_description=(
                "NAFLD is a condition where excess fat builds up in liver cells. "
                "It is associated with metabolic factors like obesity, insulin resistance, and dyslipidemia. "
                "Laboratory findings often show elevated ALT and AST."
            ),
            common_causes=[
                "Insulin resistance and metabolic syndrome",
                "Obesity",
                "Sedentary lifestyle",
                "Unhealthy diet",
                "Genetic factors",
            ],
            risk_factors=["Obesity", "Type 2 diabetes", "High cholesterol", "Sedentary lifestyle", "Age"],
            possible_symptoms=[
                "Often no symptoms in early stages",
                "Fatigue",
                "Mild right upper abdominal discomfort",
                "Elevated liver enzymes on routine testing",
            ],
            relevant_tests=["ALT", "AST", "GGT", "ALP", "Bilirubin", "Albumin", "Ultrasound", "FibroScan"],
            typical_patterns=[
                {"test": "ALT", "pattern": "high"},
                {"test": "AST", "pattern": "high"},
                {"test": "AST_ALT_ratio", "pattern": "less_than_1"},
            ],
            supporting_findings=["elevated ALT", "elevated AST", "elevated GGT"],
            contradictory_findings=["normal ALT", "AST/ALT ratio > 2"],
            differential=["Alcoholic liver disease", "Viral hepatitis", "Drug-induced liver injury", "Autoimmune hepatitis"],
            confirmatory_evaluation=["Liver function tests", "Hepatitis serologies", "Liver ultrasound", "FibroScan", "Clinical assessment"],
            name_hi="गैर-शराब फैटी लिवर रोग",
            short_description_hi="लिवर में अतिरिक्त वसा का जमा होना जो शराब से नहीं होता।",
        )

        self.mappings.extend([
            TestDiseaseMapping(
                test_name="alt", result_pattern="high",
                disease_name="nafld",
                relationship=RelationshipType.COMMON_ASSOCIATION,
                association_strength=AssociationStrength.MODERATE,
                explanation="Elevated ALT can indicate liver cell injury. It can occur in fatty liver disease, viral hepatitis, alcohol use, medications, and other conditions.",
                explanation_hi="उच्च ALT लिवर कोशिका क्षति का संकेत हो सकता है। फैटी लिवर, वायरल हेपेटाइटिस, शराब और अन्य कारण हो सकते हैं।",
            ),
            TestDiseaseMapping(
                test_name="ast", result_pattern="high",
                disease_name="nafld",
                relationship=RelationshipType.COMMON_ASSOCIATION,
                association_strength=AssociationStrength.MODERATE,
                explanation="Elevated AST can indicate liver or muscle injury. In NAFLD, ALT is often higher than AST.",
                explanation_hi="उच्च AST लिवर या मांसपेशी क्षति का संकेत है।",
            ),
        ])

    def _populate_kidney(self):
        """Kidney and renal conditions."""
        self.diseases["ckd"] = DiseaseRecord(
            name="Chronic Kidney Disease",
            common_name="Chronic Kidney Disease",
            medical_term="Chronic Kidney Disease (CKD)",
            synonyms=["chronic kidney disease", "CKD", "reduced kidney function", "renal insufficiency"],
            category=DiseaseCategory.KIDNEY,
            organ_system="Renal / Urinary",
            short_description="Progressive loss of kidney function over time.",
            detailed_description=(
                "Chronic kidney disease is the gradual loss of kidney function. "
                "The kidneys filter waste and excess fluid from blood. "
                "Reduced eGFR and/or markers of kidney damage indicate CKD."
            ),
            common_causes=[
                "Diabetes mellitus",
                "Hypertension",
                "Glomerulonephritis",
                "Polycystic kidney disease",
                "Chronic urinary obstruction",
            ],
            risk_factors=["Diabetes", "High blood pressure", "Age", "Family history", "Smoking", "Obesity"],
            possible_symptoms=[
                "Often no symptoms in early stages",
                "Fatigue and weakness",
                "Swelling in legs and ankles",
                "Changes in urination",
                "Nausea and loss of appetite",
                "Difficulty concentrating",
                "High blood pressure",
            ],
            relevant_tests=[
                "Creatinine", "eGFR", "BUN", "Urea", "Urine Protein",
                "Urine Albumin", "ACR", "Electrolytes", "CBC", "Phosphate", "PTH"
            ],
            typical_patterns=[
                {"test": "Creatinine", "pattern": "high"},
                {"test": "eGFR", "pattern": "low"},
                {"test": "BUN", "pattern": "high"},
            ],
            supporting_findings=["high creatinine", "low eGFR", "high BUN", "proteinuria"],
            contradictory_findings=["normal creatinine", "normal eGFR"],
            differential=["Acute kidney injury", "Pre-renal azotemia"],
            confirmatory_evaluation=["Creatinine and eGFR on two occasions 3 months apart", "Urinalysis", "Renal ultrasound", "Urine ACR"],
            severity_considerations="CKD is staged by eGFR. Early detection can slow progression.",
            emergency_considerations="Seek immediate care for sudden decrease in urine output, severe swelling, or confusion.",
            pregnancy_considerations="Kidney function changes during pregnancy. Close monitoring is needed in CKD.",
            name_hi="पुराणी गुर्दे की बीमारी (CKD)",
            short_description_hi="समय के साथ गुर्दे के कार्य में धीरे-धीरे कमी।",
        )

        self.mappings.extend([
            TestDiseaseMapping(
                test_name="creatinine", result_pattern="high",
                disease_name="ckd",
                relationship=RelationshipType.SUPPORTING_FINDING,
                association_strength=AssociationStrength.HIGH,
                explanation="Elevated creatinine indicates reduced kidney filtration. It requires eGFR calculation and repeat testing for CKD diagnosis.",
                explanation_hi="उच्च क्रिएटिनिन कम गुर्दा छनन दर को दर्शाता है। CKD निदान के लिए eGFR और दोहराव परीक्षण आवश्यक है।",
            ),
            TestDiseaseMapping(
                test_name="egfr", result_pattern="low",
                disease_name="ckd",
                relationship=RelationshipType.DIRECT_ASSOCIATION,
                association_strength=AssociationStrength.HIGH,
                explanation="eGFR below 60 for 3+ months indicates CKD. Staging is based on eGFR level.",
                explanation_hi="60 से कम eGFR 3 महीने से अधिक के लिए CKD को दर्शाता है।",
            ),
        ])

    def _populate_cardiovascular(self):
        """Cardiovascular and lipid conditions."""
        self.diseases["dyslipidemia"] = DiseaseRecord(
            name="Dyslipidemia",
            common_name="Abnormal Cholesterol",
            medical_term="Dyslipidemia",
            synonyms=["high cholesterol", "abnormal lipids", "hyperlipidemia"],
            category=DiseaseCategory.CARDIOVASCULAR,
            organ_system="Cardiovascular / Metabolic",
            short_description="Abnormal levels of lipids (fats) in the blood.",
            detailed_description=(
                "Dyslipidemia refers to abnormal levels of cholesterol and/or triglycerides in the blood. "
                "Elevated LDL cholesterol and low HDL cholesterol are associated with increased cardiovascular risk. "
                "However, laboratory values alone do not establish cardiovascular disease."
            ),
            common_causes=[
                "Diet high in saturated fats",
                "Sedentary lifestyle",
                "Genetic factors",
                "Diabetes",
                "Hypothyroidism",
                "Obesity",
            ],
            risk_factors=["Poor diet", "Physical inactivity", "Obesity", "Smoking", "Family history", "Age"],
            possible_symptoms=[
                "Usually no symptoms",
                "May contribute to cardiovascular risk over time",
                "Xanthomas (fatty deposits under skin) in severe cases",
            ],
            relevant_tests=[
                "Total Cholesterol", "LDL", "HDL", "Triglycerides", "Non-HDL",
                "ApoB", "Lipoprotein(a)", "Total/HDL Ratio", "LDL/HDL Ratio"
            ],
            typical_patterns=[
                {"test": "Total Cholesterol", "pattern": "high"},
                {"test": "LDL", "pattern": "high"},
                {"test": "HDL", "pattern": "low"},
                {"test": "Triglycerides", "pattern": "high"},
            ],
            supporting_findings=["high LDL", "low HDL", "high triglycerides", "high total cholesterol"],
            contradictory_findings=["normal LDL", "normal total cholesterol"],
            differential=["Familial hypercholesterolemia", "Secondary causes (diabetes, hypothyroidism, nephrotic syndrome)"],
            confirmatory_evaluation=["Fasting lipid panel", "Cardiovascular risk assessment", "Evaluation for secondary causes"],
            severity_considerations="Risk depends on overall cardiovascular risk profile, not just individual values.",
            limitations="An abnormal lipid result alone does not mean the patient has heart disease. It is a risk factor.",
            name_hi="डिसलिपिडेमिया (रक्त में वसा का असामान्य स्तर)",
            short_description_hi="रक्त में कोलेस्ट्रॉल और ट्राइग्लिसराइड्स का असामान्य स्तर।",
        )

        self.mappings.extend([
            TestDiseaseMapping(
                test_name="total_cholesterol", result_pattern="high",
                disease_name="dyslipidemia",
                relationship=RelationshipType.DIRECT_ASSOCIATION,
                association_strength=AssociationStrength.HIGH,
                explanation="Elevated total cholesterol indicates dyslipidemia. Cardiovascular risk assessment considers the full lipid profile.",
                explanation_hi="उच्च कुल कोलेस्ट्रॉल डिसलिपिडेमिया को दर्शाता है। हृदय जोखिम का मूल्यांकन पूर्ण लिपिड प्रोफाइल पर निर्भर करता है।",
            ),
            TestDiseaseMapping(
                test_name="ldl_cholesterol", result_pattern="high",
                disease_name="dyslipidemia",
                relationship=RelationshipType.DIRECT_ASSOCIATION,
                association_strength=AssociationStrength.HIGH,
                explanation="Elevated LDL cholesterol is a major modifiable cardiovascular risk factor.",
                explanation_hi="उच्च LDL कोलेस्ट्रॉल एक प्रमुख संशोधन योग्य हृदय जोखिम कारक है।",
            ),
        ])

    def _populate_coagulation(self):
        """Coagulation disorders."""
        self.diseases["iron_deficiency_coagulation"] = DiseaseRecord(
            name="Iron Deficiency",
            common_name="Low Iron",
            medical_term="Iron Deficiency",
            synonyms=[],
            category=DiseaseCategory.COAGULATION,
            organ_system="Blood / Nutrition",
            short_description="Iron deficiency.",
            detailed_description="Iron deficiency can affect multiple systems.",
            common_causes=["Diet", "Blood loss", "Malabsorption"],
            risk_factors=["Diet", "Menstruation"],
            possible_symptoms=["Fatigue", "Weakness", "Pale skin"],
            relevant_tests=["Ferritin", "Iron", "TIBC"],
            typical_patterns=[{"test": "Ferritin", "pattern": "low"}],
            supporting_findings=["low ferritin"],
            contradictory_findings=["normal ferritin"],
            differential=["Anemia of chronic disease"],
            confirmatory_evaluation=["Iron studies"],
            name_hi="आयरन की कमी",
            short_description_hi="आयरन की कमी।",
        )

    def find_associated_diseases(
        self,
        test_name: str,
        result_status: str,
        available_tests: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find diseases possibly associated with a test result."""
        available_tests = available_tests or []
        associations = []

        for mapping in self.mappings:
            if (mapping.test_name.lower() in test_name.lower() and
                mapping.result_pattern == result_status):
                disease = self.diseases.get(mapping.disease_name)
                if disease:
                    # Calculate supporting/missing evidence
                    supporting = [
                        f for f in disease.supporting_findings
                        if any(f.lower() in t.lower() for t in available_tests)
                    ]
                    missing = [
                        f for f in disease.supporting_findings
                        if not any(f.lower() in t.lower() for t in available_tests)
                    ]

                    associations.append({
                        "disease_key": mapping.disease_name,
                        "name": disease.name,
                        "common_name": disease.common_name,
                        "category": disease.category.value,
                        "organ_system": disease.organ_system,
                        "short_description": disease.short_description,
                        "name_hi": disease.name_hi,
                        "short_description_hi": disease.short_description_hi,
                        "relationship": mapping.relationship.value,
                        "association_strength": mapping.association_strength.value,
                        "explanation": mapping.explanation,
                        "explanation_hi": mapping.explanation_hi,
                        "possible_symptoms": disease.possible_symptoms,
                        "relevant_tests": disease.relevant_tests,
                        "supporting_evidence": supporting,
                        "missing_evidence": missing,
                        "differential": disease.differential,
                        "confirmatory_evaluation": disease.confirmatory_evaluation,
                        "does_not_prove": disease.limitations,
                    })

        # Sort by association strength
        strength_order = {
            AssociationStrength.HIGH: 0,
            AssociationStrength.MODERATE: 1,
            AssociationStrength.LOW: 2,
            AssociationStrength.INSUFFICIENT_DATA: 3,
        }
        associations.sort(key=lambda x: strength_order.get(x["association_strength"], 4))

        return associations

    def get_disease(self, disease_key: str) -> Optional[DiseaseRecord]:
        """Get a disease record by key."""
        return self.diseases.get(disease_key)

    def search_diseases(self, query: str, category: Optional[DiseaseCategory] = None) -> List[DiseaseRecord]:
        """Search diseases by name, synonym or category."""
        results = []
        query_lower = query.lower()

        for disease in self.diseases.values():
            if category and disease.category != category:
                continue
            if (query_lower in disease.name.lower() or
                query_lower in disease.common_name.lower() or
                any(query_lower in syn.lower() for syn in disease.synonyms)):
                results.append(disease)

        return results


# Singleton instance
knowledge_engine = DiseaseKnowledgeEngine()

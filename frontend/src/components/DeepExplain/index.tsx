import { useState, useEffect } from 'react';
import { X, AlertTriangle, CheckCircle, AlertCircle, Info, ChevronDown, ChevronUp, Eye, Edit3, HelpCircle, TrendingUp, FlaskConical, Stethoscope, Shield, Activity, FileText, History, MessageCircle, Check, XCircle, Search } from 'lucide-react';
import api from '../../services/api';

interface DeepExplainProps {
  reportId: number;
  testId: number;
  testName: string;
  result: number | string | null;
  unit: string;
  referenceRange: string;
  status: string;
  language: string;
  onClose: () => void;
}

interface DeepExplanationData {
  test_name: string;
  result: string;
  unit: string;
  reference_range: string;
  status: string;
  priority: string;
  confidence: string;
  what_it_mean: string;
  why_it_matters: string;
  why_flagged: string;
  medical_explanation: string;
  simple_explanation: string;
  possible_associations: Array<{
    condition: string;
    what_it_is: string;
    why_associated: string;
    supporting_findings: string[];
    missing_info: string[];
    confidence: string;
  }>;
  common_causes: string[];
  other_causes: string[];
  less_common_causes: string[];
  pattern_analysis: string;
  related_tests: Array<{
    name: string;
    why_relevant: string;
    current_value: string | null;
    status: string | null;
    available: boolean;
  }>;
  possible_symptoms: string[];
  what_it_does_not_prove: string[];
  trend: {
    previous_value: string | null;
    current_value: string;
    change: string;
    direction: string;
  } | null;
  missing_information: string[];
  doctor_questions: string[];
  next_steps: string[];
  safety_warning: string | null;
  source_page: string | null;
  ai_confidence: string;
  disease_associations: Array<{
    name: string;
    common_name: string;
    name_hi: string;
    short_description: string;
    association_strength: string;
    explanation: string;
    possible_symptoms: string[];
    relevant_tests: string[];
    supporting_evidence: string[];
    missing_evidence: string[];
    differential: string[];
    confirmatory_evaluation: string[];
    does_not_prove: string;
  }>;
}

export default function DeepExplain({
  reportId,
  testId,
  testName,
  result,
  unit,
  referenceRange,
  status,
  language,
  onClose,
}: DeepExplainProps) {
  const [data, setData] = useState<DeepExplanationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    overview: true,
    explanation: true,
    associations: true,
    related: false,
    symptoms: false,
    trend: false,
    safety: true,
  });
  const [showOriginal, setShowOriginal] = useState(false);
  const [exploringDisease, setExploringDisease] = useState<number | null>(null);

  useEffect(() => {
    fetchDeepExplanation();
  }, [reportId, testId]);

  const fetchDeepExplanation = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/reports/${reportId}/deep-explain/${testId}?language=${language}`);
      setData(res.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load deep explanation');
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const getPriorityColor = (priority: string) => {
    if (priority.includes('🔴')) return 'text-red-600 bg-red-50 border-red-200';
    if (priority.includes('🟠')) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  };

  const getStatusColor = (status: string) => {
    if (status === 'normal') return 'text-green-600';
    if (status === 'borderline') return 'text-yellow-600';
    if (status === 'low' || status === 'high') return 'text-orange-600';
    if (status.startsWith('critically')) return 'text-red-600';
    return 'text-gray-600';
  };

  const getConfidenceColor = (confidence: string) => {
    if (confidence === 'HIGH') return 'text-green-600';
    if (confidence === 'MODERATE') return 'text-yellow-600';
    if (confidence === 'LOW') return 'text-orange-600';
    return 'text-red-600';
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 max-w-lg w-full mx-4">
          <div className="flex items-center justify-center gap-3">
            <Activity className="w-6 h-6 text-blue-600 animate-pulse" />
            <span className="text-lg font-medium text-gray-700">Generating deep explanation...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
        <div className="bg-white rounded-2xl p-8 max-w-lg w-full mx-4">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <p className="text-gray-700">{error}</p>
            <button onClick={onClose} className="mt-4 btn-secondary">Close</button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end md:items-center justify-center">
      <div className="bg-white rounded-t-2xl md:rounded-2xl w-full md:max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FlaskConical className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Deep Explain</h2>
              <p className="text-sm text-gray-500">{testName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {/* Overview Card */}
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xl font-bold text-gray-900">{testName}</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(data.priority)}`}>
                {data.priority}
              </span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white rounded-lg p-3 border border-gray-100">
                <p className="text-xs text-gray-500 mb-1">Your Result</p>
                <p className={`text-2xl font-bold ${getStatusColor(data.status)}`}>
                  {result} <span className="text-sm font-normal text-gray-500">{unit}</span>
                </p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-gray-100">
                <p className="text-xs text-gray-500 mb-1">Reference Range</p>
                <p className="text-lg font-medium text-gray-700">{referenceRange || 'N/A'}</p>
              </div>
            </div>
            <div className="mt-3 flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1">
                <Info className="w-4 h-4 text-gray-400" />
                <span className="text-gray-500">Status:</span>
                <span className={`font-medium ${getStatusColor(data.status)}`}>{data.status}</span>
              </span>
              <span className="flex items-center gap-1">
                <Shield className="w-4 h-4 text-gray-400" />
                <span className="text-gray-500">Confidence:</span>
                <span className={`font-medium ${getConfidenceColor(data.ai_confidence)}`}>{data.ai_confidence}</span>
              </span>
            </div>
          </div>

          {/* Why It Is Flagged */}
          <Section
            title="Why Is This Flagged?"
            icon={<AlertTriangle className="w-4 h-4 text-yellow-600" />}
            expanded={expandedSections.explanation}
            onToggle={() => toggleSection('explanation')}
          >
            <p className="text-gray-700 leading-relaxed">{data.why_flagged}</p>
          </Section>

          {/* What Does It Measure */}
          <Section
            title="What Does This Test Measure?"
            icon={<FlaskConical className="w-4 h-4 text-blue-600" />}
            expanded={expandedSections.explanation}
            onToggle={() => toggleSection('explanation')}
          >
            <p className="text-gray-700 leading-relaxed">{data.what_it_mean}</p>
          </Section>

          {/* Medical Explanation */}
          <Section
            title="Medical Explanation"
            icon={<Stethoscope className="w-4 h-4 text-indigo-600" />}
            expanded={expandedSections.explanation}
            onToggle={() => toggleSection('explanation')}
          >
            <div className="space-y-3">
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">Medical</p>
                <p className="text-gray-700 leading-relaxed">{data.medical_explanation}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500 mb-1">Simple Explanation</p>
                <p className="text-gray-700 leading-relaxed">{data.simple_explanation}</p>
              </div>
            </div>
          </Section>

          {/* Possible Associations */}
          <Section
            title="🧬 Possible Health Conditions"
            icon={<Activity className="w-4 h-4 text-purple-600" />}
            expanded={expandedSections.associations}
            onToggle={() => toggleSection('associations')}
          >
            <div className="space-y-4">
              {data.possible_associations.map((assoc, i) => (
                <div key={i} className="bg-purple-50 rounded-lg p-4 border border-purple-100">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-purple-900">{assoc.condition}</h4>
                    <span className={`text-xs px-2 py-1 rounded-full bg-purple-100 text-purple-700`}>
                      {assoc.confidence}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mb-2">{assoc.what_it_is}</p>
                  <p className="text-sm text-gray-600">{assoc.why_associated}</p>
                  {assoc.supporting_findings.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-gray-500">Supporting findings:</p>
                      <ul className="text-xs text-gray-600 list-disc list-inside">
                        {assoc.supporting_findings.map((f, j) => (
                          <li key={j}>{f}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {assoc.missing_info.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium text-gray-500">Missing information:</p>
                      <ul className="text-xs text-gray-600 list-disc list-inside">
                        {assoc.missing_info.map((m, j) => (
                          <li key={j}>{m}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Common Causes */}
            {data.common_causes.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Common / Relevant Associations:</h4>
                <ul className="space-y-1">
                  {data.common_causes.map((cause, i) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
                      {cause}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Disease Knowledge Cards */}
            {data.disease_associations && data.disease_associations.length > 0 && (
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">🧬 Possible Health Conditions:</h4>
                <div className="space-y-2">
                  {data.disease_associations.map((disease, i) => (
                    <div key={i} className="bg-purple-50 rounded-lg p-3 border border-purple-100">
                      <div className="flex items-center justify-between mb-1">
                        <h5 className="font-medium text-purple-900 text-sm">{disease.name}</h5>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${disease.association_strength === 'high' ? 'bg-green-100 text-green-700' : disease.association_strength === 'moderate' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-700'}`}>
                          {disease.association_strength}
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mb-2">{disease.short_description}</p>
                      <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>Supporting: {disease.supporting_evidence.length}</span>
                        <span>•</span>
                        <span>Missing: {disease.missing_evidence.length}</span>
                      </div>
                      <button
                        onClick={() => setExploringDisease(exploringDisease === i ? null : i)}
                        className="mt-2 text-xs text-purple-600 hover:text-purple-800 font-medium flex items-center gap-1"
                      >
                        <Search className="w-3 h-3" />
                        {exploringDisease === i ? 'Hide Details' : 'Explore'}
                      </button>
                      {exploringDisease === i && (
                        <div className="mt-3 pt-3 border-t border-purple-200 space-y-2">
                          <div>
                            <p className="text-xs font-medium text-gray-600">Why it may be relevant:</p>
                            <p className="text-xs text-gray-600">{disease.explanation}</p>
                          </div>
                          {disease.supporting_evidence.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-green-700">Supporting Evidence:</p>
                              <ul className="text-xs text-green-600 list-disc list-inside">
                                {disease.supporting_evidence.map((e, j) => <li key={j}>{e}</li>)}
                              </ul>
                            </div>
                          )}
                          {disease.missing_evidence.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-red-700">Missing Evidence:</p>
                              <ul className="text-xs text-red-600 list-disc list-inside">
                                {disease.missing_evidence.map((e, j) => <li key={j}>{e}</li>)}
                              </ul>
                            </div>
                          )}
                          {disease.differential.length > 0 && (
                            <div>
                              <p className="text-xs font-medium text-gray-600">Differential:</p>
                              <p className="text-xs text-gray-500">{disease.differential.join(', ')}</p>
                            </div>
                          )}
                          <div className="bg-amber-50 rounded p-2 border border-amber-100">
                            <p className="text-xs text-amber-800">
                              <strong>⚠️ Does NOT prove:</strong> {disease.does_not_prove}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Section>

          {/* Pattern Analysis */}
          {data.pattern_analysis && (
            <Section
              title="📊 Pattern Analysis"
              icon={<Activity className="w-4 h-4 text-cyan-600" />}
              expanded={expandedSections.associations}
              onToggle={() => toggleSection('associations')}
            >
              <p className="text-gray-700 leading-relaxed">{data.pattern_analysis}</p>
            </Section>
          )}

          {/* Related Tests */}
          <Section
            title="🔬 Related Tests"
            icon={<FlaskConical className="w-4 h-4 text-teal-600" />}
            expanded={expandedSections.related}
            onToggle={() => toggleSection('related')}
          >
            <div className="space-y-2">
              {data.related_tests.map((test, i) => (
                <div key={i} className={`p-3 rounded-lg border ${test.available ? 'bg-green-50 border-green-100' : 'bg-gray-50 border-gray-100'}`}>
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{test.name}</span>
                    {test.available ? (
                      <span className="text-sm text-green-600">{test.current_value} ({test.status})</span>
                    ) : (
                      <span className="text-sm text-gray-400">Not in report</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{test.why_relevant}</p>
                </div>
              ))}
            </div>
          </Section>

          {/* Possible Symptoms */}
          <Section
            title="🩺 Possible Symptoms"
            icon={<Stethoscope className="w-4 h-4 text-rose-600" />}
            expanded={expandedSections.symptoms}
            onToggle={() => toggleSection('symptoms')}
          >
            <p className="text-sm text-gray-500 mb-3">
              Symptoms can vary and are not specific to this finding. Some people may experience:
            </p>
            <ul className="space-y-1">
              {data.possible_symptoms.map((symptom, i) => (
                <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                  <span className="text-gray-400">•</span>
                  {symptom}
                </li>
              ))}
            </ul>
          </Section>

          {/* Trend Analysis */}
          {data.trend && (
            <Section
              title="📈 Trend Analysis"
              icon={<TrendingUp className="w-4 h-4 text-indigo-600" />}
              expanded={expandedSections.trend}
              onToggle={() => toggleSection('trend')}
            >
              <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-500">Previous</span>
                  <span className="text-sm text-gray-500">Current</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-700">{data.trend.previous_value || 'N/A'}</span>
                  <span className="text-indigo-600">→</span>
                  <span className="font-medium text-indigo-700">{data.trend.current_value}</span>
                </div>
                <p className="text-sm text-gray-600 mt-2">{data.trend.change}</p>
              </div>
            </Section>
          )}

          {/* What It Does NOT Prove */}
          <Section
            title="⚠️ What This Result Does NOT Prove"
            icon={<Shield className="w-4 h-4 text-amber-600" />}
            expanded={expandedSections.safety}
            onToggle={() => toggleSection('safety')}
            variant="warning"
          >
            <ul className="space-y-2">
              {data.what_it_does_not_prove.map((item, i) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </Section>

          {/* Doctor Questions */}
          <Section
            title="👨‍⚕️ Questions for Your Doctor"
            icon={<HelpCircle className="w-4 h-4 text-blue-600" />}
            expanded={expandedSections.safety}
            onToggle={() => toggleSection('safety')}
          >
            <ul className="space-y-2">
              {data.doctor_questions.map((q, i) => (
                <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                  <span className="text-blue-600 font-bold">{i + 1}.</span>
                  {q}
                </li>
              ))}
            </ul>
          </Section>

          {/* Missing Information */}
          {data.missing_information && data.missing_information.length > 0 && (
            <Section
              title="❓ Missing Information"
              icon={<Info className="w-4 h-4 text-gray-600" />}
              expanded={expandedSections.missing}
              onToggle={() => toggleSection('missing')}
            >
              <p className="text-sm text-gray-500 mb-2">
                Because the following information is unavailable, the underlying cause cannot be determined from this report alone:
              </p>
              <ul className="space-y-1">
                {data.missing_information.map((item, i) => (
                  <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                    <XCircle className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {/* Next Steps */}
          <div className="bg-green-50 rounded-xl p-4 border border-green-200">
            <h4 className="font-medium text-green-900 mb-2 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" />
              General Next Steps
            </h4>
            <ul className="space-y-1">
              {data.next_steps.map((step, i) => (
                <li key={i} className="text-sm text-green-800 flex items-start gap-2">
                  <span className="text-green-600">✓</span>
                  {step}
                </li>
              ))}
            </ul>
          </div>

          {/* Safety Warning */}
          {data.safety_warning && (
            <div className="bg-red-50 rounded-xl p-4 border border-red-200">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
                <div>
                  <h4 className="font-medium text-red-900 mb-1">High-Priority Result</h4>
                  <p className="text-sm text-red-800">{data.safety_warning}</p>
                </div>
              </div>
            </div>
          )}

          {/* Original Report Verification */}
          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex items-center gap-3 mb-3">
              <button
                onClick={() => setShowOriginal(!showOriginal)}
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                <Eye className="w-4 h-4" />
                View Original
              </button>
              <button className="flex items-center gap-2 text-sm text-green-600 hover:text-green-800 font-medium">
                <Check className="w-4 h-4" />
                Verify Value
              </button>
              <button className="flex items-center gap-2 text-sm text-orange-600 hover:text-orange-800 font-medium">
                <Edit3 className="w-4 h-4" />
                Correct Value
              </button>
            </div>
            {showOriginal && (
              <div className="mt-3 p-4 bg-gray-100 rounded-lg">
                <p className="text-sm text-gray-600">
                  Source: {data.source_page || 'Report Page 1'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Click to view the original report image with highlighted region.
                </p>
              </div>
            )}
          </div>

          {/* AI Confidence */}
          <div className="bg-gray-50 rounded-lg p-3 border border-gray-200">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">AI Interpretation Confidence</span>
              <span className={`text-sm font-medium ${getConfidenceColor(data.ai_confidence)}`}>
                {data.ai_confidence}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              This indicates data reliability, not disease probability.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50">
          <div className="bg-amber-50 rounded-lg p-3 border border-amber-200 mb-3">
            <p className="text-xs text-amber-800 text-center">
              <strong>⚠️ Safety Notice:</strong> LabLens AI provides educational explanations of laboratory reports.
              It does not replace a qualified healthcare professional and does not establish a diagnosis.
              Laboratory findings should be interpreted together with symptoms, medical history, examination and other relevant information.
            </p>
          </div>
          <p className="text-xs text-gray-500 text-center">
            AI Confidence: {data.ai_confidence} • Evidence-based analysis • Not a diagnosis
          </p>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  icon,
  expanded,
  onToggle,
  children,
  variant = 'default',
}: {
  title: string;
  icon: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  variant?: 'default' | 'warning';
}) {
  const bgColor = variant === 'warning' ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-200';

  return (
    <div className={`rounded-xl border ${bgColor} overflow-hidden`}>
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        )}
      </button>
      {expanded && <div className="px-4 pb-4">{children}</div>}
    </div>
  );
}

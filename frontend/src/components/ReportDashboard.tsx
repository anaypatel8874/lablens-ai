import { AlertTriangle, CheckCircle, AlertCircle, Info, Search } from 'lucide-react'
import { useState } from 'react'
import DeepExplain from './DeepExplain'

export default function ReportDashboard({ data }: { data: any }) {
  const { summary, status_counts, report } = data
  const [deepExplainTest, setDeepExplainTest] = useState<any>(null)

  console.log('[ReportDashboard] Render:', {
    hasReport: !!report,
    testCount: report?.test_results?.length,
    attentionCount: report?.test_results?.filter((t: any) => t.status !== 'normal' && t.status !== 'unknown' && t.status !== 'missing').length,
    deepExplainTest: deepExplainTest?.test_name || null
  })

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Normal" value={status_counts?.normal || 0} color="green" icon={<CheckCircle className="w-5 h-5" />} />
        <StatCard label="Attention" value={(status_counts?.borderline || 0) + (status_counts?.low || 0) + (status_counts?.high || 0)} color="yellow" icon={<AlertCircle className="w-5 h-5" />} />
        <StatCard label="High Priority" value={(status_counts?.critically_low || 0) + (status_counts?.critically_high || 0)} color="red" icon={<AlertTriangle className="w-5 h-5" />} />
        <StatCard label="Total Tests" value={report.test_results?.length || 0} color="blue" icon={<Info className="w-5 h-5" />} />
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">Overall Summary</h3>
        <p className="text-gray-700 leading-relaxed">{summary.overall_summary}</p>
      </div>

      {summary.high_priority_findings?.length > 0 && (
        <div className="card border-red-200 bg-red-50">
          <h3 className="text-lg font-semibold text-red-900 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" /> High Priority Findings
          </h3>
          <ul className="space-y-2">
            {summary.high_priority_findings.map((f: string, i: number) => (
              <li key={i} className="text-red-800 text-sm">• {f}</li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-red-700 font-medium">Please consult a healthcare professional promptly regarding these findings.</p>
        </div>
      )}

      {summary.attention_findings?.length > 0 && (
        <div className="card border-yellow-200 bg-yellow-50">
          <h3 className="text-lg font-semibold text-yellow-900 mb-3 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" /> Findings Requiring Attention
          </h3>
          <ul className="space-y-2">
            {summary.attention_findings.map((f: string, i: number) => (
              <li key={i} className="text-yellow-800 text-sm">• {f}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="card overflow-x-auto">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Detailed Results</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 font-medium text-gray-500">Test</th>
              <th className="text-left py-2 font-medium text-gray-500">Result</th>
              <th className="text-left py-2 font-medium text-gray-500">Reference</th>
              <th className="text-left py-2 font-medium text-gray-500">Status</th>
              <th className="text-left py-2 font-medium text-gray-500">Action</th>
            </tr>
          </thead>
          <tbody>
            {report.test_results?.map((t: any) => {
              const isAttention = t.status !== 'normal' && t.status !== 'unknown' && t.status !== 'missing'
              return (
                <tr key={t.id} className={`border-b border-gray-100 hover:bg-gray-50 ${isAttention ? 'bg-yellow-50/50' : ''}`}>
                  <td className="py-3 font-medium text-gray-900">{t.test_name}</td>
                  <td className="py-3">{t.result || t.result_text} {t.unit}</td>
                  <td className="py-3 text-gray-500">{t.reference_text || 'N/A'}</td>
                  <td className="py-3"><StatusPill status={t.status} /></td>
                  <td className="py-3">
                    {isAttention ? (
                      <button
                        onClick={() => {
                          console.log('[Deep Explain] Button clicked:', { id: t.id, name: t.test_name, status: t.status });
                          setDeepExplainTest(t);
                        }}
                        className="flex items-center gap-1 px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-xs font-medium border border-blue-200"
                      >
                        <Search className="w-3 h-3" />
                        Deep Explain
                      </button>
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Deep Explain Modal */}
      {deepExplainTest && (
        <DeepExplain
          reportId={report.id}
          testId={deepExplainTest.id}
          testName={deepExplainTest.test_name}
          result={deepExplainTest.result}
          unit={deepExplainTest.unit}
          referenceRange={deepExplainTest.reference_text}
          status={deepExplainTest.status}
          language="en"
          onClose={() => setDeepExplainTest(null)}
        />
      )}

      {summary.doctor_questions?.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Questions for Your Doctor</h3>
          <ul className="space-y-2">
            {summary.doctor_questions.map((q: string, i: number) => (
              <li key={i} className="text-gray-700 text-sm flex items-start gap-2">
                <span className="text-blue-600 font-bold">Q.</span> {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="p-4 bg-gray-100 rounded-lg text-xs text-gray-500">
        {summary.safety_disclaimer || "This is an informational analysis only. Please consult your doctor for medical advice."}
      </div>
    </div>
  )
}

function StatCard({ label, value, color, icon }: { label: string, value: number, color: string, icon: React.ReactNode }) {
  const colors: Record<string, string> = {
    green: 'bg-green-50 text-green-700 border-green-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  }
  return (
    <div className={`card p-4 border ${colors[color]}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium opacity-80">{label}</span>
        {icon}
      </div>
      <div className="text-2xl font-bold">{value}</div>
    </div>
  )
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    normal: 'badge-normal',
    borderline: 'badge-attention',
    low: 'badge-attention',
    high: 'badge-attention',
    critically_low: 'badge-critical',
    critically_high: 'badge-critical',
    unreadable: 'px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full',
    missing: 'px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded-full',
  }
  return <span className={map[status] || 'badge-normal'}>{status.replace('_', ' ')}</span>
}

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { FileText, AlertCircle, CheckCircle, Clock, Upload } from 'lucide-react'

interface ReportListItem {
  id: number
  filename: string
  report_type: string
  status: string
  report_date: string | null
  lab_name: string | null
  result_count: number
  abnormal_count: number
  created_at: string
}

export default function DashboardPage() {
  const [reports, setReports] = useState<ReportListItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/reports').then(res => {
      setReports(res.data)
      setLoading(false)
    })
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-bold text-gray-900">My Reports</h1>
        <Link to="/report/new" className="btn-primary flex items-center gap-2">
          <Upload className="w-4 h-4" /> Upload Report
        </Link>
      </div>

      {loading ? (
        <div className="grid gap-4">
          {[1,2,3].map(i => <div key={i} className="card h-24 animate-pulse bg-gray-100" />)}
        </div>
      ) : reports.length === 0 ? (
        <div className="card text-center py-16">
          <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No reports yet</h3>
          <p className="text-gray-600 mb-4">Upload your first medical report to get started.</p>
          <Link to="/report/new" className="btn-primary">Upload Report</Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {reports.map(report => (
            <Link key={report.id} to={`/report/${report.id}`} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{report.filename}</h3>
                    <p className="text-sm text-gray-500">
                      {report.lab_name || 'Unknown Lab'} • {report.report_date || new Date(report.created_at).toLocaleDateString()}
                    </p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-gray-500">{report.result_count} parameters</span>
                      {report.abnormal_count > 0 && (
                        <span className="badge-attention flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" /> {report.abnormal_count} abnormal
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <StatusBadge status={report.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return <span className="badge-normal flex items-center gap-1"><CheckCircle className="w-3 h-3" /> Ready</span>
  if (status === 'failed') return <span className="badge-critical flex items-center gap-1"><AlertCircle className="w-3 h-3" /> Failed</span>
  return <span className="flex items-center gap-1 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded-full"><Clock className="w-3 h-3" /> Processing</span>
}

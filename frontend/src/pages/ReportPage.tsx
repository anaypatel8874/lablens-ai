import { useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import api from '../services/api'
import ReportDashboard from '../components/ReportDashboard'
import Chatbot from '../components/Chatbot'

export default function ReportPage() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [lang, setLang] = useState<'en' | 'hi' | 'hinglish'>('en')

  useEffect(() => {
    if (!id) return
    setLoading(true)
    api.get(`/reports/${id}/dashboard?language=${lang}`).then(res => {
      setData(res.data)
      setLoading(false)
    })
  }, [id, lang])

  const handleDownload = async () => {
    try {
      const res = await api.get(`/reports/${id}/download`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `lablens-report-${id}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      alert('Failed to download PDF')
    }
  }

  if (loading) return <div className="max-w-7xl mx-auto px-4 py-20 text-center">Analyzing report...</div>
  if (!data) return <div className="max-w-7xl mx-auto px-4 py-20 text-center">Report not found</div>

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{data.report.filename}</h1>
        <div className="flex items-center gap-2">
          <select value={lang} onChange={e => setLang(e.target.value as any)} className="border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="hinglish">Hinglish</option>
          </select>
          <button onClick={handleDownload} className="btn-secondary text-sm">Download PDF</button>
        </div>
      </div>
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ReportDashboard data={data} />
        </div>
        <div>
          <Chatbot reportId={parseInt(id!)} language={lang} />
        </div>
      </div>
    </div>
  )
}

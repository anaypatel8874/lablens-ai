import { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, Loader2 } from 'lucide-react'
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [reportId, setReportId] = useState<number | null>(null)
  const navigate = useNavigate()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'image/*': ['.jpg', '.jpeg', '.png'] },
    maxSize: 50 * 1024 * 1024,
  })

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Poll for report completion
  useEffect(() => {
    if (!reportId || !processing) return
    const interval = setInterval(async () => {
      try {
        const res = await api.get(`/reports/${reportId}`)
        if (res.data.status === 'completed') {
          clearInterval(interval)
          setProcessing(false)
          navigate(`/report/${reportId}`)
        } else if (res.data.status === 'failed') {
          clearInterval(interval)
          setProcessing(false)
          alert('Report processing failed. Please try again.')
        }
      } catch (err) {
        // Report not found yet, keep polling
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [reportId, processing, navigate])

  const handleUpload = async () => {
    if (files.length === 0) return
    setUploading(true)
    setProgress(0)
    try {
      for (const file of files) {
        const formData = new FormData()
        formData.append('file', file)
        const res = await api.post('/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (e) => {
            const pct = Math.round((e.loaded * 100) / (e.total || 1))
            setProgress(pct)
          }
        })
        if (res.data.report_id) {
          setReportId(res.data.report_id)
          setUploading(false)
          setProcessing(true)
          return
        }
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-12">
      <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Upload Medical Report</h2>
      <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}>
        <input {...getInputProps()} />
        <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-lg font-medium text-gray-700">{isDragActive ? 'Drop files here' : 'Drag & drop files here'}</p>
        <p className="text-sm text-gray-500 mt-1">or click to select files</p>
        <p className="text-xs text-gray-400 mt-2">PDF, JPG, JPEG, PNG up to 50MB</p>
      </div>

      {files.length > 0 && (
        <div className="mt-6 space-y-2">
          {files.map((file, i) => (
            <div key={i} className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg">
              <div className="flex items-center gap-3">
                <File className="w-5 h-5 text-blue-600" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
              <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-600">
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
          {uploading ? (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-sm text-gray-600 mt-2 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" /> Uploading... {progress}%
              </p>
            </div>
          ) : processing ? (
            <div className="mt-4 text-center">
              <div className="flex items-center justify-center gap-2 text-blue-600">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="font-medium">Analyzing report...</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">Extracting results and generating analysis</p>
            </div>
          ) : (
            <button onClick={handleUpload} className="w-full btn-primary py-3 mt-4">Upload & Analyze</button>
          )}
        </div>
      )}
    </div>
  )
}

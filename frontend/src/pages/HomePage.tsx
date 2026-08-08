import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Upload, Shield, Brain, TrendingUp, FileText, MessageCircle } from 'lucide-react'

export default function HomePage() {
  const { user } = useAuth()

  return (
    <div>
      <section className="bg-gradient-to-b from-blue-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Understand Your Lab Reports<br />
            <span className="text-blue-600">with AI</span>
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
            Upload your medical reports in PDF or image format. LabLens AI extracts, analyzes, and explains your results in simple English, Hindi, or Hinglish.
          </p>
          <div className="flex justify-center gap-4">
            {user ? (
              <Link to="/dashboard" className="btn-primary text-lg px-8 py-3">Go to Dashboard</Link>
            ) : (
              <>
                <Link to="/register" className="btn-primary text-lg px-8 py-3">Upload Your Report</Link>
                <Link to="/login" className="btn-secondary text-lg px-8 py-3">Sign In</Link>
              </>
            )}
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard icon={<Brain className="w-8 h-8 text-blue-600" />} title="AI-Powered Analysis" description="Advanced extraction and interpretation of 100+ laboratory tests across hematology, biochemistry, endocrinology, and more." />
            <FeatureCard icon={<MessageCircle className="w-8 h-8 text-blue-600" />} title="Ask My Report" description="Chat with our AI about your specific results. Get explanations in English, Hindi, or Hinglish." />
            <FeatureCard icon={<TrendingUp className="w-8 h-8 text-blue-600" />} title="Track Trends" description="Compare multiple reports over time. Visualize changes in key health markers." />
            <FeatureCard icon={<Shield className="w-8 h-8 text-blue-600" />} title="Privacy First" description="Encrypted storage, secure authentication, and complete data control. Your health data stays private." />
            <FeatureCard icon={<FileText className="w-8 h-8 text-blue-600" />} title="Download PDF" description="Generate professional, shareable PDF summaries of your AI analysis." />
            <FeatureCard icon={<Upload className="w-8 h-8 text-blue-600" />} title="Multi-Format Support" description="Upload PDFs, scanned images, mobile photos, and multi-page documents." />
          </div>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

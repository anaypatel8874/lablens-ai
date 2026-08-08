import { Outlet, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { FlaskConical, LogOut, User } from 'lucide-react'

export default function Layout() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <FlaskConical className="w-7 h-7 text-blue-600" />
            <span className="text-xl font-bold text-gray-900">LabLens AI</span>
          </Link>
          <nav className="flex items-center gap-4">
            {user ? (
              <>
                <Link to="/dashboard" className="text-gray-600 hover:text-gray-900 font-medium">Dashboard</Link>
                <div className="flex items-center gap-2">
                  <User className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-gray-700">{user.full_name || user.email}</span>
                </div>
                <button onClick={logout} className="flex items-center gap-1 text-gray-500 hover:text-red-600">
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-gray-600 hover:text-gray-900 font-medium">Login</Link>
                <Link to="/register" className="btn-primary">Get Started</Link>
              </>
            )}
          </nav>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="bg-white border-t border-gray-200 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-500 text-sm">
          <p>LabLens AI - Medical Report Analyzer. For informational purposes only. Not a substitute for professional medical advice.</p>
        </div>
      </footer>
    </div>
  )
}

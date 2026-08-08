import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { ReactNode } from 'react'

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex justify-center p-20">Loading...</div>
  if (!user) return <Navigate to="/login" />
  return <>{children}</>
}

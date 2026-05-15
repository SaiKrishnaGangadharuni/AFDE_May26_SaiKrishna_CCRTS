import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, roles }) {
  const { user } = useAuth()
  const loc = useLocation()
  if (!user) {
    return <Navigate to="/login" state={{ from: loc }} replace />
  }
  if (roles && !roles.includes(user.role?.name)) {
    return (
      <div className="card max-w-lg mx-auto mt-10">
        <h2 className="text-lg font-semibold text-rose-600">Access denied</h2>
        <p className="text-sm text-slate-600 mt-2">
          Your role ({user.role?.name}) does not have access to this page.
        </p>
      </div>
    )
  }
  return children
}

import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/auth-context'

export default function ProtectedRoute({ roles }) {
  const { token, rol } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (roles && !roles.includes(rol)) {
    return <Navigate to={`/${rol?.toLowerCase() || 'login'}`} replace />
  }
  return <Outlet />
}

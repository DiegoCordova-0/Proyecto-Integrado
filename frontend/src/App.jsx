import { Navigate, Route, Routes, Link, useNavigate } from 'react-router-dom'
import { useAuth } from './context/auth-context'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './views/Login'
import Analista from './views/Analista'
import Aprobador from './views/Aprobador'
import Auditor from './views/Auditor'
import './App.css'

function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const destination = {
    Analista: '/analista',
    Aprobador: '/aprobador',
    Auditor: '/auditor',
  }[user?.rol]
  return <>
    <nav className="nav">
      <Link className="brand" to="/">nuam</Link>
      <div className="market-identity">
        <span className="market-ticker">MERCADO ÚNICO REGIONAL · CL · PE · CO</span>
        <span className="regulatory-pill">DJ 1949 / DJ 1922 · SII</span>
      </div>
      <span className="nav-user">{user?.nombre} · {user?.rol}</span>
      <button onClick={() => { logout(); navigate('/login') }}>Cerrar sesión</button>
    </nav>
    <Routes>
      <Route path="/" element={<Navigate to={destination || '/login'} replace />} />
      <Route path="/analista" element={<ProtectedRoute roles={['Analista']} />}><Route index element={<Analista />} /></Route>
      <Route path="/aprobador" element={<ProtectedRoute roles={['Aprobador']} />}><Route index element={<Aprobador />} /></Route>
      <Route path="/auditor" element={<ProtectedRoute roles={['Auditor']} />}><Route index element={<Auditor />} /></Route>
    </Routes>
  </>
}

export default function App() {
  return <>
    <Routes><Route path="/login" element={<Login />} /><Route path="/*" element={<Layout />} /></Routes>
    <footer className="site-footer">
      nuam · Mantenedor de Calificaciones Tributarias | Cumplimiento Ley 21.719 y Ley 21.459
    </footer>
  </>
}

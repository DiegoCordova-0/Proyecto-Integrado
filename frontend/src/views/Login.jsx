import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/auth-context'

export default function Login() {
  const { login, token } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ identificador: '', password: '' })
  const [error, setError] = useState('')

  if (token) return <Navigate to="/" replace />

  async function submit(event) {
    event.preventDefault()
    setError('')
    try {
      await login(form.identificador, form.password)
      navigate('/')
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'No fue posible iniciar sesión.')
    }
  }

  return (
    <main className="auth-page">
      <form className="card auth-card" onSubmit={submit}>
        <p className="eyebrow">NUAM · DJ 1949 / DJ 1922</p>
        <h1>Acceso seguro</h1>
        <label>RUT o email<input required value={form.identificador} onChange={(e) => setForm({ ...form, identificador: e.target.value })} /></label>
        <label>Contraseña<input required type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>
        {error && <p className="error">{error}</p>}
        <button className="primary" type="submit">Ingresar</button>
      </form>
    </main>
  )
}

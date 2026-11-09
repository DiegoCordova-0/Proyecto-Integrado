import { useMemo, useState } from 'react'
import api from '../api/axios'
import { useAuth } from '../context/auth-context'

const emptyFactors = Array.from({ length: 29 }, () => '0')

export default function Analista() {
  const { user } = useAuth()
  const [idDeclaracion, setIdDeclaracion] = useState('')
  const [factors, setFactors] = useState(emptyFactors)
  const [message, setMessage] = useState('')
  const [csv, setCsv] = useState({ file: null, rows: [] })
  const sum = useMemo(() => factors.reduce((total, value) => total + (Number(value) || 0), 0), [factors])
  const invalid = sum > 1

  function updateFactor(index, value) {
    const next = [...factors]
    next[index] = value
    setFactors(next)
  }

  async function submit(event) {
    event.preventDefault()
    setMessage('')
    try {
      await api.post(`/declaraciones/${idDeclaracion}/factores`, {
        rut_usuario: user.rut,
        id_declaracion: Number(idDeclaracion),
        factores: factors.map((value) => value || '0'),
      })
      setMessage('Factores enviados correctamente.')
    } catch (error) {
      setMessage(error.response?.data?.detail?.mensaje || 'No fue posible enviar los factores.')
    }
  }

  function preview(event) {
    const file = event.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setCsv({ file, rows: String(reader.result).split(/\r?\n/).slice(0, 6) })
    reader.readAsText(file)
  }

  async function upload() {
    setMessage('')
    if (!csv.file) return
    const body = new FormData()
    body.append('archivo', csv.file)
    try {
      const { data } = await api.post('/declaraciones/carga-masiva', body, { headers: { 'Content-Type': 'multipart/form-data' } })
      const rechazadas = data.resultados.filter((resultado) => !resultado.exito)
      if (rechazadas.length > 0) {
        const detalle = rechazadas.map((resultado) => `Fila ${resultado.fila}: ${resultado.mensaje}`).join(' ')
        setMessage(`CSV procesado: ${data.filas_exitosas} exitosas y ${data.filas_rechazadas} rechazadas. ${detalle}`)
        return
      }
      setMessage(`CSV procesado correctamente: ${data.filas_exitosas} fila(s) guardada(s) en Supabase.`)
    } catch (error) {
      setMessage(error.response?.data?.detail || 'No fue posible procesar el CSV.')
    }
  }

  return <main className="page"><header className="page-header"><div><p className="eyebrow">Analista tributario</p><h1>Mantenedor de factores</h1></div></header>
    <section className={`card factor-card ${invalid ? 'warning' : ''}`}><form onSubmit={submit}>
      <label>ID declaración<input required type="number" min="1" value={idDeclaracion} onChange={(e) => setIdDeclaracion(e.target.value)} /></label>
      <div className="factor-grid">{factors.map((value, index) => <label key={index}>Factor {index + 1}<input type="number" min="0" step="0.00000001" value={value} onChange={(e) => updateFactor(index, e.target.value)} /></label>)}</div>
      <div className="summary">Suma: <strong>{sum.toFixed(8)}</strong>{invalid && <span className="error"> Excede 1.00000000</span>}</div>
      <button className="primary" disabled={!idDeclaracion || invalid} type="submit">Enviar factores</button>
    </form></section>
    <section className="card"><h2>Carga masiva CSV</h2><input type="file" accept=".csv,text/csv" onChange={preview} />{csv.rows.length > 0 && <><pre className="csv-preview">{csv.rows.join('\n')}</pre><button className="primary" onClick={upload}>Procesar CSV</button></>}</section>
    {message && <p className="notice">{message}</p>}
  </main>
}

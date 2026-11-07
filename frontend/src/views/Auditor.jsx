import { useEffect, useState } from 'react'
import api from '../api/axios'

export default function Auditor() {
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')
  useEffect(() => {
    let active = true
    async function load() {
      try {
        const { data } = await api.get('/auditoria/logs')
        if (active) setLogs(data.logs)
      } catch { if (active) setError('No fue posible cargar la bitácora.') }
    }
    load()
    const interval = setInterval(load, 10000)
    return () => { active = false; clearInterval(interval) }
  }, [])
  return <main className="page"><p className="eyebrow">Auditor</p><h1>Bitácora de trazabilidad</h1><section className="card table-wrap"><table><thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Estado</th><th>IP</th><th>Detalle</th></tr></thead><tbody>{logs.map((log, index) => <tr key={`${log.fecha_hora}-${index}`}><td>{log.fecha_hora}</td><td>{log.rut_usuario}</td><td>{log.accion}</td><td>{log.estado}</td><td>{log.ip_cliente || '-'}</td><td>{log.detalle}</td></tr>)}</tbody></table></section>{error && <p className="error">{error}</p>}</main>
}

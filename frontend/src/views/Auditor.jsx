import { useEffect, useMemo, useState } from 'react'
import api from '../api/axios'
import KpiGrid from '../components/KpiGrid'
import { downloadCsv } from '../utils/csv'

const actionOptions = [
  'UPSERT_CALIFICACION',
  'CAMBIO_ESTADO_CALIFICACION',
  'VALIDACION_FACTORES_RECHAZADA',
  'CALCULO_FACTORES_DESDE_MONTOS',
]
const knownStatuses = ['EXITO', 'APROBADO', 'RECHAZADO', 'ERROR']
const emptyFilters = { range: '', month: '', user: '', action: '', status: '' }
const rangeDurations = {
  '24h': 24 * 60 * 60 * 1000,
  '7d': 7 * 24 * 60 * 60 * 1000,
  '30d': 30 * 24 * 60 * 60 * 1000,
}

function formatTimestamp(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = (part) => String(part).padStart(2, '0')
  return `${pad(date.getDate())}/${pad(date.getMonth() + 1)}/${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function formatValue(value) {
  if (value === null || value === undefined || value === '') return '—'
  return typeof value === 'string' ? value : JSON.stringify(value, null, 2)
}

function statusBadgeClass(status) {
  const normalized = String(status || '').toUpperCase()
  if (normalized === 'EXITO' || normalized === 'APROBADO') return 'audit-status-success'
  if (normalized === 'RECHAZADO' || normalized === 'ERROR') return 'audit-status-error'
  return 'audit-status-neutral'
}

export default function Auditor() {
  const [logs, setLogs] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [selectedLog, setSelectedLog] = useState(null)
  const [filters, setFilters] = useState(emptyFilters)
  const [rangeCutoff, setRangeCutoff] = useState(null)

  const summary = useMemo(() => {
    const activeUsers = new Set(logs.map((log) => log.rut_usuario || log.usuario_rut).filter(Boolean))
    const successful = logs.filter((log) => ['EXITO', 'APROBADO'].includes(String(log.estado || '').toUpperCase())).length
    const preventive = logs.filter((log) => {
      const state = String(log.estado || '').toUpperCase()
      const action = String(log.accion || '').toUpperCase()
      return ['RECHAZADO', 'ERROR'].includes(state) || /RECHAZ|BLOQUEO/.test(action)
    }).length
    return [
      { label: 'Eventos auditados', value: logs.length },
      { label: 'Operaciones exitosas', value: successful },
      { label: 'Rechazos / bloqueos', value: preventive },
      { label: 'Usuarios activos', value: activeUsers.size },
    ]
  }, [logs])

  const availableActions = useMemo(
    () => [...new Set([...actionOptions, ...logs.map((log) => log.accion).filter(Boolean)])].sort(),
    [logs],
  )
  const availableStatuses = useMemo(
    () => [...new Set([...knownStatuses, ...logs.map((log) => String(log.estado || '').toUpperCase()).filter(Boolean)])].sort(),
    [logs],
  )
  const filteredLogs = useMemo(() => {
    const userQuery = filters.user.trim().toLowerCase()

    return logs.filter((log) => {
      const isoTimestamp = String(log.fecha_hora ?? log.timestamp ?? '')
      const timestamp = Date.parse(isoTimestamp)
      if (filters.month && isoTimestamp.slice(0, 7) !== filters.month) return false
      if (rangeCutoff !== null && (!Number.isFinite(timestamp) || timestamp < rangeCutoff)) return false
      if (userQuery && !String(log.rut_usuario ?? log.usuario_rut ?? '').toLowerCase().includes(userQuery)) return false
      if (filters.action && (log.accion ?? log.action) !== filters.action) return false
      if (filters.status && String(log.estado || '').toUpperCase() !== filters.status) return false
      return true
    })
  }, [filters, logs, rangeCutoff])

  useEffect(() => {
    let active = true
    async function load() {
      try {
        const { data } = await api.get('/auditoria/logs')
        if (active) {
          setLogs(data.logs)
          setError('')
        }
      } catch { if (active) setError('No fue posible cargar la bitácora.') }
      finally { if (active) setIsLoading(false) }
    }
    load()
    const interval = setInterval(load, 10000)
    return () => { active = false; clearInterval(interval) }
  }, [])

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  function updateRange(range) {
    setRangeCutoff(range ? Date.now() - rangeDurations[range] : null)
    setFilters((current) => ({ ...current, range, month: '' }))
  }

  function updateMonth(month) {
    setRangeCutoff(null)
    setFilters((current) => ({ ...current, month, range: '' }))
  }

  function clearFilters() {
    setRangeCutoff(null)
    setFilters(emptyFilters)
  }

  function exportAuditCsv() {
    const headers = ['Timestamp ISO', 'Fecha', 'Usuario (RUT)', 'IP', 'Acción', 'Estado', 'Detalle', 'Evento JSON']
    const rows = filteredLogs.map((log) => [
      log.fecha_hora ?? log.timestamp,
      formatTimestamp(log.fecha_hora ?? log.timestamp),
      log.rut_usuario ?? log.usuario_rut,
      log.ip_cliente ?? log.ip,
      log.accion,
      log.estado,
      log.detalle,
      JSON.stringify(log),
    ])
    downloadCsv('auditoria.csv', headers, rows)
  }

  function openLog(log) {
    setSelectedLog(log)
  }

  const selectedTimestamp = selectedLog?.fecha_hora ?? selectedLog?.timestamp
  const selectedUser = selectedLog?.rut_usuario ?? selectedLog?.usuario_rut
  const selectedIp = selectedLog?.ip_cliente ?? selectedLog?.ip
  const selectedAction = selectedLog?.accion ?? selectedLog?.action
  const selectedDetail = selectedLog?.detalle ?? selectedLog?.detail
  const selectedPayload = selectedLog?.payload ?? selectedLog?.data
  const previousValues = selectedLog?.valores_previos
    ?? selectedLog?.valores_anteriores
    ?? selectedLog?.previous_values
    ?? selectedLog?.before
    ?? selectedLog?.old_values
    ?? selectedPayload?.valores_previos
    ?? selectedPayload?.valores_anteriores
    ?? selectedPayload?.before
    ?? selectedPayload?.antes
    ?? selectedPayload?.old_values
  const nextValues = selectedLog?.valores_nuevos
    ?? selectedLog?.despues
    ?? selectedLog?.next_values
    ?? selectedLog?.after
    ?? selectedLog?.new_values
    ?? selectedPayload?.valores_nuevos
    ?? selectedPayload?.next_values
    ?? selectedPayload?.after
    ?? selectedPayload?.despues
    ?? selectedPayload?.new_values

  return <main className="page">
    <p className="eyebrow">Auditor</p>
    <h1>Bitácora de trazabilidad</h1>
    <KpiGrid items={summary} label="Resumen de auditoría" />
    <section className="card audit-filters" aria-label="Filtros de auditoría">
      <label>Rango de tiempo
        <select value={filters.range} onChange={(event) => updateRange(event.target.value)}>
          <option value="">Todos los registros</option>
          <option value="24h">Últimas 24 horas</option>
          <option value="7d">Últimos 7 días</option>
          <option value="30d">Último mes</option>
        </select>
      </label>
      <label>Mes específico
        <input type="month" value={filters.month} onChange={(event) => updateMonth(event.target.value)} />
      </label>
      <label>Usuario (RUT)
        <input type="search" value={filters.user} onChange={(event) => updateFilter('user', event.target.value)} placeholder="Buscar RUT" />
      </label>
      <label>Categoría / Acción
        <select value={filters.action} onChange={(event) => updateFilter('action', event.target.value)}>
          <option value="">Todas las acciones</option>
          {availableActions.map((action) => <option key={action} value={action}>{action}</option>)}
        </select>
      </label>
      <label>Estado
        <select value={filters.status} onChange={(event) => updateFilter('status', event.target.value)}>
          <option value="">Todos los estados</option>
          {availableStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
        </select>
      </label>
      <button type="button" className="secondary" onClick={clearFilters}>Limpiar filtros</button>
      <button type="button" className="secondary" disabled={filteredLogs.length === 0} onClick={exportAuditCsv}>Exportar CSV</button>
    </section>
    {isLoading && <p className="loading-indicator" role="status">Cargando eventos de auditoría...</p>}
    <section className="card table-wrap audit-table-wrap" aria-label="Registros de auditoría">
      <table className="audit-table">
        <thead><tr><th>Fecha</th><th>Usuario</th><th className="audit-wrap-cell">Acción</th><th>Estado</th><th>IP</th><th className="audit-wrap-cell">Detalle</th><th>Inspección</th></tr></thead>
        <tbody>{filteredLogs.length === 0
          ? <tr><td colSpan="7">{isLoading ? 'Cargando eventos...' : logs.length === 0 ? 'No hay eventos de auditoría disponibles.' : 'No hay registros que coincidan con los filtros.'}</td></tr>
          : filteredLogs.map((log, index) => {
            const timestamp = log.fecha_hora ?? log.timestamp
            const user = log.rut_usuario ?? log.usuario_rut
            const action = log.accion ?? log.action
            const state = log.estado
            return <tr key={`${timestamp}-${index}`}>
              <td><time dateTime={timestamp}>{formatTimestamp(timestamp)}</time></td>
              <td>{user || '-'}</td>
              <td className="audit-action-cell">{action || '-'}</td>
              <td><span className={`badge ${statusBadgeClass(state)}`}>{state || '-'}</span></td>
              <td>{log.ip_cliente ?? log.ip ?? '-'}</td>
              <td className="audit-wrap-cell">{formatValue(log.detalle ?? log.detail)}</td>
              <td><button type="button" className="secondary" onClick={() => openLog(log)}>Ver detalle</button></td>
            </tr>
          })}
        </tbody>
      </table>
    </section>
    {error && <p className="notice error">{error}</p>}
    {selectedLog && <div className="modal-backdrop" role="presentation" onClick={() => setSelectedLog(null)}>
      <section className="modal card audit-detail-modal" role="dialog" aria-modal="true" aria-labelledby="audit-detail-title" onClick={(event) => event.stopPropagation()}>
        <button className="modal-close" type="button" onClick={() => setSelectedLog(null)}>Cerrar</button>
        <h2 id="audit-detail-title">Detalle del evento</h2>
        <div className="audit-detail-grid">
          <div className="audit-detail-field"><span>Timestamp</span><strong className="numeric-data">{formatTimestamp(selectedTimestamp)}</strong></div>
          <div className="audit-detail-field"><span>Usuario (RUT)</span><strong>{selectedUser || '—'}</strong></div>
          <div className="audit-detail-field"><span>IP</span><strong>{selectedIp || '—'}</strong></div>
          <div className="audit-detail-field"><span>Acción</span><strong>{selectedAction || '—'}</strong></div>
          <div className="audit-detail-field"><span>Estado</span><strong><span className={`badge ${statusBadgeClass(selectedLog.estado)}`}>{selectedLog.estado || '—'}</span></strong></div>
        </div>
        {selectedDetail && <section className="audit-detail-section"><h3>Detalle</h3><pre className="audit-json">{formatValue(selectedDetail)}</pre></section>}
        {previousValues !== undefined && <section className="audit-detail-section"><h3>Antes</h3><pre className="audit-json">{formatValue(previousValues)}</pre></section>}
        {nextValues !== undefined && <section className="audit-detail-section"><h3>Después</h3><pre className="audit-json">{formatValue(nextValues)}</pre></section>}
        {selectedPayload !== undefined && <section className="audit-detail-section"><h3>Payload</h3><pre className="audit-json">{formatValue(selectedPayload)}</pre></section>}
        <details className="audit-detail-section">
          <summary>Documento completo de auditoría</summary>
          <pre className="audit-json">{formatValue(selectedLog)}</pre>
        </details>
      </section>
    </div>}
  </main>
}

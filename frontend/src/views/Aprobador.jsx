import { useCallback, useEffect, useState } from 'react'
import api from '../api/axios'

export default function Aprobador() {
  const [filters, setFilters] = useState({})
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [message, setMessage] = useState('')
  const load = useCallback(async () => {
    const { data } = await api.get('/declaraciones', { params: filters })
    // The effect synchronizes the table with the remote declaration list.
    // oxlint-disable-next-line react(set-state-in-effect)
    setItems(data)
  }, [filters])
  useEffect(() => {
    load().catch(() => {
      setMessage('No fue posible cargar las declaraciones.')
    })
  }, [load])
  async function showDetail(id) {
    try {
      const { data } = await api.get(`/declaraciones/${id}`)
      setSelected(data)
    } catch {
      setMessage('No fue posible cargar el detalle.')
    }
  }
  async function changeStatus(id, estado) {
    if (!window.confirm(`¿Confirmas marcar esta declaración como ${estado}?`)) return
    try {
      await api.patch(`/declaraciones/${id}/estado`, { estado })
      setSelected(null)
      await load()
    } catch {
      setMessage('No fue posible cambiar el estado.')
    }
  }
  return <main className="page"><p className="eyebrow">Aprobador</p><h1>Bandeja de declaraciones</h1><section className="card filters"><input placeholder="Estado" value={filters.estado || ''} onChange={(e) => setFilters({ ...filters, estado: e.target.value })} /><input placeholder="RUT empresa" value={filters.rut_empresa || ''} onChange={(e) => setFilters({ ...filters, rut_empresa: e.target.value })} /><input placeholder="Período" type="number" value={filters.periodo_tributario || ''} onChange={(e) => setFilters({ ...filters, periodo_tributario: e.target.value })} /><button onClick={load}>Filtrar</button></section><section className="card table-wrap"><table><thead><tr><th>Folio</th><th>RUT empresa</th><th>Período</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.folio}</td><td>{item.rut_empresa}</td><td>{item.periodo_tributario}</td><td>{item.estado}</td><td><button onClick={() => showDetail(item.id)}>Ver detalle</button></td></tr>)}</tbody></table></section>{selected && <div className="modal-backdrop" role="presentation" onClick={() => setSelected(null)}><section className="modal card" role="dialog" aria-modal="true" aria-labelledby="detail-title" onClick={(event) => event.stopPropagation()}><button className="modal-close" onClick={() => setSelected(null)}>Cerrar</button><h2 id="detail-title">Detalle · {selected.folio}</h2><p>Estado: <strong>{selected.estado}</strong> · Suma: <strong>{selected.suma_factores_criticos || '0.00000000'}</strong></p><div className="factor-grid">{selected.factores.map((factor, index) => <label key={index}>Factor {index + 1}<input readOnly value={factor} /></label>)}</div>{selected.estado === 'Pendiente' && <div className="modal-actions"><button className="primary" onClick={() => changeStatus(selected.id, 'Aprobado')}>Aprobar</button><button onClick={() => changeStatus(selected.id, 'Rechazado')}>Rechazar</button></div>}</section></div>}{message && <p className="error">{message}</p>}</main>
}

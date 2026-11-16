import { useCallback, useEffect, useState } from 'react'
import api from '../api/axios'

const factorIndexes = Array.from({ length: 30 }, (_, index) => index + 8)

export default function Aprobador() {
  const [filters, setFilters] = useState({ estado: 'Pendiente', mercado: '', origen: '', ejercicio: '', instrumento: '' })
  const [items, setItems] = useState([])
  const [selected, setSelected] = useState(null)
  const [message, setMessage] = useState('')

  const load = useCallback(async () => {
    try {
      const { data } = await api.get('/calificaciones', { params: filters })
      setItems(data)
    } catch {
      setMessage('No fue posible cargar las calificaciones.')
    }
  }, [filters])

  useEffect(() => {
    load()
  }, [load])

  async function changeStatus(id, estado) {
    if (!window.confirm(`¿Confirmas marcar esta calificación como ${estado}?`)) return
    try {
      await api.patch(`/calificaciones/${id}/estado`, { estado })
      setSelected(null)
      setMessage(`Calificación ${estado.toLowerCase()} correctamente.`)
      await load()
    } catch (error) {
      setMessage(error.response?.data?.detail || 'No fue posible cambiar el estado.')
    }
  }

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }))
  }

  return <main className="page">
    <p className="eyebrow">Aprobador</p>
    <h1>Bandeja de calificaciones</h1>
    <section className="card filters">
      <select aria-label="Estado" value={filters.estado} onChange={(event) => updateFilter('estado', event.target.value)}>
        <option value="">Todos los estados</option><option>Pendiente</option><option>Aprobado</option><option>Rechazado</option>
      </select>
      <select aria-label="Mercado" value={filters.mercado} onChange={(event) => updateFilter('mercado', event.target.value)}>
        <option value="">Todos los mercados</option><option>ACN</option><option>CFI</option><option>FFMM</option>
      </select>
      <select aria-label="Origen" value={filters.origen} onChange={(event) => updateFilter('origen', event.target.value)}>
        <option value="">Todos los orígenes</option><option value="CORREDORA">Corredora</option><option value="SISTEMA">Sistema</option>
      </select>
      <input aria-label="Ejercicio" placeholder="Ejercicio" type="number" value={filters.ejercicio} onChange={(event) => updateFilter('ejercicio', event.target.value)} />
      <input aria-label="Instrumento" placeholder="Instrumento" value={filters.instrumento} onChange={(event) => updateFilter('instrumento', event.target.value)} />
      <button className="primary" onClick={load}>Buscar</button>
    </section>
    <section className="card table-wrap">
      <table><thead><tr><th></th><th>Ejercicio</th><th>Mercado</th><th>Instrumento</th><th>Secuencia</th><th>Origen</th><th>Estado</th><th>Factor 8</th><th>Factor 37</th><th>Acciones</th></tr></thead>
        <tbody>{items.map((item) => <tr key={item.id}>
          <td><input type="radio" name="selected-calificacion" checked={selected?.id === item.id} onChange={() => setSelected(item)} /></td>
          <td>{item.ejercicio}</td><td>{item.mercado}</td><td>{item.instrumento}</td><td>{item.secuencia}</td><td>{item.origen}</td><td>{item.estado}</td><td>{item.factor_8}</td><td>{item.factor_37}</td>
          <td><button onClick={() => setSelected(item)}>Ver detalle</button></td>
        </tr>)}</tbody>
      </table>
    </section>
    {selected && <div className="modal-backdrop" role="presentation" onClick={() => setSelected(null)}>
      <section className="modal card" role="dialog" aria-modal="true" aria-labelledby="calificacion-detail-title" onClick={(event) => event.stopPropagation()}>
        <button className="modal-close" onClick={() => setSelected(null)}>Cerrar</button>
        <h2 id="calificacion-detail-title">Detalle de calificación</h2>
        <div className="factor-grid">
          <label>Mercado<input readOnly value={selected.mercado || ''} /></label>
          <label>Instrumento<input readOnly value={selected.instrumento || ''} /></label>
          <label>Secuencia<input readOnly value={selected.secuencia || ''} /></label>
          <label>Fecha pago<input readOnly value={selected.fecha_pago || ''} /></label>
          <label>Origen<input readOnly value={selected.origen || ''} /></label>
          <label>Fuente<input readOnly value={selected.fuente_ingreso || ''} /></label>
        </div>
        <p>Estado: <strong>{selected.estado}</strong></p>
        <div className="factor-grid">{factorIndexes.map((index) => <label key={index}>Factor {index}<input readOnly value={selected[`factor_${index}`] ?? '0.00000000'} /></label>)}</div>
        {selected.estado === 'Pendiente' && selected.origen !== 'SISTEMA' && <div className="modal-actions"><button className="primary" onClick={() => changeStatus(selected.id, 'Aprobado')}>Aprobar</button><button onClick={() => changeStatus(selected.id, 'Rechazado')}>Rechazar</button></div>}
      </section>
    </div>}
    {message && <p className="error">{message}</p>}
  </main>
}

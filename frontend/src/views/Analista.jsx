import { useCallback, useEffect, useMemo, useState } from 'react'
import api, { omitEmptyParams } from '../api/axios'
import KpiGrid from '../components/KpiGrid'
import { downloadCsv } from '../utils/csv'

const indexes = Array.from({ length: 30 }, (_, index) => index + 8)
const blank = (prefix) => Object.fromEntries(indexes.map((index) => [`${prefix}_${index}`, '0']))
const empty = () => ({
  ejercicio: new Date().getFullYear(), mercado: 'ACN', instrumento: '', fecha_pago: '',
  secuencia: '', numero_dividendo: 0, tipo_sociedad: 'A', valor_historico: 0,
  acogido_isfut: false, factor_actualizacion: 0, descripcion: '', modo: 'MONTOS',
  ...blank('monto'), ...blank('factor'),
})

function csvHeaders(prefix) {
  return ['Ejercicio', 'Mercado', 'Instrumento', 'Fecha', 'Secuencia', 'Numero de dividendo', 'Tipo sociedad', 'Valor Historico', ...indexes.map((index) => `${prefix} ${index}`)]
}

export default function Analista() {
  const [filters, setFilters] = useState({ mercado: '', origen: '', ejercicio: '', estado: '', instrumento: '' })
  const [items, setItems] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isProcessing, setIsProcessing] = useState(false)
  const [selected, setSelected] = useState(null)
  const [form, setForm] = useState(empty())
  const [modal, setModal] = useState(null)
  const [message, setMessage] = useState(null)
  const [csv, setCsv] = useState({ tipo: 'FACTORES', file: null, rows: [], errors: [] })
  const sum = useMemo(() => indexes.slice(0, 12).reduce((total, index) => total + (Number(form[`factor_${index}`]) || 0), 0), [form])
  const invalid = sum > 1
  const summary = useMemo(() => {
    const countStatus = (status) => items.filter((item) => String(item.estado || '').toUpperCase() === status).length
    return [
      { label: 'Total calificaciones', value: items.length },
      { label: 'Pendientes', value: countStatus('PENDIENTE') },
      { label: 'Aprobadas', value: countStatus('APROBADO') },
      { label: 'Rechazadas', value: countStatus('RECHAZADO') },
    ]
  }, [items])

  const fetchItems = useCallback(async () => {
    const { data } = await api.get('/calificaciones', { params: omitEmptyParams(filters) })
    return data
  }, [filters])

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      setItems(await fetchItems())
    } catch { setMessage({ text: 'No fue posible cargar las calificaciones.', type: 'error' }) }
    finally { setIsLoading(false) }
  }, [fetchItems])

  useEffect(() => {
    let active = true
    async function loadInitial() {
      try {
        const data = await fetchItems()
        if (active) {
          setItems(data)
          setMessage(null)
        }
      } catch {
        if (active) setMessage({ text: 'No fue posible cargar las calificaciones.', type: 'error' })
      } finally {
        if (active) setIsLoading(false)
      }
    }
    loadInitial()
    return () => { active = false }
  }, [fetchItems])

  function updateFilter(key, value) {
    setIsLoading(true)
    setMessage(null)
    setFilters((current) => ({ ...current, [key]: value }))
  }

  function clearFilters() {
    setIsLoading(true)
    setMessage(null)
    setFilters({ mercado: '', origen: '', ejercicio: '', estado: '', instrumento: '' })
  }

  function update(key, value) { setForm((current) => ({ ...current, [key]: value })) }
  async function calculate() {
    setIsProcessing(true)
    try {
      const { data } = await api.post('/calificaciones/calcular-montos', { montos: Object.fromEntries(indexes.map((index) => [`monto_${index}`, form[`monto_${index}`]])) })
      setForm((current) => ({ ...current, ...data.factores }))
      setMessage({ text: 'Factores calculados con truncamiento a 8 decimales.', type: 'success' })
    } catch (error) { setMessage({ text: error.response?.data?.detail || 'No fue posible calcular los factores.', type: 'error' }) }
    finally { setIsProcessing(false) }
  }
  async function save(event) {
    event.preventDefault()
    if (invalid) return
    setIsProcessing(true)
    try {
      const payload = { ...form, montos: Object.fromEntries(indexes.map((index) => [`monto_${index}`, form[`monto_${index}`]])), factores: Object.fromEntries(indexes.map((index) => [`factor_${index}`, form[`factor_${index}`]])) }
      await api[selected ? 'put' : 'post'](selected ? `/calificaciones/${selected.id}` : '/calificaciones', payload)
      setModal(null); setSelected(null); setMessage({ text: 'Calificación guardada correctamente.', type: 'success' }); await load()
    } catch (error) { setMessage({ text: error.response?.data?.detail || 'No fue posible guardar la calificación.', type: 'error' }) }
    finally { setIsProcessing(false) }
  }
  async function remove() {
    if (!selected || !window.confirm('¿Eliminar la calificación seleccionada?')) return
    setIsProcessing(true)
    try { await api.delete(`/calificaciones/${selected.id}`); setSelected(null); setMessage({ text: 'Calificación eliminada.', type: 'success' }); await load() }
    catch (error) { setMessage({ text: error.response?.data?.detail || 'No fue posible eliminar la calificación.', type: 'error' }) }
    finally { setIsProcessing(false) }
  }
  function downloadTemplate() {
    const blob = new Blob([csvHeaders(csv.tipo === 'FACTORES' ? 'Factor' : 'Monto').join(',') + '\n'], { type: 'text/csv;charset=utf-8' })
    const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `plantilla_${csv.tipo.toLowerCase()}.csv`; link.click(); URL.revokeObjectURL(link.href)
  }
  function preview(event) {
    const file = event.target.files[0]; if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const lines = String(reader.result).split(/\r?\n/).filter(Boolean)
      setCsv((current) => ({ ...current, file, rows: lines.slice(0, 8), errors: lines.length < 2 ? ['El CSV no contiene filas.'] : [] }))
    }
    reader.readAsText(file)
  }
  async function upload() {
    if (!csv.file || csv.errors.length) return
    setIsProcessing(true)
    const body = new FormData(); body.append('archivo', csv.file)
    try { const { data } = await api.post(`/calificaciones/carga-masiva?tipo_carga=${csv.tipo}`, body, { headers: { 'Content-Type': 'multipart/form-data' } }); setMessage({ text: `Carga terminada: ${data.insertados} insertados, ${data.actualizados} actualizados y ${data.rechazados.length} rechazados.`, type: 'success' }); setModal(null); await load() }
    catch (error) { setMessage({ text: error.response?.data?.detail || 'No fue posible procesar el CSV.', type: 'error' }) }
    finally { setIsProcessing(false) }
  }

  function exportItems() {
    const headers = ['Ejercicio', 'Mercado', 'Instrumento', 'Fecha pago', 'Secuencia', 'Origen', 'Fuente', 'Estado', 'Factor 8', 'Factor 37']
    const rows = items.map((item) => [
      item.ejercicio,
      item.mercado,
      item.instrumento,
      item.fecha_pago,
      item.secuencia,
      item.origen,
      item.fuente_ingreso,
      item.estado,
      item.factor_8,
      item.factor_37,
    ])
    downloadCsv('calificaciones.csv', headers, rows)
  }

  return <main className="page">
    <header className="page-header"><div><p className="eyebrow">Analista tributario</p><h1>Mantenedor de calificaciones</h1></div></header>
    <KpiGrid items={summary} label="Resumen de calificaciones" />
    <section className="card filters">
      <select aria-label="Tipo de mercado" value={filters.mercado} onChange={(e) => updateFilter('mercado', e.target.value)}><option value="">Todos los mercados</option><option>ACN</option><option>CFI</option><option>FFMM</option></select>
      <select aria-label="Origen" value={filters.origen} onChange={(e) => updateFilter('origen', e.target.value)}><option value="">Todos los orígenes</option><option value="CORREDORA">Corredora</option><option value="SISTEMA">Sistema</option></select>
      <input aria-label="Ejercicio" type="number" placeholder="Ejercicio" value={filters.ejercicio} onChange={(e) => updateFilter('ejercicio', e.target.value)} />
      <input aria-label="Instrumento" placeholder="Instrumento" value={filters.instrumento} onChange={(e) => updateFilter('instrumento', e.target.value)} />
      <button className="primary" disabled={isLoading} onClick={() => { setMessage(null); load() }}>Buscar</button><button onClick={clearFilters}>Limpiar</button>
    </section>
    {(isLoading || isProcessing) && <p className="loading-indicator" role="status">{isProcessing ? 'Procesando solicitud...' : 'Cargando calificaciones...'}</p>}
    <section className="card table-wrap"><table><thead><tr><th></th><th>Ejercicio</th><th>Mercado</th><th>Instrumento</th><th>Fecha pago</th><th>Secuencia</th><th>Origen</th><th>Fuente</th><th>Estado</th><th>Factor 8</th><th>Factor 37</th></tr></thead><tbody>{items.length === 0 ? <tr><td colSpan="11">{isLoading ? 'Cargando calificaciones...' : 'No hay calificaciones que coincidan con los filtros.'}</td></tr> : items.map((item) => <tr key={item.id}><td><input type="radio" name="selected" checked={selected?.id === item.id} onChange={() => setSelected(item)} /></td><td className="numeric-data">{item.ejercicio}</td><td>{item.mercado}</td><td>{item.instrumento}</td><td>{item.fecha_pago}</td><td className="numeric-data">{item.secuencia}</td><td><span className={`badge ${item.origen?.toLowerCase()}`}>{item.origen}</span></td><td>{item.fuente_ingreso}</td><td><span className={`badge status-${item.estado?.toLowerCase()}`}>{item.estado}</span></td><td className="numeric-data">{item.factor_8}</td><td className="numeric-data">{item.factor_37}</td></tr>)}</tbody></table></section>
    <div className="action-bar"><button className="primary" onClick={() => { setForm(empty()); setSelected(null); setMessage(null); setModal('form') }}>Ingresar</button><button disabled={isProcessing || !selected || selected.origen === 'SISTEMA'} onClick={() => { setForm({ ...empty(), ...selected }); setMessage(null); setModal('form') }}>Modificar</button><button disabled={isProcessing || !selected || selected.origen === 'SISTEMA'} onClick={remove}>Eliminar</button><button onClick={() => { setMessage(null); setModal('csv') }}>Carga masiva</button><button className="secondary" disabled={items.length === 0 || isLoading} onClick={exportItems}>Exportar CSV</button></div>
    {!modal && message && <p className={`notice ${message.type}`}>{message.text}</p>}
    {modal === 'form' && <div className="modal-backdrop"><section className="modal card" role="dialog"><button className="modal-close" onClick={() => setModal(null)}>Cerrar</button><h2>{selected ? 'Modificar' : 'Ingresar'} calificación</h2>{message && <p className={`notice ${message.type}`}>{message.text}</p>}<form onSubmit={save}><div className="factor-grid"><label>Mercado<select value={form.mercado} onChange={(e) => update('mercado', e.target.value)}><option>ACN</option><option>CFI</option><option>FFMM</option></select></label><label>Instrumento<input required value={form.instrumento} onChange={(e) => update('instrumento', e.target.value)} /></label><label>Ejercicio<input required type="number" value={form.ejercicio} onChange={(e) => update('ejercicio', e.target.value)} /></label><label>Fecha pago<input required type="date" value={form.fecha_pago?.slice(0, 10)} onChange={(e) => update('fecha_pago', e.target.value)} /></label>    <label>Secuencia<input required min="10001" type="number" value={form.secuencia} onChange={(e) => update('secuencia', e.target.value)} /></label><label>Valor histórico<input type="number" value={form.valor_historico} onChange={(e) => update('valor_historico', e.target.value)} /></label></div><div className="tabs"><button type="button" className={form.modo === 'MONTOS' ? 'primary' : ''} onClick={() => update('modo', 'MONTOS')}>Ingreso por Montos</button><button type="button" className={form.modo === 'FACTORES' ? 'primary' : ''} onClick={() => update('modo', 'FACTORES')}>Ingreso por Factores</button></div><div className="factor-grid">{indexes.map((index) => <label key={index}>{form.modo === 'MONTOS' ? 'Monto' : 'Factor'} {index}<input required type="number" min="0" step="0.00000001" value={form[`${form.modo === 'MONTOS' ? 'monto' : 'factor'}_${index}`]} onChange={(e) => update(`${form.modo === 'MONTOS' ? 'monto' : 'factor'}_${index}`, e.target.value)} /></label>)}</div>{form.modo === 'MONTOS' && <button type="button" onClick={calculate} disabled={isProcessing}>{isProcessing ? 'Calculando...' : 'Calcular factores'}</button>}<p className={invalid ? 'error summary' : 'summary'}>Suma F8-F19: {sum.toFixed(8)} / 1.00000000 {invalid && '— supera el máximo permitido'}</p><div className="modal-actions"><button type="button" onClick={() => setModal(null)}>Cancelar</button><button className="primary" disabled={invalid || isProcessing} type="submit">{isProcessing ? 'Guardando...' : 'Grabar'}</button></div></form></section></div>}
    {modal === 'csv' && <div className="modal-backdrop"><section className="modal card" role="dialog"><button className="modal-close" onClick={() => setModal(null)}>Cerrar</button><h2>Carga masiva CSV</h2>{message && <p className={`notice ${message.type}`}>{message.text}</p>}<select value={csv.tipo} onChange={(e) => setCsv({ ...csv, tipo: e.target.value })}><option value="FACTORES">Carga de Factores</option><option value="MONTOS">Carga de Montos</option></select><button onClick={downloadTemplate}>Descargar plantilla CSV</button><input type="file" accept=".csv,text/csv" onChange={preview} />{csv.rows.length > 0 && <pre className="csv-preview">{csv.rows.join('\n')}</pre>}{csv.errors.map((error) => <p className="notice error" key={error}>{error}</p>)}<div className="modal-actions"><button onClick={() => setModal(null)} disabled={isProcessing}>Cancelar</button><button className="primary" disabled={isProcessing || !csv.file || csv.errors.length > 0} onClick={upload}>{isProcessing ? 'Subiendo...' : 'Confirmar subida'}</button></div></section></div>}
  </main>
}

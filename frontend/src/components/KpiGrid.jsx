export default function KpiGrid({ items, label }) {
  return <section className="kpi-grid" aria-label={label}>
    {items.map((item) => <article className="kpi-card" key={item.label}>
      <span className="kpi-label">{item.label}</span>
      <strong className="kpi-value">{item.value}</strong>
      {item.detail && <span className="kpi-detail">{item.detail}</span>}
    </article>)}
  </section>
}

import './Dashboard.css'

export function StatCard({ number, label, variant = 'rust', meta }) {
  return (
    <div className="stat-card">
      <div className={`stat-card__number stat-card__number--${variant}`}>
        {number}
      </div>
      <div className="stat-card__label">{label}</div>
      {meta && <div className="stat-card__meta">{meta}</div>}
    </div>
  )
}

export function StatGrid({ children }) {
  return <div className="stat-grid">{children}</div>
}

export default function Dashboard({ stats = [] }) {
  return (
    <div className="dashboard-overview">
      <div className="stat-grid">
        {stats.map((s, idx) => (
          <StatCard
            key={idx}
            number={s.number}
            label={s.label}
            variant={s.variant || 'rust'}
            meta={s.meta}
          />
        ))}
      </div>
    </div>
  )
}

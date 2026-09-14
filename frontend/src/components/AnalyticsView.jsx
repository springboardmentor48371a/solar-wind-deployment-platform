import { useState, useEffect } from 'react'
import { listProjects, listSites, getPrediction } from '../api'
import './AnalyticsView.css'

function TypeBadge({ energyType }) {
  const t = (energyType || 'solar').toLowerCase()
  if (t === 'wind') return <span className="type-badge type-badge--wi">WI</span>
  if (t === 'hybrid') return <span className="type-badge type-badge--hy">HY</span>
  return <span className="type-badge type-badge--so">SO</span>
}

function TableProgressBar({ value, variant = 'rust' }) {
  const pct = Math.min(Math.max(value ?? 0, 0), 100)
  return (
    <div className="progress-bar">
      <div
        className={`progress-bar__fill progress-bar__fill--${variant}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

function CategoryPill({ category }) {
  if (!category) return <span style={{ color: 'var(--color-text-secondary)' }}>&mdash;</span>
  const isGreen = category === 'Excellent' || category === 'Highly Suitable'
  const isRed = category === 'Unsuitable'
  const pillClass = isGreen
    ? 'status-pill--green'
    : isRed
    ? 'status-pill--red'
    : 'status-pill--peach'
  return <span className={`status-pill ${pillClass}`}>{category}</span>
}

export default function AnalyticsView() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [sortKey, setSortKey] = useState('suitability_score')
  const [sortDir, setSortDir] = useState('desc')
  const [search, setSearch] = useState('')

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    setLoading(true)
    try {
      const projRes = await listProjects()
      const sitesNested = await Promise.all(
        projRes.data.map((p) =>
          listSites(p.id).then((r) =>
            r.data.map((s) => ({ ...s, project_name: p.name }))
          )
        )
      )
      const allSites = sitesNested.flat()

      const withPreds = await Promise.all(
        allSites.map(async (site) => {
          try {
            const r = await getPrediction(site.id)
            return { ...site, pred: r.data }
          } catch {
            return { ...site, pred: null }
          }
        })
      )
      setRows(withPreds)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (key) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const sorted = [...rows]
    .filter((r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      r.project_name.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => {
    const av = a.pred?.[sortKey] ?? -1
    const bv = b.pred?.[sortKey] ?? -1
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const SortHeader = ({ label, k }) => (
    <th
      onClick={() => handleSort(k)}
      className={`sortable ${sortKey === k ? 'sorted' : ''}`}
    >
      {label} {sortKey === k ? (sortDir === 'desc' ? '↓' : '↑') : ''}
    </th>
  )

  if (loading) {
    return (
      <div className="analytics-view">
        <div className="data-table__empty">
          <div style={{ color: 'var(--color-accent-rust)', marginBottom: 8, fontSize: 16 }}>&bull; &bull; &bull;</div>
          Loading site analytics &amp; ML assessments...
        </div>
      </div>
    )
  }

  return (
    <div className="analytics-view">
      {/* Overview stats per category */}
      <div className="analytics-view__stats">
        <div className="analytics-card">
          <div className="analytics-card__num analytics-card__num--olive">
            {rows.filter((r) => r.pred?.suitability_category === 'Excellent').length}
          </div>
          <div className="analytics-card__label">Excellent</div>
        </div>
        <div className="analytics-card">
          <div className="analytics-card__num analytics-card__num--olive">
            {rows.filter((r) => r.pred?.suitability_category === 'Highly Suitable').length}
          </div>
          <div className="analytics-card__label">Highly Suitable</div>
        </div>
        <div className="analytics-card">
          <div className="analytics-card__num analytics-card__num--rust">
            {rows.filter((r) => r.pred?.suitability_category === 'Moderately Suitable').length}
          </div>
          <div className="analytics-card__label">Moderately Suitable</div>
        </div>
        <div className="analytics-card">
          <div className="analytics-card__num analytics-card__num--rust">
            {rows.filter((r) => r.pred?.suitability_category === 'Low Suitability').length}
          </div>
          <div className="analytics-card__label">Low Suitability</div>
        </div>
        <div className="analytics-card">
          <div className="analytics-card__num analytics-card__num--red">
            {rows.filter((r) => r.pred?.suitability_category === 'Unsuitable').length}
          </div>
          <div className="analytics-card__label">Unsuitable</div>
        </div>
        <div className="analytics-card">
          <div className="analytics-card__num analytics-card__num--steel">
            {rows.filter((r) => !r.pred).length}
          </div>
          <div className="analytics-card__label">Unpredicted</div>
        </div>
      </div>

      {/* Rankings Data Table */}
      <div className="data-table-wrapper">
        <input
          type="text"
          className="search-input"
          placeholder="Search by site or project name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ marginBottom: '12px' }}
        />
        <div className="data-table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}>#</th>
                <th>Type</th>
                <th>Site Name</th>
                <th>Project</th>
                <SortHeader label="Suitability" k="suitability_score" />
                <SortHeader label="Resource" k="resource_score" />
                <SortHeader label="Land Cover" k="land_cover_score" />
                <SortHeader label="Geographic" k="geographic_score" />
                <SortHeader label="Infrastructure" k="infrastructure_score" />
                <SortHeader label="Economic" k="economic_score" />
                <th>Tier</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((site, i) => {
                const p = site.pred
                const suitScore = p?.suitability_score
                const suitVariant =
                  suitScore >= 75 ? 'olive' : suitScore >= 50 ? 'rust' : 'steel'

                return (
                  <tr key={site.id}>
                    <td style={{ color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                      {i + 1}
                    </td>
                    <td>
                      <TypeBadge energyType={site.energy_type} />
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{site.name}</div>
                    </td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>
                      {site.project_name}
                    </td>
                    <td>
                      {p ? (
                        <>
                          <div style={{ fontWeight: 700, color: `var(--color-accent-${suitVariant})` }}>
                            {Math.round(suitScore ?? 0)}
                          </div>
                          <TableProgressBar value={suitScore} variant={suitVariant} />
                        </>
                      ) : (
                        <span style={{ color: 'var(--color-text-secondary)' }}>&mdash;</span>
                      )}
                    </td>
                    {['resource_score', 'land_cover_score', 'geographic_score', 'infrastructure_score', 'economic_score'].map((k) => (
                      <td key={k}>
                        {p?.[k] != null ? (
                          <>
                            <div style={{ fontWeight: 500 }}>
                              {Math.round(p[k])}
                            </div>
                            <TableProgressBar value={p[k]} variant="steel" />
                          </>
                        ) : (
                          <span style={{ color: 'var(--color-text-secondary)' }}>&mdash;</span>
                        )}
                      </td>
                    ))}
                    <td>
                      <CategoryPill category={p?.suitability_category} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        {sorted.length === 0 && (
          <div className="data-table__empty">
            {rows.length > 0 ? `No matches for "${search}"` : 'No sites available for ranking.'}
          </div>
        )}
      </div>
    </div>
  )
}

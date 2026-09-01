import { useState, useEffect } from 'react'
import { listProjects, listSites, getPrediction } from '../api'

const CATEGORY_COLORS = {
  'Excellent':           '#16a34a',
  'Highly Suitable':     '#65a30d',
  'Moderately Suitable': '#ca8a04',
  'Low Suitability':     '#ea580c',
  'Unsuitable':          '#dc2626',
}

const ScoreBar = ({ value, color }) => (
  <div style={{ height: 5, background: '#e5e7eb', borderRadius: 3, width: 80 }}>
    <div style={{ height: '100%', width: `${Math.min(value ?? 0, 100)}%`, background: color || '#6b7280', borderRadius: 3 }} />
  </div>
)

export default function AnalyticsView() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [sortKey, setSortKey] = useState('suitability_score')
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => { load() }, [])

  const load = async () => {
    setLoading(true)
    try {
      const projRes = await listProjects()
      const sitesNested = await Promise.all(projRes.data.map(p => listSites(p.id).then(r => r.data.map(s => ({ ...s, project_name: p.name })))))
      const allSites = sitesNested.flat()

      const withPreds = await Promise.all(allSites.map(async site => {
        try {
          const r = await getPrediction(site.id)
          return { ...site, pred: r.data }
        } catch {
          return { ...site, pred: null }
        }
      }))
      setRows(withPreds)
    } finally {
      setLoading(false)
    }
  }

  const handleSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = [...rows].sort((a, b) => {
    const av = a.pred?.[sortKey] ?? -1
    const bv = b.pred?.[sortKey] ?? -1
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const SortHeader = ({ label, k }) => (
    <th onClick={() => handleSort(k)} style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#6b7280', cursor: 'pointer', whiteSpace: 'nowrap', userSelect: 'none', background: sortKey === k ? '#f3f4f6' : 'transparent' }}>
      {label} {sortKey === k ? (sortDir === 'desc' ? '↓' : '↑') : ''}
    </th>
  )

  if (loading) return <p style={{ fontSize: 13, color: '#9ca3af' }}>Loading analytics...</p>

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Site Analytics & Rankings</h2>
        <span style={{ fontSize: 12, color: '#9ca3af' }}>{rows.length} sites · click column to sort</span>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
        {['Excellent', 'Highly Suitable', 'Moderately Suitable', 'Low Suitability', 'Unsuitable'].map(cat => {
          const count = rows.filter(r => r.pred?.suitability_category === cat).length
          const color = CATEGORY_COLORS[cat]
          return (
            <div key={cat} style={{ background: color + '10', border: `1px solid ${color}30`, borderRadius: 8, padding: '10px 16px', minWidth: 120 }}>
              <div style={{ fontSize: 22, fontWeight: 800, color }}>{count}</div>
              <div style={{ fontSize: 11, color, fontWeight: 600 }}>{cat}</div>
            </div>
          )
        })}
        <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: '10px 16px', minWidth: 120 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#9ca3af' }}>{rows.filter(r => !r.pred).length}</div>
          <div style={{ fontSize: 11, color: '#9ca3af', fontWeight: 600 }}>No Predictions</div>
        </div>
      </div>

      {/* Rankings table */}
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ borderBottom: '1px solid #e5e7eb' }}>
            <tr>
              <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#6b7280' }}>#</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#6b7280' }}>Site</th>
              <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#6b7280' }}>Type</th>
              <SortHeader label="Suitability" k="suitability_score" />
              <SortHeader label="Solar" k="solar_score" />
              <SortHeader label="Wind" k="wind_score" />
              <SortHeader label="Land Cover" k="land_cover_score" />
              <SortHeader label="Resource" k="resource_score" />
              <SortHeader label="Geographic" k="geographic_score" />
              <th style={{ padding: '8px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, color: '#6b7280' }}>Category</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((site, i) => {
              const p = site.pred
              const catColor = p ? (CATEGORY_COLORS[p.suitability_category] || '#6b7280') : '#d1d5db'
              return (
                <tr key={site.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: '#9ca3af', fontWeight: 600 }}>{i + 1}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: '#111' }}>{site.name}</div>
                    <div style={{ fontSize: 11, color: '#9ca3af' }}>{site.project_name}</div>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: 12, color: '#6b7280', textTransform: 'capitalize' }}>{site.energy_type}</td>
                  <td style={{ padding: '10px 12px' }}>
                    {p ? (
                      <>
                        <div style={{ fontSize: 15, fontWeight: 700, color: catColor }}>{Math.round(p.suitability_score ?? 0)}</div>
                        <ScoreBar value={p.suitability_score} color={catColor} />
                      </>
                    ) : <span style={{ fontSize: 11, color: '#d1d5db' }}>—</span>}
                  </td>
                  {['solar_score', 'wind_score', 'land_cover_score', 'resource_score', 'geographic_score'].map(k => (
                    <td key={k} style={{ padding: '10px 12px' }}>
                      {p?.[k] != null ? (
                        <>
                          <div style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{Math.round(p[k])}</div>
                          <ScoreBar value={p[k]} color="#9ca3af" />
                        </>
                      ) : <span style={{ fontSize: 11, color: '#d1d5db' }}>—</span>}
                    </td>
                  ))}
                  <td style={{ padding: '10px 12px' }}>
                    {p?.suitability_category ? (
                      <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12, background: catColor + '20', color: catColor, fontWeight: 600 }}>
                        {p.suitability_category}
                      </span>
                    ) : <span style={{ fontSize: 11, color: '#d1d5db' }}>—</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {sorted.length === 0 && (
          <p style={{ padding: 20, fontSize: 13, color: '#9ca3af', textAlign: 'center' }}>No sites found.</p>
        )}
      </div>
    </div>
  )
}

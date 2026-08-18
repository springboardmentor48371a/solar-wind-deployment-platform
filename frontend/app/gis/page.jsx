'use client'

import { useEffect, useMemo, useState } from 'react'
import dynamic from 'next/dynamic'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'

// Leaflet touches `window` at import time — load client-side only.
const MapView = dynamic(() => import('../../components/LeafletSiteMap'), {
  ssr: false,
  loading: () => <div className="h-[480px] flex items-center justify-center text-ink-faint text-sm">Loading map…</div>,
})

const categoryColor = {
  Excellent: '#1e6f4c',
  'Highly Suitable': '#227a8f',
  'Moderately Suitable': '#a5670c',
  'Low Suitability': '#c26b2c',
  Unsuitable: '#b3261e',
  Unscored: '#8a988f',
}

const catClass = {
  Excellent: 'cat-excellent',
  'Highly Suitable': 'cat-highly-suitable',
  'Moderately Suitable': 'cat-moderately-suitable',
  'Low Suitability': 'cat-low-suitability',
  Unsuitable: 'cat-unsuitable',
}

const TABS = [
  { key: 'map', label: 'GIS Visualization' },
  { key: 'terrain', label: 'Terrain Maps' },
  { key: 'environmental', label: 'Environmental Analytics' },
  { key: 'compare', label: 'Site Comparison' },
]

function fmt(v, suffix = '') {
  return v === null || v === undefined ? '—' : `${v}${suffix}`
}

export default function GisView() {
  const [sites, setSites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('map')
  const [sortKey, setSortKey] = useState('overall_score')
  const [sortDir, setSortDir] = useState('desc')

  useEffect(() => {
    api
      .get('/gis/sites')
      .then((res) => setSites(res.data))
      .catch(() => setError('Could not load sites for the map.'))
      .finally(() => setLoading(false))
  }, [])

  const sortedSites = useMemo(() => {
    const copy = [...sites]
    copy.sort((a, b) => {
      const av = a[sortKey]
      const bv = b[sortKey]
      if (av === null || av === undefined) return 1
      if (bv === null || bv === undefined) return -1
      return sortDir === 'desc' ? bv - av : av - bv
    })
    return copy
  }, [sites, sortKey, sortDir])

  const toggleSort = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const SortHeader = ({ label, sortField }) => (
    <th className="cursor-pointer select-none whitespace-nowrap" onClick={() => toggleSort(sortField)}>
      {label} {sortKey === sortField ? (sortDir === 'desc' ? '↓' : '↑') : ''}
    </th>
  )

  return (
    <AppShell
      title="GIS Site Intelligence"
      subtitle={loading ? 'Loading sites…' : `${sites.length} site${sites.length === 1 ? '' : 's'} across every project you can see`}
      actions={Object.entries(categoryColor)
        .filter(([k]) => k !== 'Unscored')
        .map(([label, color]) => (
          <span key={label} className={`badge ${catClass[label]}`}>
            <span className="w-1.5 h-1.5 rounded-full inline-block mr-1" style={{ background: color }} />
            {label}
          </span>
        ))}
    >
      {error && <div className="error-banner mb-4">{error}</div>}

      <div className="flex gap-1.5 mb-4 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={tab === t.key ? 'btn-sm btn' : 'btn-sm btn-secondary'}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'map' && (
        <div className="card p-0 overflow-hidden mb-4">
          {sites.length === 0 && !loading ? (
            <div className="h-[480px] flex flex-col items-center justify-center gap-2 text-center px-8">
              <p className="text-ink-muted text-sm">No sites registered yet — the map will fill in as you add sites.</p>
            </div>
          ) : (
            <MapView sites={sites} categoryColor={categoryColor} />
          )}
        </div>
      )}

      {tab === 'terrain' && (
        <div className="card">
          <h3 className="mb-1">Terrain Maps</h3>
          <p className="text-ink-muted text-sm mb-3">Elevation, land slope, and land area per site — from the SRTM/terrain pipeline (Geographic Intelligence Engine).</p>
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Project</th>
                  <SortHeader label="Elevation" sortField="elevation_m" />
                  <SortHeader label="Land Slope" sortField="land_slope_pct" />
                  <SortHeader label="Land Area" sortField="land_area_hectares" />
                  <SortHeader label="Substation Distance" sortField="distance_to_substation_km" />
                </tr>
              </thead>
              <tbody>
                {sortedSites.map((s) => (
                  <tr key={s.site_id}>
                    <td>{s.site_name}</td>
                    <td className="text-ink-faint text-xs">{s.project_name}</td>
                    <td>{fmt(s.elevation_m, ' m')}</td>
                    <td>{fmt(s.land_slope_pct, '%')}</td>
                    <td>{fmt(s.land_area_hectares, ' ha')}</td>
                    <td>{fmt(s.distance_to_substation_km, ' km')}</td>
                  </tr>
                ))}
                {sites.length === 0 && !loading && (
                  <tr><td colSpan={6}><div className="text-ink-faint text-sm py-6 text-center">No sites to display yet.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'environmental' && (
        <div className="card">
          <h3 className="mb-1">Environmental Analytics</h3>
          <p className="text-ink-muted text-sm mb-3">Protected-area and water-body proximity, plus the environmental sub-score each feeds into the suitability formula (15% weight).</p>
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Project</th>
                  <SortHeader label="Protected Area Distance" sortField="protected_area_distance_km" />
                  <SortHeader label="Water Body Distance" sortField="water_body_distance_km" />
                  <SortHeader label="Environmental Score" sortField="environmental_score" />
                </tr>
              </thead>
              <tbody>
                {sortedSites.map((s) => (
                  <tr key={s.site_id}>
                    <td>{s.site_name}</td>
                    <td className="text-ink-faint text-xs">{s.project_name}</td>
                    <td>{fmt(s.protected_area_distance_km, ' km')}</td>
                    <td>{fmt(s.water_body_distance_km, ' km')}</td>
                    <td>{fmt(s.environmental_score)}</td>
                  </tr>
                ))}
                {sites.length === 0 && !loading && (
                  <tr><td colSpan={5}><div className="text-ink-faint text-sm py-6 text-center">No sites to display yet.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'compare' && (
        <div className="card">
          <h3 className="mb-1">Site Comparison Report</h3>
          <p className="text-ink-muted text-sm mb-3">Every visible site, ranked by suitability sub-score — click a column to sort. For a two-project side-by-side breakdown, use a project's own Compare view.</p>
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Project</th>
                  <SortHeader label="Overall" sortField="overall_score" />
                  <SortHeader label="Resource" sortField="resource_score" />
                  <SortHeader label="Geographic" sortField="geographic_score" />
                  <SortHeader label="Infrastructure" sortField="infrastructure_score" />
                  <SortHeader label="Environmental" sortField="environmental_score" />
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                {sortedSites.map((s) => (
                  <tr key={s.site_id}>
                    <td>{s.site_name}</td>
                    <td className="text-ink-faint text-xs">{s.project_name}</td>
                    <td className="font-semibold">{fmt(s.overall_score)}</td>
                    <td>{fmt(s.resource_score)}</td>
                    <td>{fmt(s.geographic_score)}</td>
                    <td>{fmt(s.infrastructure_score)}</td>
                    <td>{fmt(s.environmental_score)}</td>
                    <td><span className={`badge ${catClass[s.category] || 'cat-unscored'}`}>{s.category}</span></td>
                  </tr>
                ))}
                {sites.length === 0 && !loading && (
                  <tr><td colSpan={8}><div className="text-ink-faint text-sm py-6 text-center">No sites to display yet.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppShell>
  )
}

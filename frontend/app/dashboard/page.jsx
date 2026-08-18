'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import api from '../../lib/api'
import { useAuth } from '../../lib/AuthContext'
import AppShell from '../../components/AppShell'
import { canCreate } from '../../lib/roles'

// Plotly touches `window`/canvas at import time, so it must be loaded
// client-side only — dynamic() with ssr:false is the standard Next.js
// pattern for that.
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false })

export default function Dashboard() {
  const { user } = useAuth()
  const [summary, setSummary] = useState(null)
  const [sources, setSources] = useState([])
  const [rollup, setRollup] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/analytics/dashboard'),
      api.get('/data-sources/status'),
      api.get('/analytics/warehouse').catch(() => ({ data: [] })),
    ])
      .then(([summaryRes, sourcesRes, rollupRes]) => {
        setSummary(summaryRes.data)
        setSources(sourcesRes.data)
        setRollup(rollupRes.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const categories = summary ? Object.keys(summary.sites_by_category) : []
  const counts = summary ? Object.values(summary.sites_by_category) : []

  const greetingName = user?.full_name?.split(' ')[0] || 'there'
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  const role = user?.role

  return (
    <AppShell
      title={`${greeting}, ${greetingName}`}
      subtitle={<>Signed in as <span className="badge">{role}</span></>}
      actions={
        <>
          {canCreate(user) && <Link href="/projects"><button className="btn">+ New Project</button></Link>}
          <Link href="/gis"><button className="btn-secondary">Open GIS View</button></Link>
        </>
      }
    >
      {loading && <div className="card mb-4"><span className="spinner" /> Loading portfolio…</div>}

      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 mb-4">
          {[
            ['Active Projects', summary.active_projects, null],
            ['Total Sites', summary.total_sites, null],
            ['Avg. Suitability', summary.average_suitability ?? '—', 'out of 100'],
            ['Data Freshness', `${summary.data_freshness_pct}%`, null],
          ].map(([label, value, hint]) => (
            <div className="card" key={label}>
              <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted">{label}</div>
              <div className="text-[26px] font-extrabold mt-1">{value}</div>
              {hint && <div className="text-xs text-ink-faint mt-0.5">{hint}</div>}
            </div>
          ))}
        </div>
      )}

      <div className="card mb-4">
        <h3 className="mb-3">Sites by suitability category</h3>
        {categories.length > 0 ? (
          <Plot
            data={[{ x: categories, y: counts, type: 'bar', marker: { color: '#1e6f4c' } }]}
            layout={{
              autosize: true,
              height: 220,
              margin: { t: 10, r: 10, l: 36, b: 40 },
              font: { family: 'Inter, sans-serif', size: 12, color: '#64766e' },
              xaxis: { gridcolor: '#eef1ef' },
              yaxis: { gridcolor: '#eef1ef', zeroline: false },
              plot_bgcolor: 'rgba(0,0,0,0)',
              paper_bgcolor: 'rgba(0,0,0,0)',
            }}
            config={{ displayModeBar: false, responsive: true }}
            style={{ width: '100%' }}
          />
        ) : (
          <div className="text-ink-faint text-sm py-6 text-center">No scored sites yet — register a site to see suitability breakdown.</div>
        )}
      </div>

      {/* ---------- Role-specific dashboard body ---------- */}
      {role === 'Renewable Energy Planner' && <PlannerDashboard rollup={rollup} />}
      {role === 'GIS Analyst' && <GisAnalystDashboard rollup={rollup} sources={sources} />}
      {role === 'Project Manager' && <ProjectManagerDashboard rollup={rollup} />}
      {role === 'Administrator' && <AdminDashboard sources={sources} />}
      {(role === 'Investor / Developer' || role === 'Government / Regulator') && (
        <OversightDashboard rollup={rollup} />
      )}

      <div className="card">
        <h3 className="mb-3">Quick actions</h3>
        <div className="flex gap-2.5 flex-wrap">
          <Link href="/projects"><button className="btn">Go to Projects</button></Link>
          <Link href="/alerts"><button className="btn-secondary">View Alerts</button></Link>
          <Link href="/gis"><button className="btn-secondary">GIS View</button></Link>
          <Link href="/reports"><button className="btn-secondary">Report Builder</button></Link>
          {role === 'Administrator' && (
            <>
              <Link href="/admin/users"><button className="btn-secondary">Manage Users</button></Link>
              <Link href="/admin/integrations"><button className="btn-secondary">Integrations</button></Link>
            </>
          )}
        </div>
      </div>
    </AppShell>
  )
}

function sourceStatusBadgeClass(status) {
  if (status === 'operational') return ''
  if (status === 'not_configured') return 'badge-gray'
  return 'badge-red' // degraded / down
}

function RollupTable({ rollup, columns }) {
  if (!rollup || rollup.length === 0) {
    return <div className="text-ink-faint text-sm py-6 text-center">No warehouse data yet — refresh a site's data to populate this view.</div>
  }
  return (
    <div className="overflow-x-auto">
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
        </thead>
        <tbody>
          {rollup.map((row) => (
            <tr key={row.site_id}>
              {columns.map((c) => <td key={c.key}>{c.render ? c.render(row) : (row[c.key] ?? '—')}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PlannerDashboard({ rollup }) {
  const recommended = rollup
    .slice()
    .sort((a, b) => (b.overall_suitability_score ?? -1) - (a.overall_suitability_score ?? -1))
    .slice(0, 5)

  return (
    <div className="card mb-4">
      <h3 className="mb-1">Recommended Deployment Sites</h3>
      <p className="text-ink-muted text-sm mb-3">Ranked by suitability score, with energy forecasts and investment signal.</p>
      <RollupTable
        rollup={recommended}
        columns={[
          { key: 'site_name', label: 'Site' },
          { key: 'region_name', label: 'Region' },
          { key: 'overall_suitability_score', label: 'Suitability', render: (r) => r.overall_suitability_score ?? '—' },
          { key: 'suitability_category', label: 'Category' },
          { key: 'solar_expected_output_mwh_yr', label: 'Solar (MWh/MW/yr)' },
          { key: 'wind_expected_aep_mwh_yr', label: 'Wind (MWh/MW/yr)' },
          { key: 'financial_irr_pct', label: 'IRR %' },
        ]}
      />
    </div>
  )
}

function GisAnalystDashboard({ rollup, sources }) {
  return (
    <>
      <div className="card mb-4">
        <h3 className="mb-1">Environmental Analytics — Site Comparison</h3>
        <p className="text-ink-muted text-sm mb-3">Protected-area and substation proximity across the portfolio.</p>
        <RollupTable
          rollup={rollup}
          columns={[
            { key: 'site_name', label: 'Site' },
            { key: 'protected_area_distance_km', label: 'Protected Area (km)' },
            { key: 'substation_distance_km', label: 'Substation (km)' },
            { key: 'suitability_category', label: 'Category' },
          ]}
        />
      </div>
      <div className="card mb-4">
        <h3 className="mb-1">GIS Data Connectors</h3>
        <div className="flex flex-col gap-1 mt-2">
          {sources.map((s) => (
            <div key={s.name} className="flex items-center justify-between py-1.5">
              <span className="text-sm">{s.name}</span>
              <span className={`badge ${sourceStatusBadgeClass(s.status)}`}>{s.status}</span>
            </div>
          ))}
        </div>
        <Link href="/gis" className="text-brand text-sm inline-block mt-3">Open full terrain map →</Link>
      </div>
    </>
  )
}

function ProjectManagerDashboard({ rollup }) {
  return (
    <div className="card mb-4">
      <h3 className="mb-1">Portfolio Feasibility & Cost-Benefit</h3>
      <p className="text-ink-muted text-sm mb-3">Financial analytics across every site with a completed investment model.</p>
      <RollupTable
        rollup={rollup.filter((r) => r.financial_npv_usd != null)}
        columns={[
          { key: 'site_name', label: 'Site' },
          { key: 'financial_npv_usd', label: 'NPV ($)', render: (r) => r.financial_npv_usd?.toLocaleString?.() ?? r.financial_npv_usd },
          { key: 'financial_irr_pct', label: 'IRR %' },
          { key: 'financial_lcoe_usd_per_mwh', label: 'LCOE ($/MWh)' },
          { key: 'suitability_category', label: 'Category' },
        ]}
      />
      {rollup.filter((r) => r.financial_npv_usd != null).length === 0 && (
        <p className="text-ink-faint text-sm mt-2">No financial models run yet — open a site's intelligence panel to run one.</p>
      )}
    </div>
  )
}

function AdminDashboard({ sources }) {
  const [refreshing, setRefreshing] = useState(false)
  const [refreshMsg, setRefreshMsg] = useState('')

  const refreshWarehouse = async () => {
    setRefreshing(true)
    setRefreshMsg('')
    try {
      const res = await api.post('/analytics/warehouse/refresh')
      setRefreshMsg(`Refreshed ${res.data.rows_refreshed} site rows at ${new Date(res.data.refreshed_at).toLocaleTimeString()}.`)
    } catch (err) {
      setRefreshMsg('Refresh failed — see server logs.')
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="card mb-4">
      <h3 className="mb-1">Platform Administration</h3>
      <p className="text-ink-muted text-sm mb-3">System monitoring, data source management, and warehouse control.</p>
      <div className="flex flex-col gap-1 mb-3">
        {sources.map((s) => (
          <div key={s.name} className="flex items-center justify-between py-1.5">
            <span className="text-sm">{s.name}</span>
            <span className={`badge ${sourceStatusBadgeClass(s.status)}`}>{s.status}</span>
          </div>
        ))}
      </div>
      <div className="flex gap-2.5 flex-wrap items-center">
        <button className="btn-secondary" disabled={refreshing} onClick={refreshWarehouse}>
          {refreshing ? 'Refreshing…' : 'Refresh Data Warehouse'}
        </button>
        <Link href="/admin/users"><button className="btn-secondary">User Management</button></Link>
        <Link href="/admin/integrations"><button className="btn-secondary">Integrations</button></Link>
        <Link href="/admin/audit-log"><button className="btn-secondary">Audit Log</button></Link>
        <a href={`${(process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000')}/metrics`} target="_blank" rel="noreferrer">
          <button className="btn-secondary">Prometheus /metrics</button>
        </a>
      </div>
      {refreshMsg && <p className="text-xs text-ink-muted mt-2">{refreshMsg}</p>}
    </div>
  )
}

function OversightDashboard({ rollup }) {
  return (
    <div className="card mb-4">
      <h3 className="mb-1">Portfolio Investment Overview</h3>
      <p className="text-ink-muted text-sm mb-3">Read-only oversight across every project — suitability, energy potential, and investment metrics.</p>
      <RollupTable
        rollup={rollup}
        columns={[
          { key: 'site_name', label: 'Site' },
          { key: 'suitability_category', label: 'Category' },
          { key: 'financial_npv_usd', label: 'NPV ($)', render: (r) => r.financial_npv_usd?.toLocaleString?.() ?? '—' },
          { key: 'financial_irr_pct', label: 'IRR %' },
        ]}
      />
    </div>
  )
}

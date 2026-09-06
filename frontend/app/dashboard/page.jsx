'use client'

import { useEffect, useState } from 'react'
import dynamic from 'next/dynamic'
import Link from 'next/link'
import api from '../../lib/api'
import { useAuth } from '../../lib/AuthContext'
import AppShell from '../../components/AppShell'
import { canCreate } from '../../lib/roles'
import { useToast } from '../../lib/ToastContext'
import { getErrorMessage } from '../../lib/errorMessage'

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

    // Data source health can change moment to moment (an external API
    // going down, rate-limiting, etc.) — poll it independently every 30s
    // so the status shown doesn't just reflect the moment the page
    // loaded. This is a real polling refresh, not a background task
    // queue — deliberately lightweight, in keeping with this project's
    // actual scope rather than adding new infrastructure for it.
    const interval = setInterval(() => {
      api.get('/data-sources/status').then((res) => setSources(res.data)).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
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
  if (status === 'manually_disabled') return 'badge-amber'
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
  const [recommended, setRecommended] = useState(null)

  useEffect(() => {
    // Was reading from the Data Warehouse rollup, which only updates
    // via a separate Admin/PM-only manual "Refresh" action — a Planner
    // registering their own sites had no way to populate it themselves,
    // so this section could stay empty even with real scored sites.
    // Now computed live, no manual refresh step required.
    api.get('/analytics/recommended-sites').then((res) => setRecommended(res.data)).catch(() => setRecommended([]))
  }, [])

  return (
    <div className="card mb-4">
      <h3 className="mb-1">Recommended Deployment Sites</h3>
      <p className="text-ink-muted text-sm mb-3">Ranked by suitability score, with energy forecasts and investment signal.</p>
      {recommended === null ? (
        <span className="text-ink-faint text-sm"><span className="spinner" />Loading…</span>
      ) : recommended.length === 0 ? (
        <p className="text-ink-faint text-sm py-4 text-center">
          No scored sites yet. Register a site under Projects & Sites — it's scored automatically, no extra step needed.
        </p>
      ) : (
        <RollupTable
          rollup={recommended}
          columns={[
            { key: 'site_name', label: 'Site' },
            { key: 'project_name', label: 'Project' },
            { key: 'overall_suitability_score', label: 'Suitability', render: (r) => r.overall_suitability_score ?? '—' },
            { key: 'suitability_category', label: 'Category' },
            { key: 'solar_expected_output_mwh_yr', label: 'Solar (MWh/MW/yr)', render: (r) => r.solar_expected_output_mwh_yr ?? '—' },
            { key: 'wind_expected_aep_mwh_yr', label: 'Wind (MWh/MW/yr)', render: (r) => r.wind_expected_aep_mwh_yr ?? '—' },
            { key: 'financial_irr_pct', label: 'IRR %', render: (r) => r.financial_irr_pct ?? 'Not run yet' },
          ]}
        />
      )}
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
        <div className="flex items-center justify-between mb-1">
          <h3>GIS Data Connectors</h3>
          <span className="text-[11px] text-ink-faint">Live-checked every 30s</span>
        </div>
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
  const [progress, setProgress] = useState(null)
  const [timeline, setTimeline] = useState(null)

  useEffect(() => {
    api.get('/analytics/deployment-progress').then((res) => setProgress(res.data)).catch(() => setProgress({}))
    api.get('/analytics/deployment-timeline?limit=10').then((res) => setTimeline(res.data)).catch(() => setTimeline([]))
  }, [])

  const STATUS_ORDER = ['Prospecting', 'Under Review', 'Approved', 'Deployment Planned', 'Deployed', 'Operational', 'Cancelled']
  const totalSites = progress ? Object.values(progress).reduce((a, b) => a + b, 0) : 0

  return (
    <>
      <div className="card mb-4">
        <h3 className="mb-1">Project Progress</h3>
        <p className="text-ink-muted text-sm mb-3">Where every visible site currently stands in its deployment lifecycle.</p>
        {!progress ? (
          <span className="text-ink-faint"><span className="spinner" />Loading…</span>
        ) : totalSites === 0 ? (
          <p className="text-ink-faint text-sm">No sites registered yet.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {STATUS_ORDER.filter((s) => progress[s]).map((status) => (
              <div key={status} className="grid grid-cols-[160px_1fr_34px] items-center gap-2.5 text-[12.5px]">
                <span className="text-ink-muted">{status}</span>
                <div className="h-2 bg-surface-2 rounded-full overflow-hidden border border-border">
                  <div className="h-full bg-gradient-to-r from-[#3fae7c] to-brand" style={{ width: `${(progress[status] / totalSites) * 100}%` }} />
                </div>
                <b>{progress[status]}</b>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card mb-4">
        <h3 className="mb-1">Deployment Timeline</h3>
        <p className="text-ink-muted text-sm mb-3">Recent status changes across the portfolio.</p>
        {!timeline ? (
          <span className="text-ink-faint"><span className="spinner" />Loading…</span>
        ) : timeline.length === 0 ? (
          <p className="text-ink-faint text-sm">No status changes recorded yet.</p>
        ) : (
          <ol className="relative border-l-2 border-border ml-1.5 pl-4 space-y-2.5">
            {timeline.map((h) => (
              <li key={h.id} className="relative text-[12.5px]">
                <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-brand border-2 border-white" />
                <b>{h.previous_status ? `${h.previous_status} → ${h.new_status}` : `Created as ${h.new_status}`}</b>
                <span className="text-ink-faint ml-2">{new Date(h.changed_at).toLocaleString()}</span>
              </li>
            ))}
          </ol>
        )}
      </div>

      <div className="card mb-4">
        <h3 className="mb-1">Portfolio Feasibility & Cost-Benefit</h3>
        <p className="text-ink-muted text-sm mb-3">Financial analytics across every site with a completed investment model.</p>
        <RollupTable
          rollup={rollup.filter((r) => r.financial_npv_usd != null)}
          columns={[
            { key: 'site_name', label: 'Site' },
            { key: 'financial_npv_usd', label: 'NPV ($)', render: (r) => r.financial_npv_usd?.toLocaleString?.() ?? r.financial_npv_usd },
            { key: 'financial_lcoe_usd_per_mwh', label: 'LCOE ($/MWh)' },
            { key: 'financial_irr_pct', label: 'IRR %', render: (r) => r.financial_irr_pct ?? 'Could not converge' },
            { key: 'suitability_category', label: 'Category' },
          ]}
        />
        {rollup.filter((r) => r.financial_npv_usd != null).length === 0 && (
          <p className="text-ink-faint text-sm mt-2">No financial models run yet — open a site's intelligence panel to run one.</p>
        )}
        <Link href="/reports" className="text-brand text-sm inline-block mt-3">Generate a Feasibility Report →</Link>
      </div>
    </>
  )
}

function AdminDashboard({ sources }) {
  const [refreshing, setRefreshing] = useState(false)
  const [refreshMsg, setRefreshMsg] = useState('')
  const [platformStats, setPlatformStats] = useState(null)
  const [localSources, setLocalSources] = useState(sources)
  const [togglingSource, setTogglingSource] = useState(null)
  const { showToast } = useToast()

  useEffect(() => {
    setLocalSources(sources)
  }, [sources])

  useEffect(() => {
    api.get('/analytics/platform-stats').then((res) => setPlatformStats(res.data)).catch(() => setPlatformStats(null))
  }, [])

  const toggleSource = async (source) => {
    const isCurrentlyDisabled = source.status === 'manually_disabled'
    setTogglingSource(source.name)
    try {
      const res = await api.post(`/data-sources/${encodeURIComponent(source.name)}/override`, {
        manually_disabled: !isCurrentlyDisabled,
        reason: !isCurrentlyDisabled ? 'Paused by administrator' : undefined,
      })
      setLocalSources((prev) => prev.map((s) => (s.name === source.name ? res.data : s)))
      showToast(isCurrentlyDisabled ? `${source.name} re-enabled.` : `${source.name} manually disabled.`, 'success')
    } catch (err) {
      showToast(getErrorMessage(err, 'Could not update data source'), 'error')
    } finally {
      setTogglingSource(null)
    }
  }

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
    <>
      <div className="card mb-4">
        <h3 className="mb-1">Platform Analytics</h3>
        <p className="text-ink-muted text-sm mb-3">User base and portfolio scale, at a glance.</p>
        {!platformStats ? (
          <span className="text-ink-faint"><span className="spinner" />Loading…</span>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <div className="card-hover !py-3 text-center">
                <div className="text-2xl font-bold text-brand">{platformStats.total_users}</div>
                <div className="text-ink-faint text-[11px] uppercase tracking-wide">Total Users</div>
              </div>
              <div className="card-hover !py-3 text-center">
                <div className="text-2xl font-bold text-brand">{platformStats.active_users}</div>
                <div className="text-ink-faint text-[11px] uppercase tracking-wide">Active Users</div>
              </div>
              <div className="card-hover !py-3 text-center">
                <div className="text-2xl font-bold text-brand">{platformStats.total_projects}</div>
                <div className="text-ink-faint text-[11px] uppercase tracking-wide">Projects</div>
              </div>
              <div className="card-hover !py-3 text-center">
                <div className="text-2xl font-bold text-brand">{platformStats.total_sites}</div>
                <div className="text-ink-faint text-[11px] uppercase tracking-wide">Sites</div>
              </div>
            </div>
            <div className="text-[11px] text-ink-faint uppercase tracking-wide mb-1.5">Users by Role</div>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(platformStats.users_by_role).filter(([, count]) => count > 0).map(([role, count]) => (
                <span key={role} className="badge">{role}: {count}</span>
              ))}
            </div>
          </>
        )}
      </div>
      <div className="card mb-4">
        <h3 className="mb-1">Platform Administration</h3>
        <p className="text-ink-muted text-sm mb-3">System monitoring, data source management, and warehouse control.</p>
        <div className="flex items-center justify-between mb-1">
          <span className="text-[11px] text-ink-faint uppercase tracking-wide">Data Sources</span>
        <span className="text-[11px] text-ink-faint">Live-checked every 30s</span>
      </div>
      <div className="flex flex-col gap-1 mb-3">
        {localSources.map((s) => (
          <div key={s.name} className="flex items-center justify-between py-1.5">
            <span className="text-sm">{s.name}</span>
            <div className="flex items-center gap-2">
              <span className={`badge ${sourceStatusBadgeClass(s.status)}`}>{s.status}</span>
              <button
                className="btn-ghost btn-sm !py-0.5 !px-2 text-[11px]"
                disabled={togglingSource === s.name}
                onClick={() => toggleSource(s)}
              >
                {togglingSource === s.name ? '…' : s.status === 'manually_disabled' ? 'Re-enable' : 'Pause'}
              </button>
            </div>
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
    </>
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
          { key: 'financial_irr_pct', label: 'IRR %', render: (r) => r.financial_irr_pct ?? 'Not run yet' },
        ]}
      />
    </div>
  )
}

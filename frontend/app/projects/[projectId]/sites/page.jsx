'use client'

import { useEffect, useState, Component } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import api from '../../../../lib/api'
import AppShell from '../../../../components/AppShell'
import { useAuth } from '../../../../lib/AuthContext'
import { canWriteProject, canRunAnalysis } from '../../../../lib/roles'
import { useToast } from '../../../../lib/ToastContext'
import { getErrorMessage } from '../../../../lib/errorMessage'

const emptyForm = {
  name: '',
  latitude: '',
  longitude: '',
  land_area_hectares: '',
  elevation_m: '',
  land_slope_pct: '',
  distance_to_substation_km: '',
  existing_infrastructure: '',
  land_ownership: '',
}

const catClass = {
  Excellent: 'cat-excellent',
  'Highly Suitable': 'cat-highly-suitable',
  'Moderately Suitable': 'cat-moderately-suitable',
  'Low Suitability': 'cat-low-suitability',
  Unsuitable: 'cat-unsuitable',
}

const DEPLOYMENT_STATUSES = ['Prospecting', 'Under Review', 'Approved', 'Deployment Planned', 'Deployed', 'Operational', 'Cancelled']

// Matches scoring.py's real 35/25/15/15/10 weighting exactly.
const SCORE_COMPONENTS = [
  { key: 'resource_score', label: 'Resource', weight: 35, color: '#e8a33d' },
  { key: 'geographic_score', label: 'Geographic', weight: 25, color: '#8e6fce' },
  { key: 'infrastructure_score', label: 'Infrastructure', weight: 15, color: '#9aa0a6' },
  { key: 'environmental_score', label: 'Environmental', weight: 15, color: '#3fae7c' },
  { key: 'economic_score', label: 'Economic', weight: 10, color: '#5b9bd5' },
]

function average(values) {
  const nums = values.filter((v) => v !== null && v !== undefined)
  if (nums.length === 0) return null
  return Math.round((nums.reduce((a, b) => a + b, 0) / nums.length) * 100) / 100
}
function sum(values) {
  const nums = values.filter((v) => v !== null && v !== undefined)
  if (nums.length === 0) return null
  return Math.round(nums.reduce((a, b) => a + b, 0) * 100) / 100
}

export default function Sites() {
  const { projectId } = useParams()
  const { user } = useAuth()
  const { showToast } = useToast()
  const [project, setProject] = useState(null)
  const [sites, setSites] = useState([])
  const [comparison, setComparison] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [downloading, setDownloading] = useState('')
  const [loading, setLoading] = useState(true)
  const [selectedSiteId, setSelectedSiteId] = useState(null)

  const loadSites = () => {
    Promise.all([
      api.get(`/projects/${projectId}`),
      api.get(`/projects/${projectId}/sites/`),
      api.get(`/projects/${projectId}/sites/compare`),
    ])
      .then(([projectRes, sitesRes, compareRes]) => {
        setProject(projectRes.data)
        setSites(sitesRes.data)
        setComparison(compareRes.data)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    if (projectId) loadSites()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const downloadReport = async (format) => {
    setDownloading(format)
    try {
      const res = await api.get(`/projects/${projectId}/reports/${format}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `project-${projectId}-site-assessment.${format === 'excel' ? 'xlsx' : 'pdf'}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      showToast('Could not generate report. Try again in a moment.', 'error')
    } finally {
      setDownloading('')
    }
  }

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    setStatus('Registering site and fetching environmental, terrain & infrastructure data…')
    try {
      const payload = {
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        land_area_hectares: form.land_area_hectares ? parseFloat(form.land_area_hectares) : null,
        elevation_m: form.elevation_m ? parseFloat(form.elevation_m) : null,
        land_slope_pct: form.land_slope_pct ? parseFloat(form.land_slope_pct) : null,
        distance_to_substation_km: form.distance_to_substation_km
          ? parseFloat(form.distance_to_substation_km)
          : null,
      }
      // Explicit, longer timeout: this single request runs the entire
      // data pipeline server-side (elevation/slope, weather,
      // infrastructure, satellite, environmental, supplemental
      // weather) — a real bug found via live testing: several of
      // these stages' own individual timeouts, summed in a genuine
      // worst case, can exceed the shared 60s default, causing the
      // frontend to give up and show nothing useful while the backend
      // keeps running to completion regardless (canceling a request
      // client-side doesn't stop server-side execution).
      const res = await api.post(`/projects/${projectId}/sites/`, payload, { timeout: 180000 })
      setForm(emptyForm)
      setStatus(`Site registered: ${res.data.name}. Data pipeline complete.`)
      loadSites()
      showToast(`Site "${res.data.name}" registered successfully.`, 'success')
    } catch (err) {
      const msg = getErrorMessage(err, 'Could not register site')
      setError(msg)
      setStatus('')
      showToast(msg, 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const userCanWrite = canWriteProject(user, project)
  const userCanAnalyze = canRunAnalysis(user, project)

  return (
    <AppShell
      title="Site Management"
      subtitle={<Link href="/projects" className="text-brand">← Back to projects</Link>}
      actions={<Link href="/gis"><button type="button" className="btn-secondary">View on GIS Map</button></Link>}
    >
      {user?.role === 'GIS Analyst' && (
        <div className="card mb-4 !py-3 !px-4 text-[13px] text-ink-muted">
          As a GIS Analyst you can refresh a site's environmental/terrain/infrastructure
          data and view every comparison and report here — site creation belongs to
          Planners, Project Managers, and Admins.
        </div>
      )}

      {userCanWrite && (
        <div className="card mb-4">
          <h3 className="mb-3">Register a new site</h3>
          {error && <div className="error-banner">{error}</div>}
          {status && <div className="success-banner">{status}</div>}
          <form onSubmit={handleCreate}>
            <div className="grid sm:grid-cols-2 gap-3.5">
              <div>
                <label className="label">Site Name</label>
                <input className="input" value={form.name} onChange={update('name')} required />
              </div>
              <div>
                <label className="label">Existing Infrastructure</label>
                <input className="input" value={form.existing_infrastructure} onChange={update('existing_infrastructure')} />
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-3.5">
              <div>
                <label className="label">Latitude</label>
                <input className="input" type="number" step="any" value={form.latitude} onChange={update('latitude')} required placeholder="-90 to 90" />
              </div>
              <div>
                <label className="label">Longitude</label>
                <input className="input" type="number" step="any" value={form.longitude} onChange={update('longitude')} required placeholder="-180 to 180" />
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-3.5">
              <div>
                <label className="label">Land Area (hectares)</label>
                <input className="input" type="number" step="any" value={form.land_area_hectares} onChange={update('land_area_hectares')} />
              </div>
              <div>
                <label className="label">Elevation (m)</label>
                <input className="input" type="number" step="any" value={form.elevation_m} onChange={update('elevation_m')} placeholder="auto-fetched if left blank" />
              </div>
            </div>
            <div className="grid sm:grid-cols-2 gap-3.5">
              <div>
                <label className="label">Land Slope (%)</label>
                <input className="input" type="number" step="any" value={form.land_slope_pct} onChange={update('land_slope_pct')} placeholder="auto-estimated if left blank" />
              </div>
              <div>
                <label className="label">Distance to Nearest Substation (km)</label>
                <input
                  className="input"
                  type="number"
                  step="any"
                  value={form.distance_to_substation_km}
                  onChange={update('distance_to_substation_km')}
                  placeholder="auto-fetched from OSM if left blank"
                />
              </div>
            </div>
            <label className="label">Land Ownership</label>
            <input className="input" value={form.land_ownership} onChange={update('land_ownership')} placeholder="e.g. Private / State-owned / Leased" />
            <div className="mt-4">
              <button type="submit" disabled={submitting} className="btn">
                {submitting && <span className="spinner" />}
                {submitting ? 'Running data pipeline…' : 'Register Site'}
              </button>
            </div>
          </form>
        </div>
      )}

      {!userCanWrite && error && <div className="error-banner mb-4">{error}</div>}

      {loading ? (
        <div className="card mb-4"><span className="spinner" /> Loading sites…</div>
      ) : sites.length === 0 ? (
        <div className="card mb-4 text-ink-faint text-sm py-6 text-center">No sites registered yet.</div>
      ) : selectedSiteId === null ? (
        // Manage Sites — step 1: a simple, scannable list of registered
        // sites. Nothing computed or fetched here beyond what loadSites()
        // already has, so this loads instantly regardless of how many
        // sites exist or how slow any individual site's data pipeline is.
        <div className="card mb-4">
          <h3 className="mb-3">Registered Sites</h3>
          <div className="flex flex-col divide-y divide-border">
            {sites.map((s) => {
              const scoreEntry = comparison.find((c) => c.site_id === s.id)
              return (
                <button
                  type="button"
                  key={s.id}
                  onClick={() => setSelectedSiteId(s.id)}
                  className="flex items-center justify-between py-3 px-1 text-left hover:bg-surface-2 transition-colors"
                >
                  <div>
                    <div className="font-semibold text-[14px]">{s.name}</div>
                    <div className="text-ink-faint text-[12px] font-mono">
                      {s.latitude?.toFixed?.(4) ?? s.latitude}, {s.longitude?.toFixed?.(4) ?? s.longitude}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {scoreEntry?.overall_score != null ? (
                      <>
                        <span className="font-bold">{scoreEntry.overall_score}</span>
                        <span className={`badge ${catClass[scoreEntry.category] || 'cat-unscored'}`}>{scoreEntry.category}</span>
                      </>
                    ) : (
                      <span className="text-ink-faint text-[12px]">Not scored yet</span>
                    )}
                    <span className={`status-select !inline-block status-${(s.deployment_status || 'prospecting').toLowerCase().replace(/ /g, '-')}`}>{s.deployment_status || 'Prospecting'}</span>
                    <span className="text-ink-faint">→</span>
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ) : (
        // Manage Sites — step 2: full score evaluation and detail for
        // the one site actually selected, not every site at once.
        <div className="mb-4">
          <button type="button" className="text-brand text-[13px] hover:underline mb-3" onClick={() => setSelectedSiteId(null)}>
            ← Back to Registered Sites
          </button>
          {sites.filter((s) => s.id === selectedSiteId).map((s) => (
            <SiteCardErrorBoundary key={s.id}>
              <SiteCard
                site={s}
                projectId={projectId}
                userCanWrite={userCanWrite}
                userCanAnalyze={userCanAnalyze}
                onSiteChanged={loadSites}
                showToast={showToast}
              />
            </SiteCardErrorBoundary>
          ))}
        </div>
      )}

      <div className="card mb-4">
        <h3 className="mb-3">Site Ranking — Suitability Scoring Engine</h3>
        <div className="overflow-x-auto">
          <table>
            <thead>
              <tr>
                <th>Site</th>
                <th>Overall Score</th>
                <th>Category</th>
              </tr>
            </thead>
            <tbody>
              {comparison
                .slice()
                .sort((a, b) => (b.overall_score ?? -1) - (a.overall_score ?? -1))
                .map((c) => (
                  <tr key={c.site_id}>
                    <td>{c.site_name}</td>
                    <td className="font-mono text-xs">{c.overall_score ?? '—'}</td>
                    <td>
                      <span className={`badge ${catClass[c.category] || 'cat-unscored'}`}>{c.category}</span>
                    </td>
                  </tr>
                ))}
              {comparison.length === 0 && (
                <tr>
                  <td colSpan={3}><div className="text-ink-faint text-sm py-6 text-center">No scored sites yet.</div></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <h3 className="mb-1">Reports</h3>
        <p className="text-ink-muted text-sm mb-3">Export a full site-assessment report for this project.</p>
        <div className="flex gap-2.5 flex-wrap">
          <button type="button" className="btn" disabled={downloading === 'pdf'} onClick={() => downloadReport('pdf')}>
            {downloading === 'pdf' ? 'Preparing PDF…' : 'Download PDF'}
          </button>
          <button type="button" className="btn-secondary" disabled={downloading === 'excel'} onClick={() => downloadReport('excel')}>
            {downloading === 'excel' ? 'Preparing Excel…' : 'Download Excel'}
          </button>
        </div>
      </div>
    </AppShell>
  )
}


function Tile({ label, value, unit }) {
  return (
    <div className="bg-surface-2 border border-border rounded-md px-3 py-2 min-w-[92px]">
      <div className="text-[10.5px] text-ink-faint uppercase tracking-wide">{label}</div>
      <div className="text-[14px] font-bold text-ink">{value ?? '—'}<span className="text-[11px] font-normal text-ink-faint">{value != null ? unit : ''}</span></div>
    </div>
  )
}

function MiniBar({ label, weight, value, color }) {
  return (
    <div className="bg-surface-2 border border-border rounded-md px-3 py-2 min-w-[100px] flex-1">
      <div className="text-[10.5px] text-ink-faint uppercase tracking-wide">{label} <span className="normal-case">({weight}%)</span></div>
      <div className="text-[15px] font-bold mb-1">{value ?? '—'}</div>
      <div className="score-bar-track !h-1.5">
        <div className="score-bar-fill" style={{ width: `${Math.min(Math.max(value ?? 0, 0), 100)}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

// React error boundaries must be class components — there's no hooks
// equivalent of componentDidCatch. Wraps each site's card individually
// so a rendering crash in ONE card (e.g. an unexpected API response
// shape) shows a clear, localized message instead of a confusing
// blank flash, and doesn't take down the rest of the page or the
// other cards.
class SiteCardErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }
  componentDidCatch(error, info) {
    console.error('SiteCard crashed:', error, info)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="card border-red-200 bg-red-50">
          <h3 className="mb-1 text-red-700">Something went wrong showing this site</h3>
          <p className="text-red-600 text-sm mb-3">{String(this.state.error?.message || this.state.error)}</p>
          <button type="button" className="btn-secondary btn-sm" onClick={() => this.setState({ hasError: false, error: null })}>
            Try Again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

function SiteCard({ site, projectId, userCanWrite, userCanAnalyze, onSiteChanged, showToast }) {
  const base = `/projects/${projectId}/sites/${site.id}`

  const [intel, setIntel] = useState(null)
  const [weather, setWeather] = useState([])
  const [intelLoading, setIntelLoading] = useState(true)
  const [suitability, setSuitability] = useState(null)
  const [deepDiveOpen, setDeepDiveOpen] = useState(false)

  const [refreshing, setRefreshing] = useState(false)
  const [statusUpdating, setStatusUpdating] = useState(false)

  const [historyOpen, setHistoryOpen] = useState(false)
  const [history, setHistory] = useState(null)
  const [historyLoading, setHistoryLoading] = useState(false)

  const [ingestionOpen, setIngestionOpen] = useState(false)
  const [ingestionLog, setIngestionLog] = useState(null)
  const [ingestionLoading, setIngestionLoading] = useState(false)

  const [seasonalForecast, setSeasonalForecast] = useState(null)
  const [seasonalLoading, setSeasonalLoading] = useState(false)

  const loadAll = () => {
    setIntelLoading(true)
    return Promise.all([
      api.get(`${base}/satellite`).catch(() => null),
      api.get(`${base}/environmental-constraints`).catch(() => null),
      api.get(`${base}/solar-potential`).catch(() => null),
      api.get(`${base}/wind-potential`).catch(() => null),
      api.get(`${base}/financial-analysis`).catch(() => null),
      api.get(`${base}/telemetry?limit=10`).catch(() => null),
      api.get(`${base}/supplemental-weather`).catch(() => null),
      api.get(`${base}/technology-recommendation`).catch(() => null),
      api.get(`${base}/grid-contribution`).catch(() => null),
      api.get(`${base}/ml-risk-assessment`).catch(() => null),
      api.get(`${base}/suitability`).catch(() => null),
      api.get(`${base}/weather`).catch(() => null),
    ]).then(([satellite, environmental, solar, wind, financial, telemetry, supplementalWeather, techRec, gridContribution, riskAssessment, suit, weatherRes]) => {
      setIntel({
        satellite: satellite?.data || null,
        environmental: environmental?.data || null,
        solar: solar?.data || null,
        wind: wind?.data || null,
        financial: financial?.data?.[0] || null,
        telemetry: telemetry?.data || [],
        supplementalWeather: supplementalWeather?.data || [],
        techRec: techRec?.data || null,
        gridContribution: gridContribution?.data || null,
        riskAssessment: riskAssessment?.data || null,
      })
      setSuitability(suit?.data || null)
      setWeather(weatherRes?.data || [])
      setIntelLoading(false)
    })
  }

  // Everything loads automatically once the card mounts — the compact
  // "reference style" tiles below need no clicks at all, and the
  // detailed engineering view is one toggle away, not several.
  useEffect(() => {
    loadAll()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [site.id])

  const refresh = async () => {
    setRefreshing(true)
    try {
      // Same longer timeout as site registration — this runs the
      // identical heavy multi-stage pipeline.
      await api.post(`${base}/refresh-data`, {}, { timeout: 180000 })
      onSiteChanged()
      showToast('Site data refreshed.', 'success')
      await loadAll()
      if (historyOpen) loadHistory(true)
    } catch (err) {
      showToast(getErrorMessage(err, 'Could not refresh site data'), 'error')
    } finally {
      setRefreshing(false)
    }
  }

  const updateStatus = async (newStatus) => {
    setStatusUpdating(true)
    try {
      await api.patch(`${base}/deployment-status`, { new_status: newStatus })
      onSiteChanged()
      showToast(`Status changed to "${newStatus}".`, 'success')
      if (historyOpen) loadHistory(true)
    } catch (err) {
      showToast(getErrorMessage(err, 'Could not update deployment status'), 'error')
    } finally {
      setStatusUpdating(false)
    }
  }

  const loadHistory = async (forceReload = false) => {
    if (historyOpen && !forceReload) {
      setHistoryOpen(false)
      return
    }
    setHistoryOpen(true)
    setHistoryLoading(true)
    try {
      const res = await api.get(`${base}/deployment-history`)
      setHistory(res.data)
    } catch (err) {
      showToast('Could not load deployment history', 'error')
    } finally {
      setHistoryLoading(false)
    }
  }

  const loadIngestionLog = async () => {
    if (ingestionOpen) {
      setIngestionOpen(false)
      return
    }
    setIngestionOpen(true)
    setIngestionLoading(true)
    try {
      const res = await api.get(`${base}/ingestion-log`)
      setIngestionLog(res.data)
    } catch (err) {
      showToast('Could not load the ingestion log for that site.', 'error')
    } finally {
      setIngestionLoading(false)
    }
  }

  const loadSeasonalForecast = async () => {
    setSeasonalLoading(true)
    try {
      const res = await api.get(`${base}/seasonal-forecast`)
      setSeasonalForecast(res.data)
    } catch (err) {
      showToast(getErrorMessage(err, 'Could not compute seasonal forecast — run "Refresh data" first so solar potential exists.'), 'error')
    } finally {
      setSeasonalLoading(false)
    }
  }


  // --- Derived values for the compact "reference style" summary ---
  const avgIrradiance = average(weather.map((w) => w.solar_irradiance))
  const avgTemp = average(weather.map((w) => w.temperature))
  const totalRainfall = sum(weather.map((w) => w.rainfall))
  const avgCloud = average(weather.map((w) => w.cloud_cover_pct))
  // Real fallback: NASA POWER's CLOUD_AMT parameter sometimes has no
  // data for a given date range/location (a genuine gap in the source,
  // not a bug — confirmed via the same -999 sentinel-rejection logic
  // that fixed the earlier data-corruption bug). OpenWeather's live
  // snapshot is a real, already-fetched alternative rather than
  // leaving this blank when a perfectly good number is available.
  const openWeatherCloud = intel?.supplementalWeather?.find((w) => w.source === 'OPENWEATHER' && w.cloud_cover_pct != null)?.cloud_cover_pct
  const cloudCoverValue = avgCloud ?? openWeatherCloud
  const cloudCoverIsFallback = avgCloud == null && openWeatherCloud != null
  const dataDays = weather.length
  const bestCapacityFactor = Math.max(intel?.solar?.capacity_factor_pct ?? -1, intel?.wind?.capacity_factor_pct ?? -1)
  const leadTechnology = (intel?.wind?.capacity_factor_pct ?? -1) > (intel?.solar?.capacity_factor_pct ?? -1) ? 'wind' : 'solar'
  const estYield = leadTechnology === 'wind'
    ? (intel?.wind?.expected_aep_mwh_yr != null ? Math.round((intel.wind.expected_aep_mwh_yr * 1000 / 365) * 100) / 100 : null)
    : (intel?.solar?.expected_energy_output_mwh_yr != null ? Math.round((intel.solar.expected_energy_output_mwh_yr * 1000 / 365) * 100) / 100 : null)

  return (
    <div className="card">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3 mb-1">
        <div>
          <h3 className="mb-0.5">{site.name}</h3>
          <div className="text-ink-faint text-[12px] font-mono">
            {leadTechnology} · {site.latitude?.toFixed?.(4) ?? site.latitude}, {site.longitude?.toFixed?.(4) ?? site.longitude} · {site.elevation_m ?? '—'}m
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap justify-end">
          <select
            className={`status-select status-${(site.deployment_status || 'prospecting').toLowerCase().replace(/ /g, '-')}`}
            value={site.deployment_status || 'Prospecting'}
            disabled={!userCanWrite || statusUpdating}
            onChange={(e) => updateStatus(e.target.value)}
          >
            {DEPLOYMENT_STATUSES.map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>
          {userCanAnalyze && (
            <button type="button" className="btn-secondary btn-sm" disabled={refreshing} onClick={refresh}>
              {refreshing ? 'Refreshing…' : 'Refresh'}
            </button>
          )}
        </div>
      </div>

      {intelLoading ? (
        <div className="border-t border-border pt-3 mt-2">
          <span className="text-ink-faint text-sm"><span className="spinner" />Loading site intelligence…</span>
        </div>
      ) : (
        <>
          {/* Compact summary — always visible, no clicks required */}
          <div className="border-t border-border pt-3 mt-2">
            <div className="text-[11px] text-ink-faint uppercase tracking-wide mb-1.5">Environmental Data</div>
            <div className="flex gap-2 flex-wrap mb-3">
              <Tile label="Solar Irradiance" value={avgIrradiance} unit=" kWh/m²" />
              <Tile label="Peak Sun Hours" value={intel?.solar?.peak_sun_hours} unit=" hrs/day" />
              <Tile label="Avg Temperature" value={avgTemp} unit="°C" />
              <Tile label="Total Rainfall" value={totalRainfall} unit=" mm" />
              <Tile label="Cloud Cover" value={cloudCoverValue} unit={cloudCoverIsFallback ? '% (live)' : '%'} />
              <Tile label="Elevation" value={site.elevation_m} unit=" m" />
              <Tile label="Data Days" value={dataDays || null} unit=" days" />
            </div>

            <div className="text-[11px] text-ink-faint uppercase tracking-wide mb-1.5">ML Predictions</div>
            {suitability ? (
              <div className="bg-[#f0faf4] border border-[#bfe8cf] rounded-md px-3.5 py-2.5 mb-2.5">
                <div className="flex items-center gap-3 mb-1.5">
                  <span className="text-2xl font-bold text-[#1e6f4c]">{suitability.overall_score}<span className="text-[13px] font-normal text-ink-faint">/100</span></span>
                  <span className={`badge ${catClass[suitability.category] || 'cat-unscored'}`}>{suitability.category}</span>
                </div>
                <div className="score-bar-track !h-2">
                  <div className="score-bar-fill" style={{ width: `${Math.min(Math.max(suitability.overall_score, 0), 100)}%`, backgroundColor: '#1e6f4c' }} />
                </div>
              </div>
            ) : (
              <p className="text-ink-faint text-sm mb-2.5">No suitability score yet — click "Refresh" above.</p>
            )}

            <div className="flex gap-2 flex-wrap mb-2">
              <MiniBar label={leadTechnology === 'wind' ? 'Wind Score' : 'Solar Score'} weight="" value={leadTechnology === 'wind' ? intel?.wind?.capacity_factor_pct : intel?.solar?.capacity_factor_pct} color="#e8a33d" />
              <MiniBar label="Land Cover" weight="" value={intel?.satellite?.ndvi_mean != null ? Math.round(intel.satellite.ndvi_mean * 100) : null} color="#3fae7c" />
            </div>
            <div className="text-[12px] text-ink-muted mb-3 space-y-0.5">
              <div>⚡ Capacity Factor: <b>{bestCapacityFactor >= 0 ? `${bestCapacityFactor}%` : '—'}</b> · Est. Yield: <b>{estYield ?? '—'} MWh/day</b> per MW</div>
              <div>🌱 Land Cover: <b>{intel?.satellite?.land_cover_summary ?? '—'}</b> · NDVI: <b>{intel?.satellite?.ndvi_mean ?? '—'}</b> · Slope: <b>{site.land_slope_pct ?? '—'}°</b></div>
              {intel?.satellite?.ml_land_cover_class && (
                <div>🛰️ ML Land Cover (CNN): <b>{intel.satellite.ml_land_cover_class}</b> <span className="text-ink-faint">({intel.satellite.ml_confidence_pct}% confidence, model {intel.satellite.ml_model_version})</span></div>
              )}
            </div>

            {suitability && (
              <>
                <div className="text-[11px] text-ink-faint uppercase tracking-wide mb-1.5">Score Breakdown</div>
                <div className="flex gap-2 flex-wrap">
                  {SCORE_COMPONENTS.map((c) => (
                    <MiniBar key={c.key} label={c.label} weight={c.weight} value={suitability[c.key]} color={c.color} />
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Deep dive toggle */}
          <div className="border-t border-border pt-3 mt-3">
            <button type="button"
              className="btn-secondary btn-sm w-full sm:w-auto"
              onClick={() => setDeepDiveOpen((v) => !v)}
            >
              {deepDiveOpen ? '▴ Hide detailed engineering view' : '▾ Understand Deeply — full physics, ML & financial breakdown'}
            </button>
          </div>

          {deepDiveOpen && (
            <div className="animate-panel-in border-t border-border pt-3 mt-3">
              <div className="grid sm:grid-cols-2 gap-5 text-[12.5px]">
                {/* Environmental snapshot */}
                <div>
                  <div className="text-ink-muted font-semibold mb-1">Satellite Imagery (AWS Sentinel-2, no API key needed)</div>
                  {intel?.satellite ? (
                    <ul className="space-y-0.5">
                      <li>Provider: <b>{intel.satellite.provider}</b> ({intel.satellite.source_status})</li>
                      <li>Cloud cover: <b>{intel.satellite.cloud_cover_pct ?? '—'}%</b></li>
                      <li>NDVI mean: <b>{intel.satellite.ndvi_mean ?? '—'}</b></li>
                      <li>Land cover (NDVI rule): <b>{intel.satellite.land_cover_summary ?? '—'}</b></li>
                      {intel.satellite.ml_land_cover_class && (
                        <li>Land cover (ML CNN): <b>{intel.satellite.ml_land_cover_class}</b> <span className="text-ink-faint">({intel.satellite.ml_confidence_pct}% confidence)</span></li>
                      )}
                    </ul>
                  ) : <p className="text-ink-faint">—</p>}

                  <div className="text-ink-muted font-semibold mb-1 mt-3">Environmental / Demographic (World Bank + OSM)</div>
                  <ul className="space-y-0.5">
                    <li>Protected area: <b>{intel?.environmental?.protected_area_distance_km ?? '—'} km</b></li>
                    <li>Water body: <b>{intel?.environmental?.water_body_distance_km ?? '—'} km</b></li>
                    <li>Country: <b>{intel?.environmental?.country_iso3 ?? '—'}</b></li>
                    <li>Pop. density: <b>{intel?.environmental?.population_density_km2 ?? '—'} /km²</b></li>
                    <li>GDP per capita: <b>${intel?.environmental?.gdp_per_capita_usd ?? '—'}</b></li>
                  </ul>
                  {intel?.environmental?.data_source === 'unavailable_fetch_failed' && (
                    <p className="text-red-600 text-[11px] mt-1">Both Overpass servers were unreachable on the last refresh attempt — this isn't stale data, the fetch genuinely failed.</p>
                  )}
                  {intel?.environmental?.data_source === 'manually_disabled' && (
                    <p className="text-amber-600 text-[11px] mt-1">This connector is manually paused by an Administrator (Admin Dashboard → Data Sources).</p>
                  )}

                  {intel?.supplementalWeather?.length > 0 && (
                    <>
                      <div className="text-ink-muted font-semibold mb-1 mt-3">Live Weather Cross-Check (OpenWeather / NOAA)</div>
                      <ul className="space-y-0.5">
                        {intel.supplementalWeather.map((w) => (
                          <li key={w.id}>
                            <span className="badge badge-gray mr-1.5">{w.source}</span>
                            {w.temperature_c != null ? `${w.temperature_c}°C` : ''}
                            {w.wind_speed_ms != null ? `, ${w.wind_speed_ms} m/s` : ''}
                            {w.condition_text ? ` — ${w.condition_text}` : ''}
                            {w.forecast_period ? ` (${w.forecast_period})` : ''}
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>

                {/* Solar & Wind potential, physics + ML */}
                <div>
                  <div className="text-ink-muted font-semibold mb-1">Solar Potential Engine</div>
                  {intel?.solar ? (
                    <ul className="space-y-0.5">
                      <li>Expected output: <b>{intel.solar.expected_energy_output_mwh_yr ?? '—'} MWh/yr per MW</b></li>
                      <li>Capacity factor: <b>{intel.solar.capacity_factor_pct ?? '—'}%</b></li>
                      <li>Panel efficiency: <b>{intel.solar.panel_efficiency_pct ?? '—'}%</b></li>
                      <li>Shading loss: <b>{intel.solar.shading_loss_pct ?? '—'}%</b></li>
                      <li>Peak sun hours: <b>{intel.solar.peak_sun_hours ?? '—'}</b></li>
                    </ul>
                  ) : <p className="text-ink-faint">Not computed yet.</p>}
                  {intel?.solar?.ml_model_version ? (
                    <div className="mt-1.5 pl-2 border-l-2 border-brand/40">
                      <div className="text-[11px] text-ink-faint uppercase tracking-wide mb-0.5">
                        ML-Assisted — model {intel.solar.ml_model_version}
                      </div>
                      <ul className="space-y-0.5">
                        <li>ML performance ratio: <b>{intel.solar.ml_performance_ratio_pct}%</b> <span className="text-ink-faint">(physics: {intel.solar.performance_ratio_pct}%)</span></li>
                        <li>ML expected output: <b>{intel.solar.ml_expected_energy_output_mwh_yr} MWh/yr per MW</b></li>
                      </ul>
                    </div>
                  ) : intel?.solar ? (
                    <p className="text-[11px] text-ink-faint mt-1">ML-assisted prediction unavailable — showing physics-only estimate above.</p>
                  ) : null}

                  <div className="text-ink-muted font-semibold mb-1 mt-3">Wind Potential Engine</div>
                  {intel?.wind ? (
                    <ul className="space-y-0.5">
                      <li>Expected AEP: <b>{intel.wind.expected_aep_mwh_yr ?? '—'} MWh/yr per MW</b></li>
                      <li>Capacity factor: <b>{intel.wind.capacity_factor_pct ?? '—'}%</b></li>
                      <li>Turbine class: <b>{intel.wind.turbine_class ?? '—'}</b></li>
                      <li>Turbulence: <b>{intel.wind.turbulence_intensity_pct ?? '—'}%</b></li>
                    </ul>
                  ) : <p className="text-ink-faint">Not computed yet.</p>}
                  {intel?.wind?.ml_model_version ? (
                    <div className="mt-1.5 pl-2 border-l-2 border-brand/40">
                      <div className="text-[11px] text-ink-faint uppercase tracking-wide mb-0.5">
                        ML-Assisted — model {intel.wind.ml_model_version}
                      </div>
                      <ul className="space-y-0.5">
                        <li>ML capacity factor: <b>{intel.wind.ml_capacity_factor_pct}%</b> <span className="text-ink-faint">(physics: {intel.wind.capacity_factor_pct}%)</span></li>
                        <li>ML expected AEP: <b>{intel.wind.ml_expected_aep_mwh_yr} MWh/yr per MW</b></li>
                      </ul>
                    </div>
                  ) : intel?.wind ? (
                    <p className="text-[11px] text-ink-faint mt-1">ML-assisted prediction unavailable — showing physics-only estimate above.</p>
                  ) : null}
                </div>
              </div>

              {/* Deployment Optimization & Risk */}
              {(intel?.techRec || intel?.gridContribution || intel?.riskAssessment) && (
                <div className="border-t border-border pt-3 mt-3 text-[12.5px]">
                  <div className="text-ink-muted font-semibold mb-2">Deployment Optimization & Risk</div>
                  {intel?.techRec && (
                    <div className="mb-2">
                      <span className="badge mr-1.5">{intel.techRec.recommendation}</span>
                      <span className="text-ink-faint">{intel.techRec.reasoning}</span>
                      {intel.techRec.suggested_capacity_mw && Object.keys(intel.techRec.suggested_capacity_mw).length > 0 && (
                        <div className="mt-1">
                          Suggested capacity: {Object.entries(intel.techRec.suggested_capacity_mw).map(([k, v]) => `${k.replace('_mw', '')}: ${v} MW`).join(', ')}
                        </div>
                      )}
                    </div>
                  )}
                  {intel?.gridContribution?.homes_powered_equivalent && (
                    <div className="mb-2">
                      Grid contribution: <b>~{intel.gridContribution.homes_powered_equivalent.toLocaleString()} homes powered (equivalent)</b>
                      <p className="text-ink-faint text-[11px]">{intel.gridContribution.basis}</p>
                    </div>
                  )}
                  {intel?.riskAssessment && (
                    <div className="mb-2">
                      Risk category: <span className={`badge ${intel.riskAssessment.risk_category === 'High' ? 'badge-red' : intel.riskAssessment.risk_category === 'Medium' ? 'badge-amber' : ''}`}>{intel.riskAssessment.risk_category}</span> <span className="text-ink-faint">({intel.riskAssessment.confidence_pct}% confidence, model {intel.riskAssessment.model_version})</span>
                      <p className="text-ink-faint text-[11px] mt-0.5">{intel.riskAssessment.note}</p>
                    </div>
                  )}
                  <button type="button" className="btn-sm btn-secondary" disabled={seasonalLoading} onClick={loadSeasonalForecast}>
                    {seasonalLoading ? 'Loading…' : 'Load Seasonal Forecast'}
                  </button>
                  {seasonalForecast && (
                    <div className="mt-2 flex items-end gap-1 h-14">
                      {Object.entries(seasonalForecast.monthly_output_mwh_per_mw).map(([month, value]) => {
                        const max = Math.max(...Object.values(seasonalForecast.monthly_output_mwh_per_mw))
                        return (
                          <div key={month} className="flex flex-col items-center">
                            <div title={`${month}: ${value} MWh`} className="bg-brand/70 w-4 rounded-t" style={{ height: `${Math.max((value / max) * 40, 2)}px` }} />
                            <span className="text-[9px] text-ink-faint">{month.slice(0, 1)}</span>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}


              {/* Investment Analytics now lives on its own dedicated
                  page (Financial Analysis, in the sidebar) — kept out
                  of this detailed view to avoid two separate, redundant
                  places to run the same calculation. */}
              <div className="border-t border-border pt-3 mt-3">
                <div className="text-ink-muted font-semibold mb-2">Investment Analytics</div>
                {intel?.financial ? (
                  <div className="flex flex-wrap gap-x-5 gap-y-1 mb-2 text-[12.5px]">
                    <span>NPV: <b>${intel.financial.npv_usd?.toLocaleString?.() ?? intel.financial.npv_usd}</b></span>
                    <span>IRR: <b>{intel.financial.irr_pct ?? '—'}%</b></span>
                    <span>LCOE: <b>${intel.financial.lcoe_usd_per_mwh ?? '—'}/MWh</b></span>
                    <span>Payback: <b>{intel.financial.payback_years ?? '—'} yrs</b></span>
                  </div>
                ) : (
                  <p className="text-ink-faint text-[12px] mb-2">No financial model run yet for this site.</p>
                )}
                <Link href="/financial-analysis" className="text-brand text-[12px] hover:underline">
                  Run or view the full financial model on the Financial Analysis page →
                </Link>
              </div>

              {/* Secondary / audit detail */}
              <div className="flex gap-4 flex-wrap border-t border-border pt-2.5 mt-3">
                <button type="button" className="text-brand text-[12px] hover:underline" onClick={() => loadHistory()}>
                  {historyOpen ? 'Hide deployment history' : 'Deployment history'}
                </button>
                <button type="button" className="text-brand text-[12px] hover:underline" onClick={loadIngestionLog}>
                  {ingestionOpen ? 'Hide ingestion log' : 'Data ingestion log'}
                </button>
              </div>

              {historyOpen && (
                <div className="animate-panel-in bg-surface-2 border border-border rounded-md px-4 py-3.5 mt-2 text-[12.5px]">
                  <div className="text-ink-muted font-semibold mb-2">Deployment History — {site.name}</div>
                  {historyLoading ? (
                    <span className="text-ink-faint"><span className="spinner" />Loading history…</span>
                  ) : history && history.length > 0 ? (
                    <ol className="relative border-l-2 border-border ml-1.5 pl-4 space-y-3">
                      {history.map((h) => (
                        <li key={h.id} className="relative">
                          <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-brand border-2 border-white" />
                          <div className="flex items-baseline gap-2 flex-wrap">
                            <b>{h.previous_status ? `${h.previous_status} → ${h.new_status}` : `Created as ${h.new_status}`}</b>
                            <span className="text-ink-faint text-[11px]">{new Date(h.changed_at).toLocaleString()}</span>
                          </div>
                          {h.note && <div className="text-ink-muted mt-0.5">{h.note}</div>}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="text-ink-faint">No history yet.</p>
                  )}
                </div>
              )}

              {ingestionOpen && (
                <div className="animate-panel-in bg-surface-2 border border-border rounded-md px-4 py-3.5 mt-2">
                  {ingestionLoading ? (
                    <span className="text-ink-faint text-xs"><span className="spinner" />Loading ingestion log…</span>
                  ) : ingestionLog ? (
                    <div className="text-[12.5px]">
                      <div className="flex flex-wrap gap-x-6 gap-y-1.5 mb-2.5">
                        <span><b>{ingestionLog.weather_readings_count}</b> weather readings stored (PostgreSQL)</span>
                        <span><b>{ingestionLog.infrastructure_features_count}</b> nearby infrastructure features found via OpenStreetMap (roads, substations, transmission lines — separate from the "Existing Infrastructure" text you entered when registering this site, shown below)</span>
                        <span>PostGIS geometry: <b>{ingestionLog.has_postgis_geometry ? 'set' : 'not set (SQLite dev mode?)'}</b></span>
                        <span>Data lake archival: <b>{ingestionLog.data_lake_archival_enabled ? 'enabled (S3)' : 'not configured'}</b></span>
                        {ingestionLog.latest_weather_reading_date && (
                          <span>Latest reading: <b>{new Date(ingestionLog.latest_weather_reading_date).toLocaleDateString()}</b></span>
                        )}
                      </div>
                      {site.existing_infrastructure && (
                        <div className="text-ink-muted mb-2.5 pl-2 border-l-2 border-brand/40">
                          Your own "Existing Infrastructure" entry (not counted above, informational only): <i>{site.existing_infrastructure}</i>
                        </div>
                      )}
                      <div className="text-ink-muted font-semibold mb-1">Raw payload writes (MongoDB)</div>
                      {ingestionLog.raw_payload_events.length > 0 ? (
                        <ul className="space-y-1">
                          {ingestionLog.raw_payload_events.map((ev, i) => (
                            <li key={i} className="text-ink-muted">
                              <span className="badge badge-gray mr-1.5">{ev.source}</span>
                              {new Date(ev.fetched_at).toLocaleString()}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-ink-faint">No raw payloads recorded yet — click "Refresh data" to fetch from NASA POWER / OpenStreetMap.</p>
                      )}
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}

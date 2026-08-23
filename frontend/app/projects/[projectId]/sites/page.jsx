'use client'

import { useEffect, useState, Fragment } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import api from '../../../../lib/api'
import AppShell from '../../../../components/AppShell'
import { useAuth } from '../../../../lib/AuthContext'
import { canWriteProject, canRunAnalysis } from '../../../../lib/roles'

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

export default function Sites() {
  const { projectId } = useParams()
  const { user } = useAuth()
  const [project, setProject] = useState(null)
  const [sites, setSites] = useState([])
  const [comparison, setComparison] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [refreshingId, setRefreshingId] = useState(null)
  const [downloading, setDownloading] = useState('')
  const [loading, setLoading] = useState(true)
  const [ingestionSiteId, setIngestionSiteId] = useState(null)
  const [ingestionLog, setIngestionLog] = useState(null)
  const [ingestionLoading, setIngestionLoading] = useState(false)

  const [intelSiteId, setIntelSiteId] = useState(null)
  const [intel, setIntel] = useState(null)
  const [intelLoading, setIntelLoading] = useState(false)
  const [finForm, setFinForm] = useState({
    technology: 'solar', capacity_mw: '10', capex_usd: '8000000', opex_usd_per_yr: '100000',
    discount_rate_pct: '8', project_lifetime_yrs: '25', electricity_price_usd_per_mwh: '45',
  })
  const [finSubmitting, setFinSubmitting] = useState(false)
  const [simResult, setSimResult] = useState(null)
  const [simLoading, setSimLoading] = useState(false)

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
      setError('Could not generate report. Try again in a moment.')
    } finally {
      setDownloading('')
    }
  }

  const refreshSite = async (siteId) => {
    setRefreshingId(siteId)
    try {
      await api.post(`/projects/${projectId}/sites/${siteId}/refresh-data`)
      loadSites()
      if (ingestionSiteId === siteId) loadIngestionLog(siteId)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not refresh site data')
    } finally {
      setRefreshingId(null)
    }
  }

  const loadIngestionLog = async (siteId) => {
    if (ingestionSiteId === siteId) {
      setIngestionSiteId(null)
      setIngestionLog(null)
      return
    }
    setIngestionSiteId(siteId)
    setIngestionLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}/sites/${siteId}/ingestion-log`)
      setIngestionLog(res.data)
    } catch (err) {
      setError('Could not load the ingestion log for that site.')
    } finally {
      setIngestionLoading(false)
    }
  }

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const loadIntelligence = async (siteId) => {
    if (intelSiteId === siteId) {
      setIntelSiteId(null)
      setIntel(null)
      setSimResult(null)
      return
    }
    setIntelSiteId(siteId)
    setIntelLoading(true)
    setSimResult(null)
    const base = `/projects/${projectId}/sites/${siteId}`
    const [satellite, environmental, solar, wind, financial, telemetry, supplementalWeather, techRec, gridContribution, riskAssessment] = await Promise.all([
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
    ])
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
    setIntelLoading(false)
  }

  const [seasonalForecast, setSeasonalForecast] = useState(null)
  const [seasonalLoading, setSeasonalLoading] = useState(false)
  const loadSeasonalForecast = async (siteId) => {
    setSeasonalLoading(true)
    try {
      const res = await api.get(`/projects/${projectId}/sites/${siteId}/seasonal-forecast`)
      setSeasonalForecast(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not compute seasonal forecast — run "Refresh data" first so solar potential exists.')
    } finally {
      setSeasonalLoading(false)
    }
  }

  const [mlInvestment, setMlInvestment] = useState(null)
  const [mlInvestmentLoading, setMlInvestmentLoading] = useState(false)
  const runMlInvestmentEstimate = async (siteId) => {
    setMlInvestmentLoading(true)
    try {
      const res = await api.post(`/projects/${projectId}/sites/${siteId}/ml-investment-estimate`, {
        capacity_mw: parseFloat(finForm.capacity_mw) || 10,
        capex_usd: parseFloat(finForm.capex_usd) || 8000000,
        opex_usd_per_yr: parseFloat(finForm.opex_usd_per_yr) || 100000,
        discount_rate_pct: parseFloat(finForm.discount_rate_pct) || 8,
        project_lifetime_yrs: parseInt(finForm.project_lifetime_yrs, 10) || 25,
        electricity_price_usd_per_mwh: parseFloat(finForm.electricity_price_usd_per_mwh) || 45,
        annual_energy_mwh: (intel?.solar?.expected_energy_output_mwh_yr || 1740) * (parseFloat(finForm.capacity_mw) || 10),
      })
      setMlInvestment(res.data)
    } catch (err) {
      setError('Could not compute ML investment estimate.')
    } finally {
      setMlInvestmentLoading(false)
    }
  }

  const submitFinancialAnalysis = async (siteId) => {
    setFinSubmitting(true)
    setError('')
    try {
      const res = await api.post(`/projects/${projectId}/sites/${siteId}/financial-analysis`, {
        technology: finForm.technology,
        capacity_mw: parseFloat(finForm.capacity_mw),
        capex_usd: parseFloat(finForm.capex_usd),
        opex_usd_per_yr: parseFloat(finForm.opex_usd_per_yr),
        discount_rate_pct: parseFloat(finForm.discount_rate_pct),
        project_lifetime_yrs: parseInt(finForm.project_lifetime_yrs, 10),
        electricity_price_usd_per_mwh: parseFloat(finForm.electricity_price_usd_per_mwh),
      })
      setIntel((prev) => ({ ...prev, financial: res.data }))
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not compute financial analysis — run "Refresh data" on this site first so solar/wind potential exists.')
    } finally {
      setFinSubmitting(false)
    }
  }

  const runSimulation = async (siteId, technology) => {
    setSimLoading(true)
    try {
      const res = await api.post(`/projects/${projectId}/sites/${siteId}/simulate-output`, {
        technology,
        capacity_mw: parseFloat(finForm.capacity_mw) || 10,
        hours: 24,
      })
      setSimResult(res.data)
    } catch (err) {
      setError('Could not run power simulation.')
    } finally {
      setSimLoading(false)
    }
  }

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
      const res = await api.post(`/projects/${projectId}/sites/`, payload)
      setForm(emptyForm)
      setStatus(`Site registered: ${res.data.name}. Data pipeline complete.`)
      loadSites()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not register site')
      setStatus('')
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
      actions={<Link href="/gis"><button className="btn-secondary">View on GIS Map</button></Link>}
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

      <div className="card mb-4">
        <h3 className="mb-3">Registered Sites</h3>
        <div className="overflow-x-auto">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Lat / Long</th>
                <th>Elevation (m)</th>
                <th>Substation (km)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sites.map((s) => (
                <Fragment key={s.id}>
                  <tr>
                    <td><strong>{s.name}</strong></td>
                    <td className="font-mono text-xs">{s.latitude?.toFixed?.(4) ?? s.latitude}, {s.longitude?.toFixed?.(4) ?? s.longitude}</td>
                    <td>{s.elevation_m ?? '—'}</td>
                    <td>{s.distance_to_substation_km ?? '—'}</td>
                    <td>
                      <div className="flex gap-2 justify-end flex-wrap">
                        <button className="btn-ghost btn-sm" onClick={() => loadIntelligence(s.id)}>
                          {intelSiteId === s.id ? 'Hide intelligence' : 'Solar / Wind / Financial'}
                        </button>
                        <button className="btn-ghost btn-sm" onClick={() => loadIngestionLog(s.id)}>
                          {ingestionSiteId === s.id ? 'Hide ingestion log' : 'Data ingestion log'}
                        </button>
                        {userCanAnalyze && (
                          <button
                            className="btn-ghost btn-sm"
                            disabled={refreshingId === s.id}
                            onClick={() => refreshSite(s.id)}
                          >
                            {refreshingId === s.id ? 'Refreshing…' : 'Refresh data'}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                  {intelSiteId === s.id && (
                    <tr>
                      <td colSpan={5} className="!py-0">
                        <div className="bg-surface-2 border-y border-border -mx-3 px-4 py-3.5 my-1 text-[12.5px]">
                          {intelLoading ? (
                            <span className="text-ink-faint"><span className="spinner" />Loading site intelligence…</span>
                          ) : (
                            <div className="grid sm:grid-cols-2 gap-4">
                              <div>
                                <div className="text-ink-muted font-semibold mb-1">Satellite Imagery (Copernicus Sentinel)</div>
                                {intel?.satellite ? (
                                  <ul className="space-y-0.5">
                                    <li>Provider: <b>{intel.satellite.provider}</b> ({intel.satellite.source_status})</li>
                                    <li>Cloud cover: <b>{intel.satellite.cloud_cover_pct ?? '—'}%</b></li>
                                    <li>NDVI mean: <b>{intel.satellite.ndvi_mean ?? '—'}</b></li>
                                    <li>Land cover: <b>{intel.satellite.land_cover_summary ?? '—'}</b></li>
                                  </ul>
                                ) : <p className="text-ink-faint">Not fetched yet — run &quot;Refresh data&quot;.</p>}

                                <div className="text-ink-muted font-semibold mb-1 mt-3">Environmental / Demographic (World Bank + OSM)</div>
                                {intel?.environmental ? (
                                  <ul className="space-y-0.5">
                                    <li>Protected area: <b>{intel.environmental.protected_area_distance_km ?? '—'} km</b></li>
                                    <li>Water body: <b>{intel.environmental.water_body_distance_km ?? '—'} km</b></li>
                                    <li>Country: <b>{intel.environmental.country_iso3 ?? '—'}</b></li>
                                    <li>Pop. density: <b>{intel.environmental.population_density_km2 ?? '—'} /km²</b></li>
                                    <li>GDP per capita: <b>${intel.environmental.gdp_per_capita_usd ?? '—'}</b></li>
                                  </ul>
                                ) : <p className="text-ink-faint">Not fetched yet — run &quot;Refresh data&quot;.</p>}

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

                              <div className="sm:col-span-2 border-t border-border pt-3 mt-1">
                                <div className="text-ink-muted font-semibold mb-2">Investment Analytics</div>
                                {intel?.financial && (
                                  <div className="flex flex-wrap gap-x-5 gap-y-1 mb-2.5">
                                    <span>NPV: <b>${intel.financial.npv_usd?.toLocaleString?.() ?? intel.financial.npv_usd}</b></span>
                                    <span>IRR: <b>{intel.financial.irr_pct ?? '—'}%</b></span>
                                    <span>LCOE: <b>${intel.financial.lcoe_usd_per_mwh ?? '—'}/MWh</b></span>
                                    <span>Payback: <b>{intel.financial.payback_years ?? '—'} yrs</b></span>
                                  </div>
                                )}
                                {userCanAnalyze && (
                                  <div className="flex flex-wrap gap-2 items-end">
                                    <select className="input !w-auto !py-1.5" value={finForm.technology} onChange={(e) => setFinForm({ ...finForm, technology: e.target.value })}>
                                      <option value="solar">Solar</option>
                                      <option value="wind">Wind</option>
                                      <option value="hybrid">Hybrid</option>
                                    </select>
                                    <input className="input !w-24 !py-1.5" type="number" value={finForm.capacity_mw} onChange={(e) => setFinForm({ ...finForm, capacity_mw: e.target.value })} placeholder="MW" />
                                    <input className="input !w-32 !py-1.5" type="number" value={finForm.capex_usd} onChange={(e) => setFinForm({ ...finForm, capex_usd: e.target.value })} placeholder="CapEx $" />
                                    <input className="input !w-32 !py-1.5" type="number" value={finForm.opex_usd_per_yr} onChange={(e) => setFinForm({ ...finForm, opex_usd_per_yr: e.target.value })} placeholder="OpEx $/yr" />
                                    <input className="input !w-24 !py-1.5" type="number" value={finForm.electricity_price_usd_per_mwh} onChange={(e) => setFinForm({ ...finForm, electricity_price_usd_per_mwh: e.target.value })} placeholder="$/MWh" />
                                    <button className="btn-sm btn" disabled={finSubmitting} onClick={() => submitFinancialAnalysis(s.id)}>
                                      {finSubmitting ? 'Computing…' : 'Run Financial Model'}
                                    </button>
                                    <button className="btn-sm btn-secondary" disabled={simLoading} onClick={() => runSimulation(s.id, finForm.technology === 'wind' ? 'wind' : 'solar')}>
                                      {simLoading ? 'Simulating…' : 'Simulate 24h Output'}
                                    </button>
                                    <button className="btn-sm btn-secondary" disabled={mlInvestmentLoading} onClick={() => runMlInvestmentEstimate(s.id)}>
                                      {mlInvestmentLoading ? 'Estimating…' : 'ML Instant Estimate'}
                                    </button>
                                  </div>
                                )}
                                {mlInvestment && (
                                  <div className="mt-2 pl-2 border-l-2 border-brand/40 text-[12.5px]">
                                    <span className="text-[11px] text-ink-faint uppercase tracking-wide">ML-Assisted (model {mlInvestment.model_version})</span>
                                    <div>NPV: <b>${mlInvestment.npv_usd?.toLocaleString?.()}</b> &nbsp; IRR: <b>{mlInvestment.irr_pct}%</b></div>
                                    <p className="text-ink-faint text-[11px] mt-0.5">{mlInvestment.note}</p>
                                  </div>
                                )}
                                {simResult && (
                                  <div className="mt-2.5 flex items-end gap-[2px] h-16">
                                    {simResult.series.map((h) => (
                                      <div
                                        key={h.hour}
                                        title={`Hour ${h.hour}: ${h.output_kw} kW`}
                                        className="bg-brand/70 w-2.5 rounded-t"
                                        style={{ height: `${Math.max((h.output_kw / (parseFloat(finForm.capacity_mw || 10) * 1000)) * 100, 2)}%` }}
                                      />
                                    ))}
                                  </div>
                                )}

                                {(intel?.techRec || intel?.gridContribution || intel?.riskAssessment) && (
                                  <div className="mt-3 pt-3 border-t border-border">
                                    <div className="text-ink-muted font-semibold mb-2">Deployment Optimization & Risk (Milestone 3)</div>
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
                                    <button className="btn-sm btn-secondary" disabled={seasonalLoading} onClick={() => loadSeasonalForecast(s.id)}>
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

                                {intel?.telemetry?.length > 0 && (
                                  <div className="mt-3">
                                    <div className="text-ink-muted font-semibold mb-1">Live SCADA/IoT Telemetry (most recent)</div>
                                    <ul className="space-y-0.5">
                                      {intel.telemetry.slice(0, 5).map((t) => (
                                        <li key={t.id}>
                                          <span className="badge badge-gray mr-1.5">{t.metric_name}</span>
                                          {t.value}{t.unit ? ` ${t.unit}` : ''} — {new Date(t.recorded_at).toLocaleString()}
                                        </li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                  {ingestionSiteId === s.id && (
                    <tr>
                      <td colSpan={5} className="!py-0">
                        <div className="bg-surface-2 border-y border-border -mx-3 px-4 py-3.5 my-1">
                          {ingestionLoading ? (
                            <span className="text-ink-faint text-xs"><span className="spinner" />Loading ingestion log…</span>
                          ) : ingestionLog ? (
                            <div className="text-[12.5px]">
                              <div className="flex flex-wrap gap-x-6 gap-y-1.5 mb-2.5">
                                <span><b>{ingestionLog.weather_readings_count}</b> weather readings stored (PostgreSQL)</span>
                                <span><b>{ingestionLog.infrastructure_features_count}</b> infrastructure features stored (PostgreSQL)</span>
                                <span>PostGIS geometry: <b>{ingestionLog.has_postgis_geometry ? 'set' : 'not set (SQLite dev mode?)'}</b></span>
                                <span>Data lake archival: <b>{ingestionLog.data_lake_archival_enabled ? 'enabled (S3)' : 'not configured'}</b></span>
                                {ingestionLog.latest_weather_reading_date && (
                                  <span>Latest reading: <b>{new Date(ingestionLog.latest_weather_reading_date).toLocaleDateString()}</b></span>
                                )}
                              </div>
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
                                <p className="text-ink-faint">No raw payloads recorded yet — click &quot;Refresh data&quot; to fetch from NASA POWER / OpenStreetMap.</p>
                              )}
                            </div>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {sites.length === 0 && !loading && (
                <tr>
                  <td colSpan={5}><div className="text-ink-faint text-sm py-6 text-center">No sites registered yet.</div></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card mb-4">
        <h3 className="mb-3">Site Comparison — Suitability Scoring Engine</h3>
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
          <button className="btn" disabled={downloading === 'pdf'} onClick={() => downloadReport('pdf')}>
            {downloading === 'pdf' ? 'Preparing PDF…' : 'Download PDF'}
          </button>
          <button className="btn-secondary" disabled={downloading === 'excel'} onClick={() => downloadReport('excel')}>
            {downloading === 'excel' ? 'Preparing Excel…' : 'Download Excel'}
          </button>
        </div>
      </div>
    </AppShell>
  )
}

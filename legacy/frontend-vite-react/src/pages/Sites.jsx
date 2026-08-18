import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api from '../api'
import Navbar from '../components/Navbar'

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
  const [sites, setSites] = useState([])
  const [comparison, setComparison] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [refreshingId, setRefreshingId] = useState(null)
  const [downloading, setDownloading] = useState('')
  const [loading, setLoading] = useState(true)

  const loadSites = () => {
    Promise.all([
      api.get(`/projects/${projectId}/sites/`),
      api.get(`/projects/${projectId}/sites/compare`),
    ])
      .then(([sitesRes, compareRes]) => {
        setSites(sitesRes.data)
        setComparison(compareRes.data)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadSites()
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
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not refresh site data')
    } finally {
      setRefreshingId(null)
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

  return (
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>Site Management</h2>
            <p className="page-subtitle">
              <Link to="/projects">← Back to projects</Link>
            </p>
          </div>
          <Link to="/gis"><button className="secondary">View on GIS Map</button></Link>
        </div>

        <div className="card">
          <div className="card-header"><h3>Register a new site</h3></div>
          {error && <div className="error">{error}</div>}
          {status && <div className="success-banner">{status}</div>}
          <form onSubmit={handleCreate}>
            <div className="form-row">
              <div>
                <label>Site Name</label>
                <input value={form.name} onChange={update('name')} required />
              </div>
              <div>
                <label>Existing Infrastructure</label>
                <input value={form.existing_infrastructure} onChange={update('existing_infrastructure')} />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label>Latitude</label>
                <input type="number" step="any" value={form.latitude} onChange={update('latitude')} required placeholder="-90 to 90" />
              </div>
              <div>
                <label>Longitude</label>
                <input type="number" step="any" value={form.longitude} onChange={update('longitude')} required placeholder="-180 to 180" />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label>Land Area (hectares)</label>
                <input type="number" step="any" value={form.land_area_hectares} onChange={update('land_area_hectares')} />
              </div>
              <div>
                <label>Elevation (m)</label>
                <input type="number" step="any" value={form.elevation_m} onChange={update('elevation_m')} placeholder="auto-fetched if left blank" />
              </div>
            </div>
            <div className="form-row">
              <div>
                <label>Land Slope (%)</label>
                <input type="number" step="any" value={form.land_slope_pct} onChange={update('land_slope_pct')} placeholder="auto-estimated if left blank" />
              </div>
              <div>
                <label>Distance to Nearest Substation (km)</label>
                <input
                  type="number"
                  step="any"
                  value={form.distance_to_substation_km}
                  onChange={update('distance_to_substation_km')}
                  placeholder="auto-fetched from OSM if left blank"
                />
              </div>
            </div>
            <label>Land Ownership</label>
            <input value={form.land_ownership} onChange={update('land_ownership')} placeholder="e.g. Private / State-owned / Leased" />
            <div className="form-actions">
              <button type="submit" disabled={submitting}>
                {submitting && <span className="spinner" />}
                {submitting ? 'Running data pipeline…' : 'Register Site'}
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header"><h3>Registered Sites</h3></div>
          <div className="table-wrap">
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
                  <tr key={s.id}>
                    <td><strong>{s.name}</strong></td>
                    <td className="mono">{s.latitude?.toFixed?.(4) ?? s.latitude}, {s.longitude?.toFixed?.(4) ?? s.longitude}</td>
                    <td>{s.elevation_m ?? '—'}</td>
                    <td>{s.distance_to_substation_km ?? '—'}</td>
                    <td>
                      <button
                        className="ghost sm"
                        disabled={refreshingId === s.id}
                        onClick={() => refreshSite(s.id)}
                      >
                        {refreshingId === s.id ? 'Refreshing…' : 'Refresh data'}
                      </button>
                    </td>
                  </tr>
                ))}
                {sites.length === 0 && !loading && (
                  <tr>
                    <td colSpan={5}><div className="empty-state">No sites registered yet.</div></td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Site Comparison — Suitability Scoring Engine</h3></div>
          <div className="table-wrap">
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
                      <td className="mono">{c.overall_score ?? '—'}</td>
                      <td>
                        <span className={`badge ${catClass[c.category] || 'cat-unscored'}`}>{c.category}</span>
                      </td>
                    </tr>
                  ))}
                {comparison.length === 0 && (
                  <tr>
                    <td colSpan={3}><div className="empty-state">No scored sites yet.</div></td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Reports</h3></div>
          <p className="page-subtitle" style={{ marginBottom: 12 }}>
            Export a full site-assessment report for this project.
          </p>
          <div className="btn-row">
            <button disabled={downloading === 'pdf'} onClick={() => downloadReport('pdf')}>
              {downloading === 'pdf' ? 'Preparing PDF…' : 'Download PDF'}
            </button>
            <button className="secondary" disabled={downloading === 'excel'} onClick={() => downloadReport('excel')}>
              {downloading === 'excel' ? 'Preparing Excel…' : 'Download Excel'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

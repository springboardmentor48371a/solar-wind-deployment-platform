import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api.js'
import SiteCard from '../components/SiteCard.jsx'
import LocationPickerMap from '../components/LocationPickerMap.jsx'
import ProjectMap from '../components/ProjectMap.jsx'

const SITE_TYPES = ['solar', 'wind', 'hybrid']

export default function ProjectDetail() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [sites, setSites] = useState([])
  const [ranking, setRanking] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({
    name: '', latitude: 28.6139, longitude: 77.2090, site_type: 'hybrid',
  })

  const load = () => {
    api.get(`/projects/${projectId}`).then(({ data }) => setProject(data))
    api.get(`/projects/${projectId}/sites`).then(({ data }) => setSites(data))
    api.get(`/projects/${projectId}/sites/ranking`).then(({ data }) => setRanking(data))
  }

  useEffect(() => { load() }, [projectId])

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleLocationSelect = (lat, lon) => {
    setForm(prev => ({ ...prev, latitude: lat, longitude: lon }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post(`/projects/${projectId}/sites`, {
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
      })
      setForm({ name: '', latitude: 28.6139, longitude: 77.2090, site_type: 'hybrid' })
      setShowForm(false)
      load()
    } finally {
      setCreating(false)
    }
  }

  const scoreFor = (siteId) => ranking.find(r => r.site_id === siteId)

  if (!project) return <div className="page"><p>Loading…</p></div>

  return (
    <div className="page">
      <Link to="/projects" className="back-link">← All projects</Link>
      <div className="section-header">
        <div>
          <h1>{project.name}</h1>
          <p className="page-subtitle">{project.objective || project.description || 'No objective set'}</p>
        </div>
        <div className="action-button-group">
          {sites.length > 1 && (
            <Link to={`/projects/${projectId}/compare`} className="btn-secondary">
              📊 Compare Sites
            </Link>
          )}
          <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Register Site'}
          </button>
        </div>
      </div>

      {showForm && (
        <form className="inline-form site-registration-modal" onSubmit={handleCreate}>
          <h2>📍 Site Registration & Location Search</h2>
          <div className="form-row">
            <div>
              <label>Site Name</label>
              <input
                value={form.name}
                onChange={update('name')}
                placeholder="e.g. Delhi Site 1, Bawana Substation Site..."
                required
              />
            </div>
            <div>
              <label>Preferred Technology</label>
              <select value={form.site_type} onChange={update('site_type')}>
                {SITE_TYPES.map(t => <option key={t} value={t}>{t.toUpperCase()}</option>)}
              </select>
            </div>
          </div>

          <div className="map-picker-section">
            <label>Interactive Map & Location Search</label>
            <LocationPickerMap
              initialLat={form.latitude}
              initialLon={form.longitude}
              onLocationSelect={handleLocationSelect}
            />
          </div>

          <div className="form-row" style={{ marginTop: '12px' }}>
            <div>
              <label>Captured Latitude</label>
              <input
                type="number"
                step="any"
                value={form.latitude}
                onChange={update('latitude')}
                required
              />
            </div>
            <div>
              <label>Captured Longitude</label>
              <input
                type="number"
                step="any"
                value={form.longitude}
                onChange={update('longitude')}
                required
              />
            </div>
          </div>

          <button className="btn-primary" type="submit" disabled={creating} style={{ marginTop: '12px' }}>
            {creating ? 'Fetching Datasets & Analyzing Site…' : 'Register & Run Full Analysis'}
          </button>
          <p className="hint">
            Latitude and longitude identify the location. Remaining environmental factors are automatically fetched
            from datasets/live APIs and processed through solar, wind, suitability, and energy forecasting engines.
          </p>
        </form>
      )}

      {sites.length > 0 && (
        <ProjectMap sites={sites} ranking={ranking} />
      )}

      {ranking.length > 0 && (
        <div className="card" style={{ marginTop: '20px' }}>
          <div className="section-header-compact">
            <h2>🏆 Site Ranking & Recommendations</h2>
            {sites.length > 1 && (
              <Link to={`/projects/${projectId}/compare`} className="btn-link">View Side-by-Side Comparison →</Link>
            )}
          </div>
          <table className="ranking-table">
            <thead>
              <tr><th>#</th><th>Site Name</th><th>Overall Score</th><th>Suitability Category</th><th>Recommendation</th><th>Details</th></tr>
            </thead>
            <tbody>
              {ranking.map((r, i) => (
                <tr key={r.site_id}>
                  <td>{i + 1}</td>
                  <td><Link to={`/projects/${projectId}/sites/${r.site_id}`}><strong>{r.site_name}</strong></Link></td>
                  <td><strong>{r.overall_score.toFixed(1)}</strong> / 100</td>
                  <td><span className="badge-cat">{r.category}</span></td>
                  <td><span className="badge-tech">{r.recommended_technology.toUpperCase()}</span></td>
                  <td><Link to={`/projects/${projectId}/sites/${r.site_id}`} className="btn-sm">View Analysis →</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <h2>All Project Sites ({sites.length})</h2>
      {sites.length === 0 ? (
        <div className="empty-state">
          <p>No sites registered yet for this project.</p>
        </div>
      ) : (
        <div className="site-grid">
          {sites.map(s => (
            <SiteCard key={s.id} projectId={projectId} site={s} score={scoreFor(s.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

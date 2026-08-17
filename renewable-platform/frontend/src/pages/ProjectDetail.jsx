import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api.js'
import SiteCard from '../components/SiteCard.jsx'

const SITE_TYPES = ['solar', 'wind', 'hybrid']

export default function ProjectDetail() {
  const { projectId } = useParams()
  const [project, setProject] = useState(null)
  const [sites, setSites] = useState([])
  const [ranking, setRanking] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState({
    name: '', latitude: '', longitude: '', region: '',
    land_area_hectares: '', elevation_m: '', site_type: 'hybrid',
  })

  const load = () => {
    api.get(`/projects/${projectId}`).then(({ data }) => setProject(data))
    api.get(`/projects/${projectId}/sites`).then(({ data }) => setSites(data))
    api.get(`/projects/${projectId}/sites/ranking`).then(({ data }) => setRanking(data))
  }

  useEffect(() => { load() }, [projectId])

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleCreate = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await api.post(`/projects/${projectId}/sites`, {
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        land_area_hectares: form.land_area_hectares ? parseFloat(form.land_area_hectares) : null,
        elevation_m: form.elevation_m ? parseFloat(form.elevation_m) : null,
      })
      setForm({ name: '', latitude: '', longitude: '', region: '', land_area_hectares: '', elevation_m: '', site_type: 'hybrid' })
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
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Register Site'}
        </button>
      </div>

      {showForm && (
        <form className="inline-form" onSubmit={handleCreate}>
          <div className="form-row">
            <div>
              <label>Site name</label>
              <input value={form.name} onChange={update('name')} required />
            </div>
            <div>
              <label>Region</label>
              <input value={form.region} onChange={update('region')} />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label>Latitude</label>
              <input type="number" step="any" value={form.latitude} onChange={update('latitude')} required />
            </div>
            <div>
              <label>Longitude</label>
              <input type="number" step="any" value={form.longitude} onChange={update('longitude')} required />
            </div>
          </div>
          <div className="form-row">
            <div>
              <label>Land area (hectares)</label>
              <input type="number" step="any" value={form.land_area_hectares} onChange={update('land_area_hectares')} />
            </div>
            <div>
              <label>Elevation (m)</label>
              <input type="number" step="any" value={form.elevation_m} onChange={update('elevation_m')} />
            </div>
          </div>
          <label>Preferred technology</label>
          <select value={form.site_type} onChange={update('site_type')}>
            {SITE_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <button className="btn-primary" type="submit" disabled={creating}>
            {creating ? 'Analyzing site…' : 'Register & Analyze Site'}
          </button>
          <p className="hint">This runs the full pipeline: environmental data → solar/wind prediction → suitability scoring → energy forecasting.</p>
        </form>
      )}

      {ranking.length > 0 && (
        <>
          <h2>Site Ranking</h2>
          <table className="ranking-table">
            <thead>
              <tr><th>#</th><th>Site</th><th>Score</th><th>Category</th><th>Recommended</th></tr>
            </thead>
            <tbody>
              {ranking.map((r, i) => (
                <tr key={r.site_id}>
                  <td>{i + 1}</td>
                  <td><Link to={`/projects/${projectId}/sites/${r.site_id}`}>{r.site_name}</Link></td>
                  <td>{r.overall_score.toFixed(1)}</td>
                  <td>{r.category}</td>
                  <td>{r.recommended_technology}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      <h2>All Sites</h2>
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

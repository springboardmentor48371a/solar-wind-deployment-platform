import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', description: '', objective: '', region: '' })
  const [loading, setLoading] = useState(true)

  const load = () => api.get('/projects').then(({ data }) => setProjects(data)).finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleCreate = async (e) => {
    e.preventDefault()
    await api.post('/projects', form)
    setForm({ name: '', description: '', objective: '', region: '' })
    setShowForm(false)
    load()
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this project and all its sites?')) return
    await api.delete(`/projects/${id}`)
    load()
  }

  return (
    <div className="page">
      <div className="section-header">
        <h1>Projects</h1>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ New Project'}
        </button>
      </div>

      {showForm && (
        <form className="inline-form" onSubmit={handleCreate}>
          <div className="form-row">
            <div>
              <label>Project name</label>
              <input value={form.name} onChange={update('name')} required />
            </div>
            <div>
              <label>Region</label>
              <input value={form.region} onChange={update('region')} placeholder="e.g. Rajasthan, India" />
            </div>
          </div>
          <label>Objective</label>
          <input value={form.objective} onChange={update('objective')} placeholder="e.g. Identify 5 MW hybrid site" />
          <label>Description</label>
          <textarea value={form.description} onChange={update('description')} rows={3} />
          <button className="btn-primary" type="submit">Create Project</button>
        </form>
      )}

      {loading ? <p>Loading…</p> : (
        <div className="project-list">
          {projects.map(p => (
            <div key={p.id} className="project-row">
              <Link to={`/projects/${p.id}`}>
                <strong>{p.name}</strong>
                <span className="muted"> — {p.site_count} site{p.site_count !== 1 ? 's' : ''} · {p.region || 'no region set'}</span>
              </Link>
              <button className="btn-danger small" onClick={() => handleDelete(p.id)}>Delete</button>
            </div>
          ))}
          {projects.length === 0 && <p className="muted">No projects yet.</p>}
        </div>
      )}
    </div>
  )
}

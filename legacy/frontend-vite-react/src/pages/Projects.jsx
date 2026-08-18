import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api'
import Navbar from '../components/Navbar'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [form, setForm] = useState({ name: '', objective: '', region: '' })
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)
  const [deletingId, setDeletingId] = useState(null)
  const [confirmId, setConfirmId] = useState(null)
  const [loading, setLoading] = useState(true)

  const loadProjects = () => {
    api.get('/projects/').then((res) => setProjects(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => {
    loadProjects()
  }, [])

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setCreating(true)
    try {
      await api.post('/projects/', form)
      setForm({ name: '', objective: '', region: '' })
      loadProjects()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create project')
    } finally {
      setCreating(false)
    }
  }

  const handleDelete = async (id) => {
    setError('')
    setDeletingId(id)
    try {
      await api.delete(`/projects/${id}`)
      setConfirmId(null)
      loadProjects()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not delete project')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>Projects</h2>
            <p className="page-subtitle">Create renewable energy projects and manage their candidate sites.</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Create a new project</h3></div>
          {error && <div className="error">{error}</div>}
          <form onSubmit={handleCreate}>
            <div className="form-row">
              <div>
                <label>Project Name</label>
                <input value={form.name} onChange={update('name')} placeholder="e.g. Andhra Coastal Solar Farm" required />
              </div>
              <div>
                <label>Region</label>
                <input value={form.region} onChange={update('region')} placeholder="e.g. Andhra Pradesh, IN" />
              </div>
            </div>
            <label>Objective</label>
            <textarea rows={2} value={form.objective} onChange={update('objective')} placeholder="What is this project trying to achieve?" />
            <div className="form-actions">
              <button type="submit" disabled={creating}>
                {creating && <span className="spinner" />}
                {creating ? 'Creating…' : 'Create Project'}
              </button>
            </div>
          </form>
        </div>

        <div className="card">
          <div className="card-header"><h3>Your Projects</h3></div>
          {loading ? (
            <div className="empty-state"><span className="spinner" /> Loading projects…</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Region</th>
                    <th>Created</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id}>
                      <td><strong>{p.name}</strong></td>
                      <td>{p.region || '—'}</td>
                      <td>{new Date(p.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="btn-row">
                          <Link to={`/projects/${p.id}/sites`}>
                            <button className="sm">Manage Sites</button>
                          </Link>
                          {confirmId === p.id ? (
                            <>
                              <button
                                className="danger sm"
                                disabled={deletingId === p.id}
                                onClick={() => handleDelete(p.id)}
                              >
                                {deletingId === p.id ? 'Deleting…' : 'Confirm delete'}
                              </button>
                              <button className="ghost sm" onClick={() => setConfirmId(null)}>Cancel</button>
                            </>
                          ) : (
                            <button className="secondary sm" onClick={() => setConfirmId(p.id)}>Delete</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {projects.length === 0 && (
                    <tr>
                      <td colSpan={4}>
                        <div className="empty-state">No projects yet — create your first one above.</div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

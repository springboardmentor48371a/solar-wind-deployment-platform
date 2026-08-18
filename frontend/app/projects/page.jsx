'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'
import { useAuth } from '../../lib/AuthContext'
import { canCreate, canWriteProject } from '../../lib/roles'

export default function Projects() {
  const { user } = useAuth()
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

  const userCanCreate = canCreate(user)

  const roleBlurb = {
    'GIS Analyst': 'As a GIS Analyst, you can run analysis and view every project, but project creation belongs to Planners, Project Managers, and Admins.',
    'Investor / Developer': 'You have read-only portfolio visibility across every project.',
    'Government / Regulator': 'You have read-only compliance visibility across every project.',
  }[user?.role]

  return (
    <AppShell
      title="Projects"
      subtitle={userCanCreate ? 'Create renewable energy projects and manage their candidate sites.' : 'View projects and drill into site-level analysis.'}
    >
      {roleBlurb && <div className="card mb-4 !py-3 !px-4 text-[13px] text-ink-muted">{roleBlurb}</div>}

      {userCanCreate && (
        <div className="card mb-4">
          <h3 className="mb-3">Create a new project</h3>
          {error && <div className="error-banner">{error}</div>}
          <form onSubmit={handleCreate}>
            <div className="grid sm:grid-cols-2 gap-3.5">
              <div>
                <label className="label">Project Name</label>
                <input className="input" value={form.name} onChange={update('name')} placeholder="e.g. Andhra Coastal Solar Farm" required />
              </div>
              <div>
                <label className="label">Region</label>
                <input className="input" value={form.region} onChange={update('region')} placeholder="e.g. Andhra Pradesh, IN" />
              </div>
            </div>
            <label className="label">Objective</label>
            <textarea
              className="input"
              rows={2}
              value={form.objective}
              onChange={update('objective')}
              placeholder="What is this project trying to achieve?"
            />
            <div className="mt-4">
              <button type="submit" disabled={creating} className="btn">
                {creating && <span className="spinner" />}
                {creating ? 'Creating…' : 'Create Project'}
              </button>
            </div>
          </form>
        </div>
      )}

      {!userCanCreate && error && <div className="error-banner">{error}</div>}

      <div className="card">
        <h3 className="mb-3">{userCanCreate ? 'Your Projects' : 'All Projects'}</h3>
        {loading ? (
          <div className="text-ink-faint text-sm py-6 text-center"><span className="spinner" /> Loading projects…</div>
        ) : (
          <div className="overflow-x-auto">
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
                {projects.map((p) => {
                  const canDelete = canWriteProject(user, p)
                  return (
                    <tr key={p.id}>
                      <td><strong>{p.name}</strong></td>
                      <td>{p.region || '—'}</td>
                      <td>{new Date(p.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="flex gap-2 flex-wrap justify-end">
                          <Link href={`/projects/${p.id}/sites`}>
                            <button className="btn btn-sm">{userCanCreate ? 'Manage Sites' : 'View Sites'}</button>
                          </Link>
                          {canDelete && (
                            confirmId === p.id ? (
                              <>
                                <button
                                  className="btn-danger btn-sm"
                                  disabled={deletingId === p.id}
                                  onClick={() => handleDelete(p.id)}
                                >
                                  {deletingId === p.id ? 'Deleting…' : 'Confirm delete'}
                                </button>
                                <button className="btn-ghost btn-sm" onClick={() => setConfirmId(null)}>Cancel</button>
                              </>
                            ) : (
                              <button className="btn-secondary btn-sm" onClick={() => setConfirmId(p.id)}>Delete</button>
                            )
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
                {projects.length === 0 && (
                  <tr>
                    <td colSpan={4}>
                      <div className="text-ink-faint text-sm py-6 text-center">
                        {userCanCreate ? 'No projects yet — create your first one above.' : 'No projects to show yet.'}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  )
}

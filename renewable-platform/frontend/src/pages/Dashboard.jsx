import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'

export default function Dashboard({ user }) {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/projects').then(({ data }) => setProjects(data)).finally(() => setLoading(false))
  }, [])

  const totalSites = projects.reduce((sum, p) => sum + p.site_count, 0)

  return (
    <div className="page">
      <h1>Welcome back, {user.full_name.split(' ')[0]} 👋</h1>
      <p className="page-subtitle">Here's an overview of your renewable energy planning workspace.</p>

      <div className="stat-grid">
        <div className="stat-card">
          <span className="stat-value">{projects.length}</span>
          <span className="stat-label">Active Projects</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{totalSites}</span>
          <span className="stat-label">Candidate Sites</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{user.role.replaceAll('_', ' ')}</span>
          <span className="stat-label">Your Role</span>
        </div>
      </div>

      <div className="section-header">
        <h2>Your Projects</h2>
        <Link className="btn-primary small" to="/projects">Manage Projects →</Link>
      </div>

      {loading ? <p>Loading…</p> : projects.length === 0 ? (
        <div className="empty-state">
          <p>No projects yet. Create your first renewable energy project to get started.</p>
          <Link className="btn-primary" to="/projects">+ Create Project</Link>
        </div>
      ) : (
        <div className="project-grid">
          {projects.map(p => (
            <Link key={p.id} to={`/projects/${p.id}`} className="project-card">
              <h3>{p.name}</h3>
              <p>{p.description || 'No description'}</p>
              <div className="project-card-footer">
                <span>{p.site_count} site{p.site_count !== 1 ? 's' : ''}</span>
                <span>{p.region || '—'}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

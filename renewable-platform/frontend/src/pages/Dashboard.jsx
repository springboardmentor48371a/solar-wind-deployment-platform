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
  const roleName = user.role?.replaceAll('_', ' ') || 'renewable energy planner'

  return (
    <div className="page">
      <div className="dashboard-welcome-banner">
        <div>
          <h1>Welcome back, {user.full_name.split(' ')[0]} 👋</h1>
          <p className="page-subtitle">
            Role: <span className="role-highlight">{roleName.toUpperCase()}</span> · Solar & Wind Deployment Intelligence Workspace
          </p>
        </div>
        {user.role === 'administrator' && (
          <Link to="/admin" className="btn-secondary">⚙️ Admin Panel</Link>
        )}
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span className="stat-value">{projects.length}</span>
          <span className="stat-label">Active Projects</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{totalSites}</span>
          <span className="stat-label">Evaluated Sites</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">Live + Synthetic</span>
          <span className="stat-label">Data Sources</span>
        </div>
      </div>

      {/* ROLE-SPECIFIC DASHBOARD SECTIONS */}
      {user.role === 'gis_analyst' && (
        <div className="card role-specific-card">
          <h2>🗺️ GIS Analyst Focus View</h2>
          <p>Access spatial layers, elevation profiles, slope penalties, and infrastructure proximity metrics for your candidate sites.</p>
          <div className="action-button-group" style={{ marginTop: '12px' }}>
            <Link to="/projects" className="btn-primary">Explore GIS Project Maps →</Link>
          </div>
        </div>
      )}

      {user.role === 'project_manager' && (
        <div className="card role-specific-card">
          <h2>📈 Project Manager Executive Summary</h2>
          <p>Review project-level site rankings, financial forecasts, payback timelines, and multi-site comparative reports.</p>
          <div className="action-button-group" style={{ marginTop: '12px' }}>
            <Link to="/projects" className="btn-primary">View Project Rankings & Financials →</Link>
          </div>
        </div>
      )}

      {user.role === 'administrator' && (
        <div className="card role-specific-card">
          <h2>⚙️ Administrator Overview</h2>
          <p>Manage platform access, configure external data-provider credentials (NASA POWER, OpenStreetMap Overpass, Open-Elevation), and monitor usage statistics.</p>
          <div className="action-button-group" style={{ marginTop: '12px' }}>
            <Link to="/admin" className="btn-primary">Go to Admin Control Panel →</Link>
          </div>
        </div>
      )}

      <div className="section-header" style={{ marginTop: '24px' }}>
        <h2>Your Renewable Projects</h2>
        <Link className="btn-primary small" to="/projects">Manage Projects →</Link>
      </div>

      {loading ? <p>Loading workspace projects…</p> : projects.length === 0 ? (
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

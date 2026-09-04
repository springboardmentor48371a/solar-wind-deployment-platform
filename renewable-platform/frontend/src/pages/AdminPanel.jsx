import React, { useEffect, useState } from 'react'
import api from '../api.js'

const ROLES = [
  { value: 'renewable_energy_planner', label: 'Renewable Energy Planner' },
  { value: 'gis_analyst', label: 'GIS Analyst' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'administrator', label: 'Administrator' },
]

export default function AdminPanel() {
  const [users, setUsers] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = async () => {
    try {
      const [uRes, sRes] = await Promise.all([
        api.get('/admin/users'),
        api.get('/admin/system-stats')
      ])
      setUsers(uRes.data)
      setStats(sRes.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load administrator settings')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadData() }, [])

  const handleRoleChange = async (userId, newRole) => {
    try {
      await api.put(`/admin/users/${userId}/role`, { role: newRole })
      loadData()
    } catch (err) {
      alert('Failed to update user role')
    }
  }

  if (loading) return <div className="page"><p>Loading admin panel...</p></div>
  if (error) return <div className="page"><p className="error-text">{error}</p></div>

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <h1>⚙️ Administrator Control Panel</h1>
          <p className="page-subtitle">Manage platform users, role assignments, and system-wide data integrations.</p>
        </div>
      </div>

      {stats && (
        <div className="card">
          <h2>📊 System Statistics & Data Provider Status</h2>
          <dl className="metric-list">
            <div><dt>Registered Users</dt><dd>{stats.total_users}</dd></div>
            <div><dt>Total Projects</dt><dd>{stats.total_projects}</dd></div>
            <div><dt>Registered Sites</dt><dd>{stats.total_sites}</dd></div>
            <div><dt>Avg Suitability Score</dt><dd>{stats.average_suitability_score} / 100</dd></div>
          </dl>
          <div className="provider-status-grid" style={{ marginTop: '16px' }}>
            {Object.entries(stats.data_providers || {}).map(([key, provider]) => (
              <div key={key} className="provider-card">
                <span className="dot-active"></span>
                <strong>{key.toUpperCase()}</strong>: {provider}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h2>👥 User Management & Role Authorization</h2>
        <table className="ranking-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Current Role</th>
              <th>Assign New Role</th>
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.full_name}</td>
                <td>{u.email}</td>
                <td><span className="role-tag">{u.role}</span></td>
                <td>
                  <select
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                    className="role-select"
                  >
                    {ROLES.map(r => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

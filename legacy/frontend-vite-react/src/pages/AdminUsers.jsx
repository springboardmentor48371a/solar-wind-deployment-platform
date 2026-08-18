import React, { useEffect, useState } from 'react'
import api from '../api'
import Navbar from '../components/Navbar'
import { useAuth } from '../AuthContext'

const ROLES = [
  'Renewable Energy Planner',
  'GIS Analyst',
  'Project Manager',
  'Administrator',
]

export default function AdminUsers() {
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)

  const load = () => api.get('/admin/users/').then((res) => setUsers(res.data)).finally(() => setLoading(false))

  useEffect(() => {
    load()
  }, [])

  const updateRole = async (id, role) => {
    setError('')
    setBusyId(id)
    try {
      await api.patch(`/admin/users/${id}/role`, { role })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update role')
    } finally {
      setBusyId(null)
    }
  }

  const toggleActive = async (id, isActive) => {
    setError('')
    setBusyId(id)
    try {
      await api.patch(`/admin/users/${id}/active`, { is_active: !isActive })
      load()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update status')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>User Management</h2>
            <p className="page-subtitle">Administrator only. Changes take effect immediately.</p>
          </div>
        </div>
        {error && <div className="error">{error}</div>}

        <div className="card">
          {loading ? (
            <div className="empty-state"><span className="spinner" /> Loading users…</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td><strong>{u.full_name}</strong></td>
                      <td className="faint">{u.email}</td>
                      <td>
                        <select
                          value={u.role}
                          disabled={busyId === u.id}
                          onChange={(e) => updateRole(u.id, e.target.value)}
                          style={{ margin: 0, minWidth: 180 }}
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <span className={`badge ${u.is_active ? '' : 'badge-red'}`}>
                          {u.is_active ? 'Active' : 'Disabled'}
                        </span>
                      </td>
                      <td>
                        <button
                          className="secondary sm"
                          disabled={u.id === currentUser?.id || busyId === u.id}
                          onClick={() => toggleActive(u.id, u.is_active)}
                          title={u.id === currentUser?.id ? "You can't disable your own account" : ''}
                        >
                          {busyId === u.id ? 'Updating…' : u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </td>
                    </tr>
                  ))}
                  {users.length === 0 && (
                    <tr><td colSpan={5}><div className="empty-state">No users found.</div></td></tr>
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

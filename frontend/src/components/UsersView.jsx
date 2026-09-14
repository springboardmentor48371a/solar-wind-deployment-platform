import { useState, useEffect } from 'react'
import { listUsers, updateUserRole, deactivateUser } from '../api'
import './UsersView.css'

const ROLES = [
  { value: 'energy_planner', label: 'Energy Planner' },
  { value: 'gis_analyst', label: 'GIS Analyst' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'administrator', label: 'Administrator' },
]

export default function UsersView() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    load()
  }, [])

  const load = async () => {
    setLoading(true)
    try {
      const res = await listUsers()
      setUsers(res.data)
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (id, role) => {
    await updateUserRole(id, role)
    load()
  }

  const handleDeactivate = async (id) => {
    if (!window.confirm('Are you sure you want to deactivate this user account?')) return
    await deactivateUser(id)
    load()
  }

  const filtered = users.filter((u) =>
    u.full_name.toLowerCase().includes(search.toLowerCase()) ||
    u.email.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="users-view">
      <input
        type="text"
        className="search-input"
        placeholder="Search by name or email..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ marginBottom: '16px' }}
      />
      <div className="users-view__table-wrapper">
        <table className="users-view__table">
          <thead>
            <tr>
              <th>Full Name</th>
              <th>Email Address</th>
              <th>Assigned Role</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((u) => (
              <tr key={u.id}>
                <td>
                  <div style={{ fontWeight: 600 }}>{u.full_name}</div>
                </td>
                <td style={{ color: 'var(--color-text-secondary)' }}>{u.email}</td>
                <td>
                  <select
                    className="users-view__role-select"
                    value={u.role}
                    onChange={(e) => handleRoleChange(u.id, e.target.value)}
                  >
                    {ROLES.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <span
                    className={`users-view__status-pill ${
                      u.is_active
                        ? 'users-view__status-pill--active'
                        : 'users-view__status-pill--inactive'
                    }`}
                  >
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  {u.is_active && (
                    <button
                      type="button"
                      onClick={() => handleDeactivate(u.id)}
                      className="btn-destructive"
                    >
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && !loading && (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
            {users.length > 0 ? `No matches for "${search}"` : 'No user accounts found.'}
          </div>
        )}
      </div>
    </div>
  )
}

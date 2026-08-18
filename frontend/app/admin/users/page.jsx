'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '../../../lib/api'
import AppShell from '../../../components/AppShell'
import { useAuth } from '../../../lib/AuthContext'

// Unlike the public Register page, this admin-only screen is allowed to
// grant every role — an Administrator promoting someone is the intended,
// gated path for Project Manager / Administrator access.
const ROLES = [
  'Renewable Energy Planner',
  'GIS Analyst',
  'Project Manager',
  'Investor / Developer',
  'Government / Regulator',
  'Administrator',
]

export default function AdminUsers() {
  const { user: currentUser, impersonate } = useAuth()
  const router = useRouter()
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

  const handleViewAs = async (id) => {
    setError('')
    setBusyId(id)
    try {
      await impersonate(id)
      router.push('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not switch to that user')
      setBusyId(null)
    }
  }

  return (
    <AppShell title="User Management" subtitle="Administrator only. Changes take effect immediately.">
      {error && <div className="error-banner">{error}</div>}

      <div className="card">
        {loading ? (
          <div className="text-ink-faint text-sm py-6 text-center"><span className="spinner" /> Loading users…</div>
        ) : (
          <div className="overflow-x-auto">
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
                    <td className="text-ink-faint">{u.email}</td>
                    <td>
                      <select
                        className="input py-1.5 min-w-[190px]"
                        value={u.role}
                        disabled={busyId === u.id}
                        onChange={(e) => updateRole(u.id, e.target.value)}
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
                      <div className="flex gap-2 flex-wrap justify-end">
                        {u.role !== 'Administrator' && u.id !== currentUser?.id && (
                          <button
                            className="btn-ghost btn-sm"
                            disabled={busyId === u.id || !u.is_active}
                            onClick={() => handleViewAs(u.id)}
                            title={!u.is_active ? "Can't view as a disabled account" : 'Browse the app as this user'}
                          >
                            👁️ View as
                          </button>
                        )}
                        <button
                          className="btn-secondary btn-sm"
                          disabled={u.id === currentUser?.id || busyId === u.id}
                          onClick={() => toggleActive(u.id, u.is_active)}
                          title={u.id === currentUser?.id ? "You can't disable your own account" : ''}
                        >
                          {busyId === u.id ? 'Updating…' : u.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr><td colSpan={5}><div className="text-ink-faint text-sm py-6 text-center">No users found.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  )
}

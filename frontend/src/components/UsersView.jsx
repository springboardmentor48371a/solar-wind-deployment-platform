import { useState, useEffect } from 'react'
import { listUsers, updateUserRole, deactivateUser } from '../api'

const ROLES = ['energy_planner', 'gis_analyst', 'project_manager', 'administrator']

export default function UsersView() {
  const [users, setUsers] = useState([])

  useEffect(() => { load() }, [])

  const load = async () => {
    const res = await listUsers()
    setUsers(res.data)
  }

  const handleRoleChange = async (id, role) => {
    await updateUserRole(id, role)
    load()
  }

  const handleDeactivate = async (id) => {
    if (!confirm('Deactivate this user?')) return
    await deactivateUser(id)
    load()
  }

  return (
    <div>
      <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 20 }}>User Management</h2>
      <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb' }}>
              {['Name', 'Email', 'Role', 'Status', 'Actions'].map(h => (
                <th key={h} style={{ padding: '10px 16px', textAlign: 'left', fontWeight: 600, color: '#6b7280', fontSize: 12 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                <td style={{ padding: '12px 16px', fontWeight: 500 }}>{u.full_name}</td>
                <td style={{ padding: '12px 16px', color: '#6b7280' }}>{u.email}</td>
                <td style={{ padding: '12px 16px' }}>
                  <select value={u.role} onChange={e => handleRoleChange(u.id, e.target.value)}
                    style={{ fontSize: 12, padding: '4px 8px', border: '1px solid #e5e7eb', borderRadius: 4 }}>
                    {ROLES.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
                  </select>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12, background: u.is_active ? '#dcfce7' : '#fee2e2', color: u.is_active ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  {u.is_active && (
                    <button onClick={() => handleDeactivate(u.id)}
                      style={{ fontSize: 11, padding: '4px 10px', border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer', background: '#fff', color: '#dc2626' }}>
                      Deactivate
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import api from '../api'
import Navbar from '../components/Navbar'

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/audit-logs/').then((res) => setLogs(res.data)).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>Audit Log</h2>
            <p className="page-subtitle">Administrator only. Most recent 100 events.</p>
          </div>
        </div>

        <div className="card">
          {loading ? (
            <div className="empty-state"><span className="spinner" /> Loading events…</div>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>User ID</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>IP</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((l) => (
                    <tr key={l.id}>
                      <td className="mono faint">{new Date(l.created_at).toLocaleString()}</td>
                      <td>{l.user_id ?? '—'}</td>
                      <td><span className="badge badge-gray">{l.action}</span></td>
                      <td>{l.resource ?? '—'}</td>
                      <td className="mono faint">{l.ip_address ?? '—'}</td>
                    </tr>
                  ))}
                  {logs.length === 0 && (
                    <tr><td colSpan={5}><div className="empty-state">No events logged yet.</div></td></tr>
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

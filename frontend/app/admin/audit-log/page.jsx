'use client'

import { useEffect, useState } from 'react'
import api from '../../../lib/api'
import AppShell from '../../../components/AppShell'

export default function AuditLog() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/admin/audit-logs/').then((res) => setLogs(res.data)).finally(() => setLoading(false))
  }, [])

  return (
    <AppShell title="Audit Log" subtitle="Administrator only. Most recent 100 events.">
      <div className="card">
        {loading ? (
          <div className="text-ink-faint text-sm py-6 text-center"><span className="spinner" /> Loading events…</div>
        ) : (
          <div className="overflow-x-auto">
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
                    <td className="font-mono text-xs text-ink-faint">{new Date(l.created_at).toLocaleString()}</td>
                    <td>{l.user_id ?? '—'}</td>
                    <td><span className="badge badge-gray">{l.action}</span></td>
                    <td>{l.resource ?? '—'}</td>
                    <td className="font-mono text-xs text-ink-faint">{l.ip_address ?? '—'}</td>
                  </tr>
                ))}
                {logs.length === 0 && (
                  <tr><td colSpan={5}><div className="text-ink-faint text-sm py-6 text-center">No events logged yet.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  )
}

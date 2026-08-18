'use client'

import { useEffect, useState } from 'react'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'

const severityBadge = {
  info: '',
  warning: 'badge-amber',
  critical: 'badge-red',
}

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [markingId, setMarkingId] = useState(null)
  const [filter, setFilter] = useState('all')

  const load = () => api.get('/alerts/').then((res) => setAlerts(res.data)).finally(() => setLoading(false))

  useEffect(() => {
    load()
  }, [])

  const markRead = async (id) => {
    setMarkingId(id)
    try {
      await api.patch(`/alerts/${id}/read`)
      load()
    } finally {
      setMarkingId(null)
    }
  }

  const visible = alerts.filter((a) => (filter === 'unread' ? !a.is_read : true))
  const unreadCount = alerts.filter((a) => !a.is_read).length

  return (
    <AppShell
      title="Alerts"
      subtitle={`${unreadCount} unread of ${alerts.length} total`}
      actions={
        <>
          <button className={filter === 'all' ? 'btn btn-sm' : 'btn-secondary btn-sm'} onClick={() => setFilter('all')}>All</button>
          <button className={filter === 'unread' ? 'btn btn-sm' : 'btn-secondary btn-sm'} onClick={() => setFilter('unread')}>Unread</button>
        </>
      }
    >
      {loading && <div className="card mb-3"><span className="spinner" /> Loading alerts…</div>}
      {!loading && visible.length === 0 && <div className="card"><div className="text-ink-faint text-sm py-6 text-center">No alerts to show.</div></div>}

      {visible.map((a) => (
        <div key={a.id} className="card mb-3" style={{ opacity: a.is_read ? 0.65 : 1 }}>
          <div className="flex items-center justify-between">
            <strong>{a.title}</strong>
            <span className={`badge ${severityBadge[a.severity] || ''}`}>{a.severity}</span>
          </div>
          <p className="text-sm my-2">{a.message}</p>
          <div className="flex items-center justify-between">
            <span className="text-ink-faint text-xs">
              {a.category} · {new Date(a.created_at).toLocaleString()}
            </span>
            {!a.is_read && (
              <button className="btn-secondary btn-sm" disabled={markingId === a.id} onClick={() => markRead(a.id)}>
                {markingId === a.id ? 'Marking…' : 'Mark as read'}
              </button>
            )}
          </div>
        </div>
      ))}
    </AppShell>
  )
}

import React, { useEffect, useState } from 'react'
import api from '../api'
import Navbar from '../components/Navbar'

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
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>Alerts</h2>
            <p className="page-subtitle">{unreadCount} unread of {alerts.length} total</p>
          </div>
          <div className="btn-row">
            <button className={filter === 'all' ? '' : 'secondary'} onClick={() => setFilter('all')}>All</button>
            <button className={filter === 'unread' ? '' : 'secondary'} onClick={() => setFilter('unread')}>Unread</button>
          </div>
        </div>

        {loading && <div className="card"><span className="spinner" /> Loading alerts…</div>}
        {!loading && visible.length === 0 && <div className="card"><div className="empty-state">No alerts to show.</div></div>}

        {visible.map((a) => (
          <div key={a.id} className="card" style={{ opacity: a.is_read ? 0.65 : 1 }}>
            <div className="row-between">
              <strong>{a.title}</strong>
              <span className={`badge ${severityBadge[a.severity] || ''}`}>{a.severity}</span>
            </div>
            <p style={{ fontSize: 14, margin: '8px 0' }}>{a.message}</p>
            <div className="row-between">
              <span className="faint" style={{ fontSize: 12 }}>
                {a.category} · {new Date(a.created_at).toLocaleString()}
              </span>
              {!a.is_read && (
                <button className="secondary sm" disabled={markingId === a.id} onClick={() => markRead(a.id)}>
                  {markingId === a.id ? 'Marking…' : 'Mark as read'}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

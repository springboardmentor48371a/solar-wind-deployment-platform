import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import api from '../api'
import { useAuth } from '../AuthContext'
import Navbar from '../components/Navbar'

const catClass = {
  Excellent: 'cat-excellent',
  'Highly Suitable': 'cat-highly-suitable',
  'Moderately Suitable': 'cat-moderately-suitable',
  'Low Suitability': 'cat-low-suitability',
  Unsuitable: 'cat-unsuitable',
}

export default function Dashboard() {
  const { user } = useAuth()
  const [summary, setSummary] = useState(null)
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.get('/analytics/dashboard'), api.get('/data-sources/status')])
      .then(([summaryRes, sourcesRes]) => {
        setSummary(summaryRes.data)
        setSources(sourcesRes.data)
      })
      .finally(() => setLoading(false))
  }, [])

  const chartData = summary
    ? Object.entries(summary.sites_by_category).map(([category, count]) => ({ category, count }))
    : []

  const greetingName = user?.full_name?.split(' ')[0] || 'there'
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening'

  return (
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>{greeting}, {greetingName}</h2>
            <p className="page-subtitle">
              Signed in as <span className="badge">{user?.role}</span>
            </p>
          </div>
          <div className="btn-row">
            <Link to="/projects"><button>+ New Project</button></Link>
            <Link to="/gis"><button className="secondary">Open GIS View</button></Link>
          </div>
        </div>

        {loading && <div className="card"><span className="spinner" /> Loading portfolio…</div>}

        {summary && (
          <div className="grid grid-4" style={{ marginBottom: 4 }}>
            <div className="stat-tile">
              <div className="stat-label">Active Projects</div>
              <div className="stat-value">{summary.active_projects}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Total Sites</div>
              <div className="stat-value">{summary.total_sites}</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Avg. Suitability</div>
              <div className="stat-value">{summary.average_suitability ?? '—'}</div>
              <div className="stat-hint">out of 100</div>
            </div>
            <div className="stat-tile">
              <div className="stat-label">Data Freshness</div>
              <div className="stat-value">{summary.data_freshness_pct}%</div>
            </div>
          </div>
        )}

        <div className="card">
          <div className="card-header">
            <h3>Sites by suitability category</h3>
          </div>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef1ef" vertical={false} />
                <XAxis dataKey="category" tick={{ fontSize: 11, fill: '#64766e' }} axisLine={{ stroke: '#e3e8e6' }} tickLine={false} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64766e' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{ borderRadius: 8, border: '1px solid #e3e8e6', fontSize: 13 }}
                  cursor={{ fill: '#f8faf9' }}
                />
                <Bar dataKey="count" fill="#1e6f4c" radius={[6, 6, 0, 0]} maxBarSize={54} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">No scored sites yet — register a site to see suitability breakdown.</div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Data connectors</h3>
          </div>
          <div className="stack-sm">
            {sources.map((s) => (
              <div key={s.name} className="row-between" style={{ padding: '6px 0' }}>
                <span>{s.name}</span>
                <span
                  className={`badge ${s.status === 'operational' ? '' : 'badge-red'}`}
                >
                  <span className="badge-dot" />
                  {s.status}
                  {s.latency_ms ? ` · ${s.latency_ms}ms` : ''}
                </span>
              </div>
            ))}
            {sources.length === 0 && !loading && <div className="empty-state">No connector data available.</div>}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Quick actions</h3></div>
          <div className="btn-row">
            <Link to="/projects"><button>Go to Projects</button></Link>
            <Link to="/alerts"><button className="secondary">View Alerts</button></Link>
            <Link to="/gis"><button className="secondary">GIS View</button></Link>
            {user?.role === 'Administrator' && (
              <Link to="/admin/users"><button className="secondary">Manage Users</button></Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

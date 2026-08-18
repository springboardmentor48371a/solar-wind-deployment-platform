import React from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const Icon = ({ path }) => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    {path}
  </svg>
)

const icons = {
  dashboard: <Icon path={<><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></>} />,
  projects: <Icon path={<><path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" /></>} />,
  gis: <Icon path={<><path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6z" /><path d="M9 3v15" /><path d="M15 6v15" /></>} />,
  alerts: <Icon path={<><path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" /></>} />,
  users: <Icon path={<><circle cx="9" cy="8" r="3.2" /><path d="M2.5 20c0-3.5 3-6 6.5-6s6.5 2.5 6.5 6" /><path d="M17 4.5c1.8.4 3 1.9 3 3.5s-1.2 3.1-3 3.5" /><path d="M19.5 14.2c2 .6 3.5 2.6 3.5 5.3" /></>} />,
  audit: <Icon path={<><path d="M9 3h9a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V8z" /><path d="M9 3v5H4" /><path d="M8 13h8M8 17h5" /></>} />,
  settings: <Icon path={<><circle cx="12" cy="12" r="3.2" /><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1 1.55V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1.11-1.55 1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.7 1.7 0 0 0 .34-1.87 1.7 1.7 0 0 0-1.55-1H3a2 2 0 1 1 0-4h.09a1.7 1.7 0 0 0 1.55-1.11 1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.7 1.7 0 0 0 1.87.34H9a1.7 1.7 0 0 0 1-1.55V3a2 2 0 1 1 4 0v.09a1.7 1.7 0 0 0 1 1.55 1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.7 1.7 0 0 0-.34 1.87V9a1.7 1.7 0 0 0 1.55 1H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.55 1z" /></>} />,
  logout: <Icon path={<><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></>} />,
}

const initials = (name = '') =>
  name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join('') || '?'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  if (!user) return null

  const linkClass = ({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`

  return (
    <nav className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-mark">☀️</div>
        <div className="sidebar-brand-text">
          Solstice OS
          <span>Deployment Intelligence</span>
        </div>
      </div>

      <div className="sidebar-section-label">Overview</div>
      <div className="sidebar-links">
        <NavLink to="/dashboard" className={linkClass}>{icons.dashboard} Dashboard</NavLink>
        <NavLink to="/projects" className={linkClass}>{icons.projects} Projects & Sites</NavLink>
        <NavLink to="/gis" className={linkClass}>{icons.gis} GIS View</NavLink>
        <NavLink to="/alerts" className={linkClass}>{icons.alerts} Alerts</NavLink>
      </div>

      {user.role === 'Administrator' && (
        <>
          <div className="sidebar-section-label">Administration</div>
          <div className="sidebar-links">
            <NavLink to="/admin/users" className={linkClass}>{icons.users} Users</NavLink>
            <NavLink to="/admin/audit-log" className={linkClass}>{icons.audit} Audit Log</NavLink>
          </div>
        </>
      )}

      <div className="sidebar-section-label">Account</div>
      <div className="sidebar-links">
        <NavLink to="/settings" className={linkClass}>{icons.settings} Settings</NavLink>
      </div>

      <div className="sidebar-footer">
        <div className="sidebar-user">
          <div className="sidebar-avatar">{initials(user.full_name)}</div>
          <div className="sidebar-user-info">
            <div className="sidebar-user-name">{user.full_name}</div>
            <div className="sidebar-user-role">{user.role}</div>
          </div>
        </div>
        <button
          className="secondary sm"
          style={{ width: '100%', marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
          onClick={() => {
            logout()
            navigate('/login')
          }}
        >
          {icons.logout} Sign out
        </button>
      </div>
    </nav>
  )
}

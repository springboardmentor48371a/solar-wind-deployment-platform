import { useState } from 'react'

const sidebarLinks = {
  energy_planner:  [{ label: 'Projects & Sites', key: 'projects' }, { label: 'Map View', key: 'map' }, { label: 'Analytics', key: 'analytics' }],
  gis_analyst:     [{ label: 'Map View', key: 'map' }, { label: 'Sites', key: 'projects' }, { label: 'Analytics', key: 'analytics' }],
  project_manager: [{ label: 'Projects & Sites', key: 'projects' }, { label: 'Map View', key: 'map' }, { label: 'Analytics', key: 'analytics' }],
  administrator:   [{ label: 'Projects & Sites', key: 'projects' }, { label: 'Map View', key: 'map' }, { label: 'Analytics', key: 'analytics' }, { label: 'User Management', key: 'users' }],
}

export default function Layout({ user, children, activePage, onNavigate, onLogout }) {
  const links = sidebarLinks[user?.role] || []

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: 'Segoe UI, sans-serif' }}>
      {/* Sidebar */}
      <div style={{ width: 220, background: '#fff', borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px 16px', borderBottom: '1px solid #e5e7eb' }}>
          <div style={{ fontWeight: 700, fontSize: 15 }}>Solar & Wind</div>
          <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>Intelligence Platform</div>
        </div>
        <nav style={{ flex: 1, padding: '12px 8px' }}>
          {links.map(link => (
            <button key={link.key} onClick={() => onNavigate(link.key)}
              style={{ display: 'block', width: '100%', textAlign: 'left', padding: '9px 12px', marginBottom: 2, border: 'none', borderRadius: 6, cursor: 'pointer', fontSize: 13, fontWeight: 500, background: activePage === link.key ? '#f3f4f6' : 'transparent', color: activePage === link.key ? '#111' : '#6b7280' }}>
              {link.label}
            </button>
          ))}
        </nav>
        <div style={{ padding: 16, borderTop: '1px solid #e5e7eb' }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#111' }}>{user?.full_name}</div>
          <div style={{ fontSize: 11, color: '#9ca3af', textTransform: 'capitalize', marginBottom: 10 }}>{user?.role?.replace(/_/g, ' ')}</div>
          <button onClick={onLogout} style={{ width: '100%', padding: '7px 0', border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff', fontSize: 12, color: '#6b7280' }}>Logout</button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, background: '#f9fafb', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>{children}</div>
      </div>
    </div>
  )
}

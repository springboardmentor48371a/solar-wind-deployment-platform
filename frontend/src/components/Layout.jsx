import { useState } from 'react'
import './Layout.css'

const sidebarLinks = {
  energy_planner: [
    { label: 'Projects & Sites', key: 'projects', context: 'Portfolio' },
    { label: 'Map View', key: 'map', context: 'Spatial Intelligence' },
    { label: 'Analytics', key: 'analytics', context: 'Evaluation' },
  ],
  gis_analyst: [
    { label: 'Map View', key: 'map', context: 'Spatial Intelligence' },
    { label: 'Sites', key: 'projects', context: 'Site Inventory' },
    { label: 'Analytics', key: 'analytics', context: 'Suitability' },
  ],
  project_manager: [
    { label: 'Projects & Sites', key: 'projects', context: 'Portfolio' },
    { label: 'Map View', key: 'map', context: 'Field Overview' },
    { label: 'Analytics', key: 'analytics', context: 'Performance' },
  ],
  administrator: [
    { label: 'User Management', key: 'users', context: 'Access Control' },
  ],
}

export default function Layout({
  user,
  children,
  activePage,
  onNavigate,
  onLogout,
  eyebrow,
  title,
  headerActions,
}) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const links = sidebarLinks[user?.role] || []

  // Resolve active page metadata for default header
  const currentLink = links.find((l) => l.key === activePage) || links[0]
  const roleName = (user?.role || 'User').replace(/_/g, ' ')
  const defaultEyebrow = `${roleName} · ${currentLink?.context || currentLink?.label || 'Overview'}`
  const defaultTitle = currentLink?.label || 'Dashboard'

  const displayEyebrow = eyebrow !== undefined ? eyebrow : defaultEyebrow
  const displayTitle = title !== undefined ? title : defaultTitle

  const handleNavClick = (key) => {
    onNavigate(key)
    setMobileOpen(false)
  }

  return (
    <div className="layout">
      {/* Mobile Top Bar (< 900px) */}
      <header className="layout__mobile-header">
        <div>
          <div className="layout__mobile-brand-title">Solar &amp; Wind</div>
          <div className="layout__brand-subtitle">Intelligence Platform</div>
        </div>
        <button
          type="button"
          className="layout__hamburger"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle navigation menu"
        >
          <span />
          <span />
          <span />
        </button>
      </header>

      {/* Backdrop for mobile drawer */}
      {mobileOpen && (
        <div
          className="layout__backdrop"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Shell */}
      <aside className={`layout__sidebar ${mobileOpen ? 'layout__sidebar--open' : ''}`}>
        <div className="layout__brand">
          <div className="layout__brand-title">Solar &amp; Wind</div>
          <div className="layout__brand-subtitle">Intelligence Platform</div>
        </div>

        <nav className="layout__nav" aria-label="Main Navigation">
          {links.map((link) => {
            const isActive = activePage === link.key
            return (
              <button
                key={link.key}
                type="button"
                onClick={() => handleNavClick(link.key)}
                className={`layout__nav-link ${isActive ? 'layout__nav-link--active' : ''}`}
              >
                {link.label}
              </button>
            )
          })}
        </nav>

        <div className="layout__user-block">
          <div className="layout__user-name" title={user?.full_name || 'User'}>
            {user?.full_name || 'User'}
          </div>
          <div className="layout__user-role">
            {roleName}
          </div>
          <button
            type="button"
            onClick={onLogout}
            className="layout__logout-btn"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="layout__main">
        <div className="layout__container">
          {/* Universal Header Pattern */}
          {(displayEyebrow || displayTitle) && (
            <header className="layout__header">
              <div className="layout__header-meta">
                {displayEyebrow && (
                  <div className="layout__eyebrow">{displayEyebrow}</div>
                )}
                {displayTitle && (
                  <h1 className="layout__title">{displayTitle}</h1>
                )}
              </div>
              {headerActions && (
                <div className="layout__header-actions">{headerActions}</div>
              )}
            </header>
          )}

          {children}
        </div>
      </main>
    </div>
  )
}

import React from 'react'
import { Link, useLocation } from 'react-router-dom'

export default function Navbar({ user, onLogout }) {
  const location = useLocation()
  const isActive = (path) => location.pathname === path

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <span className="brand-icon">⚡</span>
        <span>Solar &amp; Wind Intelligence</span>
      </div>
      <nav className="navbar-links">
        <Link className={isActive('/') ? 'active' : ''} to="/">Dashboard</Link>
        <Link className={isActive('/projects') ? 'active' : ''} to="/projects">Projects</Link>
        {user.role === 'administrator' && (
          <Link className={isActive('/admin') ? 'active' : ''} to="/admin">Admin Panel</Link>
        )}
      </nav>
      <div className="navbar-user">
        <div className="user-chip">
          <span className="user-name">{user.full_name}</span>
          <span className="user-role">{user.role.replaceAll('_', ' ')}</span>
        </div>
        <button className="btn-ghost" onClick={onLogout}>Log out</button>
      </div>
    </header>
  )
}

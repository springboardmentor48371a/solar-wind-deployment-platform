import React, { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Projects from './pages/Projects.jsx'
import ProjectDetail from './pages/ProjectDetail.jsx'
import SiteDetail from './pages/SiteDetail.jsx'
import SiteComparison from './pages/SiteComparison.jsx'
import AdminPanel from './pages/AdminPanel.jsx'

function useAuth() {
  const [user, setUser] = useState(() => {
    try {
      const raw = localStorage.getItem('user')
      return raw ? JSON.parse(raw) : null
    } catch (e) {
      localStorage.removeItem('user')
      localStorage.removeItem('token')
      return null
    }
  })
  return { user, setUser }
}

function RequireAuth({ user, children, requiredRole }) {
  if (!user) return <Navigate to="/login" replace />
  if (requiredRole && user.role !== requiredRole) return <Navigate to="/" replace />
  return children
}

export default function App() {
  const { user, setUser } = useAuth()

  return (
    <div className="app-shell">
      {user && <Navbar user={user} onLogout={() => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        setUser(null)
      }} />}
      <main className="content">
        <Routes>
          <Route path="/login" element={<Login setUser={setUser} />} />
          <Route path="/register" element={<Register setUser={setUser} />} />
          <Route path="/" element={
            <RequireAuth user={user}><Dashboard user={user} /></RequireAuth>
          } />
          <Route path="/projects" element={
            <RequireAuth user={user}><Projects /></RequireAuth>
          } />
          <Route path="/projects/:projectId" element={
            <RequireAuth user={user}><ProjectDetail /></RequireAuth>
          } />
          <Route path="/projects/:projectId/compare" element={
            <RequireAuth user={user}><SiteComparison /></RequireAuth>
          } />
          <Route path="/projects/:projectId/sites/:siteId" element={
            <RequireAuth user={user}><SiteDetail /></RequireAuth>
          } />
          <Route path="/admin" element={
            <RequireAuth user={user} requiredRole="administrator"><AdminPanel /></RequireAuth>
          } />
        </Routes>
      </main>
    </div>
  )
}

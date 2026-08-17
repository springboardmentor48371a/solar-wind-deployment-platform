import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Projects from './pages/Projects.jsx'
import ProjectDetail from './pages/ProjectDetail.jsx'
import SiteDetail from './pages/SiteDetail.jsx'

function useAuth() {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  })
  return { user, setUser }
}

function RequireAuth({ user, children }) {
  if (!user) return <Navigate to="/login" replace />
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
          <Route path="/projects/:projectId/sites/:siteId" element={
            <RequireAuth user={user}><SiteDetail /></RequireAuth>
          } />
        </Routes>
      </main>
    </div>
  )
}

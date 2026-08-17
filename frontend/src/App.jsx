import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './components/Login'
import EnergyPlannerDashboard from './pages/EnergyPlannerDashboard'
import GISAnalystDashboard from './pages/GISAnalystDashboard'
import ProjectManagerDashboard from './pages/ProjectManagerDashboard'
import AdminDashboard from './pages/AdminDashboard'
import { getProfile } from './api'

const ROLE_ROUTES = {
  energy_planner: '/dashboard/planner',
  gis_analyst: '/dashboard/gis',
  project_manager: '/dashboard/manager',
  administrator: '/dashboard/admin',
}

function ProtectedRoute({ user, children }) {
  if (!user) return <Navigate to="/" replace />
  return children
}

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    if (accessToken) {
      localStorage.setItem('access_token', accessToken)
      localStorage.setItem('refresh_token', refreshToken)
      window.history.replaceState({}, '', '/')
    }
    const token = localStorage.getItem('access_token')
    if (token) {
      getProfile(token)
        .then(res => setUser(res.data))
        .catch(() => localStorage.removeItem('access_token'))
        .finally(() => setChecking(false))
    } else {
      setChecking(false)
    }
  }, [])

  const handleSuccess = () => {
    const token = localStorage.getItem('access_token')
    getProfile(token).then(res => setUser(res.data))
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  if (checking) return null

  const dashboardProps = { user, onLogout: handleLogout }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={
          user ? <Navigate to={ROLE_ROUTES[user.role]} replace /> : <Login onSuccess={handleSuccess} />
        } />
        <Route path="/dashboard/planner" element={
          <ProtectedRoute user={user}><EnergyPlannerDashboard {...dashboardProps} /></ProtectedRoute>
        } />
        <Route path="/dashboard/gis" element={
          <ProtectedRoute user={user}><GISAnalystDashboard {...dashboardProps} /></ProtectedRoute>
        } />
        <Route path="/dashboard/manager" element={
          <ProtectedRoute user={user}><ProjectManagerDashboard {...dashboardProps} /></ProtectedRoute>
        } />
        <Route path="/dashboard/admin" element={
          <ProtectedRoute user={user}><AdminDashboard {...dashboardProps} /></ProtectedRoute>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

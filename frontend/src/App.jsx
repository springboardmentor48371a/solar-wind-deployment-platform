import { useState, useEffect } from 'react'
import Login from './components/Login'
import Dashboard from './components/Dashboard'
import { getProfile } from './api'

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    // Handle Google OAuth redirect
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

  return user
    ? <Dashboard user={user} onLogout={handleLogout} />
    : <Login onSuccess={handleSuccess} />
}

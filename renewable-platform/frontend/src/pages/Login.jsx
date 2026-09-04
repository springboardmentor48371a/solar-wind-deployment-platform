import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api.js'

export default function Login({ setUser }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', { email, password })
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      setUser(data.user)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>☀️ Deployment Intelligence</h1>
        <p className="subtitle">Sign in to your renewable energy workspace</p>
        {error && <div className="error-banner">{error}</div>}

        <label>Email</label>
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="Enter your email" />
        <label>Password</label>
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Signing in…' : 'Sign in'}
        </button>
        <p className="auth-switch">No account? <Link to="/register">Register</Link></p>
      </form>
    </div>
  )
}

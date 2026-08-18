import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials and try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-mark">☀️</div>
        <h2>Solstice OS</h2>
        <p className="muted" style={{ marginBottom: 18 }}>
          Solar &amp; Wind Deployment Intelligence — sign in to continue
        </p>
        {error && <div className="error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label>Email</label>
          <input
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          <label>Password</label>
          <input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <div className="form-actions" style={{ marginTop: 18 }}>
            <button type="submit" disabled={loading} style={{ width: '100%' }}>
              {loading && <span className="spinner" />}
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </div>
        </form>
        <p className="auth-foot">
          No account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  )
}

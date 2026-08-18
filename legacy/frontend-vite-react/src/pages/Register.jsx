import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import api from '../api'

// Self-service sign-up only offers roles the backend will actually honor.
// Project Manager and Administrator carry portfolio-wide access, so those
// are granted by an existing Administrator afterward (Admin -> Users),
// never chosen at sign-up. The backend enforces this independently even
// if this list is ever changed here.
const ROLES = [
  'Renewable Energy Planner',
  'GIS Analyst',
]

export default function Register() {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: ROLES[0],
  })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await api.post('/auth/register', form)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 1200)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-mark">☀️</div>
        <h2>Create your account</h2>
        <p className="muted" style={{ marginBottom: 18 }}>Join the deployment intelligence platform</p>
        {error && <div className="error">{error}</div>}
        {success && <div className="success-banner">Account created! Redirecting to login…</div>}
        <form onSubmit={handleSubmit}>
          <label>Full Name</label>
          <input value={form.full_name} onChange={update('full_name')} placeholder="Jane Doe" required />
          <label>Email</label>
          <input type="email" value={form.email} onChange={update('email')} placeholder="you@company.com" required />
          <label>Password</label>
          <input type="password" value={form.password} onChange={update('password')} placeholder="••••••••" required />
          <p className="hint">At least 8 characters, with an uppercase letter, a lowercase letter, and a number.</p>
          <label>Role</label>
          <select value={form.role} onChange={update('role')}>
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <p className="hint">
            Need Project Manager or Administrator access? Sign up here, then have an
            existing Administrator upgrade your role from Admin → Users.
          </p>
          <div className="form-actions" style={{ marginTop: 18 }}>
            <button type="submit" disabled={loading} style={{ width: '100%' }}>
              {loading && <span className="spinner" />}
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </div>
        </form>
        <p className="auth-foot">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

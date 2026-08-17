import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api.js'

const ROLES = [
  { value: 'renewable_energy_planner', label: 'Renewable Energy Planner' },
  { value: 'gis_analyst', label: 'GIS Analyst' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'administrator', label: 'Administrator' },
]

export default function Register({ setUser }) {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: ROLES[0].value, organization: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/auth/register', form)
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      setUser(data.user)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create your account</h1>
        <p className="subtitle">Join the deployment intelligence workspace</p>
        {error && <div className="error-banner">{error}</div>}
        <label>Full name</label>
        <input value={form.full_name} onChange={update('full_name')} required />
        <label>Email</label>
        <input type="email" value={form.email} onChange={update('email')} required />
        <label>Password</label>
        <input type="password" value={form.password} onChange={update('password')} required minLength={6} />
        <label>Role</label>
        <select value={form.role} onChange={update('role')}>
          {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
        </select>
        <label>Organization (optional)</label>
        <input value={form.organization} onChange={update('organization')} />
        <button className="btn-primary" type="submit" disabled={loading}>
          {loading ? 'Creating…' : 'Create account'}
        </button>
        <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
      </form>
    </div>
  )
}

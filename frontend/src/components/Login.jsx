import { useState } from 'react'
import api, { login, register } from '../api'
import './Login.css'

const ROLES = [
  { value: 'energy_planner', label: 'Energy Planner' },
  { value: 'gis_analyst', label: 'GIS Analyst' },
  { value: 'project_manager', label: 'Project Manager' },
  { value: 'administrator', label: 'Administrator' },
]

export default function Login({ onSuccess }) {
  const [isRegister, setIsRegister] = useState(false)
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: 'energy_planner',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = isRegister
        ? await register(form)
        : await login(form.email, form.password)
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    try {
      const res = await api.get('/auth/google/login')
      window.location.href = res.data.url
    } catch {
      setError('Failed to initiate Google login.')
    }
  }

  return (
    <div className="login-page">
      <div className="login-page__brand">
        <div className="login-page__brand-title">Solar &amp; Wind</div>
        <div className="login-page__brand-subtitle">Intelligence Platform</div>
      </div>

      <div className="login-card">
        <div className="login-card__tabs">
          <button
            type="button"
            className={`login-card__tab ${!isRegister ? 'login-card__tab--active' : ''}`}
            onClick={() => { setIsRegister(false); setError('') }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`login-card__tab ${isRegister ? 'login-card__tab--active' : ''}`}
            onClick={() => { setIsRegister(true); setError('') }}
          >
            Register
          </button>
        </div>

        <form className="login-card__form" onSubmit={submit}>
          {isRegister && (
            <div className="login-card__field">
              <label className="login-card__label" htmlFor="login-fullname">Full Name</label>
              <input
                id="login-fullname"
                className="login-card__input"
                name="full_name"
                value={form.full_name}
                onChange={handle}
                placeholder="Jane Doe"
                required
              />
            </div>
          )}

          <div className="login-card__field">
            <label className="login-card__label" htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              className="login-card__input"
              name="email"
              type="email"
              value={form.email}
              onChange={handle}
              placeholder="name@organization.com"
              required
            />
          </div>

          <div className="login-card__field">
            <label className="login-card__label" htmlFor="login-password">Password</label>
            <div className="login-card__password-wrap">
              <input
                id="login-password"
                className="login-card__input"
                name="password"
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={handle}
                placeholder="••••••••"
                required
              />
              {form.password && (
                <button
                  type="button"
                  className="login-card__password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              )}
            </div>
          </div>

          {isRegister && (
            <div className="login-card__field">
              <label className="login-card__label" htmlFor="login-role">Assigned Role</label>
              <select
                id="login-role"
                className="login-card__select"
                name="role"
                value={form.role}
                onChange={handle}
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>
                    {r.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {error && (
            <div className="login-card__error" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="login-card__submit-btn"
            disabled={loading}
          >
            {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="login-card__divider">
          <span>or</span>
        </div>

        <button
          type="button"
          onClick={handleGoogleLogin}
          className="login-card__google-btn"
        >
          <img
            src="https://www.google.com/favicon.ico"
            width={16}
            height={16}
            alt="Google"
          />
          Continue with Google
        </button>
      </div>
    </div>
  )
}

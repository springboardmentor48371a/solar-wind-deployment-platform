import { useState } from 'react'
import { login, register } from '../api'

const ROLES = ['energy_planner', 'gis_analyst', 'project_manager', 'administrator']

const inputStyle = { width: '100%', padding: '8px 10px', border: '1px solid #ccc', borderRadius: 4, fontSize: 14, marginTop: 4 }
const label = { fontSize: 13, color: '#444', display: 'block', marginTop: 12 }

export default function Login({ onSuccess }) {
  const [isRegister, setIsRegister] = useState(false)
  const [form, setForm] = useState({ full_name: '', email: '', password: '', role: 'energy_planner' })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = isRegister ? await register(form) : await login(form.email, form.password)
      localStorage.setItem('access_token', res.data.access_token)
      localStorage.setItem('refresh_token', res.data.refresh_token)
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f5f5f5' }}>
      <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 8, padding: 32, width: 360 }}>
        <h2 style={{ marginBottom: 4 }}>Solar & Wind Platform</h2>
        <p style={{ fontSize: 13, color: '#888', marginBottom: 20 }}>Renewable Energy Intelligence</p>

        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <button onClick={() => setIsRegister(false)} style={{ flex: 1, padding: '7px 0', background: !isRegister ? '#111' : '#fff', color: !isRegister ? '#fff' : '#111', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer' }}>Login</button>
          <button onClick={() => setIsRegister(true)} style={{ flex: 1, padding: '7px 0', background: isRegister ? '#111' : '#fff', color: isRegister ? '#fff' : '#111', border: '1px solid #ccc', borderRadius: 4, cursor: 'pointer' }}>Register</button>
        </div>

        <form onSubmit={submit}>
          {isRegister && (
            <>
              <label style={label}>Full Name</label>
              <input style={inputStyle} name="full_name" value={form.full_name} onChange={handle} placeholder="John Doe" required />
            </>
          )}
          <label style={label}>Email</label>
          <input style={inputStyle} name="email" type="email" value={form.email} onChange={handle} placeholder="you@example.com" required />

          <label style={label}>Password</label>
          <div style={{ position: 'relative', marginTop: 4 }}>
            <input
              style={{ ...inputStyle, marginTop: 0, paddingRight: 36 }}
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
                onClick={() => setShowPassword(p => !p)}
                style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: '#aaa', display: 'flex', alignItems: 'center' }}>
                {showPassword ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/>
                    <path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                )}
              </button>
            )}
          </div>

          {isRegister && (
            <>
              <label style={label}>Role</label>
              <select style={inputStyle} name="role" value={form.role} onChange={handle}>
                {ROLES.map(r => <option key={r} value={r}>{r.replace(/_/g, ' ')}</option>)}
              </select>
            </>
          )}

          {error && <p style={{ color: 'red', fontSize: 13, marginTop: 10 }}>{error}</p>}

          <button type="submit" disabled={loading} style={{ marginTop: 16, width: '100%', padding: '9px 0', background: '#111', color: '#fff', border: 'none', borderRadius: 4, fontSize: 14, cursor: 'pointer' }}>
            {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', margin: '16px 0', color: '#aaa', fontSize: 13 }}>or</div>

        <button onClick={async () => {
          const res = await import('../api').then(m => m.default.get('/auth/google/login'))
          window.location.href = res.data.url
        }} style={{ width: '100%', padding: '9px 0', background: '#fff', border: '1px solid #ccc', borderRadius: 4, fontSize: 14, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
          <img src="https://www.google.com/favicon.ico" width={16} alt="google" /> Continue with Google
        </button>
      </div>
    </div>
  )
}

'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../lib/AuthContext'

// All 6 roles from the spec, self-service — no staff PIN gate.
// (Deliberately simplified; see backend/app/routers/auth.py's ALL_ROLES
// comment for the tradeoff this removed.)
const ROLES = [
  'Renewable Energy Planner',
  'GIS Analyst',
  'Project Manager',
  'Investor / Developer',
  'Government / Regulator',
  'Administrator',
]

export default function Register() {
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: ROLES[0],
  })
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { registerAndLogin } = useAuth()
  const router = useRouter()

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = { full_name: form.full_name, email: form.email, password: form.password, role: form.role }
      // Straight into the app — no "now go log back in" detour.
      await registerAndLogin(payload, form.password, remember)
      router.push('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(1000px_500px_at_15%_-10%,#eaf5ee_0%,transparent_55%),radial-gradient(900px_500px_at_100%_110%,#e4f2ea_0%,transparent_55%)] bg-bg">
      <div className="w-full max-w-[400px] bg-surface border border-border rounded-lg p-8 shadow-lg">
        <Link href="/" className="inline-block mb-3.5">
          <div className="w-[42px] h-[42px] rounded-xl bg-gradient-to-br from-[#3fae7c] to-brand flex items-center justify-center text-xl shadow hover:scale-105 transition-transform">☀️</div>
        </Link>
        <h2 className="text-[22px]">Create your account</h2>
        <p className="text-ink-muted mb-4.5 mt-1">Join the deployment intelligence platform</p>
        {error && <div className="error-banner">{error}</div>}

        <form onSubmit={handleSubmit} className="flex flex-col">
          <label className="label">Full Name</label>
          <input className="input" value={form.full_name} onChange={update('full_name')} placeholder="Jane Doe" required />
          <label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={update('email')} placeholder="you@company.com" required />
          <label className="label">Password</label>
          <input className="input" type="password" value={form.password} onChange={update('password')} placeholder="••••••••" required />
          <p className="text-xs text-ink-faint mt-1">At least 8 characters, with an uppercase letter, a lowercase letter, and a number.</p>

          <label className="label">I am a</label>
          <select className="input" value={form.role} onChange={update('role')}>
            {ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>

          <label className="flex items-center gap-2 mt-3.5 text-[13px] text-ink-muted cursor-pointer select-none">
            <input
              type="checkbox"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
              className="w-4 h-4 rounded border-border accent-brand"
            />
            Remember me on this device
          </label>

          <div className="mt-4.5">
            <button type="submit" disabled={loading} className="btn w-full">
              {loading && <span className="spinner" />}
              {loading ? 'Creating account…' : 'Create account & continue'}
            </button>
          </div>
        </form>
        <p className="mt-4 text-[13px] text-ink-muted text-center">
          Already have an account? <Link href="/login" className="text-brand font-medium hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

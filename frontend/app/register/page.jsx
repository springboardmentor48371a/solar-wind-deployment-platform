'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../lib/AuthContext'

// Self-service roles the backend actually honors without a PIN.
const SELF_SERVICE_ROLES = ['Renewable Energy Planner', 'Investor / Developer', 'Government / Regulator']
// "Staff" roles need the shared staff PIN — both to register and to log in.
const STAFF_ROLES = ['GIS Analyst', 'Project Manager', 'Administrator']

export default function Register() {
  const [isStaff, setIsStaff] = useState(false)
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    role: SELF_SERVICE_ROLES[0],
    pin: '',
  })
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { registerAndLogin } = useAuth()
  const router = useRouter()

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const toggleStaff = () => {
    const next = !isStaff
    setIsStaff(next)
    setForm({ ...form, role: next ? STAFF_ROLES[0] : SELF_SERVICE_ROLES[0], pin: '' })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const payload = isStaff
        ? { full_name: form.full_name, email: form.email, password: form.password, role: form.role, pin: form.pin }
        : { full_name: form.full_name, email: form.email, password: form.password, role: form.role }

      // Straight into the app — no "now go log back in" detour. Reuses
      // the same PIN for the immediate login, since staff accounts need
      // it there too.
      await registerAndLogin(payload, form.password, isStaff ? form.pin : undefined, remember)
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

          {!isStaff && (
            <>
              <label className="label">I am a</label>
              <select className="input" value={form.role} onChange={update('role')}>
                {SELF_SERVICE_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </>
          )}

          <button
            type="button"
            onClick={toggleStaff}
            className="flex items-center justify-between mt-4 p-3 rounded-sm border border-border bg-surface-2 hover:bg-[#eef1ef] transition text-left"
          >
            <span className="text-[13px] font-medium">Registering as GIS Analyst / Project Manager / Admin?</span>
            <span className={`w-9 h-5 rounded-full relative transition ${isStaff ? 'bg-brand' : 'bg-[#d7ddda]'}`}>
              <span
                className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${isStaff ? 'translate-x-[18px]' : 'translate-x-0.5'}`}
              />
            </span>
          </button>

          {isStaff && (
            <div className="mt-3.5 p-3.5 rounded-sm border border-border bg-surface-2 animate-fadeIn">
              <label className="label mt-0">Staff Role</label>
              <select className="input" value={form.role} onChange={update('role')}>
                {STAFF_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
              <label className="label">Staff PIN</label>
              <input
                className="input tracking-[0.3em] font-mono text-center"
                type="password"
                inputMode="numeric"
                value={form.pin}
                onChange={update('pin')}
                placeholder="••••••"
                required={isStaff}
                maxLength={32}
              />
              <p className="text-xs text-ink-faint mt-1">
                Ask whoever runs this platform for the current staff PIN. You&apos;ll
                also need it every time you log in.
              </p>
            </div>
          )}

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

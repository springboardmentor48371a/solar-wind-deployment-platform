'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../lib/AuthContext'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [pin, setPin] = useState('')
  const [remember, setRemember] = useState(true)
  const [needsPin, setNeedsPin] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password, pin || undefined, remember)
      router.push('/dashboard')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (detail === 'STAFF_PIN_REQUIRED') {
        setNeedsPin(true)
        setError(
          pin
            ? 'Incorrect staff PIN. Ask an administrator for the current PIN.'
            : 'This is a staff account. Enter your staff PIN to continue.'
        )
      } else {
        setError(detail || 'Login failed. Check your credentials and try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(1000px_500px_at_15%_-10%,#eaf5ee_0%,transparent_55%),radial-gradient(900px_500px_at_100%_110%,#e4f2ea_0%,transparent_55%)] bg-bg">
      <div className="w-full max-w-[400px] bg-surface border border-border rounded-lg p-8 shadow-lg transition-all">
        <Link href="/" className="inline-block mb-3.5">
          <div className="w-[42px] h-[42px] rounded-xl bg-gradient-to-br from-[#3fae7c] to-brand flex items-center justify-center text-xl shadow hover:scale-105 transition-transform">☀️</div>
        </Link>
        <h2 className="text-[22px]">Solstice OS</h2>
        <p className="text-ink-muted mb-4.5 mt-1">Solar &amp; Wind Deployment Intelligence — sign in to continue</p>
        {error && <div className="error-banner">{error}</div>}
        <form onSubmit={handleSubmit} className="flex flex-col">
          <label className="label">Email</label>
          <input
            className="input"
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
            disabled={needsPin}
          />
          <label className="label">Password</label>
          <input
            className="input"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            disabled={needsPin}
          />

          {needsPin && (
            <div className="mt-1 animate-fadeIn">
              <label className="label">Staff PIN</label>
              <input
                className="input tracking-[0.3em] font-mono text-center"
                type="password"
                inputMode="numeric"
                placeholder="••••••"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                required
                autoFocus
                maxLength={32}
              />
              <p className="text-xs text-ink-faint mt-1">
                GIS Analyst / Project Manager / Administrator accounts require this
                on every sign-in, in addition to your password.
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
              {loading ? 'Signing in…' : needsPin ? 'Verify PIN & sign in' : 'Sign in'}
            </button>
          </div>
          {needsPin && (
            <button
              type="button"
              className="btn-ghost btn-sm mt-2 self-center"
              onClick={() => {
                setNeedsPin(false)
                setPin('')
                setError('')
              }}
            >
              ← Use a different account
            </button>
          )}
        </form>
        <p className="mt-4 text-[13px] text-ink-muted text-center">
          No account? <Link href="/register" className="text-brand font-medium hover:underline">Create one</Link>
        </p>
      </div>
    </div>
  )
}

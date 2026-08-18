'use client'

import { useState } from 'react'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'
import { useAuth } from '../../lib/AuthContext'

const initials = (name = '') =>
  name.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('') || '?'

export default function Settings() {
  const { user } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)
    setSaving(true)
    try {
      await api.post('/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
      setSuccess(true)
      setCurrentPassword('')
      setNewPassword('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not change password')
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppShell title="Settings" subtitle="Manage your account and security preferences.">
      <div className="max-w-[560px]">
        <div className="card mb-4">
          <h3 className="mb-3">Account</h3>
          <div className="flex items-center gap-3.5">
            <div className="w-[46px] h-[46px] rounded-full bg-brand-light text-brand-dark flex items-center justify-center font-bold text-[15px] flex-shrink-0">
              {initials(user?.full_name)}
            </div>
            <div>
              <div className="font-bold">{user?.full_name}</div>
              <div className="text-ink-faint text-[13px]">{user?.email}</div>
              <span className="badge mt-1.5 inline-flex">{user?.role}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h3 className="mb-3">Change Password</h3>
          {error && <div className="error-banner">{error}</div>}
          {success && <div className="success-banner">Password updated successfully.</div>}
          <form onSubmit={handleSubmit}>
            <label className="label">Current Password</label>
            <input
              className="input"
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <label className="label">New Password</label>
            <input
              className="input"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <p className="text-xs text-ink-faint mt-1">At least 8 characters, with an uppercase letter, a lowercase letter, and a number.</p>
            <div className="mt-4">
              <button type="submit" disabled={saving} className="btn">
                {saving && <span className="spinner" />}
                {saving ? 'Updating…' : 'Update Password'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </AppShell>
  )
}

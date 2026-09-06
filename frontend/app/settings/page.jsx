'use client'

import { useState } from 'react'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'
import { useAuth } from '../../lib/AuthContext'
import { useToast } from '../../lib/ToastContext'
import { getErrorMessage } from '../../lib/errorMessage'

const initials = (name = '') =>
  name.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('') || '?'

export default function Settings() {
  const { user, refreshUser } = useAuth()
  const { showToast } = useToast()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [profileError, setProfileError] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleProfileSubmit = async (e) => {
    e.preventDefault()
    setProfileError('')
    setSavingProfile(true)
    try {
      await api.patch('/auth/me', { full_name: fullName, email })
      await refreshUser()
      showToast('Profile updated.', 'success')
    } catch (err) {
      const msg = getErrorMessage(err, 'Could not update profile')
      setProfileError(msg)
      showToast(msg, 'error')
    } finally {
      setSavingProfile(false)
    }
  }

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
      setError(getErrorMessage(err, 'Could not change password'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <AppShell title="Settings" subtitle="Manage your account and security preferences.">
      <div className="max-w-[560px]">
        <div className="card mb-4">
          <h3 className="mb-3">Account</h3>
          <div className="flex items-center gap-3.5 mb-4">
            <div className="w-[46px] h-[46px] rounded-full bg-brand-light text-brand-dark flex items-center justify-center font-bold text-[15px] flex-shrink-0">
              {initials(user?.full_name)}
            </div>
            <span className="badge">{user?.role}</span>
          </div>
          {profileError && <div className="error-banner">{profileError}</div>}
          <form onSubmit={handleProfileSubmit}>
            <label className="label">Full Name</label>
            <input className="input" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            <label className="label">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <div className="mt-4">
              <button type="submit" disabled={savingProfile} className="btn">
                {savingProfile && <span className="spinner" />}
                {savingProfile ? 'Saving…' : 'Save Profile'}
              </button>
            </div>
          </form>
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

import React, { useState } from 'react'
import api from '../api'
import Navbar from '../components/Navbar'
import { useAuth } from '../AuthContext'

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
    <div>
      <Navbar />
      <div className="container" style={{ maxWidth: 560 }}>
        <div className="page-header">
          <div>
            <h2>Settings</h2>
            <p className="page-subtitle">Manage your account and security preferences.</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Account</h3></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
            <div
              style={{
                width: 46, height: 46, borderRadius: '50%', background: 'var(--brand-light)',
                color: 'var(--brand-dark)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontWeight: 700, fontSize: 15, flexShrink: 0,
              }}
            >
              {initials(user?.full_name)}
            </div>
            <div>
              <div style={{ fontWeight: 700 }}>{user?.full_name}</div>
              <div className="faint" style={{ fontSize: 13 }}>{user?.email}</div>
              <span className="badge" style={{ marginTop: 6 }}>{user?.role}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header"><h3>Change Password</h3></div>
          {error && <div className="error">{error}</div>}
          {success && <div className="success-banner">Password updated successfully.</div>}
          <form onSubmit={handleSubmit}>
            <label>Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
            />
            <label>New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
            <p className="hint">At least 8 characters, with an uppercase letter, a lowercase letter, and a number.</p>
            <div className="form-actions">
              <button type="submit" disabled={saving}>
                {saving && <span className="spinner" />}
                {saving ? 'Updating…' : 'Update Password'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

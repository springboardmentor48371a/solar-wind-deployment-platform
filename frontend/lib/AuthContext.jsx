'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import api from './api'
import {
  getToken,
  setTokens,
  clearTokens,
  stashAdminSession,
  getAdminStash,
  clearAdminStash,
} from './tokenStorage'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [adminStashUser, setAdminStashUser] = useState(null)

  const loadUser = async () => {
    const token = getToken()
    if (!token) {
      setLoading(false)
      return
    }
    try {
      const res = await api.get('/auth/me')
      setUser(res.data)
      setAdminStashUser(res.data.impersonated_by ? getAdminStash()?.user ?? null : null)
    } catch (err) {
      clearTokens()
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadUser()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const login = async (email, password, remember = true) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await api.post('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    setTokens(res.data.access_token, res.data.refresh_token, remember)
    await loadUser()
  }

  // Registration -> straight into the app, no "now go log in again" detour.
  const registerAndLogin = async (registerPayload, password, remember = true) => {
    await api.post('/auth/register', registerPayload)
    await login(registerPayload.email, password, remember)
  }

  const logout = () => {
    clearTokens()
    clearAdminStash()
    setUser(null)
    setAdminStashUser(null)
  }

  // Admin "view as" — stash the admin's own session, swap to the target
  // user's, and reload. See tokenStorage.js for why the stash is
  // sessionStorage-only.
  const impersonate = async (targetUserId) => {
    if (!user) return
    const res = await api.post(`/admin/users/${targetUserId}/impersonate`)
    stashAdminSession(user)
    setTokens(res.data.access_token, res.data.refresh_token, false)
    await loadUser()
  }

  const returnToAdmin = async () => {
    const stash = getAdminStash()
    if (!stash) {
      logout()
      return
    }
    setTokens(stash.token, stash.refresh, true)
    clearAdminStash()
    setAdminStashUser(null)
    await loadUser()
  }

  const isImpersonating = Boolean(user?.impersonated_by)

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        registerAndLogin,
        logout,
        impersonate,
        returnToAdmin,
        isImpersonating,
        adminStashUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}

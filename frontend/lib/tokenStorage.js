'use client'

// Centralizes where auth tokens live, since three different things need
// to agree on it: AuthContext (login/logout), api.js (attaching the
// Authorization header + the silent-refresh interceptor), and the admin
// impersonation flow (which needs to stash the *original* admin session
// somewhere separate while "viewing as" someone else).
//
// Remember me: checked -> localStorage (survives closing the browser).
// Unchecked -> sessionStorage (cleared when the tab/browser closes) —
// the standard, expected meaning of an unchecked "remember me" box.

const TOKEN_KEY = 'token'
const REFRESH_KEY = 'refresh_token'
const REMEMBER_KEY = 'remember_me'

const ADMIN_STASH_TOKEN = 'admin_stash_token'
const ADMIN_STASH_REFRESH = 'admin_stash_refresh'
const ADMIN_STASH_USER = 'admin_stash_user'

function remembering() {
  if (typeof window === 'undefined') return true
  return localStorage.getItem(REMEMBER_KEY) !== '0'
}

// Where the *current* tokens live — read defensively from both, since a
// stray value can end up in the "wrong" one (e.g. remember-me was toggled
// between sessions).
export function getToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY)
}

export function getRefreshToken() {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(REFRESH_KEY) || sessionStorage.getItem(REFRESH_KEY)
}

export function setTokens(accessToken, refreshToken, remember) {
  clearTokens()
  localStorage.setItem(REMEMBER_KEY, remember ? '1' : '0')
  const store = remember ? localStorage : sessionStorage
  store.setItem(TOKEN_KEY, accessToken)
  store.setItem(REFRESH_KEY, refreshToken)
}

// Used by api.js's silent-refresh interceptor to replace an expired
// access token in whichever storage currently holds the session, without
// needing to know the original remember-me choice.
export function updateAccessToken(accessToken) {
  const store = remembering() ? localStorage : sessionStorage
  store.setItem(TOKEN_KEY, accessToken)
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  sessionStorage.removeItem(TOKEN_KEY)
  sessionStorage.removeItem(REFRESH_KEY)
}

// --- Admin impersonation stash ---
// Deliberately sessionStorage-only: an impersonation session shouldn't
// silently survive a full browser restart days later. The original admin
// session is put here while "viewing as" someone else, and restored (or
// discarded) explicitly via returnToAdmin() / logout().

export function stashAdminSession(adminUser) {
  const token = getToken()
  const refresh = getRefreshToken()
  if (!token || !refresh) return
  sessionStorage.setItem(ADMIN_STASH_TOKEN, token)
  sessionStorage.setItem(ADMIN_STASH_REFRESH, refresh)
  sessionStorage.setItem(ADMIN_STASH_USER, JSON.stringify(adminUser))
}

export function getAdminStash() {
  if (typeof window === 'undefined') return null
  const token = sessionStorage.getItem(ADMIN_STASH_TOKEN)
  const refresh = sessionStorage.getItem(ADMIN_STASH_REFRESH)
  if (!token || !refresh) return null
  const userJson = sessionStorage.getItem(ADMIN_STASH_USER)
  return { token, refresh, user: userJson ? JSON.parse(userJson) : null }
}

export function clearAdminStash() {
  sessionStorage.removeItem(ADMIN_STASH_TOKEN)
  sessionStorage.removeItem(ADMIN_STASH_REFRESH)
  sessionStorage.removeItem(ADMIN_STASH_USER)
}

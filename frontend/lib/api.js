'use client'

import axios from 'axios'
import { getToken, getRefreshToken, updateAccessToken, clearTokens } from './tokenStorage'

// Falls back to localhost for local dev; set NEXT_PUBLIC_API_BASE_URL at
// build time when deploying the frontend against a non-local backend.
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

// A request with NO timeout at all (axios's default) will wait forever
// for a response — if the backend ever hangs for any reason (a slow
// query, a network blip, anything), the UI shows a spinner/"Computing…"
// literally forever with zero error, indistinguishable from "broken."
// 60s is generous enough to not falsely trip on legitimately slow
// operations (site registration triggers a whole external-API
// pipeline — NASA POWER, OSM, satellite imagery, World Bank,
// sequentially) while still guaranteeing every hung request eventually
// surfaces as a real, visible, catchable error instead of an infinite
// silent wait.
const api = axios.create({ baseURL, timeout: 60000 })

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Auto-refresh: if a request fails with 401 (expired access token), try once
// to exchange the refresh token for a new access token and replay the
// original request. Falls through to logout (via the 401 propagating) if
// the refresh token is also invalid/expired.
let refreshPromise = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const isAuthEndpoint = originalRequest?.url?.startsWith('/auth/')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        return Promise.reject(error)
      }

      try {
        if (!refreshPromise) {
          refreshPromise = axios
            .post(`${baseURL}/auth/refresh`, { refresh_token: refreshToken })
            .finally(() => {
              refreshPromise = null
            })
        }
        const res = await refreshPromise
        updateAccessToken(res.data.access_token)
        originalRequest.headers.Authorization = `Bearer ${res.data.access_token}`
        return api(originalRequest)
      } catch (refreshError) {
        clearTokens()
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api

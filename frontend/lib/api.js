'use client'

import axios from 'axios'
import { getToken, getRefreshToken, updateAccessToken, clearTokens } from './tokenStorage'

// Falls back to localhost for local dev; set NEXT_PUBLIC_API_BASE_URL at
// build time when deploying the frontend against a non-local backend.
const baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const api = axios.create({ baseURL })

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

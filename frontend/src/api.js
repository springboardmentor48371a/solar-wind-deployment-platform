import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000' })

export const register = (data) => api.post('/auth/register', data)

export const login = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/auth/login', form)
}

export const getProfile = (token) =>
  api.get('/users/me', { headers: { Authorization: `Bearer ${token}` } })

export default api

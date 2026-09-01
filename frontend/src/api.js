import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Auth
export const register = (data) => api.post('/auth/register', data)
export const login = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/auth/login', form)
}
export const getProfile = (token) =>
  api.get('/users/me', { headers: { Authorization: `Bearer ${token}` } })

// Users (admin)
export const listUsers = () => api.get('/users/')
export const updateUserRole = (id, role) => api.patch(`/users/${id}/role?role=${role}`)
export const deactivateUser = (id) => api.patch(`/users/${id}/deactivate`)

// Regions
export const listRegions = () => api.get('/regions/')
export const createRegion = (data) => api.post('/regions/', data)

// Projects
export const listProjects = () => api.get('/projects/')
export const createProject = (data) => api.post('/projects/', data)
export const updateProject = (id, data) => api.patch(`/projects/${id}`, data)
export const deleteProject = (id) => api.delete(`/projects/${id}`)

// Sites
export const listSites = (projectId) => api.get(`/sites/?project_id=${projectId}`)
export const previewLocation = (lat, lon) => api.get(`/sites/preview?lat=${lat}&lon=${lon}`)
export const createSite = (data) => api.post('/sites/', data)
export const updateSiteStatus = (id, status, notes) => api.patch(`/sites/${id}/status`, { status, notes })
export const deleteSite = (id) => api.delete(`/sites/${id}`)
export const compareSites = (ids) => api.get(`/sites/compare?ids=${ids.join(',')}`)

// Environmental
export const collectEnvData = (siteId, days = 30) => api.post(`/environmental/${siteId}/collect?days=${days}`)
export const getEnvSummary = (siteId) => api.get(`/environmental/${siteId}/summary`)
export const getEnvData = (siteId) => api.get(`/environmental/${siteId}`)

// Predictions (ML)
export const getPrediction = (siteId) => api.get(`/predictions/${siteId}`)
export const runPrediction = (siteId) => api.post(`/predictions/${siteId}/run`)

export default api

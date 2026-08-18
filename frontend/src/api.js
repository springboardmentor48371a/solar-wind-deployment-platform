import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',
});

// Auth
export const registerUser = (userData) => api.post('/register/', userData);
export const loginUser = (loginData) => api.post('/login/', loginData);

// Creation
export const createProject = (userId, projectData) => api.post(`/projects/?user_id=${userId}`, projectData);
export const registerSite = (projectId, siteData) => api.post(`/projects/${projectId}/sites/`, siteData);

// Data Fetching
export const getProjects = (userId) => api.get(`/users/${userId}/projects/`);
export const getSites = (projectId) => api.get(`/projects/${projectId}/sites/`);
export const getAllUsers = () => api.get('/users/');

// Analytics (Simulated AI Engine)
export const getProjectAnalytics = (projectId) => api.get(`/projects/${projectId}/analytics/`);

export default api;
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Log all requests
api.interceptors.request.use(
  (config) => {
    console.log('📤 Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('📤 Request Error:', error);
    return Promise.reject(error);
  }
);

// Log all responses
api.interceptors.response.use(
  (response) => {
    console.log('📥 Response:', response.status, response.config.url);
    console.log('📥 Data:', response.data);
    return response;
  },
  (error) => {
    console.error('📥 Response Error:', error.response?.status, error.response?.config?.url);
    console.error('📥 Error Data:', error.response?.data);
    return Promise.reject(error);
  }
);

export const register = async (userData) => {
  console.log('📝 Registering user:', userData.email);
  const response = await api.post('/auth/register', userData);
  console.log('✅ Registration response:', response.data);
  return response.data;
};

export const login = async (credentials) => {
  console.log('🔐 Login attempt for:', credentials.email);
  const response = await api.post('/auth/login', credentials);
  console.log('✅ Login response:', response.data);
  
  if (response.data && response.data.access_token) {
    console.log('🎫 Storing token...');
    localStorage.setItem('token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
    console.log('✅ Token stored successfully');
  }
  return response.data;
};

export const logout = () => {
  console.log('🚪 Logging out...');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getCurrentUser = async () => {
  const token = localStorage.getItem('token');
  console.log('🔑 Getting current user, token exists:', !!token);
  
  if (!token) {
    throw new Error('No token found');
  }
  
  const response = await api.get('/auth/me', {
    params: { token: token }
  });
  console.log('👤 Current user:', response.data);
  return response.data;
};

export default api;
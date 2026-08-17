import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';
import type { User, LoginCredentials, RegisterCredentials, TokenResponse, AuthState } from '../types/auth';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
  error: string | null;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('solar_wind_token'));
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  // Check initial authentication token session on load
  useEffect(() => {
    const fetchCurrentUser = async () => {
      const storedToken = localStorage.getItem('solar_wind_token');
      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const response = await api.get<User>('/api/auth/me');
        setUser(response.data);
        setToken(storedToken);
      } catch (err: any) {
        console.error('Session authentication failed:', err);
        localStorage.removeItem('solar_wind_token');
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCurrentUser();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post<TokenResponse>('/api/auth/login', credentials);
      const { access_token, user: userData } = response.data;

      localStorage.setItem('solar_wind_token', access_token);
      setToken(access_token);
      setUser(userData);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Invalid email or password. Please try again.';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Register User
      await api.post<User>('/api/auth/register', {
        full_name: credentials.full_name,
        email: credentials.email,
        password: credentials.password,
        confirm_password: credentials.confirm_password
      });

      // 2. Automatically log in after registration
      await login({
        email: credentials.email,
        password: credentials.password
      });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed. Please check details and try again.';
      setError(message);
      throw new Error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    try {
      api.post('/api/auth/logout').catch(() => {});
    } finally {
      localStorage.removeItem('solar_wind_token');
      setToken(null);
      setUser(null);
      setError(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        error,
        clearError,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

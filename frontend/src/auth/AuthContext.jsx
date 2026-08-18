import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { apiClient, setAccessToken } from "../services/apiClient.js";

const TOKEN_STORAGE_KEY = "renewable_energy_access_token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY));
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setAccessToken(token);
  }, [token]);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const user = await apiClient.getCurrentUser();
        if (isMounted) {
          setCurrentUser(user);
        }
      } catch (error) {
        if (isMounted) {
          clearSession();
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    restoreSession();

    return () => {
      isMounted = false;
    };
  }, [token]);

  function saveToken(nextToken) {
    localStorage.setItem(TOKEN_STORAGE_KEY, nextToken);
    setAccessToken(nextToken);
    setToken(nextToken);
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setAccessToken(null);
    setToken(null);
    setCurrentUser(null);
  }

  async function login(email, password) {
    const tokenResponse = await apiClient.login(email, password);
    saveToken(tokenResponse.access_token);
    setLoading(true);
    try {
      setAccessToken(tokenResponse.access_token);
      const user = await apiClient.getCurrentUser();
      setCurrentUser(user);
      return user;
    } catch (error) {
      clearSession();
      throw error;
    } finally {
      setLoading(false);
    }
  }

  async function loginWithToken(nextToken) {
    saveToken(nextToken);
    setLoading(true);
    try {
      setAccessToken(nextToken);
      const user = await apiClient.getCurrentUser();
      setCurrentUser(user);
      return user;
    } catch (error) {
      clearSession();
      throw error;
    } finally {
      setLoading(false);
    }
  }

  async function register(payload) {
    return apiClient.register(payload);
  }

  function logout() {
    clearSession();
  }

  const value = useMemo(
    () => ({
      currentUser,
      token,
      isAuthenticated: Boolean(token && currentUser),
      loading,
      login,
      loginWithToken,
      register,
      logout,
    }),
    [currentUser, loading, token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider.");
  }
  return context;
}

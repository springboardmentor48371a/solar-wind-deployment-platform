import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RenewableBackground } from '../components/background/RenewableBackground';
import { AuthCard } from '../components/auth/AuthCard';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';
import { PlatformDashboard } from '../components/dashboard/PlatformDashboard';

export const AuthView: React.FC<{ initialTab?: 'login' | 'register' }> = ({ initialTab = 'login' }) => {
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(initialTab);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (location.pathname === '/register') {
      setActiveTab('register');
    } else if (location.pathname === '/login') {
      setActiveTab('login');
    }
  }, [location.pathname]);

  const handleTabChange = (tab: 'login' | 'register') => {
    setActiveTab(tab);
    navigate(tab === 'login' ? '/login' : '/register');
  };

  return (
    <div className="min-h-screen w-full relative flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      {/* 1. Renewable Energy Animated SVG Background */}
      <RenewableBackground />

      {/* 2. Glassmorphic Authentication Card */}
      <AuthCard activeTab={activeTab} onTabChange={handleTabChange}>
        {activeTab === 'login' ? (
          <LoginForm onSwitchToRegister={() => handleTabChange('register')} />
        ) : (
          <RegisterForm onSwitchToLogin={() => handleTabChange('login')} />
        )}
      </AuthCard>
    </div>
  );
};

export const AppRoutes: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-amber-500">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-amber-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-bold tracking-wider text-slate-300">Initializing Intelligence Platform...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthView initialTab="login" />}
      />
      <Route
        path="/register"
        element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <AuthView initialTab="register" />}
      />
      <Route
        path="/dashboard"
        element={isAuthenticated ? <PlatformDashboard /> : <Navigate to="/login" replace />}
      />
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />}
      />
    </Routes>
  );
};

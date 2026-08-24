import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Projects from './pages/Projects';
import Sites from './pages/Sites';
import SiteDetails from './pages/Sitedetails';
import Dashboard from './pages/Dashboard';
import Predict from './pages/Predict';
function App() {
  const isAuthenticated = !!localStorage.getItem('token');

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Login />} />
        <Route path="/register" element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <Register />} />
        
        {/* Protected routes */}
        <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" replace />} />
        <Route path="/projects" element={isAuthenticated ? <Projects /> : <Navigate to="/login" replace />} />
        <Route path="/projects/:projectId/sites" element={isAuthenticated ? <Sites /> : <Navigate to="/login" replace />} />
        <Route path="/sites/:siteId" element={isAuthenticated ? <SiteDetails /> : <Navigate to="/login" replace />} />
        <Route path="/predict" element={isAuthenticated ? <Predict /> : <Navigate to="/login" />} />
        {/* Default route */}
        <Route path="/" element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} replace />} />
      </Routes>
    </Router>
  );
}

export default App;
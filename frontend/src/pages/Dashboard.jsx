import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Background from '../components/Background';
import EnergyPlannerDashboard from './dashboards/EnergyPlannerDashboard';
import GISAnalystDashboard from './dashboards/GISAnalystDashboard';
import ProjectManagerDashboard from './dashboards/ProjectManagerDashboard';
import AdminDashboard from './dashboards/AdminDashboard';

const API_URL = 'http://localhost:8000/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('energy');
  const [stats, setStats] = useState({ projects: 0, sites: 0, avgScore: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const projRes = await axios.get(`${API_URL}/projects`, { headers });
      setStats(prev => ({ ...prev, projects: projRes.data.length }));

      const siteRes = await axios.get(`${API_URL}/sites`, { headers });
      setStats(prev => ({ ...prev, sites: siteRes.data.length }));

      let total = 0, count = 0;
      for (const site of siteRes.data) {
        try {
          const scoreRes = await axios.get(`${API_URL}/suitability/score/${site.id}`, { headers });
          total += scoreRes.data.overall_score || 0;
          count++;
        } catch (e) {}
      }
      setStats(prev => ({ ...prev, avgScore: count > 0 ? Math.round(total / count) : 0 }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (loading) return <div style={styles.loading}>Loading Dashboard...</div>;

  return (
    <>
      <Background />
      <div style={styles.container}>
        {/* Header */}
        <div style={styles.header}>
          <h1 style={styles.title}>📊 Dashboard</h1>
          <div style={styles.headerActions}>
            <span style={styles.userName}>👋 {user.name || 'User'}</span>
            <button onClick={() => navigate('/projects')} style={styles.projectsBtn}>📋 Projects</button>
            <button onClick={handleLogout} style={styles.logoutBtn}>Logout</button>
          </div>
        </div>

        {/* Quick Stats */}
        <div style={styles.statsGrid}>
          <div style={styles.statCard}>
            <h3>{stats.projects}</h3>
            <p>Total Projects</p>
          </div>
          <div style={styles.statCard}>
            <h3>{stats.sites}</h3>
            <p>Total Sites</p>
          </div>
          <div style={styles.statCard}>
            <h3>{stats.avgScore}</h3>
            <p>Avg Suitability</p>
          </div>
        </div>

        {/* Tabs */}
        <div style={styles.tabs}>
          {['energy', 'gis', 'project', 'admin'].map(tab => (
            <button
              key={tab}
              style={{ ...styles.tabBtn, ...(activeTab === tab ? styles.tabActive : {}) }}
              onClick={() => setActiveTab(tab)}
            >
              {tab === 'energy' && '⚡ Energy Planner'}
              {tab === 'gis' && '🗺️ GIS Analyst'}
              {tab === 'project' && '📋 Project Manager'}
              {tab === 'admin' && '🔧 Admin'}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div style={styles.content}>
          {activeTab === 'energy' && <EnergyPlannerDashboard />}
          {activeTab === 'gis' && <GISAnalystDashboard />}
          {activeTab === 'project' && <ProjectManagerDashboard />}
          {activeTab === 'admin' && <AdminDashboard />}
        </div>
      </div>
    </>
  );
};

// ============================================
// STYLES (Dark Glassmorphic)
// ============================================
const styles = {
  container: {
    position: 'relative',
    zIndex: 1,
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '20px',
    minHeight: '100vh',
    color: '#ffffff',
    fontFamily: 'Inter, -apple-system, sans-serif',
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    color: '#ffffff',
    fontSize: '20px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    borderRadius: '16px',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    marginBottom: '24px',
  },
  title: {
    fontSize: '28px',
    fontWeight: '600',
    margin: 0,
    color: '#ffffff',
  },
  headerActions: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  userName: {
    fontSize: '16px',
    color: 'rgba(255,255,255,0.8)',
  },
  projectsBtn: {
    padding: '8px 16px',
    background: 'rgba(25, 118, 210, 0.6)',
    backdropFilter: 'blur(4px)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    color: '#ffffff',
    cursor: 'pointer',
    fontSize: '14px',
  },
  logoutBtn: {
    padding: '8px 16px',
    background: 'rgba(220, 53, 69, 0.6)',
    backdropFilter: 'blur(4px)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    color: '#ffffff',
    cursor: 'pointer',
    fontSize: '14px',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '16px',
    marginBottom: '24px',
  },
  statCard: {
    background: 'rgba(255, 255, 255, 0.05)',
    backdropFilter: 'blur(8px)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: '12px',
    padding: '20px',
    textAlign: 'center',
    color: '#ffffff',
  },
  statCard: {
    h3: {
      fontSize: '32px',
      margin: '0 0 4px 0',
      fontWeight: '600',
    },
    p: {
      margin: 0,
      fontSize: '14px',
      color: 'rgba(255,255,255,0.6)',
    },
  },
  tabs: {
    display: 'flex',
    gap: '4px',
    marginBottom: '24px',
    background: 'rgba(255, 255, 255, 0.03)',
    borderRadius: '12px',
    padding: '6px',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    flexWrap: 'wrap',
  },
  tabBtn: {
    padding: '10px 20px',
    background: 'transparent',
    border: 'none',
    borderRadius: '8px',
    color: 'rgba(255,255,255,0.6)',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '500',
    transition: 'all 0.2s',
  },
  tabActive: {
    background: 'rgba(255, 255, 255, 0.08)',
    color: '#ffffff',
  },
  content: {
    background: 'rgba(255, 255, 255, 0.03)',
    backdropFilter: 'blur(8px)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: '16px',
    padding: '24px',
    minHeight: '300px',
  },
};

export default Dashboard;
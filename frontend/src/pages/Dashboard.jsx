import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('energy');
  const [stats, setStats] = useState({ projects: 0, sites: 0, avgScore: 0 });
  const [recentProjects, setRecentProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showSiteModal, setShowSiteModal] = useState(false);
  const [projectForm, setProjectForm] = useState({ project_name: '', description: '', technology: 'SOLAR', budget: 0 });
  const [siteForm, setSiteForm] = useState({ site_name: '', latitude: '', longitude: '', region: '', land_area: '', elevation: '' });
  const [modalError, setModalError] = useState('');
  const [projects, setProjects] = useState([]);

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
      setProjects(projRes.data);
      setRecentProjects(projRes.data.slice(0, 5));
      setStats(prev => ({ ...prev, projects: projRes.data.length }));

      const siteRes = await axios.get(`${API_URL}/sites`, { headers });
      setStats(prev => ({ ...prev, sites: siteRes.data.length }));

      let totalScore = 0, count = 0;
      for (const site of siteRes.data) {
        try {
          const scoreRes = await axios.get(`${API_URL}/suitability/score/${site.id}`, { headers });
          totalScore += scoreRes.data.overall_score || 0;
          count++;
        } catch (e) { /* ignore */ }
      }
      setStats(prev => ({ ...prev, avgScore: count > 0 ? Math.round(totalScore / count) : 0 }));

    } catch (err) {
      console.error('Dashboard fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Create Project
  const handleCreateProject = async (e) => {
    e.preventDefault();
    setModalError('');
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/projects`, projectForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowProjectModal(false);
      setProjectForm({ project_name: '', description: '', technology: 'SOLAR', budget: 0 });
      fetchData();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to create project');
    }
  };

  // Create Site
  const handleCreateSite = async (e) => {
    e.preventDefault();
    setModalError('');
    if (!projects.length) {
      setModalError('Create a project first before adding a site.');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/sites`, {
        ...siteForm,
        project_id: projects[0].id,
        latitude: parseFloat(siteForm.latitude),
        longitude: parseFloat(siteForm.longitude),
        land_area: parseFloat(siteForm.land_area) || 0,
        elevation: parseFloat(siteForm.elevation) || 0
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowSiteModal(false);
      setSiteForm({ site_name: '', latitude: '', longitude: '', region: '', land_area: '', elevation: '' });
      fetchData();
    } catch (err) {
      setModalError(err.response?.data?.detail || 'Failed to create site');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (loading) {
    return <div style={styles.loading}>Loading Dashboard...</div>;
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>📊 Dashboard</h1>
        <div style={styles.headerActions}>
          <span style={styles.userName}>👋 {user.name || 'User'}</span>
          <button onClick={() => setShowProjectModal(true)} style={styles.actionBtnGreen}>➕ Project</button>
          <button onClick={() => setShowSiteModal(true)} style={styles.actionBtnBlue}>📍 Site</button>
          <button onClick={() => navigate('/projects')} style={styles.projectsBtn}>📋 Manage</button>
          <button onClick={handleLogout} style={styles.logoutBtn}>Logout</button>
        </div>
      </div>

      {/* Stats Cards */}
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

      {/* Recent Projects */}
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>📋 Recent Projects</h3>
        {recentProjects.length === 0 ? (
          <p style={styles.emptyText}>No projects yet. Click "➕ Project" to create one!</p>
        ) : (
          <div style={styles.projectList}>
            {recentProjects.map(proj => (
              <div key={proj.id} style={styles.projectItem}>
                <span>{proj.project_name}</span>
                <span style={styles.techBadge}>{proj.technology}</span>
                <span style={proj.status === 'ACTIVE' ? styles.activeBadge : styles.draftBadge}>
                  {proj.status}
                </span>
              </div>
            ))}
          </div>
        )}
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
        {activeTab === 'energy' && <div><h3>⚡ Energy Planner</h3><p>Recommended sites, forecasts, and investment analysis.</p></div>}
        {activeTab === 'gis' && <div><h3>🗺️ GIS Analyst</h3><p>Interactive map with site markers.</p></div>}
        {activeTab === 'project' && <div><h3>📋 Project Manager</h3><p>Project progress, feasibility reports.</p></div>}
        {activeTab === 'admin' && <div><h3>🔧 Admin</h3><p>User management, platform analytics.</p></div>}
      </div>

      {/* Create Project Modal */}
      {showProjectModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h2>Create New Project</h2>
            {modalError && <div style={styles.error}>{modalError}</div>}
            <form onSubmit={handleCreateProject}>
              <input placeholder="Project Name" value={projectForm.project_name} onChange={(e) => setProjectForm({...projectForm, project_name: e.target.value})} required style={styles.input} />
              <textarea placeholder="Description" value={projectForm.description} onChange={(e) => setProjectForm({...projectForm, description: e.target.value})} style={styles.textarea} rows="2" />
              <select value={projectForm.technology} onChange={(e) => setProjectForm({...projectForm, technology: e.target.value})} style={styles.input}>
                <option value="SOLAR">☀️ Solar</option>
                <option value="WIND">💨 Wind</option>
                <option value="HYBRID">⚡ Hybrid</option>
              </select>
              <input type="number" placeholder="Budget ($)" value={projectForm.budget} onChange={(e) => setProjectForm({...projectForm, budget: parseFloat(e.target.value)})} style={styles.input} />
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowProjectModal(false)} style={styles.cancelBtn}>Cancel</button>
                <button type="submit" style={styles.submitBtn}>Create</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Site Modal */}
      {showSiteModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h2>Register New Site</h2>
            {modalError && <div style={styles.error}>{modalError}</div>}
            <form onSubmit={handleCreateSite}>
              <input placeholder="Site Name" value={siteForm.site_name} onChange={(e) => setSiteForm({...siteForm, site_name: e.target.value})} required style={styles.input} />
              <div style={styles.row}>
                <input type="number" step="0.000001" placeholder="Latitude" value={siteForm.latitude} onChange={(e) => setSiteForm({...siteForm, latitude: e.target.value})} required style={{...styles.input, width: '48%'}} />
                <input type="number" step="0.000001" placeholder="Longitude" value={siteForm.longitude} onChange={(e) => setSiteForm({...siteForm, longitude: e.target.value})} required style={{...styles.input, width: '48%'}} />
              </div>
              <input placeholder="Region" value={siteForm.region} onChange={(e) => setSiteForm({...siteForm, region: e.target.value})} style={styles.input} />
              <div style={styles.row}>
                <input type="number" placeholder="Land Area (acres)" value={siteForm.land_area} onChange={(e) => setSiteForm({...siteForm, land_area: e.target.value})} style={{...styles.input, width: '48%'}} />
                <input type="number" placeholder="Elevation (m)" value={siteForm.elevation} onChange={(e) => setSiteForm({...siteForm, elevation: e.target.value})} style={{...styles.input, width: '48%'}} />
              </div>
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowSiteModal(false)} style={styles.cancelBtn}>Cancel</button>
                <button type="submit" style={styles.submitBtn}>Register</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

const styles = {
  container: { padding: '20px', maxWidth: '1400px', margin: '0 auto', backgroundColor: '#f5f7fa', minHeight: '100vh' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px', backgroundColor: 'white', borderRadius: '12px', marginBottom: '16px' },
  title: { fontSize: '28px', color: '#1a237e', margin: 0 },
  headerActions: { display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' },
  userName: { fontSize: '16px', color: '#333' },
  actionBtnGreen: { padding: '8px 16px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  actionBtnBlue: { padding: '8px 16px', backgroundColor: '#1976d2', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  projectsBtn: { padding: '8px 16px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  logoutBtn: { padding: '8px 16px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '16px' },
  statCard: { backgroundColor: 'white', padding: '16px', borderRadius: '12px', textAlign: 'center' },
  section: { backgroundColor: 'white', padding: '16px', borderRadius: '12px', marginBottom: '16px' },
  sectionTitle: { fontSize: '18px', margin: '0 0 12px 0' },
  emptyText: { color: '#999', textAlign: 'center' },
  projectList: { display: 'flex', flexDirection: 'column', gap: '8px' },
  projectItem: { display: 'flex', justifyContent: 'space-between', padding: '10px 12px', backgroundColor: '#f8f9fa', borderRadius: '6px', alignItems: 'center' },
  techBadge: { backgroundColor: '#e3f2fd', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', color: '#1565c0' },
  activeBadge: { color: '#4CAF50', fontWeight: '500' },
  draftBadge: { color: '#FFC107', fontWeight: '500' },
  tabs: { display: 'flex', gap: '5px', marginBottom: '16px', backgroundColor: 'white', padding: '10px', borderRadius: '12px', flexWrap: 'wrap' },
  tabBtn: { padding: '10px 20px', backgroundColor: 'transparent', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '14px', fontWeight: '500', color: '#666' },
  tabActive: { backgroundColor: '#1a237e', color: 'white' },
  content: { backgroundColor: 'white', padding: '20px', borderRadius: '12px', minHeight: '150px' },
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', fontSize: '18px', color: '#666' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  modal: { backgroundColor: 'white', padding: '30px', borderRadius: '12px', width: '500px', maxWidth: '90%', maxHeight: '90%', overflowY: 'auto' },
  input: { width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', marginBottom: '10px', boxSizing: 'border-box' },
  textarea: { width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '6px', fontSize: '14px', marginBottom: '10px', boxSizing: 'border-box', fontFamily: 'Arial' },
  row: { display: 'flex', justifyContent: 'space-between' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' },
  cancelBtn: { padding: '10px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  submitBtn: { padding: '10px 20px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' },
  error: { backgroundColor: '#ffebee', color: '#c62828', padding: '10px', borderRadius: '6px', marginBottom: '10px' },
};

export default Dashboard;
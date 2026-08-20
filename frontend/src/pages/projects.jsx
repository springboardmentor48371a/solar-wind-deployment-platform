import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Background from '../components/Background';

const API_URL = 'http://localhost:8000/api';

function Projects() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    project_name: '',
    description: '',
    technology: 'SOLAR',
    budget: 0
  });
  const [error, setError] = useState('');
  const [stats, setStats] = useState({ total: 0, solar: 0, wind: 0, hybrid: 0 });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
      const stats = {
        total: response.data.length,
        solar: response.data.filter(p => p.technology === 'SOLAR').length,
        wind: response.data.filter(p => p.technology === 'WIND').length,
        hybrid: response.data.filter(p => p.technology === 'HYBRID').length
      };
      setStats(stats);
    } catch (err) {
      console.error(err);
      if (err.response?.status === 401) navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/projects`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({ project_name: '', description: '', technology: 'SOLAR', budget: 0 });
      fetchProjects();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create project');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this project?')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${API_URL}/projects/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchProjects();
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (loading) return <div style={styles.loading}>Loading...</div>;

  return (
    <>
      <Background />
      <div style={styles.container}>
        <div style={styles.header}>
          <div>
            <h1 style={styles.title}>🌞 Solar & Wind Intelligence</h1>
            <p style={styles.subtitle}>AI-powered renewable energy deployment</p>
          </div>
          <div style={styles.headerActions}>
            <span style={styles.userName}>👋 {user.name || 'User'}</span>
            <button onClick={() => navigate('/dashboard')} style={styles.dashboardBtn}>📊 Dashboard</button>
            <button onClick={handleLogout} style={styles.logoutBtn}>Logout</button>
          </div>
        </div>

        <div style={styles.statsGrid}>
          <div style={styles.statCard}><h3>{stats.total}</h3><p>Total Projects</p></div>
          <div style={styles.statCard}><h3>{stats.solar}</h3><p>☀️ Solar</p></div>
          <div style={styles.statCard}><h3>{stats.wind}</h3><p>💨 Wind</p></div>
          <div style={styles.statCard}><h3>{stats.hybrid}</h3><p>⚡ Hybrid</p></div>
        </div>

        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>📋 Projects</h2>
          <button onClick={() => setShowModal(true)} style={styles.addButton}>+ New Project</button>
        </div>

        {projects.length === 0 ? (
          <div style={styles.emptyState}>No projects yet. Create one!</div>
        ) : (
          <div style={styles.grid}>
            {projects.map(proj => (
              <div key={proj.id} style={styles.card}>
                <div style={styles.cardHeader}>
                  <h3>{proj.project_name}</h3>
                  <span style={styles.techBadge}>{proj.technology}</span>
                </div>
                <p style={styles.cardDesc}>{proj.description || 'No description'}</p>
                <div style={styles.cardFooter}>
                  <span style={styles.statusBadge}>{proj.status}</span>
                  <span>💰 ${proj.budget?.toLocaleString()}</span>
                </div>
                <div style={styles.cardActions}>
                  <button onClick={() => navigate(`/projects/${proj.id}/sites`)} style={styles.viewBtn}>📍 Sites</button>
                  <button onClick={() => handleDelete(proj.id)} style={styles.deleteBtn}>🗑️</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {showModal && (
          <div style={styles.modalOverlay}>
            <div style={styles.modal}>
              <h2>Create Project</h2>
              {error && <div style={styles.error}>{error}</div>}
              <form onSubmit={handleSubmit}>
                <input placeholder="Project Name" value={formData.project_name} onChange={e => setFormData({...formData, project_name: e.target.value})} required style={styles.input} />
                <textarea placeholder="Description" value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} rows="2" style={styles.textarea} />
                <select value={formData.technology} onChange={e => setFormData({...formData, technology: e.target.value})} style={styles.input}>
                  <option value="SOLAR">☀️ Solar</option>
                  <option value="WIND">💨 Wind</option>
                  <option value="HYBRID">⚡ Hybrid</option>
                </select>
                <input type="number" placeholder="Budget ($)" value={formData.budget} onChange={e => setFormData({...formData, budget: parseFloat(e.target.value)})} style={styles.input} />
                <div style={styles.modalActions}>
                  <button type="button" onClick={() => setShowModal(false)} style={styles.cancelBtn}>Cancel</button>
                  <button type="submit" style={styles.submitBtn}>Create</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

const styles = {
  container: { position: 'relative', zIndex: 1, maxWidth: '1400px', margin: '0 auto', padding: '20px', minHeight: '100vh', color: '#fff' },
  loading: { display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: '#fff', fontSize: '20px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 24px', background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(12px)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.08)', marginBottom: '24px' },
  title: { fontSize: '28px', fontWeight: '600', margin: 0 },
  subtitle: { color: 'rgba(255,255,255,0.6)', margin: 0 },
  headerActions: { display: 'flex', gap: '12px', alignItems: 'center' },
  userName: { color: 'rgba(255,255,255,0.8)' },
  dashboardBtn: { padding: '8px 16px', background: 'rgba(25,118,210,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  logoutBtn: { padding: '8px 16px', background: 'rgba(220,53,69,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '16px', marginBottom: '24px' },
  statCard: { background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '20px', textAlign: 'center' },
  sectionHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' },
  sectionTitle: { fontSize: '22px' },
  addButton: { padding: '10px 20px', background: 'rgba(76,175,80,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '20px' },
  card: { background: 'rgba(255,255,255,0.05)', backdropFilter: 'blur(8px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '16px', padding: '20px' },
  cardHeader: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' },
  techBadge: { background: 'rgba(100,200,255,0.2)', padding: '4px 12px', borderRadius: '20px', fontSize: '12px' },
  cardDesc: { color: 'rgba(255,255,255,0.7)', marginBottom: '12px' },
  cardFooter: { display: 'flex', justifyContent: 'space-between', fontSize: '14px', color: 'rgba(255,255,255,0.6)' },
  statusBadge: { background: 'rgba(255,193,7,0.2)', padding: '4px 12px', borderRadius: '20px', fontSize: '12px' },
  cardActions: { display: 'flex', gap: '10px', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid rgba(255,255,255,0.05)' },
  viewBtn: { flex: 1, padding: '8px', background: 'rgba(25,118,210,0.5)', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  deleteBtn: { padding: '8px 12px', background: 'rgba(220,53,69,0.5)', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  emptyState: { padding: '50px', textAlign: 'center', background: 'rgba(255,255,255,0.03)', borderRadius: '16px', color: 'rgba(255,255,255,0.5)' },
  modalOverlay: { position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 },
  modal: { background: 'rgba(20,30,50,0.9)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '20px', padding: '30px', width: '500px', maxWidth: '90%', maxHeight: '90%', overflowY: 'auto', color: '#fff' },
  input: { width: '100%', padding: '12px', marginBottom: '12px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', boxSizing: 'border-box' },
  textarea: { width: '100%', padding: '12px', marginBottom: '12px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#fff', fontFamily: 'inherit', boxSizing: 'border-box' },
  modalActions: { display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' },
  cancelBtn: { padding: '10px 20px', background: 'rgba(108,117,125,0.5)', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  submitBtn: { padding: '10px 20px', background: 'rgba(76,175,80,0.6)', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer' },
  error: { background: 'rgba(220,53,69,0.2)', padding: '10px', borderRadius: '8px', marginBottom: '12px', color: '#ff6b6b' },
};

export default Projects;
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

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
  const [stats, setStats] = useState({
    total: 0,
    solar: 0,
    wind: 0,
    hybrid: 0
  });

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
      console.error('Error fetching projects:', err);
      if (err.response?.status === 401) {
        navigate('/login');
      }
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
    if (window.confirm('Are you sure you want to delete this project?')) {
      try {
        const token = localStorage.getItem('token');
        await axios.delete(`${API_URL}/projects/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        fetchProjects();
      } catch (err) {
        console.error('Error deleting project:', err);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  if (loading) {
    return <div style={styles.loading}>Loading projects...</div>;
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>🌞 Solar & Wind Deployment Intelligence</h1>
          <p style={styles.subtitle}>AI-powered renewable energy site selection platform</p>
        </div>
        <div style={styles.headerActions}>
          <span style={styles.userName}>👋 {JSON.parse(localStorage.getItem('user') || '{}').name || 'User'}</span>
          <button onClick={handleLogout} style={styles.logoutButton}>Logout</button>
        </div>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.total}</h3>
          <p style={styles.statLabel}>Total Projects</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.solar}</h3>
          <p style={styles.statLabel}>Solar Projects</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.wind}</h3>
          <p style={styles.statLabel}>Wind Projects</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.hybrid}</h3>
          <p style={styles.statLabel}>Hybrid Projects</p>
        </div>
      </div>

      {/* Projects Section */}
      <div style={styles.sectionHeader}>
        <h2 style={styles.sectionTitle}>📋 Projects</h2>
        <button onClick={() => setShowModal(true)} style={styles.addButton}>
          + New Project
        </button>
      </div>

      {projects.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No projects yet. Create your first project to get started!</p>
        </div>
      ) : (
        <div style={styles.grid}>
          {projects.map((project) => (
            <div key={project.id} style={styles.card}>
              <div style={styles.cardHeader}>
                <h3 style={styles.cardTitle}>{project.project_name}</h3>
                <span style={styles.technologyBadge}>{project.technology}</span>
              </div>
              <p style={styles.cardDescription}>{project.description || 'No description'}</p>
              <div style={styles.cardFooter}>
                <span style={styles.statusBadge}>{project.status}</span>
                <span style={styles.budget}>💰 ${project.budget?.toLocaleString()}</span>
              </div>
              <div style={styles.cardActions}>
                <button 
                  onClick={() => navigate(`/projects/${project.id}/sites`)} 
                  style={styles.viewButton}
                >
                  📍 View Sites
                </button>
                <button 
                  onClick={() => handleDelete(project.id)} 
                  style={styles.deleteButton}
                >
                  🗑️ Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Project Modal */}
      {showModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h2 style={styles.modalTitle}>Create New Project</h2>
            {error && <div style={styles.error}>{error}</div>}
            <form onSubmit={handleSubmit}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Project Name *</label>
                <input
                  type="text"
                  value={formData.project_name}
                  onChange={(e) => setFormData({...formData, project_name: e.target.value})}
                  required
                  style={styles.input}
                  placeholder="Enter project name"
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  style={styles.textarea}
                  rows="3"
                  placeholder="Describe your project"
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Technology</label>
                <select
                  value={formData.technology}
                  onChange={(e) => setFormData({...formData, technology: e.target.value})}
                  style={styles.select}
                >
                  <option value="SOLAR">☀️ Solar</option>
                  <option value="WIND">💨 Wind</option>
                  <option value="HYBRID">⚡ Hybrid</option>
                </select>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Budget ($)</label>
                <input
                  type="number"
                  value={formData.budget}
                  onChange={(e) => setFormData({...formData, budget: parseFloat(e.target.value)})}
                  style={styles.input}
                  placeholder="Enter budget"
                />
              </div>
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowModal(false)} style={styles.cancelButton}>
                  Cancel
                </button>
                <button type="submit" style={styles.submitButton}>
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    maxWidth: '1400px',
    margin: '0 auto',
    fontFamily: 'Arial, sans-serif',
    minHeight: '100vh',
    backgroundColor: '#f5f7fa'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
    padding: '20px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.05)'
  },
  title: {
    fontSize: '28px',
    color: '#1a237e',
    margin: 0
  },
  subtitle: {
    color: '#666',
    margin: '5px 0 0 0',
    fontSize: '14px'
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px'
  },
  userName: {
    fontSize: '16px',
    color: '#333'
  },
  logoutButton: {
    padding: '8px 16px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '20px',
    marginBottom: '30px'
  },
  statCard: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
    textAlign: 'center'
  },
  statNumber: {
    fontSize: '32px',
    margin: 0,
    color: '#1a237e'
  },
  statLabel: {
    color: '#666',
    margin: '5px 0 0 0',
    fontSize: '14px'
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px'
  },
  sectionTitle: {
    fontSize: '22px',
    color: '#333',
    margin: 0
  },
  addButton: {
    padding: '10px 24px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
    gap: '20px'
  },
  card: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '12px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
    border: '1px solid #e9ecef'
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px'
  },
  cardTitle: {
    fontSize: '18px',
    margin: 0,
    color: '#333'
  },
  technologyBadge: {
    padding: '4px 12px',
    backgroundColor: '#e3f2fd',
    borderRadius: '20px',
    fontSize: '12px',
    color: '#1565c0'
  },
  cardDescription: {
    color: '#666',
    marginBottom: '15px',
    fontSize: '14px'
  },
  cardFooter: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '14px',
    color: '#666'
  },
  statusBadge: {
    padding: '4px 12px',
    backgroundColor: '#fff3cd',
    borderRadius: '20px',
    fontSize: '12px',
    color: '#856404'
  },
  budget: {
    fontSize: '14px'
  },
  cardActions: {
    display: 'flex',
    gap: '10px',
    marginTop: '15px',
    paddingTop: '15px',
    borderTop: '1px solid #e9ecef'
  },
  viewButton: {
    padding: '8px 16px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    flex: 1
  },
  deleteButton: {
    padding: '8px 16px',
    backgroundColor: '#dc3545',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    flex: 1
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000
  },
  modal: {
    backgroundColor: 'white',
    padding: '30px',
    borderRadius: '12px',
    width: '500px',
    maxWidth: '90%',
    maxHeight: '90%',
    overflowY: 'auto'
  },
  modalTitle: {
    fontSize: '24px',
    marginBottom: '20px',
    color: '#333'
  },
  formGroup: {
    marginBottom: '15px'
  },
  label: {
    display: 'block',
    marginBottom: '5px',
    fontWeight: '500',
    color: '#333'
  },
  input: {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px'
  },
  textarea: {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
    fontFamily: 'Arial, sans-serif',
    resize: 'vertical'
  },
  select: {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px'
  },
  modalActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '10px',
    marginTop: '20px'
  },
  cancelButton: {
    padding: '10px 20px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
  },
  submitButton: {
    padding: '10px 20px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer'
  },
  loading: {
    textAlign: 'center',
    padding: '50px',
    fontSize: '18px',
    color: '#666'
  },
  emptyState: {
    textAlign: 'center',
    padding: '50px',
    backgroundColor: 'white',
    borderRadius: '12px',
    color: '#666'
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '10px',
    borderRadius: '6px',
    marginBottom: '15px'
  }
};

export default Projects;
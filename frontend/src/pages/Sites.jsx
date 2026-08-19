import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function Sites() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [sites, setSites] = useState([]);
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    site_name: '',
    latitude: '',
    longitude: '',
    region: '',
    land_area: '',
    elevation: '',
    land_ownership: '',
    existing_infrastructure: ''
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (projectId) {
      fetchProject();
      fetchSites();
    }
  }, [projectId]);

  const fetchProject = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProject(response.data);
    } catch (err) {
      console.error('Error fetching project:', err);
    }
  };

  const fetchSites = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/sites?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSites(response.data);
    } catch (err) {
      console.error('Error fetching sites:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_URL}/sites`, {
        ...formData,
        project_id: parseInt(projectId)
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setShowModal(false);
      setFormData({
        site_name: '',
        latitude: '',
        longitude: '',
        region: '',
        land_area: '',
        elevation: '',
        land_ownership: '',
        existing_infrastructure: ''
      });
      fetchSites();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create site');
    }
  };

  if (loading) {
    return <div style={styles.loading}>Loading sites...</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <button onClick={() => navigate('/projects')} style={styles.backButton}>
            ← Back to Projects
          </button>
          <h1 style={styles.title}>{project?.project_name} - Sites</h1>
        </div>
        <button onClick={() => setShowModal(true)} style={styles.addButton}>
          + New Site
        </button>
      </div>

      {sites.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No sites registered yet. Add your first site!</p>
        </div>
      ) : (
        <div style={styles.grid}>
          {sites.map((site) => (
            <div key={site.id} style={styles.card}>
              <h3 style={styles.cardTitle}>{site.site_name}</h3>
              <div style={styles.coordinates}>
                <span>📍 {site.latitude}, {site.longitude}</span>
              </div>
              <div style={styles.siteDetails}>
                {site.region && <span>🏷️ {site.region}</span>}
                {site.land_area && <span>📐 {site.land_area} acres</span>}
                {site.elevation && <span>⛰️ {site.elevation}m</span>}
              </div>
              <div style={styles.cardActions}>
                <button 
                  onClick={() => navigate(`/sites/${site.id}/analyze`)} 
                  style={styles.analyzeButton}
                >
                  Analyze Site
                </button>
                <button 
                  onClick={() => navigate(`/sites/${site.id}`)} 
                  style={styles.viewButton}
                >
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h2 style={styles.modalTitle}>Register New Site</h2>
            {error && <div style={styles.error}>{error}</div>}
            <form onSubmit={handleSubmit}>
              <div style={styles.formGroup}>
                <label style={styles.label}>Site Name *</label>
                <input
                  type="text"
                  value={formData.site_name}
                  onChange={(e) => setFormData({...formData, site_name: e.target.value})}
                  required
                  style={styles.input}
                />
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Latitude *</label>
                  <input
                    type="number"
                    step="0.000001"
                    value={formData.latitude}
                    onChange={(e) => setFormData({...formData, latitude: parseFloat(e.target.value)})}
                    required
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Longitude *</label>
                  <input
                    type="number"
                    step="0.000001"
                    value={formData.longitude}
                    onChange={(e) => setFormData({...formData, longitude: parseFloat(e.target.value)})}
                    required
                    style={styles.input}
                  />
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Region</label>
                <input
                  type="text"
                  value={formData.region}
                  onChange={(e) => setFormData({...formData, region: e.target.value})}
                  style={styles.input}
                />
              </div>
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Land Area (acres)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.land_area}
                    onChange={(e) => setFormData({...formData, land_area: parseFloat(e.target.value)})}
                    style={styles.input}
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Elevation (m)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.elevation}
                    onChange={(e) => setFormData({...formData, elevation: parseFloat(e.target.value)})}
                    style={styles.input}
                  />
                </div>
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Land Ownership</label>
                <input
                  type="text"
                  value={formData.land_ownership}
                  onChange={(e) => setFormData({...formData, land_ownership: e.target.value})}
                  style={styles.input}
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Existing Infrastructure</label>
                <textarea
                  value={formData.existing_infrastructure}
                  onChange={(e) => setFormData({...formData, existing_infrastructure: e.target.value})}
                  style={styles.textarea}
                  rows="2"
                  placeholder="e.g., roads, power lines, etc."
                />
              </div>
              <div style={styles.modalActions}>
                <button type="button" onClick={() => setShowModal(false)} style={styles.cancelButton}>
                  Cancel
                </button>
                <button type="submit" style={styles.submitButton}>
                  Register Site
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
    maxWidth: '1200px',
    margin: '0 auto'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px'
  },
  title: {
    fontSize: '28px',
    color: '#333',
    margin: '10px 0 0 0'
  },
  backButton: {
    padding: '8px 16px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  addButton: {
    padding: '10px 20px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '20px'
  },
  card: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
    border: '1px solid #e9ecef'
  },
  cardTitle: {
    fontSize: '18px',
    margin: '0 0 10px 0',
    color: '#333'
  },
  coordinates: {
    color: '#666',
    fontSize: '14px',
    marginBottom: '10px'
  },
  siteDetails: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '10px',
    marginBottom: '15px',
    fontSize: '14px',
    color: '#495057'
  },
  cardActions: {
    display: 'flex',
    gap: '10px',
    marginTop: '15px',
    paddingTop: '15px',
    borderTop: '1px solid #e9ecef'
  },
  analyzeButton: {
    padding: '6px 12px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    flex: 1
  },
  viewButton: {
    padding: '6px 12px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
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
    borderRadius: '8px',
    width: '600px',
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
  formRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '15px'
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
    borderRadius: '4px',
    fontSize: '14px'
  },
  textarea: {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    fontSize: '14px',
    fontFamily: 'Arial, sans-serif',
    resize: 'vertical'
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
    borderRadius: '4px',
    cursor: 'pointer'
  },
  submitButton: {
    padding: '10px 20px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
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
    backgroundColor: '#f8f9fa',
    borderRadius: '8px',
    color: '#666'
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '10px',
    borderRadius: '4px',
    marginBottom: '15px'
  }
};

export default Sites; 
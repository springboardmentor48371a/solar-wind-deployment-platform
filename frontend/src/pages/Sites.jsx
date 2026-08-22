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
  const [geocoding, setGeocoding] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    site_name: '',
    location: '',
    latitude: '',
    longitude: '',
    region: '',
    land_area: '',
    elevation: '',
    land_ownership: '',
    existing_infrastructure: ''
  });

  useEffect(() => {
    if (projectId) {
      fetchProject();
      fetchSites();
    }
  }, [projectId]);

  const fetchProject = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/projects/${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProject(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchSites = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/sites?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSites(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 🔥 Fetch coordinates from location name
  const fetchCoordinates = async () => {
    if (!formData.location.trim()) {
      setError('Please enter a location name first.');
      return;
    }

    setGeocoding(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(
        `${API_URL}/geocode`,
        { location: formData.location },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (res.data.latitude && res.data.longitude) {
        setFormData(prev => ({
          ...prev,
          latitude: res.data.latitude,
          longitude: res.data.longitude,
          region: res.data.display_name || prev.region
        }));
        setError('✅ Coordinates found!');
      } else {
        setError('❌ Location not found. Please try again.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch coordinates');
    } finally {
      setGeocoding(false);
    }
  };

  const handleSubmit = async (e) => {
  e.preventDefault();
  setError('');

  // Validate coordinates
  if (!formData.latitude || !formData.longitude) {
    setError('Please fetch coordinates from location name first.');
    return;
  }

  const payload = {
    project_id: parseInt(projectId) || null,
    site_name: formData.site_name.trim(),
    latitude: parseFloat(formData.latitude),
    longitude: parseFloat(formData.longitude),
    region: formData.region || null,
    land_area: parseFloat(formData.land_area) || 0,
    elevation: parseFloat(formData.elevation) || 0,
    land_ownership: formData.land_ownership || null,
    existing_infrastructure: formData.existing_infrastructure || null
  };

  try {
    const token = localStorage.getItem('token');
    await axios.post(`${API_URL}/sites`, payload, {
      headers: { Authorization: `Bearer ${token}` }
    });
    setShowModal(false);
    setFormData(initialState);
    fetchSites();
    setError(''); 
    await fetchSites();
    alert('Site created successfully!');
  } catch (err) {
    setError(err.response?.data?.detail || 'Failed to create site');
  }
};
  if (loading) return <div style={styles.loading}>Loading sites...</div>;

  return (
    <div style={styles.container}>
      {/* Header */}
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

      {/* Site Cards */}
      {sites.length === 0 ? (
        <div style={styles.emptyState}>
          <p>No sites registered yet. Add your first site!</p>
        </div>
      ) : (
        <div style={styles.grid}>
          {sites.map(site => (
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
                <button onClick={() => navigate(`/sites/${site.id}/analyze`)} style={styles.analyzeButton}>
                  Analyze Site
                </button>
                <button onClick={() => navigate(`/sites/${site.id}`)} style={styles.viewButton}>
                  View Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ========================================================= */}
      {/* REGISTER SITE MODAL – with Location Auto-Fill */}
      {/* ========================================================= */}
      {showModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h2 style={styles.modalTitle}>📌 Register New Site</h2>
            {error && <div style={styles.error}>{error}</div>}

            <form onSubmit={handleSubmit}>
              {/* Site Name */}
              <div style={styles.formGroup}>
                <label style={styles.label}>Site Name *</label>
                <input
                  type="text"
                  value={formData.site_name}
                  onChange={(e) => setFormData({ ...formData, site_name: e.target.value })}
                  required
                  style={styles.input}
                  placeholder="Enter site name"
                />
              </div>

              {/* Location + Get Coordinates */}
              <div style={styles.formGroup}>
                <label style={styles.label}>📍 Location Name *</label>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    required
                    style={{ ...styles.input, flex: 1 }}
                    placeholder="e.g., Hyderabad, India"
                  />
                  <button
                    type="button"
                    onClick={fetchCoordinates}
                    disabled={geocoding || !formData.location.trim()}
                    style={styles.geocodeButton}
                  >
                    {geocoding ? '⏳ Fetching...' : '🔍 Get Coordinates'}
                  </button>
                </div>
                <small style={{ color: '#666', display: 'block', marginTop: '5px' }}>
                  Type a location and click "Get Coordinates" to auto-fill lat/lon.
                </small>
              </div>

              {/* Latitude & Longitude (auto-filled, read-only) */}
              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Latitude *</label>
                  <input
                    type="text"
                    value={formData.latitude}
                    onChange={(e) => setFormData({ ...formData, latitude: e.target.value })}
                    required
                    style={{ ...styles.input, background: '#f0f0f0' }}
                    placeholder="Auto-filled"
                    readOnly
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Longitude *</label>
                  <input
                    type="text"
                    value={formData.longitude}
                    onChange={(e) => setFormData({ ...formData, longitude: e.target.value })}
                    required
                    style={{ ...styles.input, background: '#f0f0f0' }}
                    placeholder="Auto-filled"
                    readOnly
                  />
                </div>
              </div>

              {/* Other Fields */}
              <div style={styles.formGroup}>
                <label style={styles.label}>Region</label>
                <input
                  type="text"
                  value={formData.region}
                  onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  style={styles.input}
                  placeholder="Region"
                />
              </div>

              <div style={styles.formRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Land Area (acres)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.land_area}
                    onChange={(e) => setFormData({ ...formData, land_area: e.target.value })}
                    style={styles.input}
                    placeholder="Land area"
                  />
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Elevation (m)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={formData.elevation}
                    onChange={(e) => setFormData({ ...formData, elevation: e.target.value })}
                    style={styles.input}
                    placeholder="Elevation"
                  />
                </div>
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Land Ownership</label>
                <input
                  type="text"
                  value={formData.land_ownership}
                  onChange={(e) => setFormData({ ...formData, land_ownership: e.target.value })}
                  style={styles.input}
                  placeholder="Land ownership"
                />
              </div>

              <div style={styles.formGroup}>
                <label style={styles.label}>Existing Infrastructure</label>
                <textarea
                  value={formData.existing_infrastructure}
                  onChange={(e) => setFormData({ ...formData, existing_infrastructure: e.target.value })}
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

// ============================================
// STYLES
// ============================================
const styles = {
  container: {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto',
    fontFamily: 'Arial, sans-serif',
    minHeight: '100vh',
    backgroundColor: '#f5f7fa'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px'
  },
  title: {
    fontSize: '28px',
    color: '#1a237e',
    margin: '10px 0 0 0'
  },
  backButton: {
    padding: '8px 16px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px'
  },
  addButton: {
    padding: '10px 20px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
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
    borderRadius: '12px',
    boxShadow: '0 2px 10px rgba(0,0,0,0.05)',
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
    borderRadius: '12px',
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
    borderRadius: '6px',
    fontSize: '14px',
    boxSizing: 'border-box'
  },
  textarea: {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
    fontFamily: 'Arial, sans-serif',
    resize: 'vertical',
    boxSizing: 'border-box'
  },
  geocodeButton: {
    padding: '10px 16px',
    backgroundColor: '#1976d2',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '14px',
    whiteSpace: 'nowrap'
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

export default Sites;
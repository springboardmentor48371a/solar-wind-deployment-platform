import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const initialState = {
  site_name: '',
  location: '',
  latitude: '',
  longitude: '',
  region: '',
  land_area: '',
  elevation: '',
  land_ownership: '',
  existing_infrastructure: ''
};

function Sites() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [sites, setSites] = useState([]);
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

  const [showModal, setShowModal] = useState(false);
  const [geocoding, setGeocoding] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState('');
  const [formData, setFormData] = useState(initialState);

  useEffect(() => {
    if (projectId) {
      fetchProject();
      fetchSites();
    }
  }, [projectId]);

  // ================================
  // FETCH PROJECT
  // ================================
  const fetchProject = async () => {
    try {
      const token = localStorage.getItem('token');

      const res = await axios.get(
        `${API_URL}/projects/${projectId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setProject(res.data);
    } catch (err) {
      console.error('Project error:', err);
    }
  };

  // ================================
  // FETCH SITES
  // ================================
  const fetchSites = async () => {
    try {
      const token = localStorage.getItem('token');

      const res = await axios.get(
        `${API_URL}/sites?project_id=${projectId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      setSites(res.data);
    } catch (err) {
      console.error('Sites error:', err);
    } finally {
      setLoading(false);
    }
  };

  // ================================
  // GET COORDINATES + ELEVATION
  // ================================
  const fetchCoordinates = async () => {
    if (!formData.location.trim()) {
      setError('Please enter a location first.');
      return;
    }

    setGeocoding(true);
    setError('');

    try {
      const token = localStorage.getItem('token');

      const res = await axios.post(
        `${API_URL}/geocode`,
        {
          location: formData.location.trim()
        },
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      const data = res.data;

      if (
        data.latitude === undefined ||
        data.longitude === undefined
      ) {
        setError('Location not found.');
        return;
      }

      setFormData(prev => ({
        ...prev,

        // Automatic coordinates
        latitude: data.latitude,
        longitude: data.longitude,

        // Automatic elevation
        elevation:
          data.elevation !== undefined &&
          data.elevation !== null
            ? data.elevation
            : '',

        // Automatic region/address
        region:
          data.display_name ||
          prev.region
      }));

      setError(
        `✅ Location found: ${data.latitude}, ${data.longitude}` +
        (
          data.elevation !== undefined
            ? ` | Elevation: ${data.elevation} m`
            : ''
        )
      );

    } catch (err) {
      console.error('Geocoding error:', err);

      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to fetch location information.'
      );
    } finally {
      setGeocoding(false);
    }
  };

  // ================================
  // CREATE SITE
  // ================================
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.site_name.trim()) {
      setError('Please enter a site name.');
      return;
    }

    if (
      formData.latitude === '' ||
      formData.longitude === ''
    ) {
      setError('Please click "Get Coordinates" first.');
      return;
    }

    setSaving(true);

    try {
      const token = localStorage.getItem('token');

      const payload = {
        project_id: parseInt(projectId),

        site_name: formData.site_name.trim(),

        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),

        region: formData.region || null,

        land_area:
          formData.land_area !== ''
            ? parseFloat(formData.land_area)
            : 0,

        elevation:
          formData.elevation !== ''
            ? parseFloat(formData.elevation)
            : 0,

        land_ownership:
          formData.land_ownership || null,

        existing_infrastructure:
          formData.existing_infrastructure || null
      };

      console.log('Creating site:', payload);

      await axios.post(
        `${API_URL}/sites`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      setShowModal(false);
      setFormData(initialState);

      await fetchSites();

      alert('✅ Site created successfully!');

    } catch (err) {
      console.error('Create site error:', err);

      setError(
        err.response?.data?.detail ||
        err.response?.data?.error ||
        'Failed to create site.'
      );
    } finally {
      setSaving(false);
    }
  };

  // ================================
  // OPEN NEW SITE MODAL
  // ================================
  const openNewSite = () => {
    setFormData(initialState);
    setError('');
    setShowModal(true);
  };

  // ================================
  // LOADING
  // ================================
  if (loading) {
    return (
      <div style={styles.loading}>
        Loading sites...
      </div>
    );
  }

  // ================================
  // UI
  // ================================
  return (
    <div style={styles.container}>

      {/* HEADER */}
      <div style={styles.header}>

        <div>
          <button
            onClick={() => navigate('/projects')}
            style={styles.backButton}
          >
            ← Back to Projects
          </button>

          <h1 style={styles.title}>
            {project?.project_name || 'Project'} - Sites
          </h1>
        </div>

        <button
          onClick={openNewSite}
          style={styles.addButton}
        >
          + New Site
        </button>

      </div>

      {/* SITES */}
      {sites.length === 0 ? (

        <div style={styles.emptyState}>
          <p>
            No sites registered yet. Add your first site!
          </p>
        </div>

      ) : (

        <div style={styles.grid}>

          {sites.map(site => (

            <div
              key={site.id}
              style={styles.card}
            >

              <h3 style={styles.cardTitle}>
                {site.site_name}
              </h3>

              <div style={styles.coordinates}>
                📍 {site.latitude}, {site.longitude}
              </div>

              <div style={styles.siteDetails}>

                {site.region && (
                  <span>
                    🏷️ {site.region}
                  </span>
                )}

                {site.land_area !== undefined &&
                  site.land_area !== null && (
                    <span>
                      📐 {site.land_area} acres
                    </span>
                  )}

                {site.elevation !== undefined &&
                  site.elevation !== null && (
                    <span>
                      ⛰️ {site.elevation} m
                    </span>
                  )}

              </div>

              <div style={styles.cardActions}>

                <button
                  onClick={() =>
                    navigate(`/sites/${site.id}`)
                  }
                  style={styles.analyzeButton}
                >
                  🔬 Analyze Site
                </button>

                <button
                  onClick={() =>
                    navigate(`/sites/${site.id}`)
                  }
                  style={styles.viewButton}
                >
                  View Details
                </button>

              </div>

            </div>

          ))}

        </div>

      )}

      {/* ================================
          NEW SITE MODAL
      ================================= */}

      {showModal && (

        <div style={styles.modalOverlay}>

          <div style={styles.modal}>

            <h2 style={styles.modalTitle}>
              📌 Register New Site
            </h2>

            {error && (
              <div style={styles.error}>
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>

              {/* SITE NAME */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  Site Name *
                </label>

                <input
                  type="text"
                  value={formData.site_name}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      site_name: e.target.value
                    })
                  }
                  required
                  style={styles.input}
                  placeholder="e.g. Hyderabad Solar Site"
                />

              </div>

              {/* LOCATION */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  📍 Location *
                </label>

                <div style={styles.locationRow}>

                  <input
                    type="text"
                    value={formData.location}
                    onChange={e =>
                      setFormData({
                        ...formData,
                        location: e.target.value
                      })
                    }
                    required
                    style={{
                      ...styles.input,
                      flex: 1
                    }}
                    placeholder="e.g. Hyderabad, India"
                  />

                  <button
                    type="button"
                    onClick={fetchCoordinates}
                    disabled={
                      geocoding ||
                      !formData.location.trim()
                    }
                    style={styles.geocodeButton}
                  >
                    {geocoding
                      ? '⏳ Fetching...'
                      : '🔍 Get Coordinates'}
                  </button>

                </div>

                <small style={styles.helpText}>
                  Enter a location and click Get Coordinates.
                  Latitude, longitude and elevation will be
                  filled automatically.
                </small>

              </div>

              {/* LATITUDE + LONGITUDE */}
              <div style={styles.formRow}>

                <div style={styles.formGroup}>

                  <label style={styles.label}>
                    Latitude *
                  </label>

                  <input
                    type="number"
                    step="any"
                    value={formData.latitude}
                    readOnly
                    required
                    style={styles.readOnlyInput}
                    placeholder="Auto-filled"
                  />

                </div>

                <div style={styles.formGroup}>

                  <label style={styles.label}>
                    Longitude *
                  </label>

                  <input
                    type="number"
                    step="any"
                    value={formData.longitude}
                    readOnly
                    required
                    style={styles.readOnlyInput}
                    placeholder="Auto-filled"
                  />

                </div>

              </div>

              {/* ELEVATION */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  ⛰️ Elevation (m)
                </label>

                <input
                  type="number"
                  step="0.1"
                  value={formData.elevation}
                  readOnly
                  style={styles.readOnlyInput}
                  placeholder="Automatically calculated"
                />

              </div>

              {/* REGION */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  Region
                </label>

                <input
                  type="text"
                  value={formData.region}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      region: e.target.value
                    })
                  }
                  style={styles.input}
                  placeholder="Automatically filled"
                />

              </div>

              {/* LAND AREA */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  Land Area (acres)
                </label>

                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formData.land_area}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      land_area: e.target.value
                    })
                  }
                  style={styles.input}
                  placeholder="e.g. 100"
                />

              </div>

              {/* LAND OWNERSHIP */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  Land Ownership
                </label>

                <input
                  type="text"
                  value={formData.land_ownership}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      land_ownership: e.target.value
                    })
                  }
                  style={styles.input}
                  placeholder="e.g. Private / Government"
                />

              </div>

              {/* INFRASTRUCTURE */}
              <div style={styles.formGroup}>

                <label style={styles.label}>
                  Existing Infrastructure
                </label>

                <textarea
                  value={formData.existing_infrastructure}
                  onChange={e =>
                    setFormData({
                      ...formData,
                      existing_infrastructure:
                        e.target.value
                    })
                  }
                  style={styles.textarea}
                  rows="3"
                  placeholder="e.g. road, power line, substation..."
                />

              </div>

              {/* BUTTONS */}
              <div style={styles.modalActions}>

                <button
                  type="button"
                  onClick={() => {
                    setShowModal(false);
                    setError('');
                  }}
                  style={styles.cancelButton}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  disabled={saving}
                  style={{
                    ...styles.submitButton,
                    opacity: saving ? 0.7 : 1
                  }}
                >
                  {saving
                    ? 'Saving...'
                    : 'Register Site'}
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
    gridTemplateColumns:
      'repeat(auto-fill, minmax(300px, 1fr))',
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
    padding: '8px 12px',
    backgroundColor: '#28a745',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    flex: 1
  },

  viewButton: {
    padding: '8px 12px',
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

  locationRow: {
    display: 'flex',
    gap: '10px'
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

  readOnlyInput: {
    width: '100%',
    padding: '10px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    fontSize: '14px',
    boxSizing: 'border-box',
    backgroundColor: '#f0f0f0',
    color: '#333'
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

  helpText: {
    color: '#666',
    display: 'block',
    marginTop: '5px'
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
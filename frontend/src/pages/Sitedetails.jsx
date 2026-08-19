import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function SiteDetails() {
  const { siteId } = useParams();
  const navigate = useNavigate();
  const [site, setSite] = useState(null);
  const [environmentalData, setEnvironmentalData] = useState(null);
  const [solarData, setSolarData] = useState(null);
  const [windData, setWindData] = useState(null);
  const [suitability, setSuitability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchSiteDetails();
  }, [siteId]);

  const fetchSiteDetails = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Get site details
      const siteRes = await axios.get(`${API_URL}/sites/${siteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSite(siteRes.data);

      // Get environmental data
      try {
        const envRes = await axios.get(`${API_URL}/environmental/${siteId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setEnvironmentalData(envRes.data.data);
      } catch (e) {
        console.log('No environmental data found');
      }

      // Get solar assessment
      try {
        const solarRes = await axios.get(`${API_URL}/solar/assessment/${siteId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSolarData(solarRes.data.data);
      } catch (e) {
        console.log('No solar data found');
      }

      // Get wind assessment
      try {
        const windRes = await axios.get(`${API_URL}/wind/assessment/${siteId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setWindData(windRes.data.data);
      } catch (e) {
        console.log('No wind data found');
      }

      // Get suitability score
      try {
        const suitRes = await axios.get(`${API_URL}/suitability/score/${siteId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSuitability(suitRes.data.data);
      } catch (e) {
        console.log('No suitability data found');
      }

    } catch (err) {
      console.error('Error fetching site details:', err);
    } finally {
      setLoading(false);
    }
  };

  const analyzeSite = async () => {
    setAnalyzing(true);
    try {
      const token = localStorage.getItem('token');
      
      // Step 1: Fetch environmental data
      await axios.get(`${API_URL}/environmental/fetch/${siteId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Step 2: Analyze solar
      await axios.post(`${API_URL}/solar/analyze/${siteId}`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Step 3: Analyze wind
      await axios.post(`${API_URL}/wind/analyze/${siteId}`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Step 4: Analyze suitability
      await axios.post(`${API_URL}/suitability/analyze/${siteId}`, null, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Refresh data
      await fetchSiteDetails();
      alert('✅ Site analysis completed successfully!');
    } catch (err) {
      console.error('Analysis error:', err);
      alert('❌ Analysis failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return <div style={styles.loading}>Loading site details...</div>;
  }

  return (
    <div style={styles.container}>
      <button onClick={() => navigate(-1)} style={styles.backButton}>
        ← Back
      </button>

      {/* Site Info */}
      <div style={styles.header}>
        <h1 style={styles.title}>📍 {site?.site_name}</h1>
        <button 
          onClick={analyzeSite} 
          disabled={analyzing}
          style={styles.analyzeButton}
        >
          {analyzing ? 'Analyzing...' : '🔬 Analyze Site'}
        </button>
      </div>

      <div style={styles.infoGrid}>
        <div style={styles.infoCard}>
          <label>Project</label>
          <p>{site?.project_id}</p>
        </div>
        <div style={styles.infoCard}>
          <label>Coordinates</label>
          <p>{site?.latitude}, {site?.longitude}</p>
        </div>
        <div style={styles.infoCard}>
          <label>Region</label>
          <p>{site?.region || 'N/A'}</p>
        </div>
        <div style={styles.infoCard}>
          <label>Land Area</label>
          <p>{site?.land_area || 'N/A'} acres</p>
        </div>
        <div style={styles.infoCard}>
          <label>Elevation</label>
          <p>{site?.elevation || 'N/A'} m</p>
        </div>
        <div style={styles.infoCard}>
          <label>Land Ownership</label>
          <p>{site?.land_ownership || 'N/A'}</p>
        </div>
      </div>

      {/* Environmental Data */}
      {environmentalData && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>🌍 Environmental Data</h2>
          <div style={styles.dataGrid}>
            <div style={styles.dataItem}>
              <label>Solar Irradiance</label>
              <p>{environmentalData.solar_irradiance} kWh/m²/day</p>
            </div>
            <div style={styles.dataItem}>
              <label>Temperature</label>
              <p>{environmentalData.temperature} °C</p>
            </div>
            <div style={styles.dataItem}>
              <label>Wind Speed</label>
              <p>{environmentalData.wind_speed} m/s</p>
            </div>
            <div style={styles.dataItem}>
              <label>Rainfall</label>
              <p>{environmentalData.rainfall} mm/year</p>
            </div>
            <div style={styles.dataItem}>
              <label>Cloud Cover</label>
              <p>{environmentalData.cloud_cover} %</p>
            </div>
          </div>
        </div>
      )}

      {/* Solar Analysis */}
      {solarData && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>☀️ Solar Potential</h2>
          <div style={styles.dataGrid}>
            <div style={styles.dataItem}>
              <label>Peak Sun Hours</label>
              <p>{solarData.peak_sun_hours} hours</p>
            </div>
            <div style={styles.dataItem}>
              <label>Annual Energy</label>
              <p>{solarData.annual_energy_mwh} MWh</p>
            </div>
            <div style={styles.dataItem}>
              <label>Capacity Factor</label>
              <p>{solarData.capacity_factor} %</p>
            </div>
            <div style={styles.dataItem}>
              <label>Quality Score</label>
              <p>{solarData.quality_score} / 100</p>
            </div>
          </div>
        </div>
      )}

      {/* Wind Analysis */}
      {windData && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>💨 Wind Potential</h2>
          <div style={styles.dataGrid}>
            <div style={styles.dataItem}>
              <label>Avg Wind Speed</label>
              <p>{windData.avg_wind_speed} m/s</p>
            </div>
            <div style={styles.dataItem}>
              <label>Annual Energy</label>
              <p>{windData.annual_energy_mwh} MWh</p>
            </div>
            <div style={styles.dataItem}>
              <label>Capacity Factor</label>
              <p>{windData.capacity_factor} %</p>
            </div>
            <div style={styles.dataItem}>
              <label>Quality Score</label>
              <p>{windData.quality_score} / 100</p>
            </div>
          </div>
        </div>
      )}

      {/* Suitability Score */}
      {suitability && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>🏆 Suitability Score</h2>
          <div style={styles.scoreCard}>
            <div style={styles.scoreMain}>
              <div style={styles.bigScore}>{suitability.overall_score}</div>
              <div style={styles.category}>{suitability.category}</div>
            </div>
            <div style={styles.scoreDetails}>
              <div style={styles.scoreItem}>
                <label>Renewable Resource</label>
                <div style={styles.scoreBar}>
                  <div style={{...styles.scoreFill, width: `${suitability.scores.renewable_resource}%`}} />
                </div>
                <span>{suitability.scores.renewable_resource}%</span>
              </div>
              <div style={styles.scoreItem}>
                <label>Geographic Suitability</label>
                <div style={styles.scoreBar}>
                  <div style={{...styles.scoreFill, width: `${suitability.scores.geographic_suitability}%`}} />
                </div>
                <span>{suitability.scores.geographic_suitability}%</span>
              </div>
              <div style={styles.scoreItem}>
                <label>Infrastructure</label>
                <div style={styles.scoreBar}>
                  <div style={{...styles.scoreFill, width: `${suitability.scores.infrastructure}%`}} />
                </div>
                <span>{suitability.scores.infrastructure}%</span>
              </div>
              <div style={styles.scoreItem}>
                <label>Environmental Impact</label>
                <div style={styles.scoreBar}>
                  <div style={{...styles.scoreFill, width: `${suitability.scores.environmental}%`}} />
                </div>
                <span>{suitability.scores.environmental}%</span>
              </div>
              <div style={styles.scoreItem}>
                <label>Economic Feasibility</label>
                <div style={styles.scoreBar}>
                  <div style={{...styles.scoreFill, width: `${suitability.scores.economic}%`}} />
                </div>
                <span>{suitability.scores.economic}%</span>
              </div>
            </div>
          </div>
          <div style={styles.recommendations}>
            <h4>📌 Recommendations</h4>
            {suitability.recommendations?.map((rec, i) => (
              <p key={i}>• {rec}</p>
            ))}
          </div>
        </div>
      )}

      {/* No Data Message */}
      {!environmentalData && !solarData && !windData && !suitability && (
        <div style={styles.emptyState}>
          <p>No analysis data found. Click "Analyze Site" to run analysis.</p>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    padding: '20px',
    maxWidth: '1200px',
    margin: '0 auto',
    fontFamily: 'Arial, sans-serif',
    backgroundColor: '#f5f7fa',
    minHeight: '100vh'
  },
  backButton: {
    padding: '8px 16px',
    backgroundColor: '#6c757d',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    marginBottom: '20px'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px'
  },
  title: {
    fontSize: '28px',
    color: '#1a237e',
    margin: 0
  },
  analyzeButton: {
    padding: '12px 24px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px'
  },
  infoGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: '15px',
    marginBottom: '30px'
  },
  infoCard: {
    backgroundColor: 'white',
    padding: '15px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
  },
  section: {
    backgroundColor: 'white',
    padding: '20px',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
    marginBottom: '20px'
  },
  sectionTitle: {
    fontSize: '20px',
    color: '#333',
    marginBottom: '15px',
    borderBottom: '2px solid #f0f0f0',
    paddingBottom: '10px'
  },
  dataGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '15px'
  },
  dataItem: {
    padding: '10px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px'
  },
  scoreCard: {
    display: 'grid',
    gridTemplateColumns: '200px 1fr',
    gap: '30px',
    alignItems: 'center'
  },
  scoreMain: {
    textAlign: 'center'
  },
  bigScore: {
    fontSize: '48px',
    fontWeight: 'bold',
    color: '#1a237e'
  },
  category: {
    fontSize: '18px',
    color: '#4CAF50',
    fontWeight: '600'
  },
  scoreDetails: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '15px'
  },
  scoreItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px'
  },
  scoreBar: {
    flex: 1,
    height: '8px',
    backgroundColor: '#e9ecef',
    borderRadius: '4px',
    overflow: 'hidden'
  },
  scoreFill: {
    height: '100%',
    backgroundColor: '#4CAF50',
    borderRadius: '4px'
  },
  recommendations: {
    marginTop: '20px',
    padding: '15px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px'
  },
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: '100vh',
    fontSize: '18px',
    color: '#666'
  },
  emptyState: {
    textAlign: 'center',
    padding: '50px',
    backgroundColor: 'white',
    borderRadius: '8px'
  }
};

export default SiteDetails;
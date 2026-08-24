import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// =========================================================
// ANALYSIS VALUE NORMALIZATION
// =========================================================
// The backend may contain older/stale assessment rows. These
// helpers make the UI display only physically meaningful values.
// Quality scores are ALWAYS 0-100.
// Wind power density is ALWAYS W/m² when wind speed is available.

const clamp = (value, min, max) => {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return null;
  }

  return Math.min(max, Math.max(min, number));
};

const getSolarQualityScore = (data) => {
  if (!data) return null;

  const stored = clamp(data.quality_score, 0, 100);

  // Use the backend score only if it is already a valid quality score.
  if (stored !== null && Number(data.quality_score) >= 0 && Number(data.quality_score) <= 100) {
    return Number(stored.toFixed(2));
  }

  // Never use ml_prediction / annual-energy prediction as quality.
  const peakSunHours = Number(data.peak_sun_hours);
  const capacityFactor = Number(data.capacity_factor);

  if (!Number.isFinite(peakSunHours)) {
    return null;
  }

  const peakScore =
    Math.min(100, Math.max(0, peakSunHours / 6.0 * 100));

  const cfScore =
    Number.isFinite(capacityFactor)
      ? Math.min(100, Math.max(0, capacityFactor / 25.0 * 100))
      : 0;

  return Number(
    (peakScore * 0.75 + cfScore * 0.25).toFixed(2)
  );
};

const getWindPowerDensity = (data) => {
  if (!data) return null;

  const direct =
    Number(data.wind_power_density ?? data.power_density);

  if (Number.isFinite(direct) && direct >= 0) {
    return Number(direct.toFixed(2));
  }

  const speed = Number(data.avg_wind_speed);

  if (!Number.isFinite(speed) || speed < 0) {
    return null;
  }

  // Standard air-density approximation at sea level.
  return Number(
    (0.5 * 1.225 * Math.pow(speed, 3)).toFixed(2)
  );
};

const getWindQualityScore = (data) => {
  if (!data) return null;

  const stored = Number(data.quality_score);

  if (
    Number.isFinite(stored) &&
    stored >= 0 &&
    stored <= 100
  ) {
    return Number(stored.toFixed(2));
  }

  const wpd = getWindPowerDensity(data);

  if (wpd === null) {
    return null;
  }

  // 500 W/m² = 100 resource points.
  return Number(
    Math.min(100, Math.max(0, (wpd / 500) * 100)).toFixed(2)
  );
};

const normalizeSolarData = (data) => {
  if (!data) return null;

  return {
    ...data,
    quality_score: getSolarQualityScore(data)
  };
};

const normalizeWindData = (data) => {
  if (!data) return null;

  const windPowerDensity = getWindPowerDensity(data);

  return {
    ...data,
    wind_power_density: windPowerDensity,
    power_density: windPowerDensity,
    quality_score: getWindQualityScore({
      ...data,
      wind_power_density: windPowerDensity
    })
  };
};


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
  const [analysisMessage, setAnalysisMessage] = useState('');

  useEffect(() => {
    if (!siteId) return;

    const token = localStorage.getItem('token');

    if (!token) {
      navigate('/login');
      return;
    }

    fetchSiteDetails();
  }, [siteId]);

  // =========================================================
  // LOAD ALL EXISTING DATA
  // =========================================================
  const fetchSiteDetails = async () => {
    try {
      setLoading(true);

      const token = localStorage.getItem('token');

      const config = {
        headers: {
          Authorization: `Bearer ${token}`
        }
      };

      // Site information
      const siteRes = await axios.get(
        `${API_URL}/sites/${siteId}`,
        config
      );

      setSite(siteRes.data);

      // Load all saved analysis results independently
      const results = await Promise.allSettled([
        axios.get(
          `${API_URL}/environmental/${siteId}`,
          config
        ),

        axios.get(
          `${API_URL}/solar/assessment/${siteId}`,
          config
        ),

        axios.get(
          `${API_URL}/wind/assessment/${siteId}`,
          config
        ),

        axios.get(
          `${API_URL}/suitability/score/${siteId}`,
          config
        )
      ]);

      // Environmental
      if (results[0].status === 'fulfilled') {
        setEnvironmentalData(results[0].value.data);
      } else {
        setEnvironmentalData(null);
      }

      // Solar
      if (results[1].status === 'fulfilled') {
        setSolarData(
          normalizeSolarData(results[1].value.data)
        );
      } else {
        setSolarData(null);
      }

      // Wind
      if (results[2].status === 'fulfilled') {
        setWindData(
          normalizeWindData(results[2].value.data)
        );
      } else {
        setWindData(null);
      }

      // Suitability
      if (results[3].status === 'fulfilled') {
        setSuitability(results[3].value.data);
      } else {
        setSuitability(null);
      }

    } catch (error) {
      console.error(
        'Error loading site details:',
        error
      );
    } finally {
      setLoading(false);
    }
  };

  // =========================================================
  // COMPLETE SITE ANALYSIS
  // =========================================================
  const analyzeSite = async () => {
    if (!siteId || analyzing) return;

    const token = localStorage.getItem('token');

    if (!token) {
      navigate('/login');
      return;
    }

    setAnalyzing(true);
    setAnalysisMessage('Running complete site analysis...');

    const config = {
      headers: {
        Authorization: `Bearer ${token}`
      }
    };

    try {
      // One backend request performs the complete analysis:
      // NASA environmental data -> solar -> wind -> suitability.
      const response = await axios.post(
        `${API_URL}/sites/${siteId}/analyze`,
        {},
        config
      );

      console.log(
        'Complete site analysis:',
        response.data
      );

      // Immediately use the newly calculated values.
      // Never display ML annual-resource predictions as quality scores.
      if (response.data?.solar) {
        setSolarData(
          normalizeSolarData(response.data.solar)
        );
      }

      if (response.data?.wind) {
        setWindData(
          normalizeWindData(response.data.wind)
        );
      }

      if (response.data?.environmental) {
        setEnvironmentalData(
          response.data.environmental
        );
      }

      if (response.data?.suitability) {
        setSuitability(
          response.data.suitability
        );
      }

      setAnalysisMessage(
        'Latest analysis calculated. Verifying saved results...'
      );

      // Reload persisted values as a final consistency check.
      await fetchSiteDetails();

      setAnalysisMessage(
        '✅ Site analysis completed'
      );

    } catch (error) {
      console.error(
        'Site analysis error:',
        error
      );

      const message =
        error.response?.data?.detail ||
        error.response?.data?.error ||
        error.message ||
        'Analysis failed';

      setAnalysisMessage(
        `❌ ${message}`
      );

    } finally {
      setAnalyzing(false);
    }
  };

  // =========================================================
  // LOADING
  // =========================================================
  if (loading) {
    return (
      <div style={styles.loading}>
        Loading site details...
      </div>
    );
  }

  // =========================================================
  // PAGE
  // =========================================================
  return (
    <div style={styles.container}>

      {/* BACK */}
      <button
        onClick={() => navigate(-1)}
        style={styles.backButton}
      >
        ← Back
      </button>

      {/* HEADER */}
      <div style={styles.header}>

        <div>
          <h1 style={styles.title}>
            📍 {site?.site_name || 'Site Details'}
          </h1>

          {analysisMessage && (
            <p style={styles.analysisMessage}>
              {analysisMessage}
            </p>
          )}
        </div>

        <button
          type="button"
          onClick={analyzeSite}
          disabled={analyzing}
          style={{
            ...styles.analyzeButton,
            opacity: analyzing ? 0.7 : 1
          }}
        >
          {analyzing
            ? '⏳ Analyzing...'
            : '🔬 Analyze Site'}
        </button>

      </div>

      {/* =====================================================
          SITE INFORMATION
      ===================================================== */}
      <div style={styles.infoGrid}>

        <div style={styles.infoCard}>
          <label>Project</label>
          <p>{site?.project_id ?? 'N/A'}</p>
        </div>

        <div style={styles.infoCard}>
          <label>Latitude</label>
          <p>{site?.latitude ?? 'N/A'}</p>
        </div>

        <div style={styles.infoCard}>
          <label>Longitude</label>
          <p>{site?.longitude ?? 'N/A'}</p>
        </div>

        <div style={styles.infoCard}>
          <label>Region</label>
          <p>{site?.region || 'N/A'}</p>
        </div>

        <div style={styles.infoCard}>
          <label>Land Area</label>
          <p>
            {site?.land_area ?? 'N/A'} acres
          </p>
        </div>

        <div style={styles.infoCard}>
          <label>Elevation</label>
          <p>
            {site?.elevation ?? 'N/A'} m
          </p>
        </div>

        <div style={styles.infoCard}>
          <label>Land Ownership</label>
          <p>
            {site?.land_ownership || 'N/A'}
          </p>
        </div>

        <div style={styles.infoCard}>
          <label>Infrastructure</label>
          <p>
            {site?.existing_infrastructure || 'N/A'}
          </p>
        </div>

      </div>

      {/* =====================================================
          ENVIRONMENTAL
      ===================================================== */}
      {environmentalData && (
        <div style={styles.section}>

          <h2 style={styles.sectionTitle}>
            🌍 Environmental Conditions
          </h2>

          <div style={styles.dataGrid}>

            <DataItem
              label="Solar Irradiance"
              value={`${environmentalData.solar_irradiance ?? 'N/A'} kWh/m²/day`}
            />

            <DataItem
              label="Temperature"
              value={`${environmentalData.temperature ?? 'N/A'} °C`}
            />

            <DataItem
              label="Wind Speed"
              value={`${environmentalData.wind_speed ?? 'N/A'} m/s`}
            />

            <DataItem
              label="Rainfall"
              value={`${environmentalData.rainfall ?? 'N/A'} mm/year`}
            />

            <DataItem
              label="Cloud Cover"
              value={`${environmentalData.cloud_cover ?? 'N/A'} %`}
            />

          </div>
        </div>
      )}

      {/* =====================================================
          SOLAR
      ===================================================== */}
      {solarData && (
        <div style={styles.section}>

          <h2 style={styles.sectionTitle}>
            ☀️ Solar Potential
          </h2>

          <div style={styles.dataGrid}>

            <DataItem
              label="Peak Sun Hours"
              value={`${solarData.peak_sun_hours ?? 'N/A'} hours`}
            />

            <DataItem
              label="Annual Energy"
              value={`${solarData.annual_energy_mwh ?? 'N/A'} MWh`}
            />

            <DataItem
              label="Capacity Factor"
              value={`${solarData.capacity_factor ?? 'N/A'} %`}
            />

            <DataItem
              label="Quality Score"
              value={`${
                getSolarQualityScore(solarData) ?? 'N/A'
              } / 100`}
            />

          </div>
        </div>
      )}

      {/* =====================================================
          WIND
      ===================================================== */}
      {windData && (
        <div style={styles.section}>

          <h2 style={styles.sectionTitle}>
            💨 Wind Potential
          </h2>

          <div style={styles.dataGrid}>

            <DataItem
              label="Average Wind Speed"
              value={`${windData.avg_wind_speed ?? 'N/A'} m/s`}
            />

            <DataItem
              label="Wind Power Density"
              value={`${
                getWindPowerDensity(windData) ?? 'N/A'
              } W/m²`}
            />

            <DataItem
              label="Annual Energy"
              value={`${windData.annual_energy_mwh ?? 'N/A'} MWh`}
            />

            <DataItem
              label="Capacity Factor"
              value={`${windData.capacity_factor ?? 'N/A'} %`}
            />

            <DataItem
              label="Quality Score"
              value={`${
                getWindQualityScore(windData) ?? 'N/A'
              } / 100`}
            />

          </div>
        </div>
      )}

      {/* =====================================================
          SUITABILITY
      ===================================================== */}
      {suitability && (
        <div style={styles.section}>

          <h2 style={styles.sectionTitle}>
            🏆 Overall Site Suitability
          </h2>

          <div style={styles.scoreCard}>

            <div style={styles.scoreMain}>

              <div style={styles.bigScore}>
                {suitability.overall_score ?? 'N/A'}
              </div>

              <div style={styles.category}>
                {suitability.category ?? 'N/A'}
              </div>

            </div>

            <div style={styles.scoreDetails}>

              <ScoreItem
                label="Renewable Resource"
                value={suitability.scores?.renewable_resource}
              />

              <ScoreItem
                label="Geographic Suitability"
                value={suitability.scores?.geographic_suitability}
              />

              <ScoreItem
                label="Infrastructure"
                value={suitability.scores?.infrastructure}
              />

              <ScoreItem
                label="Environmental Impact"
                value={suitability.scores?.environmental}
              />

              <ScoreItem
                label="Economic Feasibility"
                value={suitability.scores?.economic}
              />

            </div>
          </div>

          {suitability.recommendations?.length > 0 && (
            <div style={styles.recommendations}>

              <h3>
                📌 Recommendations
              </h3>

              {suitability.recommendations.map(
                (recommendation, index) => (
                  <p key={index}>
                    • {recommendation}
                  </p>
                )
              )}

            </div>
          )}

        </div>
      )}

      {/* =====================================================
          EMPTY
      ===================================================== */}
      {!environmentalData &&
        !solarData &&
        !windData &&
        !suitability && (
          <div style={styles.emptyState}>
            <h3>No analysis available</h3>
            <p>
              Click "Analyze Site" to calculate the
              renewable energy potential.
            </p>
          </div>
        )}

    </div>
  );
}

// =========================================================
// DATA ITEM
// =========================================================
function DataItem({ label, value }) {
  return (
    <div style={styles.dataItem}>
      <label>{label}</label>
      <p>{value}</p>
    </div>
  );
}

// =========================================================
// SCORE ITEM
// =========================================================
function ScoreItem({ label, value }) {
  const score =
    typeof value === 'number'
      ? Math.max(0, Math.min(100, value))
      : 0;

  return (
    <div style={styles.scoreItem}>

      <label>{label}</label>

      <div style={styles.scoreBar}>
        <div
          style={{
            ...styles.scoreFill,
            width: `${score}%`
          }}
        />
      </div>

      <span>
        {value ?? 'N/A'}
        {value !== undefined && '%'}
      </span>

    </div>
  );
}

// =========================================================
// STYLES
// =========================================================
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
    gap: '20px',
    marginBottom: '25px'
  },

  title: {
    fontSize: '28px',
    color: '#1a237e',
    margin: 0
  },

  analysisMessage: {
    margin: '8px 0 0',
    color: '#555',
    fontSize: '14px'
  },

  analyzeButton: {
    padding: '12px 24px',
    backgroundColor: '#4CAF50',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '16px',
    fontWeight: '600',
    whiteSpace: 'nowrap'
  },

  infoGrid: {
    display: 'grid',
    gridTemplateColumns:
      'repeat(auto-fill, minmax(180px, 1fr))',
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
    gridTemplateColumns:
      'repeat(auto-fill, minmax(200px, 1fr))',
    gap: '15px'
  },

  dataItem: {
    padding: '14px',
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
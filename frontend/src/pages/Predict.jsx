import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

function Predict() {
  const [location, setLocation] = useState('');
  const [landArea, setLandArea] = useState(100);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/ml/predict-location`,
        { location, land_area: landArea },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.error || 'Prediction failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
      <h2>🌞 Predict Suitability by Location</h2>
      <p style={{ color: '#666' }}>Just type a place name – no coordinates needed!</p>

      <form onSubmit={handlePredict}>
        <div style={{ marginBottom: '15px' }}>
          <label>📍 Location Name</label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="e.g., Hyderabad, India"
            required
            style={{ width: '100%', padding: '10px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
        <div style={{ marginBottom: '15px' }}>
          <label>📐 Land Area (acres) – optional</label>
          <input
            type="number"
            value={landArea}
            onChange={(e) => setLandArea(parseFloat(e.target.value))}
            style={{ width: '100%', padding: '10px', marginTop: '5px', border: '1px solid #ddd', borderRadius: '4px' }}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '10px 20px',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {loading ? 'Analyzing...' : 'Predict Suitability'}
        </button>
      </form>

      {error && <div style={{ color: 'red', marginTop: '15px' }}>{error}</div>}

      {result && (
        <div style={{ marginTop: '20px', padding: '15px', background: '#f0f0f0', borderRadius: '8px' }}>
          <h3>📊 Prediction Result</h3>
          <p><strong>📍 Location:</strong> {result.location}</p>
          <p><strong>🌍 Coordinates:</strong> {result.latitude}, {result.longitude}</p>
          <p>
            <strong>⭐ Suitability Score:</strong>
            <span style={{ fontSize: '28px', fontWeight: 'bold', marginLeft: '10px', color: '#1a237e' }}>
              {result.suitability_score}
            </span>
          </p>
          <p>
            <strong>🏷️ Category:</strong>
            <span style={{
              background: result.category === 'Excellent' || result.category === 'Highly Suitable' ? '#4CAF50' :
                         result.category === 'Moderately Suitable' ? '#FFC107' : '#f44336',
              padding: '4px 12px',
              borderRadius: '12px',
              color: 'white',
              marginLeft: '10px'
            }}>
              {result.category}
            </span>
          </p>
          <hr />
          <h4>🌍 Environmental Data</h4>
          <ul style={{ listStyle: 'none', padding: 0 }}>
            <li>☀️ Solar Irradiance: {result.environmental_data.solar_irradiance} kWh/m²/day</li>
            <li>🌡️ Temperature: {result.environmental_data.temperature} °C</li>
            <li>💨 Wind Speed: {result.environmental_data.wind_speed} m/s</li>
            <li>☁️ Cloud Cover: {result.environmental_data.cloud_cover} %</li>
            <li>🌧️ Rainfall: {result.environmental_data.rainfall} mm/year</li>
          </ul>
        </div>
      )}
    </div>
  );
}

export default Predict;
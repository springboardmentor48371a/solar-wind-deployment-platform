import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

const API_URL = 'http://localhost:8000/api';

const GISAnalystDashboard = () => {
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSite, setSelectedSite] = useState(null);

  useEffect(() => {
    fetchSites();
  }, []);

  const fetchSites = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${API_URL}/sites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSites(res.data);
    } catch (err) {
      console.error('Error fetching sites:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={styles.loading}>Loading GIS map...</div>;

  return (
    <div>
      <h2 style={styles.sectionTitle}>🗺️ GIS Analyst Dashboard</h2>

      <div style={styles.mapContainer}>
        <MapContainer center={[20, 78]} zoom={5} style={{ height: '500px', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {sites.map(site => (
            <Marker
              key={site.id}
              position={[site.latitude, site.longitude]}
              eventHandlers={{
                click: () => setSelectedSite(site)
              }}
            >
              <Popup>
                <strong>{site.site_name}</strong><br />
                Lat: {site.latitude}<br />
                Lon: {site.longitude}<br />
                Region: {site.region || 'N/A'}<br />
                <button onClick={() => window.location.href = `/sites/${site.id}`}>View Details</button>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {selectedSite && (
        <div style={styles.siteInfo}>
          <h3>{selectedSite.site_name}</h3>
          <p>Latitude: {selectedSite.latitude}, Longitude: {selectedSite.longitude}</p>
          <p>Region: {selectedSite.region || 'N/A'}</p>
          <p>Land Area: {selectedSite.land_area || 'N/A'} acres</p>
          <p>Elevation: {selectedSite.elevation || 'N/A'} m</p>
        </div>
      )}

      <div style={styles.placeholder}>
        <p>📊 Environmental analytics, terrain maps, and site comparison reports will appear here.</p>
      </div>
    </div>
  );
};

const styles = {
  sectionTitle: { fontSize: '24px', marginBottom: '20px' },
  mapContainer: { marginBottom: '20px', borderRadius: '8px', overflow: 'hidden' },
  siteInfo: { backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px', marginBottom: '20px' },
  placeholder: { backgroundColor: '#f8f9fa', padding: '30px', borderRadius: '8px', textAlign: 'center', color: '#666' },
  loading: { padding: '50px', textAlign: 'center', color: '#666' },
};

export default GISAnalystDashboard;
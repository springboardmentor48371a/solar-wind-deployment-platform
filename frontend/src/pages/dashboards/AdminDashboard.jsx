import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const AdminDashboard = () => {
  const [stats, setStats] = useState({ users: 0, projects: 0, sites: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      const token = localStorage.getItem('token');
      // We need endpoints to get user count etc. For now we'll just fetch projects/sites
      const projRes = await axios.get(`${API_URL}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const siteRes = await axios.get(`${API_URL}/sites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats({
        users: 5, // placeholder
        projects: projRes.data.length,
        sites: siteRes.data.length,
      });
    } catch (err) {
      console.error('Error fetching admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={styles.loading}>Loading admin data...</div>;

  return (
    <div>
      <h2 style={styles.sectionTitle}>🔧 Admin Dashboard</h2>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.users}</h3>
          <p style={styles.statLabel}>Registered Users</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.projects}</h3>
          <p style={styles.statLabel}>Total Projects</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{stats.sites}</h3>
          <p style={styles.statLabel}>Total Sites</p>
        </div>
      </div>

      <div style={styles.placeholder}>
        <p>🔐 User management, platform analytics, data source management, and system monitoring will appear here.</p>
      </div>
    </div>
  );
};

const styles = {
  sectionTitle: { fontSize: '24px', marginBottom: '20px' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginBottom: '20px' },
  statCard: { backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px', textAlign: 'center' },
  statNumber: { fontSize: '28px', margin: 0, color: '#1a237e' },
  statLabel: { fontSize: '14px', color: '#666', margin: '5px 0 0 0' },
  placeholder: { backgroundColor: '#f8f9fa', padding: '30px', borderRadius: '8px', textAlign: 'center', color: '#666' },
  loading: { padding: '50px', textAlign: 'center', color: '#666' },
};

export default AdminDashboard;
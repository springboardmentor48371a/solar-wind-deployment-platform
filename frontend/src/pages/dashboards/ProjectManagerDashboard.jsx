import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const ProjectManagerDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const projRes = await axios.get(`${API_URL}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(projRes.data);
      const siteRes = await axios.get(`${API_URL}/sites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSites(siteRes.data);
    } catch (err) {
      console.error('Error fetching project data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={styles.loading}>Loading project data...</div>;

  return (
    <div>
      <h2 style={styles.sectionTitle}>📋 Project Manager Dashboard</h2>

      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{projects.length}</h3>
          <p style={styles.statLabel}>Total Projects</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{sites.length}</h3>
          <p style={styles.statLabel}>Total Sites</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>
            {projects.filter(p => p.status === 'ACTIVE').length}
          </h3>
          <p style={styles.statLabel}>Active Projects</p>
        </div>
      </div>

      <div style={styles.section}>
        <h3>📁 Projects Overview</h3>
        <div style={styles.table}>
          <div style={styles.tableHeader}>
            <span>Project</span>
            <span>Technology</span>
            <span>Status</span>
            <span>Budget</span>
            <span>Sites</span>
          </div>
          {projects.map(proj => (
            <div key={proj.id} style={styles.tableRow}>
              <span>{proj.project_name}</span>
              <span>{proj.technology}</span>
              <span style={proj.status === 'ACTIVE' ? styles.activeBadge : styles.draftBadge}>
                {proj.status}
              </span>
              <span>${proj.budget?.toLocaleString()}</span>
              <span>{sites.filter(s => s.project_id === proj.id).length}</span>
            </div>
          ))}
        </div>
      </div>

      <div style={styles.placeholder}>
        <p>📈 Feasibility reports, cost-benefit analysis, and deployment timelines will appear here.</p>
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
  section: { backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px', marginBottom: '20px' },
  table: { display: 'flex', flexDirection: 'column', gap: '8px' },
  tableHeader: { display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', padding: '10px', backgroundColor: '#e9ecef', fontWeight: 'bold', borderRadius: '4px' },
  tableRow: { display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr 1fr', padding: '10px', alignItems: 'center', borderBottom: '1px solid #dee2e6' },
  activeBadge: { padding: '4px 8px', backgroundColor: '#d4edda', borderRadius: '4px', color: '#155724', width: 'fit-content' },
  draftBadge: { padding: '4px 8px', backgroundColor: '#fff3cd', borderRadius: '4px', color: '#856404', width: 'fit-content' },
  placeholder: { backgroundColor: '#f8f9fa', padding: '30px', borderRadius: '8px', textAlign: 'center', color: '#666' },
  loading: { padding: '50px', textAlign: 'center', color: '#666' },
};

export default ProjectManagerDashboard;
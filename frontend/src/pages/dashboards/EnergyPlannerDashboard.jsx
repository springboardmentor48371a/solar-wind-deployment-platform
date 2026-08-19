import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, ArcElement, Title, Tooltip, Legend);

const API_URL = 'http://localhost:8000/api';

const EnergyPlannerDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [investment, setInvestment] = useState(null);
  const [selectedSite, setSelectedSite] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');

      // Get recommendations
      const recRes = await axios.get(`${API_URL}/optimization/recommend`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRecommendations(recRes.data.recommendations || []);

      if (recRes.data.top_site) {
        const site = recRes.data.top_site;
        setSelectedSite(site);

        // Get forecast for top site
        const foreRes = await axios.get(`${API_URL}/forecasting/site/${site.site_id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setForecast(foreRes.data);

        // Get investment analysis
        const invRes = await axios.post(`${API_URL}/investment/analyze/${site.site_id}`, null, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setInvestment(invRes.data);
      }
    } catch (err) {
      console.error('Error fetching energy dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div style={styles.loading}>Loading energy planner data...</div>;

  const topSite = recommendations[0] || null;

  // Chart data for forecast
  const forecastChartData = {
    labels: forecast?.base_monthly?.map(d => `Month ${d.month}`) || [],
    datasets: [
      {
        label: 'Solar (MWh)',
        data: forecast?.base_monthly?.map(d => d.solar_mwh) || [],
        borderColor: '#FFA000',
        backgroundColor: 'rgba(255,160,0,0.1)',
        fill: true,
      },
      {
        label: 'Wind (MWh)',
        data: forecast?.base_monthly?.map(d => d.wind_mwh) || [],
        borderColor: '#1976D2',
        backgroundColor: 'rgba(25,118,210,0.1)',
        fill: true,
      },
    ],
  };

  // Suitability scores for top sites (bar chart)
  const scoreChartData = {
    labels: recommendations.slice(0, 5).map(s => s.site_name),
    datasets: [
      {
        label: 'Suitability Score',
        data: recommendations.slice(0, 5).map(s => s.overall_score),
        backgroundColor: ['#4CAF50', '#8BC34A', '#FFC107', '#FF9800', '#f44336'],
      },
    ],
  };

  return (
    <div>
      <h2 style={styles.sectionTitle}>⚡ Energy Planner Dashboard</h2>

      {/* Summary Cards */}
      <div style={styles.statsGrid}>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{recommendations.length}</h3>
          <p style={styles.statLabel}>Total Sites Analyzed</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{topSite?.overall_score || 0}</h3>
          <p style={styles.statLabel}>Top Site Score</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{topSite?.category || 'N/A'}</h3>
          <p style={styles.statLabel}>Top Site Category</p>
        </div>
        <div style={styles.statCard}>
          <h3 style={styles.statNumber}>{forecast?.annual_estimate || 0} MWh</h3>
          <p style={styles.statLabel}>Annual Energy Estimate</p>
        </div>
      </div>

      {/* Top Sites Table */}
      <div style={styles.section}>
        <h3>🏆 Recommended Deployment Sites</h3>
        <div style={styles.table}>
          <div style={styles.tableHeader}>
            <span>Rank</span>
            <span>Site Name</span>
            <span>Score</span>
            <span>Category</span>
            <span>Annual Energy (MWh)</span>
          </div>
          {recommendations.slice(0, 5).map((site, i) => (
            <div key={site.site_id} style={styles.tableRow}>
              <span>#{i + 1}</span>
              <span>{site.site_name}</span>
              <span><strong>{site.overall_score}</strong></span>
              <span style={getCategoryStyle(site.category)}>{site.category}</span>
              <span>{site.annual_energy_mwh}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Charts */}
      <div style={styles.chartGrid}>
        <div style={styles.chartCard}>
          <h4>Monthly Energy Forecast</h4>
          <Line data={forecastChartData} options={{ responsive: true }} />
        </div>
        <div style={styles.chartCard}>
          <h4>Top Sites Suitability Scores</h4>
          <Bar data={scoreChartData} options={{ responsive: true }} />
        </div>
      </div>

      {/* Investment Summary */}
      {investment && (
        <div style={styles.section}>
          <h3>💰 Investment Analysis for {investment.site_name}</h3>
          <div style={styles.investmentGrid}>
            <div style={styles.investmentItem}>
              <label>CAPEX</label>
              <p>${investment.investment.capex.toLocaleString()}</p>
            </div>
            <div style={styles.investmentItem}>
              <label>Annual Revenue</label>
              <p>${investment.investment.annual_revenue.toLocaleString()}</p>
            </div>
            <div style={styles.investmentItem}>
              <label>Annual Net Profit</label>
              <p>${investment.investment.annual_net_profit.toLocaleString()}</p>
            </div>
            <div style={styles.investmentItem}>
              <label>Payback Period</label>
              <p>{investment.investment.payback_period_years} years</p>
            </div>
            <div style={styles.investmentItem}>
              <label>ROI</label>
              <p>{investment.investment.roi_percent}%</p>
            </div>
            <div style={styles.investmentItem}>
              <label>NPV (10yr)</label>
              <p>${investment.investment.npv_10yr.toLocaleString()}</p>
            </div>
          </div>
          <div style={styles.recommendation}>
            <strong>Recommendation:</strong> {investment.recommendation}
          </div>
        </div>
      )}
    </div>
  );
};

const getCategoryStyle = (category) => {
  const styles = {
    'Excellent': { backgroundColor: '#4CAF50', color: 'white', padding: '4px 12px', borderRadius: '20px' },
    'Highly Suitable': { backgroundColor: '#8BC34A', color: 'white', padding: '4px 12px', borderRadius: '20px' },
    'Moderately Suitable': { backgroundColor: '#FFC107', padding: '4px 12px', borderRadius: '20px' },
    'Low Suitability': { backgroundColor: '#FF9800', color: 'white', padding: '4px 12px', borderRadius: '20px' },
    'Unsuitable': { backgroundColor: '#f44336', color: 'white', padding: '4px 12px', borderRadius: '20px' },
  };
  return styles[category] || {};
};

const styles = {
  sectionTitle: { fontSize: '24px', marginBottom: '20px' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px', marginBottom: '20px' },
  statCard: { backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px', textAlign: 'center' },
  statNumber: { fontSize: '28px', margin: 0, color: '#1a237e' },
  statLabel: { fontSize: '14px', color: '#666', margin: '5px 0 0 0' },
  section: { backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px', marginBottom: '20px' },
  table: { display: 'flex', flexDirection: 'column', gap: '8px' },
  tableHeader: { display: 'grid', gridTemplateColumns: '0.5fr 2fr 1fr 1.5fr 1.5fr', padding: '10px', backgroundColor: '#e9ecef', fontWeight: 'bold', borderRadius: '4px' },
  tableRow: { display: 'grid', gridTemplateColumns: '0.5fr 2fr 1fr 1.5fr 1.5fr', padding: '10px', alignItems: 'center', borderBottom: '1px solid #dee2e6' },
  chartGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' },
  chartCard: { backgroundColor: '#f8f9fa', padding: '15px', borderRadius: '8px' },
  investmentGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px', marginBottom: '10px' },
  investmentItem: { backgroundColor: 'white', padding: '10px', borderRadius: '4px', border: '1px solid #dee2e6' },
  recommendation: { backgroundColor: '#d4edda', padding: '10px', borderRadius: '4px', color: '#155724' },
  loading: { padding: '50px', textAlign: 'center', color: '#666' },
};

export default EnergyPlannerDashboard;
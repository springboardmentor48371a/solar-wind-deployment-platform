import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import L from 'leaflet';

// Fix default Leaflet icon paths
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const ROLES = [
  "Renewable Energy Planner",
  "GIS Analyst",
  "Project Manager",
  "Administrator"
];

const API_BASE_URL = 'http://127.0.0.1:8000';

function LocationPicker({ position, onPositionChange }) {
  useMapEvents({
    click(e) {
      onPositionChange(e.latlng.lat, e.latlng.lng);
    },
  });
  return position ? <Marker position={position}><Popup>Selected Coordinates</Popup></Marker> : null;
}

export default function App() {
  const [isLogin, setIsLogin] = useState(true);
  const [user, setUser] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Admin Data
  const [adminUserList, setAdminUserList] = useState([]);

  // Projects & Sites Data
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [sites, setSites] = useState([]);

  // Selection & Comparison Engine State
  const [selectedSiteIds, setSelectedSiteIds] = useState([]);
  const [comparisonSites, setComparisonSites] = useState([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);

  // Modals
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showSiteModal, setShowSiteModal] = useState(false);
  const [showGisEditModal, setShowGisEditModal] = useState(false);
  const [activeSiteForGis, setActiveSiteForGis] = useState(null);
  const [showMapModal, setShowMapModal] = useState(false);

  // Forms
  const [newProject, setNewProject] = useState({
    name: '',
    description: '',
    target_capacity_mw: 150,
    region: 'Rajasthan',
    status: 'Active',
    timeline_cod: 'Q3 2027'
  });

  const [newSite, setNewSite] = useState({
    site_name: '',
    latitude: 27.0234,
    longitude: 71.8741,
    elevation_m: 210,
    land_area_sqkm: 12.5,
    region: 'Rajasthan',
    land_ownership: 'Government Lease',
    existing_infrastructure: '400kV corridor within 4km'
  });

  const [gisForm, setGisForm] = useState({
    latitude: 0,
    longitude: 0,
    elevation_m: 0,
    slope_deg: 0,
    vegetation_ndvi: 0,
    solar_ghi: 0,
    avg_temp: 0
  });

  const [authData, setAuthData] = useState({
    email: 'planner@energygrid.gov',
    password: 'planner123',
    full_name: 'Elena Rostova',
    role: ROLES[0]
  });

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch(`${API_BASE_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => res.ok ? res.json() : Promise.reject())
        .then(userData => {
          setUser(userData);
          if (userData.role === 'Administrator') {
            fetchAdminUsers(token);
          } else {
            fetchProjects(token);
          }
        })
        .catch(() => {
          localStorage.removeItem('token');
          setUser(null);
        });
    }
  }, []);

  const fetchAdminUsers = async (token) => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (Array.isArray(data)) setAdminUserList(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchProjects = async (token) => {
    try {
      const res = await fetch(`${API_BASE_URL}/projects/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) {
        setProjects(data);
        const activeId = selectedProjectId || data[0].id;
        setSelectedProjectId(activeId);
        fetchSitesForProject(activeId, token);
      } else {
        setProjects([]);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchSitesForProject = async (projectId, token) => {
    try {
      const res = await fetch(`${API_BASE_URL}/projects/sites?project_id=${projectId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setSites(Array.isArray(data) ? data : []);
      setSelectedSiteIds([]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSelectProject = (id) => {
    setSelectedProjectId(id);
    const token = localStorage.getItem('token');
    fetchSitesForProject(id, token);
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    try {
      const payload = {
        name: newProject.name.trim(),
        description: newProject.description || "Renewable project portfolio",
        target_capacity_mw: parseFloat(newProject.target_capacity_mw) || 100.0,
        region: newProject.region.trim() || "Rajasthan",
        status: newProject.status || "Active",
        timeline_cod: newProject.timeline_cod || "Q3 2027"
      };
      const res = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to create project");
      const created = await res.json();
      setProjects(prev => [...prev, created]);
      setSelectedProjectId(created.id);
      fetchSitesForProject(created.id, token);
      setShowProjectModal(false);
      setNewProject({ name: '', description: '', target_capacity_mw: 150, region: 'Rajasthan', status: 'Active', timeline_cod: 'Q3 2027' });
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteProject = async (e, projectId) => {
    e.stopPropagation();
    if (!window.confirm("Delete this project and all associated sites?")) return;
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/projects/${projectId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Deletion failed");
      const remaining = projects.filter(p => p.id !== projectId);
      setProjects(remaining);
      if (selectedProjectId === projectId) {
        const nextId = remaining.length > 0 ? remaining[0].id : null;
        setSelectedProjectId(nextId);
        if (nextId) fetchSitesForProject(nextId, token);
        else setSites([]);
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleCreateSite = async (e) => {
    e.preventDefault();
    if (!selectedProjectId) return alert("Select a project first!");
    const token = localStorage.getItem('token');
    try {
      const payload = {
        ...newSite,
        project_id: selectedProjectId,
        latitude: parseFloat(newSite.latitude),
        longitude: parseFloat(newSite.longitude),
        elevation_m: parseFloat(newSite.elevation_m),
        land_area_sqkm: parseFloat(newSite.land_area_sqkm)
      };
      const res = await fetch(`${API_BASE_URL}/projects/sites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to register site");
      const created = await res.json();
      setSites(prev => [...prev, created]);
      setShowSiteModal(false);
      fetchProjects(token);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteSite = async (siteId) => {
    if (!window.confirm("Are you sure you want to delete this candidate site?")) return;
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/projects/sites/${siteId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error("Failed to delete site");
      setSites(prev => prev.filter(s => s.id !== siteId));
      setSelectedSiteIds(prev => prev.filter(id => id !== siteId));
    } catch (err) {
      alert(err.message);
    }
  };

  const handleSaveGis = async (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/projects/sites/${activeSiteForGis.id}/gis-data`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          latitude: parseFloat(gisForm.latitude),
          longitude: parseFloat(gisForm.longitude),
          elevation_m: parseFloat(gisForm.elevation_m),
          slope_deg: parseFloat(gisForm.slope_deg),
          vegetation_ndvi: parseFloat(gisForm.vegetation_ndvi),
          solar_ghi: parseFloat(gisForm.solar_ghi),
          avg_temp: parseFloat(gisForm.avg_temp)
        })
      });
      if (!res.ok) throw new Error("Failed to update GIS data");
      const updated = await res.json();
      setSites(prev => prev.map(s => s.id === updated.id ? updated : s));
      setShowGisEditModal(false);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleToggleApproval = async (site) => {
    const token = localStorage.getItem('token');
    const newStatus = !site.is_approved;
    try {
      const res = await fetch(`${API_BASE_URL}/projects/sites/${site.id}/approval`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          is_approved: newStatus,
          is_shortlisted: true,
          approval_notes: newStatus 
            ? "Approved for Phase 1 construction by Project Manager" 
            : "Approval revoked by Project Manager"
        })
      });
      if (!res.ok) throw new Error("Approval update failed");
      const updated = await res.json();
      setSites(prev => prev.map(s => s.id === updated.id ? updated : s));
    } catch (err) {
      alert(err.message);
    }
  };

  // Module 3: NASA POWER Climate Sync
  const handleSyncNasa = async (siteId) => {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/environmental/sync/${siteId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "NASA sync failed");

      setSites(prev => prev.map(s => s.id === siteId ? data.site : s));
      alert(`🛰️ ${data.message}\n• Solar GHI: ${data.telemetry.solar_ghi} kWh/m²\n• Avg Temp: ${data.telemetry.avg_temp}°C\n• Rainfall: ${data.telemetry.rainfall_mm} mm\n• Cloud Cover: ${data.telemetry.cloud_cover_pct}%`);
    } catch (err) {
      alert(`NASA Sync Failed: ${err.message}`);
    }
  };

  // Module 4: OpenStreetMap Spatial Proximity Scan
  const handleScanOsm = async (siteId) => {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/gis/scan/${siteId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "OSM Scan failed");

      setSites(prev => prev.map(s => s.id === siteId ? data.site : s));
      alert(`🗺️ ${data.message}\n• Substation: ${data.spatial_analytics.substation_dist_km} km\n• Transmission Line: ${data.spatial_analytics.transmission_line_dist_km} km\n• Access Road: ${data.spatial_analytics.access_road_dist_km} km\n• Risk Index: ${data.spatial_analytics.interconnect_risk}`);
    } catch (err) {
      alert(`OSM Scan Failed: ${err.message}`);
    }
  };

  // Module 5: Solar Potential ML Predictor
  const handlePredictSolar = async (siteId) => {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/solar/predict/${siteId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Solar ML prediction failed");

      setSites(prev => prev.map(s => s.id === siteId ? data.site : s));
      alert(
        `☀️ ${data.message}\n` +
        `• Capacity Factor (Derated): ${data.solar_analytics.predicted_capacity_factor}%\n` +
        `• Annual Yield: ${data.solar_analytics.annual_yield_gwh} GWh\n` +
        `• Installable Capacity: ${data.solar_analytics.installable_capacity_mw} MW\n` +
        `• Cell Operating Temp: ${data.solar_analytics.t_cell_celsius}°C\n` +
        `• Thermal Derate Loss: -${data.solar_analytics.temp_derate_loss_pct}%\n` +
        `• Performance Ratio (PR): ${data.solar_analytics.performance_ratio_pct}%\n` +
        `• Model: ${data.solar_analytics.model_type}`
      );
    } catch (err) {
      alert(`Solar ML Failed: ${err.message}`);
    }
  };

  // Module 6: Wind Potential Predictor
  const handlePredictWind = async (siteId) => {
    const token = localStorage.getItem('token');
    try {
      const res = await fetch(`${API_BASE_URL}/wind/predict/${siteId}`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Wind prediction failed");

      setSites(prev => prev.map(s => s.id === siteId ? data.site : s));
      alert(
        `💨 ${data.message}\n` +
        `• 50m Wind Speed: ${data.wind_analytics.wind_speed_50m} m/s\n` +
        `• 100m Hub Speed: ${data.wind_analytics.wind_speed_100m} m/s\n` +
        `• Wind Power Density: ${data.wind_analytics.wind_power_density_w_m2} W/m²\n` +
        `• Capacity Factor: ${data.wind_analytics.predicted_capacity_factor}%\n` +
        `• Annual Wind Yield: ${data.wind_analytics.annual_yield_gwh} GWh\n` +
        `• Turbulence Intensity: ${data.wind_analytics.turbulence_intensity_pct}%\n` +
        `• Turbine Class: ${data.wind_analytics.turbine_class}`
      );
    } catch (err) {
      alert(`Wind Prediction Failed: ${err.message}`);
    }
  };

  const toggleSiteSelection = (siteId) => {
    setSelectedSiteIds(prev =>
      prev.includes(siteId) ? prev.filter(id => id !== siteId) : [...prev, siteId]
    );
  };

  const handleRunComparison = async () => {
    if (selectedSiteIds.length < 2) {
      alert("Please select at least 2 candidate sites to compare.");
      return;
    }
    const token = localStorage.getItem('token');
    const query = selectedSiteIds.map(id => `site_ids=${id}`).join('&');
    try {
      const res = await fetch(`${API_BASE_URL}/projects/sites/compare?${query}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Comparison failed");
      setComparisonSites(data);
      setShowComparisonModal(true);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const endpoint = isLogin ? `${API_BASE_URL}/auth/login` : `${API_BASE_URL}/auth/register`;
    const payload = isLogin ? { email: authData.email, password: authData.password } : authData;

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed');

      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      if (data.user.role === 'Administrator') {
        fetchAdminUsers(data.access_token);
      } else {
        fetchProjects(data.access_token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Role Flags
  const isPlanner = user?.role === 'Renewable Energy Planner';
  const isGis = user?.role === 'GIS Analyst';
  const isPM = user?.role === 'Project Manager';
  const isAdmin = user?.role === 'Administrator';

  // Permission Logic
  const canCreateProject = isPlanner || isPM;
  const canAddSite = isPlanner || isGis;
  const canEditGis = isGis || isAdmin;
  const canApprove = isPM;

  const activeProject = projects.find(p => p.id === selectedProjectId);

  if (!user) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#070d19', color: '#fff', fontFamily: 'system-ui, sans-serif' }}>
        <div style={{ backgroundColor: '#111827', border: '1px solid #1f2937', borderRadius: '16px', padding: '32px', width: '100%', maxWidth: '420px' }}>
          <div style={{ textAlign: 'center', marginBottom: '24px' }}>
            <div style={{ fontSize: '32px' }}>☀️ 💨</div>
            <h2 style={{ margin: '8px 0 4px 0' }}>Solar & Wind Intelligence</h2>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: '13px' }}>Milestone 1 & 2 — Operational Platform</p>
          </div>

          {error && <div style={{ background: '#450a0a', border: '1px solid #dc2626', color: '#f87171', padding: '10px', borderRadius: '6px', fontSize: '12px', marginBottom: '14px' }}>{error}</div>}

          <form onSubmit={handleAuth}>
            {!isLogin && (
              <>
                <label style={lbl}>Full Name</label>
                <input style={inp} required value={authData.full_name} onChange={e => setAuthData({ ...authData, full_name: e.target.value })} />
                <label style={lbl}>Platform Role</label>
                <select style={inp} value={authData.role} onChange={e => setAuthData({ ...authData, role: e.target.value })}>
                  {ROLES.map(r => <option key={r} value={r} style={{ backgroundColor: '#111827' }}>{r}</option>)}
                </select>
              </>
            )}

            <label style={lbl}>Email Address</label>
            <input style={inp} type="email" required value={authData.email} onChange={e => setAuthData({ ...authData, email: e.target.value })} />

            <label style={lbl}>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                style={{ ...inp, paddingRight: '40px' }}
                type={showPassword ? 'text' : 'password'}
                required
                value={authData.password}
                onChange={e => setAuthData({ ...authData, password: e.target.value })}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: 'absolute', right: '10px', top: '35%', background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}
              >
                {showPassword ? '👁️' : '🔒'}
              </button>
            </div>

            <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: 'linear-gradient(to right, #f59e0b, #06b6d4)', border: 'none', borderRadius: '8px', color: '#000', fontWeight: 'bold', cursor: 'pointer', marginTop: '10px' }}>
              {loading ? 'Processing...' : isLogin ? 'Sign In' : 'Create Account'}
            </button>
          </form>

          <p style={{ textAlign: 'center', fontSize: '13px', color: '#94a3b8', marginTop: '18px' }}>
            {isLogin ? "Need an account? " : "Already have an account? "}
            <span onClick={() => { setIsLogin(!isLogin); setError(''); }} style={{ color: '#38bdf8', cursor: 'pointer', textDecoration: 'underline' }}>
              {isLogin ? 'Sign up' : 'Log in'}
            </span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#070d18', color: '#f8fafc', fontFamily: 'system-ui, sans-serif' }}>
      
      {/* Top Banner */}
      <div style={{ padding: '20px 36px', borderBottom: '1px solid #142033', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ textTransform: 'uppercase', fontSize: '11px', letterSpacing: '1px', color: isAdmin ? '#ef4444' : '#38bdf8', fontWeight: 'bold' }}>
            {user.role} WORKSPACE
          </div>
          <h1 style={{ margin: '4px 0 0 0', fontSize: '24px', fontWeight: 'bold' }}>
            {isAdmin ? 'System Governance & Platform Administration' : 'Projects & Sites Registry'}
          </h1>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: 600, fontSize: '13px' }}>{user.full_name}</div>
            <div style={{ fontSize: '11px', color: '#94a3b8' }}>{user.email}</div>
          </div>
          <button
            onClick={() => { localStorage.removeItem('token'); setUser(null); }}
            style={{ padding: '6px 12px', background: '#dc2626', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '12px' }}
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* 1. ADMIN DASHBOARD */}
      {isAdmin ? (
        <div style={{ padding: '32px 36px', maxWidth: '1240px', margin: '0 auto' }}>
          <h3 style={{ margin: '0 0 4px 0', fontSize: '20px', color: '#f8fafc' }}>
            🛡️ Platform Security & User Governance
          </h3>
          <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0 0 24px 0' }}>
            Live directory of registered users, RBAC roles, and infrastructure status.
          </p>

          <div style={{ background: '#0d1526', border: '1px solid #1e293b', borderRadius: '12px', padding: '20px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                  <th style={{ padding: '10px' }}>UID</th>
                  <th style={{ padding: '10px' }}>Full Name</th>
                  <th style={{ padding: '10px' }}>Login Email</th>
                  <th style={{ padding: '10px' }}>Assigned Role</th>
                  <th style={{ padding: '10px' }}>Organization</th>
                  <th style={{ padding: '10px' }}>Department</th>
                  <th style={{ padding: '10px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {adminUserList.map((u) => (
                  <tr key={u.id} style={{ borderBottom: '1px solid #142033' }}>
                    <td style={{ padding: '10px', color: '#64748b' }}>#{u.id}</td>
                    <td style={{ padding: '10px', fontWeight: 'bold' }}>{u.full_name}</td>
                    <td style={{ padding: '10px', color: '#38bdf8' }}>{u.email}</td>
                    <td style={{ padding: '10px', fontWeight: 'bold', color: '#ef4444' }}>{u.role}</td>
                    <td style={{ padding: '10px', color: '#cbd5e1' }}>{u.organization}</td>
                    <td style={{ padding: '10px', color: '#94a3b8' }}>{u.department}</td>
                    <td style={{ padding: '10px', color: '#10b981' }}>● Active</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* 2. OPERATIONAL PROJECTS & SITES VIEW */
        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', minHeight: 'calc(100vh - 85px)' }}>
          
          {/* Left Column: Portfolios */}
          <div style={{ borderRight: '1px solid #142033', padding: '24px 20px', backgroundColor: '#09101d' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <span style={{ fontSize: '12px', fontWeight: 'bold', letterSpacing: '0.5px', color: '#94a3b8', textTransform: 'uppercase' }}>
                Project Portfolios ({projects.length})
              </span>
              {canCreateProject ? (
                <button
                  onClick={() => setShowProjectModal(true)}
                  style={{ padding: '5px 14px', background: '#059669', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold', cursor: 'pointer' }}
                >
                  + New
                </button>
              ) : (
                <span style={{ fontSize: '10px', color: '#64748b' }}>Creation Locked</span>
              )}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {projects.map((proj) => {
                const isSelected = proj.id === selectedProjectId;
                return (
                  <div
                    key={proj.id}
                    onClick={() => handleSelectProject(proj.id)}
                    style={{
                      backgroundColor: isSelected ? '#101c30' : '#0d1626',
                      border: isSelected ? '1px solid #1e3a5f' : '1px solid #142033',
                      borderRadius: '10px',
                      padding: '16px',
                      cursor: 'pointer'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '15px', color: isSelected ? '#38bdf8' : '#e2e8f0' }}>
                        {proj.name}
                      </div>
                      {canCreateProject && (
                        <button
                          onClick={(e) => handleDeleteProject(e, proj.id)}
                          title="Delete Project"
                          style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '14px' }}
                        >
                          🗑️
                        </button>
                      )}
                    </div>
                    <div style={{ color: '#64748b', fontSize: '12px', marginBottom: '12px' }}>
                      Target: {proj.target_capacity_mw} MW • {proj.region}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#10b981', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 600 }}>
                        {proj.status || 'Active'}
                      </span>
                      <span style={{ fontSize: '12px', color: '#64748b' }}>
                        Timeline: {proj.timeline_cod || 'Q3 2027'}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Sites */}
          <div style={{ padding: '24px 32px' }}>
            {activeProject ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '22px', fontWeight: 'bold' }}>{activeProject.name}</h2>
                    <span style={{ fontSize: '13px', color: '#64748b' }}>
                      Region: {activeProject.region} • Target Capacity: {activeProject.target_capacity_mw} MW
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: '10px' }}>
                    {selectedSiteIds.length >= 2 && (
                      <button
                        onClick={handleRunComparison}
                        style={{ padding: '8px 16px', background: '#f59e0b', color: '#000', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
                      >
                        ⚖️ Compare Selected ({selectedSiteIds.length})
                      </button>
                    )}
                    {canAddSite && (
                      <button
                        onClick={() => setShowSiteModal(true)}
                        style={{ padding: '8px 18px', background: '#059669', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 'bold', cursor: 'pointer' }}
                      >
                        + Add Site
                      </button>
                    )}
                  </div>
                </div>

                {/* Sites List */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {sites.map((site) => {
                    const isSelected = selectedSiteIds.includes(site.id);
                    return (
                      <div
                        key={site.id}
                        style={{
                          backgroundColor: '#0c1524',
                          border: isSelected ? '1.5px solid #38bdf8' : site.is_approved ? '1px solid #10b981' : '1px solid #16243b',
                          borderRadius: '12px',
                          padding: '20px'
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSiteSelection(site.id)}
                              style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                            />
                            <div style={{ width: '36px', height: '36px', borderRadius: '8px', backgroundColor: '#13233c', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
                              ⚡
                            </div>
                            <div>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 'bold' }}>{site.site_name}</h3>
                                {site.is_approved && (
                                  <span style={{ backgroundColor: '#065f46', color: '#6ee7b7', fontSize: '10px', padding: '2px 6px', borderRadius: '4px', fontWeight: 'bold' }}>
                                    APPROVED
                                  </span>
                                )}
                              </div>
                              <span style={{ fontSize: '12px', color: '#64748b' }}>
                                solar • {site.latitude?.toFixed(4)}°N, {site.longitude?.toFixed(4)}°E • {site.elevation_m}m • {site.land_area_sqkm} km²
                              </span>
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            {/* MODULE 3: NASA POWER CLIMATE SYNC */}
                            {canAddSite && (
                              <button
                                onClick={() => handleSyncNasa(site.id)}
                                title="Fetch live NASA POWER irradiance and weather data"
                                style={{
                                  padding: '6px 12px',
                                  background: 'linear-gradient(to right, #0284c7, #06b6d4)',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '12px',
                                  cursor: 'pointer',
                                  fontWeight: 600
                                }}
                              >
                                🛰️ Sync NASA Data
                              </button>
                            )}

                            {/* MODULE 4: OPENSTREETMAP SPATIAL GRID SCAN */}
                            {canEditGis && (
                              <button
                                onClick={() => handleScanOsm(site.id)}
                                title="Query OpenStreetMap for nearby substations, transmission lines, and roads"
                                style={{
                                  padding: '6px 12px',
                                  background: 'linear-gradient(to right, #059669, #10b981)',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '12px',
                                  cursor: 'pointer',
                                  fontWeight: 600
                                }}
                              >
                                🗺️ Scan OSM Grid
                              </button>
                            )}

                            {/* MODULE 5: SOLAR MACHINE LEARNING PREDICTOR */}
                            {canAddSite && (
                              <button
                                onClick={() => handlePredictSolar(site.id)}
                                title="Execute Module 5 Random Forest ML yield and thermal derating model"
                                style={{
                                  padding: '6px 12px',
                                  background: 'linear-gradient(to right, #d97706, #f59e0b)',
                                  color: '#000',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '12px',
                                  cursor: 'pointer',
                                  fontWeight: 'bold'
                                }}
                              >
                                ☀️ Predict Solar ML
                              </button>
                            )}

                            {/* MODULE 6: WIND POTENTIAL PREDICTOR */}
                            {canAddSite && (
                              <button
                                onClick={() => handlePredictWind(site.id)}
                                title="Execute Module 6 hub-height wind shear and power density estimation model"
                                style={{
                                  padding: '6px 12px',
                                  background: 'linear-gradient(to right, #0284c7, #38bdf8)',
                                  color: '#000',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '12px',
                                  cursor: 'pointer',
                                  fontWeight: 'bold'
                                }}
                              >
                                💨 Predict Wind
                              </button>
                            )}

                            {canEditGis && (
                              <button
                                onClick={() => {
                                  setActiveSiteForGis(site);
                                  setGisForm({
                                    latitude: site.latitude,
                                    longitude: site.longitude,
                                    elevation_m: site.elevation_m,
                                    slope_deg: site.slope_deg || 2.1,
                                    vegetation_ndvi: site.vegetation_ndvi || 0.18,
                                    solar_ghi: site.solar_ghi || 5.69,
                                    avg_temp: site.avg_temp || 28.4
                                  });
                                  setShowGisEditModal(true);
                                }}
                                style={{ padding: '6px 12px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', fontWeight: 600 }}
                              >
                                🗺️ Edit GIS
                              </button>
                            )}

                            {canApprove && (
                              <button
                                onClick={() => handleToggleApproval(site)}
                                style={{
                                  padding: '6px 12px',
                                  background: site.is_approved ? '#4b5563' : '#10b981',
                                  color: '#fff',
                                  border: 'none',
                                  borderRadius: '6px',
                                  fontSize: '12px',
                                  cursor: 'pointer',
                                  fontWeight: 600
                                }}
                              >
                                {site.is_approved ? 'Revoke Approval' : '✓ Give Final Approval'}
                              </button>
                            )}

                            {canAddSite && (
                              <button
                                onClick={() => handleDeleteSite(site.id)}
                                style={{ padding: '6px 10px', background: 'rgba(239, 68, 68, 0.15)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '6px', fontSize: '12px', cursor: 'pointer' }}
                              >
                                🗑️
                              </button>
                            )}

                            <span style={{ backgroundColor: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 'bold' }}>
                              {site.suitability_score || 7.8} / 10 ▲
                            </span>
                          </div>
                        </div>

                        {/* Metric Tiles */}
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px' }}>
                          <div style={metricBoxStyle}>
                            <span style={metricLbl}>Solar (GHI)</span>
                            <span style={metricVal}>{site.solar_ghi} kWh/m²</span>
                          </div>
                          <div style={metricBoxStyle}>
                            <span style={metricLbl}>Avg Temp</span>
                            <span style={metricVal}>{site.avg_temp} °C</span>
                          </div>
                          <div style={metricBoxStyle}>
                            <span style={metricLbl}>Rainfall</span>
                            <span style={metricVal}>{site.rainfall_mm || 133.8} mm</span>
                          </div>
                          <div style={metricBoxStyle}>
                            <span style={metricLbl}>Cloud Cover</span>
                            <span style={metricVal}>{site.cloud_cover_pct || 70.2} %</span>
                          </div>
                          <div style={metricBoxStyle}>
                            <span style={metricLbl}>Capacity Factor</span>
                            <span style={metricVal}>{site.capacity_factor || 17} %</span>
                          </div>
                          <div style={metricBoxStyle}>
                            <span style={metricLbl}>Est Yield</span>
                            <span style={metricVal}>{site.est_yield_gwh || 1485.6}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
                Select a project from the left panel to manage sites.
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL 1: Create Project */}
      {showProjectModal && (
        <div style={modalBackdrop}>
          <div style={modalBox}>
            <h3 style={{ margin: '0 0 16px 0' }}>Create Project Portfolio</h3>
            <form onSubmit={handleCreateProject}>
              <label style={lbl}>Project Name</label>
              <input style={inp} required placeholder="e.g. Rajasthan Solar Phase 1" value={newProject.name} onChange={e => setNewProject({ ...newProject, name: e.target.value })} />
              <label style={lbl}>Target Capacity (MW)</label>
              <input style={inp} type="number" required value={newProject.target_capacity_mw} onChange={e => setNewProject({ ...newProject, target_capacity_mw: e.target.value })} />
              <label style={lbl}>Region</label>
              <input style={inp} required value={newProject.region} onChange={e => setNewProject({ ...newProject, region: e.target.value })} />
              <label style={lbl}>Planned Timeline (COD)</label>
              <input style={inp} value={newProject.timeline_cod} onChange={e => setNewProject({ ...newProject, timeline_cod: e.target.value })} />
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button type="submit" style={{ flex: 1, padding: '10px', background: '#059669', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Create Project</button>
                <button type="button" onClick={() => setShowProjectModal(false)} style={{ flex: 1, padding: '10px', background: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Add Site with Map Picker */}
      {showSiteModal && (
        <div style={modalBackdrop}>
          <div style={{ ...modalBox, maxWidth: '640px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h3 style={{ margin: 0 }}>Add Candidate Site</h3>
              <button
                type="button"
                onClick={() => setShowMapModal(!showMapModal)}
                style={{ padding: '6px 12px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '12px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                {showMapModal ? 'Hide Map' : '🗺️ Pick on Map'}
              </button>
            </div>

            {showMapModal && (
              <div style={{ height: '240px', borderRadius: '8px', overflow: 'hidden', marginBottom: '14px', border: '1px solid #1e293b' }}>
                <MapContainer center={[newSite.latitude, newSite.longitude]} zoom={6} style={{ height: '100%', width: '100%' }}>
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  <LocationPicker
                    position={[newSite.latitude, newSite.longitude]}
                    onPositionChange={(lat, lng) => setNewSite(prev => ({ ...prev, latitude: parseFloat(lat.toFixed(4)), longitude: parseFloat(lng.toFixed(4)) }))}
                  />
                </MapContainer>
              </div>
            )}

            <form onSubmit={handleCreateSite}>
              <label style={lbl}>Site Name</label>
              <input style={inp} required placeholder="e.g. Bareilly Solar Array" value={newSite.site_name} onChange={e => setNewSite({ ...newSite, site_name: e.target.value })} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={lbl}>Latitude (°N)</label>
                  <input style={inp} type="number" step="0.0001" required value={newSite.latitude} onChange={e => setNewSite({ ...newSite, latitude: e.target.value })} />
                </div>
                <div>
                  <label style={lbl}>Longitude (°E)</label>
                  <input style={inp} type="number" step="0.0001" required value={newSite.longitude} onChange={e => setNewSite({ ...newSite, longitude: e.target.value })} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={lbl}>Elevation (m)</label>
                  <input style={inp} type="number" required value={newSite.elevation_m} onChange={e => setNewSite({ ...newSite, elevation_m: e.target.value })} />
                </div>
                <div>
                  <label style={lbl}>Land Area (km²)</label>
                  <input style={inp} type="number" step="0.1" required value={newSite.land_area_sqkm} onChange={e => setNewSite({ ...newSite, land_area_sqkm: e.target.value })} />
                </div>
              </div>
              <label style={lbl}>Region</label>
              <input style={inp} required value={newSite.region} onChange={e => setNewSite({ ...newSite, region: e.target.value })} />
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button type="submit" style={{ flex: 1, padding: '10px', background: '#059669', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Register Site</button>
                <button type="button" onClick={() => setShowSiteModal(false)} style={{ flex: 1, padding: '10px', background: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: GIS Editor */}
      {showGisEditModal && (
        <div style={modalBackdrop}>
          <div style={{ ...modalBox, maxWidth: '520px' }}>
            <h3 style={{ margin: '0 0 8px 0', color: '#38bdf8' }}>GIS & Terrain Editor</h3>
            <form onSubmit={handleSaveGis}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={lbl}>Latitude</label>
                  <input style={inp} type="number" step="0.0001" value={gisForm.latitude} onChange={e => setGisForm({ ...gisForm, latitude: e.target.value })} />
                </div>
                <div>
                  <label style={lbl}>Longitude</label>
                  <input style={inp} type="number" step="0.0001" value={gisForm.longitude} onChange={e => setGisForm({ ...gisForm, longitude: e.target.value })} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={lbl}>Elevation (m)</label>
                  <input style={inp} type="number" value={gisForm.elevation_m} onChange={e => setGisForm({ ...gisForm, elevation_m: e.target.value })} />
                </div>
                <div>
                  <label style={lbl}>Slope Angle (°)</label>
                  <input style={inp} type="number" step="0.1" value={gisForm.slope_deg} onChange={e => setGisForm({ ...gisForm, slope_deg: e.target.value })} />
                </div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={lbl}>Solar GHI (kWh/m²)</label>
                  <input style={inp} type="number" step="0.01" value={gisForm.solar_ghi} onChange={e => setGisForm({ ...gisForm, solar_ghi: e.target.value })} />
                </div>
                <div>
                  <label style={lbl}>Avg Temp (°C)</label>
                  <input style={inp} type="number" step="0.1" value={gisForm.avg_temp} onChange={e => setGisForm({ ...gisForm, avg_temp: e.target.value })} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                <button type="submit" style={{ flex: 1, padding: '10px', background: '#0284c7', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}>Update GIS Data</button>
                <button type="button" onClick={() => setShowGisEditModal(false)} style={{ flex: 1, padding: '10px', background: '#334155', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: Multi-Site Comparison Matrix */}
      {showComparisonModal && (
        <div style={modalBackdrop}>
          <div style={{ ...modalBox, maxWidth: '960px', width: '90vw' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#f59e0b', fontSize: '20px' }}>
                ⚖️ Multi-Site Comparison Matrix (Module 2)
              </h3>
              <button
                onClick={() => setShowComparisonModal(false)}
                style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '18px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${comparisonSites.length}, 1fr)`, gap: '16px' }}>
              {comparisonSites.map(s => (
                <div key={s.id} style={{ background: '#070d19', border: '1px solid #1e293b', borderRadius: '8px', padding: '16px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#38bdf8', marginBottom: '8px' }}>
                    {s.site_name}
                  </div>
                  <div style={{ borderBottom: '1px solid #142033', paddingBottom: '6px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Coordinates</span>
                    <div style={{ fontSize: '13px' }}>{s.latitude?.toFixed(4)}°N, {s.longitude?.toFixed(4)}°E</div>
                  </div>
                  <div style={{ borderBottom: '1px solid #142033', paddingBottom: '6px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Elevation & Slope</span>
                    <div style={{ fontSize: '13px' }}>{s.elevation_m}m • {s.slope_deg || 2.1}° slope</div>
                  </div>
                  <div style={{ borderBottom: '1px solid #142033', paddingBottom: '6px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Land Area & Ownership</span>
                    <div style={{ fontSize: '13px' }}>{s.land_area_sqkm} km² • {s.land_ownership}</div>
                  </div>
                  <div style={{ borderBottom: '1px solid #142033', paddingBottom: '6px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Solar GHI / Avg Temp</span>
                    <div style={{ fontSize: '13px', color: '#f59e0b' }}>{s.solar_ghi} kWh/m² • {s.avg_temp}°C</div>
                  </div>
                  <div style={{ borderBottom: '1px solid #142033', paddingBottom: '6px', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Capacity Factor / Est Yield</span>
                    <div style={{ fontSize: '13px', color: '#10b981' }}>{s.capacity_factor || 17}% • {s.est_yield_gwh || 1450} GWh</div>
                  </div>
                  <div>
                    <span style={{ fontSize: '11px', color: '#64748b' }}>Approval Status</span>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: s.is_approved ? '#10b981' : '#f59e0b' }}>
                      {s.is_approved ? 'APPROVED' : 'PENDING'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

const inp = { width: '100%', padding: '9px 12px', backgroundColor: '#050a12', border: '1px solid #1e293b', borderRadius: '6px', color: '#fff', marginTop: '4px', marginBottom: '12px', boxSizing: 'border-box' };
const lbl = { fontSize: '12px', color: '#94a3b8', display: 'block', fontWeight: 500 };
const modalBackdrop = { position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '20px' };
const modalBox = { backgroundColor: '#0d1526', border: '1px solid #1e293b', borderRadius: '12px', padding: '24px', width: '100%', maxWidth: '440px' };
const metricBoxStyle = { backgroundColor: '#060c16', border: '1px solid #132034', borderRadius: '6px', padding: '10px', display: 'flex', flexDirection: 'column', gap: '4px' };
const metricLbl = { fontSize: '11px', color: '#64748b' };
const metricVal = { fontSize: '13px', fontWeight: 'bold', color: '#e2e8f0' };
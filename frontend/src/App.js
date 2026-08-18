import React, { useState, useEffect } from 'react';
import { registerUser, loginUser, createProject, registerSite, getProjects, getSites, getAllUsers, getProjectAnalytics } from './api';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow, iconAnchor: [12, 41], popupAnchor: [1, -34] });
L.Marker.prototype.options.icon = DefaultIcon;

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [activeUser, setActiveUser] = useState({ id: null, name: '', role: '' });
  const [authMode, setAuthMode] = useState('login'); 
  const [activeTab, setActiveTab] = useState(''); 

  const [authForm, setAuthForm] = useState({ username: '', email: '', password: '', role: 'Renewable Energy Planner' });
  const [projectForm, setProjectForm] = useState({ name: '', description: '' });
  const [siteForm, setSiteForm] = useState({ name: '', latitude: '', longitude: '', region: '', land_area: '', elevation: '', existing_infrastructure: '', land_ownership: '' });
  const [selectedProjectId, setSelectedProjectId] = useState('');
  
  const [projectsList, setProjectsList] = useState([]);
  const [sitesList, setSitesList] = useState([]);
  const [mapSites, setMapSites] = useState([]);
  const [usersList, setUsersList] = useState([]);
  const [analyticsData, setAnalyticsData] = useState([]);

  useEffect(() => {
    if (isLoggedIn) {
      fetchProjects();
      if (activeUser.role === 'Administrator') fetchAllUsers();
    }
  }, [isLoggedIn, activeUser.role]);

  const fetchProjects = async () => {
    try {
      const response = await getProjects(activeUser.id);
      setProjectsList(response.data);
    } catch (error) { console.error("Failed to fetch projects"); }
  };

  const loadSitesForProject = async (projectId) => {
    try {
      const siteRes = await getSites(projectId);
      setSitesList(siteRes.data);
      setMapSites(siteRes.data);
      
      const analyticsRes = await getProjectAnalytics(projectId);
      setAnalyticsData(analyticsRes.data);
    } catch (error) { console.error("Failed to fetch project details"); }
  };

  const fetchAllUsers = async () => {
    try {
      const response = await getAllUsers();
      setUsersList(response.data);
    } catch (error) { console.error("Failed to fetch users"); }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    try {
      if (authMode === 'register') {
        await registerUser({ full_name: authForm.username, email: authForm.email, password: authForm.password, role_name: authForm.role });
        alert('Registration successful! Please log in.');
        setAuthMode('login');
      } else {
        const response = await loginUser({ email: authForm.email, password: authForm.password });
        setActiveUser({ id: response.data.user_id, name: response.data.full_name, role: response.data.role });
        setIsLoggedIn(true);
        
        if (response.data.role === 'Renewable Energy Planner') setActiveTab('planner_forecasts');
        if (response.data.role === 'GIS Analyst') setActiveTab('gis_visualization');
        if (response.data.role === 'Project Manager') setActiveTab('pm_progress');
        if (response.data.role === 'Administrator') setActiveTab('admin_users');
      }
    } catch (error) { alert('Authentication Failed. Check credentials.'); }
  };

  const handleProjectSubmit = async (e) => {
    e.preventDefault();
    try {
      await createProject(activeUser.id, projectForm);
      alert(`Project Created Successfully!`);
      setProjectForm({ name: '', description: '' });
      fetchProjects();
      setActiveTab('pm_progress');
    } catch (error) { alert('Error creating project'); }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setActiveUser({ id: null, name: '', role: '' });
    setActiveTab('');
  };

  const ProjectLogo = ({ size = 40, color = "#3b82f6" }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2v2"></path><path d="M12 20v2"></path><path d="M4.93 4.93l1.41 1.41"></path><path d="M17.66 17.66l1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="M6.34 17.66l-1.41 1.41"></path><path d="M19.07 4.93l-1.41 1.41"></path><circle cx="12" cy="12" r="4"></circle>
    </svg>
  );

  const mapCenter = mapSites.length > 0 ? [mapSites[0].lat || mapSites[0].latitude, mapSites[0].lon || mapSites[0].longitude] : [22.8120, 75.8911];

  if (!isLoggedIn) {
    return (
      <div style={{ display: 'flex', height: '100vh', backgroundColor: '#f8fafc' }}>
        <div style={{ flex: 1.2, display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '60px', color: 'white', backgroundImage: "linear-gradient(rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.9)), url('https://images.unsplash.com/photo-1466611653911-95081537e5b7?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80')", backgroundSize: 'cover' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '30px' }}><div style={{ backgroundColor: 'white', padding: '10px', borderRadius: '12px' }}><ProjectLogo size={32} color="#0f172a" /></div><h1 style={{ fontSize: '28px', margin: 0, fontWeight: '700' }}>Solar & Wind Intelligence</h1></div>
          <h2 style={{ fontSize: '42px', fontWeight: '800', lineHeight: '1.2' }}>Deploy renewable energy with AI-driven precision.</h2>
        </div>
        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', backgroundColor: 'white', padding: '40px' }}>
          <div style={{ width: '100%', maxWidth: '420px' }}>
            <div style={{ textAlign: 'center', marginBottom: '40px' }}><div style={{ display: 'flex', justifyContent: 'center', marginBottom: '15px' }}><ProjectLogo size={48} color="#3b82f6" /></div><h2 style={{ color: '#0f172a', fontSize: '26px', margin: '0 0 10px', fontWeight: '700' }}>{authMode === 'login' ? 'Welcome Back' : 'Create an Account'}</h2></div>
            <form onSubmit={handleAuthSubmit} style={styles.formGrid}>
              {authMode === 'register' && ( <input style={styles.input} placeholder="Full Name" required onChange={e => setAuthForm({...authForm, username: e.target.value})} /> )}
              <input style={styles.input} type="email" placeholder="Email Address" required onChange={e => setAuthForm({...authForm, email: e.target.value})} />
              <input style={styles.input} type="password" placeholder="Password" required onChange={e => setAuthForm({...authForm, password: e.target.value})} />
              {authMode === 'register' && (
                <select style={styles.input} onChange={e => setAuthForm({...authForm, role: e.target.value})}>
                  <option>Renewable Energy Planner</option>
                  <option>GIS Analyst</option>
                  <option>Project Manager</option>
                  <option>Administrator</option>
                </select>
              )}
              <button style={styles.primaryButton} type="submit">{authMode === 'login' ? 'Sign In' : 'Register Now'}</button>
            </form>
            <p style={styles.switchAuth} onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>{authMode === 'login' ? "Don't have an account? Sign up" : "Already have an account? Sign in"}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.dashboardLayout}>
      <div style={styles.sidebar}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '40px' }}><ProjectLogo size={32} color="white" /><h3 style={{ color: 'white', margin: 0, fontSize: '18px' }}>Intelligence</h3></div>
        <div style={styles.userBadge}>{activeUser.name.charAt(0).toUpperCase()}</div>
        <p style={styles.welcomeText}>Welcome back,<br/><span style={{color: 'white', fontWeight: 'bold'}}>{activeUser.name}</span></p>
        <p style={{ color: '#3b82f6', fontSize: '12px', fontWeight: 'bold', marginTop: '-35px', marginBottom: '30px', textTransform: 'uppercase', letterSpacing: '1px' }}>Role: {activeUser.role}</p>
        
        <div style={styles.navGroup}>
          
          {/* RENEWABLE ENERGY PLANNER */}
          {activeUser.role === 'Renewable Energy Planner' && (
            <>
              <button style={activeTab === 'planner_forecasts' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('planner_forecasts')}>📈 Energy Forecasts</button>
              <button style={activeTab === 'planner_scores' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('planner_scores')}>🎯 Suitability Scores</button>
              <button style={activeTab === 'planner_investment' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('planner_investment')}>💰 Investment Recs</button>
            </>
          )}

          {/* GIS ANALYST */}
          {activeUser.role === 'GIS Analyst' && (
            <>
              <button style={activeTab === 'gis_visualization' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('gis_visualization')}>🌍 GIS Visualization</button>
              <button style={activeTab === 'gis_analytics' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('gis_analytics')}>🌱 Environmental Analytics</button>
              <button style={activeTab === 'gis_comparison' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('gis_comparison')}>📊 Site Comparison</button>
            </>
          )}

          {/* PROJECT MANAGER (Includes Project Initialization) */}
          {activeUser.role === 'Project Manager' && (
            <>
              <button style={activeTab === 'pm_create' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('pm_create')}>📁 Initialize Project</button>
              <button style={activeTab === 'pm_progress' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('pm_progress')}>📋 Project Progress</button>
              <button style={activeTab === 'pm_cost' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('pm_cost')}>💵 Cost-Benefit Analysis</button>
              <button style={activeTab === 'pm_timelines' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('pm_timelines')}>⏳ Deployment Timelines</button>
            </>
          )}

          {/* ADMINISTRATOR */}
          {activeUser.role === 'Administrator' && (
            <>
              <button style={activeTab === 'pm_create' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('pm_create')}>📁 Initialize Project</button>
              <button style={activeTab === 'admin_users' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('admin_users')}>👥 User Management</button>
              <button style={activeTab === 'admin_analytics' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('admin_analytics')}>📈 Platform Analytics</button>
              <button style={activeTab === 'admin_system' ? styles.activeNavBtn : styles.navBtn} onClick={() => setActiveTab('admin_system')}>⚙️ System Monitoring</button>
            </>
          )}

        </div>
        <button style={styles.logoutBtn} onClick={handleLogout}>🚪 Logout</button>
      </div>

      <div style={styles.mainContent}>
        
        {/* PROJECT SELECTOR FOR ANALYTICS TABS */}
        {activeUser.role !== 'Administrator' && activeTab !== 'pm_create' && (
          <div style={{ marginBottom: '30px', display: 'flex', gap: '15px' }}>
             <select style={{...styles.input, width: '300px'}} onChange={(e) => loadSitesForProject(e.target.value)}>
                <option value="">-- Select Active Project to Analyze --</option>
                {projectsList.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
          </div>
        )}

        {/* --- PROJECT MANAGER: INITIALIZE PROJECT --- */}
        {activeTab === 'pm_create' && (
          <div style={styles.formCard}>
            <h2 style={styles.pageHeader}>Initialize New Project</h2>
            <form onSubmit={handleProjectSubmit} style={styles.formGrid}>
              <input style={styles.input} placeholder="Project Name" required value={projectForm.name} onChange={e => setProjectForm({...projectForm, name: e.target.value})} />
              <textarea style={{...styles.input, height: '120px'}} placeholder="Detailed Description & Objectives" required value={projectForm.description} onChange={e => setProjectForm({...projectForm, description: e.target.value})} />
              <button style={styles.primaryButton} type="submit">Deploy Project</button>
            </form>
          </div>
        )}

        {/* --- RENEWABLE ENERGY PLANNER DASHBOARDS --- */}
        {activeTab === 'planner_forecasts' && (
          <div>
            <h2 style={styles.pageHeader}>Energy Generation Forecasts</h2>
            <div style={styles.chartCard}>
              {analyticsData.length === 0 ? <p style={styles.mutedText}>Select a project from the dropdown above to view forecasts.</p> : analyticsData.map((data, idx) => (
                <div key={idx} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px', color: '#475569', fontWeight: '600' }}>
                    <span>{data.site_name}</span>
                    <span>{data.solar_forecast_mw} MW Solar | {data.wind_forecast_mw} MW Wind</span>
                  </div>
                  <div style={{ width: '100%', backgroundColor: '#f1f5f9', borderRadius: '4px', height: '10px', marginBottom: '4px' }}>
                    <div style={{ width: `${Math.min(data.solar_forecast_mw * 2, 100)}%`, backgroundColor: '#eab308', height: '100%', borderRadius: '4px' }}></div>
                  </div>
                  <div style={{ width: '100%', backgroundColor: '#f1f5f9', borderRadius: '4px', height: '10px' }}>
                    <div style={{ width: `${Math.min(data.wind_forecast_mw * 2, 100)}%`, backgroundColor: '#3b82f6', height: '100%', borderRadius: '4px' }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'planner_scores' && (
          <div>
            <h2 style={styles.pageHeader}>Site Suitability Scores</h2>
            <div style={styles.chartCard}>
              {analyticsData.length === 0 ? <p style={styles.mutedText}>Select a project to view suitability.</p> : analyticsData.map((data, idx) => (
                <div key={idx} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px', color: '#475569', fontWeight: '600' }}>
                    <span>{data.site_name}</span>
                    <span style={{ color: data.suitability_score > 80 ? '#16a34a' : '#ea580c' }}>{data.suitability_score} / 100</span>
                  </div>
                  <div style={{ width: '100%', backgroundColor: '#f1f5f9', borderRadius: '4px', height: '12px' }}>
                    <div style={{ width: `${data.suitability_score}%`, backgroundColor: data.suitability_score > 80 ? '#16a34a' : '#ea580c', height: '100%', borderRadius: '4px' }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- GIS ANALYST DASHBOARDS --- */}
        {activeTab === 'gis_visualization' && (
          <div style={{ ...styles.formCard, padding: '0', overflow: 'hidden', height: '75vh', maxWidth: '100%' }}>
            <MapContainer key={`${mapCenter[0]}-${mapCenter[1]}`} center={mapCenter} zoom={7} style={{ height: '100%', width: '100%' }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {mapSites.map((site, idx) => (
                <Marker key={idx} position={[site.lat || site.latitude, site.lon || site.longitude]}>
                  <Popup><strong>{site.name}</strong><br/>Area: {site.area} sq km</Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}
        
        {activeTab === 'gis_comparison' && (
           <div>
             <h2 style={styles.pageHeader}>Site Comparison Reports</h2>
             <div style={{ overflowX: 'auto', backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', border: '1px solid #e2e8f0' }}>
               <table style={styles.table}>
                 <thead style={{ backgroundColor: '#f8fafc' }}>
                   <tr><th style={styles.tableHeader}>Site Name</th><th style={styles.tableHeader}>Region</th><th style={styles.tableHeader}>Area (sq km)</th><th style={styles.tableHeader}>Coordinates</th></tr>
                 </thead>
                 <tbody>
                   {sitesList.map(site => (
                     <tr key={site.id}>
                       <td style={styles.tableCell}><strong style={{color: '#0f172a'}}>{site.name}</strong></td>
                       <td style={styles.tableCell}>{site.region}</td><td style={styles.tableCell}>{site.area}</td><td style={styles.tableCell}>{site.lat}, {site.lon}</td>
                     </tr>
                   ))}
                 </tbody>
               </table>
             </div>
           </div>
        )}

        {/* --- PROJECT MANAGER DASHBOARDS --- */}
        {activeTab === 'pm_progress' && (
          <div>
            <h2 style={styles.pageHeader}>Project Progress & Status</h2>
            <div style={styles.gridContainer}>
              {projectsList.length === 0 ? <p style={styles.mutedText}>No active projects found. Use "Initialize Project" to create one.</p> : 
                projectsList.map(proj => (
                  <div key={proj.id} style={styles.dataCard}>
                    <div style={styles.statusBadge}>{proj.status}</div>
                    <h3 style={{marginTop: '15px', color: '#1e293b'}}>{proj.name}</h3>
                    <p style={styles.mutedText}>{proj.desc}</p>
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {activeTab === 'pm_cost' && (
          <div>
            <h2 style={styles.pageHeader}>Cost-Benefit Analysis</h2>
            <div style={styles.chartCard}>
              {analyticsData.length === 0 ? <p style={styles.mutedText}>Select a project to view revenue metrics.</p> : analyticsData.map((data, idx) => (
                <div key={idx} style={{ marginBottom: '20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px', color: '#475569', fontWeight: '600' }}>
                    <span>{data.site_name}</span>
                    <span>${data.est_revenue_usd.toLocaleString()} / year</span>
                  </div>
                  <div style={{ width: '100%', backgroundColor: '#f1f5f9', borderRadius: '4px', height: '16px' }}>
                    <div style={{ width: `${Math.min((data.est_revenue_usd / 1500000) * 100, 100)}%`, backgroundColor: '#10b981', height: '100%', borderRadius: '4px' }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- ADMINISTRATOR DASHBOARD --- */}
        {activeTab === 'admin_users' && (
          <div>
            <h2 style={styles.pageHeader}>User Management</h2>
            <div style={{ overflowX: 'auto', backgroundColor: 'white', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', border: '1px solid #e2e8f0' }}>
              <table style={styles.table}>
                <thead style={{ backgroundColor: '#f8fafc' }}>
                  <tr><th style={styles.tableHeader}>User Name</th><th style={styles.tableHeader}>Email</th><th style={styles.tableHeader}>System Role</th><th style={styles.tableHeader}>Status</th></tr>
                </thead>
                <tbody>
                  {usersList.map(user => (
                    <tr key={user.id}>
                      <td style={styles.tableCell}><strong>{user.name}</strong></td>
                      <td style={styles.tableCell}>{user.email}</td>
                      <td style={styles.tableCell}><span style={{ padding: '4px 10px', backgroundColor: '#f1f5f9', borderRadius: '6px', fontSize: '12px', fontWeight: '600' }}>{user.role}</span></td>
                      <td style={styles.tableCell}>{user.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* PENDINGS PLACEHOLDER */}
        {(activeTab === 'planner_investment' || activeTab === 'gis_analytics' || activeTab === 'pm_timelines' || activeTab === 'admin_analytics' || activeTab === 'admin_system') && (
            <div style={styles.chartCard}>
                <h3 style={{ color: '#0f172a' }}>Module In Development</h3>
                <p style={styles.mutedText}>This specific intelligence module is scheduled for the next agile sprint.</p>
            </div>
        )}

      </div>
    </div>
  );
}

const styles = {
  switchAuth: { textAlign: 'center', marginTop: '25px', fontSize: '14px', cursor: 'pointer', color: '#3b82f6', fontWeight: '600' },
  formGrid: { display: 'flex', flexDirection: 'column', gap: '16px' },
  input: { padding: '14px 16px', borderRadius: '8px', fontSize: '15px', backgroundColor: '#f8fafc', color: '#334155', border: '1px solid #e2e8f0' },
  primaryButton: { padding: '14px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px', fontSize: '15px', fontWeight: '600', cursor: 'pointer' },
  dashboardLayout: { display: 'flex', height: '100vh', backgroundColor: '#f1f5f9' },
  sidebar: { width: '280px', backgroundColor: '#0f172a', padding: '30px 24px', display: 'flex', flexDirection: 'column' },
  userBadge: { width: '48px', height: '48px', backgroundColor: '#334155', color: 'white', borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', fontSize: '20px', fontWeight: 'bold', marginBottom: '15px' },
  welcomeText: { color: '#94a3b8', fontSize: '13px', marginBottom: '40px', lineHeight: '1.6' },
  navGroup: { display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1 },
  navBtn: { padding: '14px 16px', backgroundColor: 'transparent', color: '#94a3b8', border: 'none', textAlign: 'left', fontSize: '15px', cursor: 'pointer', borderRadius: '8px', fontWeight: '500' },
  activeNavBtn: { padding: '14px 16px', backgroundColor: '#1e293b', color: 'white', border: 'none', textAlign: 'left', fontSize: '15px', cursor: 'pointer', borderRadius: '8px', fontWeight: '600' },
  logoutBtn: { padding: '14px', backgroundColor: 'transparent', color: '#ef4444', border: '1px solid #ef4444', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' },
  mainContent: { flexGrow: 1, padding: '50px 60px', overflowY: 'auto' },
  pageHeader: { color: '#0f172a', fontSize: '24px', marginBottom: '30px', fontWeight: '700' },
  formCard: { backgroundColor: 'white', padding: '40px', borderRadius: '16px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', maxWidth: '900px' },
  gridContainer: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' },
  dataCard: { backgroundColor: 'white', padding: '25px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)', cursor: 'pointer', border: '1px solid #e2e8f0', transition: 'transform 0.2s' },
  chartCard: { backgroundColor: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)', border: '1px solid #e2e8f0', marginBottom: '20px' },
  statusBadge: { display: 'inline-block', padding: '4px 10px', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '20px', fontSize: '12px', fontWeight: '600' },
  mutedText: { color: '#64748b', fontSize: '14px', lineHeight: '1.5' },
  table: { width: '100%', borderCollapse: 'collapse' },
  tableHeader: { padding: '16px 24px', textAlign: 'left', borderBottom: '2px solid #e2e8f0', color: '#64748b', fontWeight: '600', fontSize: '13px', textTransform: 'uppercase' },
  tableCell: { padding: '16px 24px', borderBottom: '1px solid #f1f5f9', color: '#475569', fontSize: '15px' },
};

export default App;
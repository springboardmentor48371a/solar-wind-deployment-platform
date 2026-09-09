import React, { useState, useEffect } from 'react'
import { Sun, Wind, ShieldAlert, LogOut, Plus, MapPin, BarChart3, Settings as SettingsIcon, FileSpreadsheet, Bell, RefreshCw } from 'lucide-react'
import Dashboard from './components/Dashboard'
import MapView from './components/MapView'
import WeightSettings from './components/WeightSettings'
import SiteList from './components/SiteList'
import SiteDetails from './components/SiteDetails'

const API_BASE = 'http://localhost:8000/api'

export default function App() {
  // Auth state
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [role, setRole] = useState(localStorage.getItem('role') || '')
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '')
  const [fullName, setFullName] = useState(localStorage.getItem('fullName') || '')
  
  // Login Form
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)
  const [regName, setRegName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regPhone, setRegPhone] = useState('')
  const [regOrg, setRegOrg] = useState('')
  const [regRole, setRegRole] = useState('Planner')
  const [error, setError] = useState('')

  // App state
  const [projects, setProjects] = useState([])
  const [activeProject, setActiveProject] = useState(null)
  const [sites, setSites] = useState([])
  const [activeSite, setActiveSite] = useState(null)
  const [infraData, setInfraData] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [showWeightsModal, setShowWeightsModal] = useState(false)
  
  // Suitability Weights state
  const [weights, setWeights] = useState({
    weight_resource: 0.35,
    weight_geographic: 0.25,
    weight_infrastructure: 0.15,
    weight_environment: 0.15,
    weight_economic: 0.10
  })

  // Create Project Form
  const [showCreateProj, setShowCreateProj] = useState(false)
  const [newProjName, setNewProjName] = useState('')
  const [newProjDesc, setNewProjDesc] = useState('')
  const [newProjRegion, setNewProjRegion] = useState('Gujarat/Rajasthan')

  // Create Site Mode
  const [clickCoords, setClickCoords] = useState(null)
  const [showCreateSite, setShowCreateSite] = useState(false)
  const [newSiteName, setNewSiteName] = useState('')
  const [newSiteArea, setNewSiteArea] = useState(100)
  const [newSiteType, setNewSiteType] = useState('Desert')
  const [newSiteOwnership, setNewSiteOwnership] = useState('Government')

  // Alert/Notification poll
  useEffect(() => {
    if (token) {
      fetchProjects()
      fetchInfrastructure()
      fetchNotifications()
    }
  }, [token])

  useEffect(() => {
    if (activeProject) {
      fetchSites(activeProject.project_id)
    }
  }, [activeProject])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Login failed')
      }
      const data = await res.json()
      
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('role', data.role)
      localStorage.setItem('userId', data.user_id)
      localStorage.setItem('fullName', data.full_name)
      
      setToken(data.access_token)
      setRole(data.role)
      setUserId(data.user_id)
      setFullName(data.full_name)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: regName,
          email: regEmail,
          password: regPassword,
          phone_number: regPhone,
          organization: regOrg,
          role_name: regRole
        })
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Registration failed')
      }
      setIsRegistering(false)
      setEmail(regEmail)
      setPassword(regPassword)
      setError('Registration successful! Please log in.')
    } catch (err) {
      setError(err.message)
    }
  }

  const handleLogout = () => {
    localStorage.clear()
    setToken('')
    setRole('')
    setUserId('')
    setFullName('')
    setProjects([])
    setSites([])
    setActiveProject(null)
    setActiveSite(null)
  }

  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_BASE}/projects`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (res.ok) {
        const data = await res.json()
        setProjects(data)
        if (data.length > 0 && !activeProject) {
          setActiveProject(data[0])
        }
      }
    } catch (err) {
      console.error(err)
    }
  }

  const fetchSites = async (projId) => {
    try {
      const res = await fetch(`${API_BASE}/sites?project_id=${projId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (res.ok) {
        const data = await res.json()
        setSites(data)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const fetchInfrastructure = async () => {
    try {
      const res = await fetch(`${API_BASE}/infrastructure`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (res.ok) {
        const data = await res.json()
        setInfraData(data)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API_BASE}/notifications`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (res.ok) {
        const data = await res.json()
        setNotifications(data)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleCreateProject = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch(`${API_BASE}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          project_name: newProjName,
          description: newProjDesc,
          region: newProjRegion
        })
      })
      if (res.ok) {
        const newProj = await res.json()
        setProjects([...projects, newProj])
        setActiveProject(newProj)
        setShowCreateProj(false)
        setNewProjName('')
        setNewProjDesc('')
        fetchNotifications()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleCreateSite = async (e) => {
    e.preventDefault()
    if (!clickCoords) return
    try {
      const res = await fetch(`${API_BASE}/sites`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          project_id: activeProject.project_id,
          site_name: newSiteName,
          latitude: clickCoords.lat,
          longitude: clickCoords.lng,
          land_area: parseFloat(newSiteArea),
          land_type: newSiteType,
          ownership: newSiteOwnership
        })
      })
      if (res.ok) {
        const newSite = await res.json()
        setSites([...sites, newSite])
        setActiveSite(newSite)
        setShowCreateSite(false)
        setClickCoords(null)
        setNewSiteName('')
        fetchNotifications()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleRecalculateWeights = async (newWeights) => {
    setWeights(newWeights)
    if (!activeSite) return
    try {
      const res = await fetch(`${API_BASE}/sites/${activeSite.site_id}/recalculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newWeights)
      })
      if (res.ok) {
        const updatedAssess = await res.json()
        // Update local activeSite
        const updatedSite = {
          ...activeSite,
          assessments: [updatedAssess]
        }
        setActiveSite(updatedSite)
        // Update sites list
        setSites(sites.map(s => s.site_id === activeSite.site_id ? updatedSite : s))
      }
    } catch (err) {
      console.error(err)
    }
  }

  const markNotificationRead = async (notifId) => {
    try {
      const res = await fetch(`${API_BASE}/notifications/${notifId}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      if (res.ok) {
        setNotifications(notifications.map(n => n.notification_id === notifId ? { ...n, is_read: true } : n))
      }
    } catch (err) {
      console.error(err)
    }
  }

  // --- Auth View Layout ---
  if (!token) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', background: 'radial-gradient(circle at center, #0f172a, #020617)', padding: '20px' }}>
        <div className="glass-card" style={{ width: '100%', maxLength: '20px', maxWidth: '440px', padding: '35px', boxShadow: '0 20px 40px rgba(0,0,0,0.5)' }}>
          <div style={{ textAlign: 'center', marginBottom: '30px' }}>
            <div style={{ display: 'inline-flex', gap: '8px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '50%', marginBottom: '15px' }}>
              <Sun size={28} color="var(--solar)" style={{ filter: 'drop-shadow(0 0 8px var(--solar-glow))' }} />
              <Wind size={28} color="var(--wind)" style={{ filter: 'drop-shadow(0 0 8px var(--wind-glow))' }} />
            </div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: '700', marginBottom: '5px' }}>Solar & Wind</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Deployment Intelligence Platform</p>
          </div>

          {error && (
            <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', padding: '10px 14px', borderRadius: '8px', fontSize: '0.875rem', marginBottom: '20px' }}>
              {error}
            </div>
          )}

          {!isRegistering ? (
            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: '15px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Email Address</label>
                <input className="form-input" type="email" placeholder="e.g. planner@renewable.in" required value={email} onChange={e => setEmail(e.target.value)} />
              </div>
              <div style={{ marginBottom: '25px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Password</label>
                <input className="form-input" type="password" placeholder="••••••••" required value={password} onChange={e => setPassword(e.target.value)} />
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px' }}>
                Sign In
              </button>
              <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Don't have an account?{' '}
                <button type="button" onClick={() => setIsRegistering(true)} style={{ background: 'none', border: 'none', color: 'var(--solar)', fontWeight: '600', cursor: 'pointer', outline: 'none' }}>
                  Register here
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Full Name</label>
                <input className="form-input" type="text" placeholder="Your Name" required value={regName} onChange={e => setRegName(e.target.value)} />
              </div>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Email Address</label>
                <input className="form-input" type="email" placeholder="Your Email" required value={regEmail} onChange={e => setRegEmail(e.target.value)} />
              </div>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Password</label>
                <input className="form-input" type="password" placeholder="Min. 6 characters" required value={regPassword} onChange={e => setRegPassword(e.target.value)} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Phone</label>
                  <input className="form-input" type="text" placeholder="Phone Number" value={regPhone} onChange={e => setRegPhone(e.target.value)} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Organization</label>
                  <input className="form-input" type="text" placeholder="Company/Govt" value={regOrg} onChange={e => setRegOrg(e.target.value)} />
                </div>
              </div>
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600', marginBottom: '6px' }}>Assigned Platform Role</label>
                <select className="form-input" value={regRole} onChange={e => setRegRole(e.target.value)} style={{ paddingRight: '30px' }}>
                  <option value="Planner">Planner</option>
                  <option value="GIS Analyst">GIS Analyst</option>
                  <option value="Project Manager">Project Manager</option>
                  <option value="Admin">Administrator</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '12px' }}>
                Create Account
              </button>
              <div style={{ textAlign: 'center', marginTop: '20px', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                Already registered?{' '}
                <button type="button" onClick={() => setIsRegistering(false)} style={{ background: 'none', border: 'none', color: 'var(--solar)', fontWeight: '600', cursor: 'pointer', outline: 'none' }}>
                  Sign In
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    )
  }

  // --- Dashboard View Layout ---
  return (
    <div className="dashboard-grid">
      {/* Left Sidebar */}
      <div style={{ background: 'var(--bg-secondary)', borderRight: '1px solid var(--glass-border)', padding: '24px', display: 'flex', flexDirection: 'column', height: '100vh', justifyContent: 'space-between' }}>
        <div>
          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '30px' }}>
            <Sun size={24} color="var(--solar)" style={{ filter: 'drop-shadow(0 0 6px var(--solar-glow))' }} />
            <h2 style={{ fontSize: '1.25rem', fontWeight: '700', fontFamily: 'var(--font-display)' }}>Renewable IQ</h2>
          </div>

          {/* User Profile Info */}
          <div className="glass-card" style={{ padding: '12px 16px', marginBottom: '24px', background: 'rgba(255,255,255,0.02)' }}>
            <p style={{ fontSize: '0.875rem', fontWeight: '600' }}>{fullName}</p>
            <p style={{ fontSize: '0.75rem', color: 'var(--solar)', fontWeight: '600', display: 'inline-block', padding: '2px 6px', background: 'var(--solar-glow)', borderRadius: '4px', marginTop: '4px' }}>
              {role}
            </p>
          </div>

          {/* Project Selector */}
          <div style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'between', marginBottom: '10px' }}>
              <label style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)', fontWeight: '600' }}>Current Project</label>
              {(role === 'Planner' || role === 'Project Manager' || role === 'Admin') && (
                <button onClick={() => setShowCreateProj(true)} style={{ background: 'none', border: 'none', color: 'var(--solar)', cursor: 'pointer', outline: 'none', display: 'inline-flex' }}>
                  <Plus size={16} />
                </button>
              )}
            </div>
            {showCreateProj ? (
              <form onSubmit={handleCreateProject} className="glass-card" style={{ padding: '12px', background: 'var(--bg-tertiary)' }}>
                <input className="form-input" style={{ fontSize: '0.875rem', marginBottom: '8px' }} type="text" placeholder="Project Name" required value={newProjName} onChange={e => setNewProjName(e.target.value)} />
                <input className="form-input" style={{ fontSize: '0.875rem', marginBottom: '8px' }} type="text" placeholder="Region (e.g. Gujarat)" required value={newProjRegion} onChange={e => setNewProjRegion(e.target.value)} />
                <textarea className="form-input" style={{ fontSize: '0.875rem', marginBottom: '8px', height: '60px' }} placeholder="Description..." value={newProjDesc} onChange={e => setNewProjDesc(e.target.value)} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
                  <button type="submit" className="btn btn-primary" style={{ padding: '6px', fontSize: '0.75rem' }}>Save</button>
                  <button type="button" className="btn btn-secondary" style={{ padding: '6px', fontSize: '0.75rem' }} onClick={() => setShowCreateProj(false)}>Cancel</button>
                </div>
              </form>
            ) : (
              <select className="form-input" value={activeProject?.project_id || ''} onChange={e => {
                const proj = projects.find(p => p.project_id === e.target.value)
                if (proj) setActiveProject(proj)
              }}>
                {projects.map(p => (
                  <option key={p.project_id} value={p.project_id}>{p.project_name}</option>
                ))}
              </select>
            )}
          </div>

          {/* Navigation Items */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start', background: 'rgba(255,255,255,0.03)' }} onClick={() => setShowWeightsModal(true)}>
              <SettingsIcon size={16} /> Suitability Weights
            </button>
          </div>
        </div>

        {/* Logout Button */}
        <div>
          <button className="btn btn-secondary" onClick={handleLogout} style={{ width: '100%', justifyContent: 'center', borderColor: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5' }}>
            <LogOut size={16} /> Sign Out
          </button>
        </div>
      </div>

      {/* Main Panel */}
      <div className="main-content">
        {/* Top Header / Warning Badge */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: '700' }}>{activeProject ? activeProject.project_name : 'No Project Selected'}</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>Region: {activeProject ? activeProject.region : 'Indian Hubs'}</p>
          </div>

          {/* Demo Mode Warn Badge */}
          {activeSite?.assessments?.[0]?.is_hybrid_mode ? (
            <div className="demo-banner" style={{ background: 'rgba(245, 158, 11, 0.15)', borderColor: 'rgba(245, 158, 11, 0.3)', color: '#fcd34d' }}>
              <ShieldAlert size={18} />
              <span>Hybrid Mode — Real Wind ML / Synthetic Solar Fallback</span>
            </div>
          ) : activeSite?.assessments?.[0]?.is_synthetic === false ? (
            <div className="demo-banner" style={{ background: 'rgba(16, 185, 129, 0.15)', borderColor: 'rgba(16, 185, 129, 0.3)', color: '#6ee7b7' }}>
              <ShieldAlert size={18} />
              <span>Production Mode — Real Historical ML Predictors</span>
            </div>
          ) : (
            <div className="demo-banner">
              <ShieldAlert size={18} />
              <span>Active Demo Mode — Displaying Synthetic ML Predictor Yields</span>
            </div>
          )}
        </div>

        {/* Top Stats & Dashboard Widgets */}
        <Dashboard activeProject={activeProject} token={token} sites={sites} />

        {/* Map & Sites split view */}
        <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '24px', height: '500px' }}>
          
          {/* Sites Directory */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '100%', padding: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: '600' }}>Candidate Sites ({sites.length})</h3>
              <button className="btn btn-secondary" style={{ padding: '6px 10px', fontSize: '0.75rem' }} onClick={() => fetchSites(activeProject?.project_id)}>
                <RefreshCw size={12} /> Reload
              </button>
            </div>
            <SiteList sites={sites} activeSite={activeSite} onSelect={site => {
              setActiveSite(site)
            }} />
          </div>

          {/* Leaflet Spatial Map */}
          <div className="glass-card" style={{ height: '100%', padding: '0', overflow: 'hidden', position: 'relative' }}>
            {showCreateSite && clickCoords && (
              <div className="glass-card" style={{ position: 'absolute', top: '15px', left: '15px', zIndex: 1000, width: '280px', padding: '15px', background: 'rgba(15,20,32,0.95)', border: '1px solid var(--solar)' }}>
                <h4 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '10px', color: 'var(--solar)' }}>Register Selected Location</h4>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>Lat: {clickCoords.lat.toFixed(4)}, Lng: {clickCoords.lng.toFixed(4)}</p>
                <form onSubmit={handleCreateSite}>
                  <div style={{ marginBottom: '8px' }}>
                    <input className="form-input" style={{ fontSize: '0.75rem', padding: '6px 8px' }} type="text" placeholder="Site Name" required value={newSiteName} onChange={e => setNewSiteName(e.target.value)} />
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '10px' }}>
                    <div>
                      <label style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Area (Acres)</label>
                      <input className="form-input" style={{ fontSize: '0.75rem', padding: '6px' }} type="number" required value={newSiteArea} onChange={e => setNewSiteArea(e.target.value)} />
                    </div>
                    <div>
                      <label style={{ fontSize: '0.65rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Land Type</label>
                      <select className="form-input" style={{ fontSize: '0.75rem', padding: '6px' }} value={newSiteType} onChange={e => setNewSiteType(e.target.value)}>
                        <option value="Desert">Desert</option>
                        <option value="Barren">Barren</option>
                        <option value="Plain">Plain</option>
                        <option value="Agricultural">Agricultural</option>
                      </select>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '15fr 10fr', gap: '6px' }}>
                    <button type="submit" className="btn btn-primary" style={{ padding: '6px', fontSize: '0.75rem' }}>Create Site</button>
                    <button type="button" className="btn btn-secondary" style={{ padding: '6px', fontSize: '0.75rem' }} onClick={() => {
                      setShowCreateSite(false)
                      setClickCoords(null)
                    }}>Cancel</button>
                  </div>
                </form>
              </div>
            )}
            
            <MapView 
              sites={sites} 
              infraData={infraData} 
              activeSite={activeSite} 
              onSiteSelect={site => {
                setActiveSite(site)
              }} 
              onMapClick={coords => {
                if (role === 'Planner' || role === 'GIS Analyst' || role === 'Admin') {
                  setClickCoords(coords)
                  setShowCreateSite(true)
                }
              }}
            />
          </div>
        </div>

        {/* Notifications and Reports section */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          
          {/* Notifications feed */}
          <div className="glass-card" style={{ maxHeight: '250px', overflowY: 'auto' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bell size={18} color="var(--solar)" /> Environmental & System Alerts
            </h3>
            {notifications.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No alerts triggered for this project corridor.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {notifications.map(n => (
                  <div key={n.notification_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: n.is_read ? 'transparent' : 'rgba(239, 68, 68, 0.05)', borderLeft: `3px solid ${n.notification_type === 'Weather' ? 'var(--risk)' : 'var(--solar)'}`, borderRadius: '4px' }}>
                    <div>
                      <p style={{ fontSize: '0.875rem', fontWeight: '600', color: n.is_read ? 'var(--text-secondary)' : 'var(--text-primary)' }}>{n.title}</p>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{n.message}</p>
                    </div>
                    {!n.is_read && (
                      <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.65rem' }} onClick={() => markNotificationRead(n.notification_id)}>Mark Read</button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Selected Site detailed panel */}
          <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {activeSite ? (
              <SiteDetails site={activeSite} weights={weights} onRecalculate={handleRecalculateWeights} />
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                <MapPin size={36} style={{ marginBottom: '10px', color: 'var(--text-muted)' }} />
                <p style={{ fontSize: '0.875rem' }}>Select a candidate site from the sidebar or click on the map to evaluate detailed resource potential, capacity factors, and cash flow forecasting.</p>
              </div>
            )}
          </div>
        </div>

        {/* Weights Settings modal overlay */}
        {showWeightsModal && (
          <WeightSettings weights={weights} onSave={w => {
            handleRecalculateWeights(w)
            setShowWeightsModal(false)
          }} onClose={() => setShowWeightsModal(false)} />
        )}
      </div>
    </div>
  )
}

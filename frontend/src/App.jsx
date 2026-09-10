import React, { useState, useRef, useEffect } from 'react';
import { 
  Sun, 
  Wind, 
  Mail, 
  Lock, 
  UserCheck, 
  User, 
  Eye, 
  EyeOff, 
  ChevronDown, 
  Copy, 
  Check, 
  AlertTriangle, 
  AlertCircle, 
  FolderPlus, 
  LogOut,
  MapPin,
  Trash2
} from 'lucide-react';
import MapPickerModal from './components/MapPickerModal';

const API_BASE = 'http://127.0.0.1:8000';

export default function App() {
  // Authentication states
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('Renewable Energy Planner');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [loggedInUser, setLoggedInUser] = useState(null);

  // Profile Dropdown & Sign Out Modal states
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [showSignOutConfirm, setShowSignOutConfirm] = useState(false);
  const [emailCopied, setEmailCopied] = useState(false);
  const dropdownRef = useRef(null);

  const [activeNav, setActiveNav] = useState('projects');

  // Projects State
  const [projects, setProjects] = useState([
    {
      id: 'p1',
      name: 'Tamil Nadu Solar Farm',
      description: 'Large scale solar deployment across Tamil Nadu plains',
      status: 'Planning'
    }
  ]);
  const [selectedProjectId, setSelectedProjectId] = useState('p1');

  // Sites State
  const [sites, setSites] = useState([]);
  const [selectedSiteId, setSelectedSiteId] = useState(null);

  // Modal 1: + New Project Portfolio
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');

  // Modal 2: + Add Site to Project
  const [isAddSiteModalOpen, setIsAddSiteModalOpen] = useState(false);
  const [isLiveMapOpen, setIsLiveMapOpen] = useState(false);
  const [siteIdentifier, setSiteIdentifier] = useState('');
  const [siteLat, setSiteLat] = useState(9.3639);
  const [siteLong, setSiteLong] = useState(78.8395);
  const [siteTech, setSiteTech] = useState('Solar PV');

  const roles = [
    'Renewable Energy Planner',
    'GIS Analyst',
    'Project Manager',
    'Administrator'
  ];

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch Projects from backend
  const fetchProjects = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/projects`);
      if (res.ok) {
        const data = await res.json();
        if (data.length > 0) {
          setProjects(data);
          if (!selectedProjectId) setSelectedProjectId(data[0].id);
        }
      }
    } catch (_) {}
  };

  // Fetch Sites for selected project
  const fetchSitesForProject = async (projId) => {
    if (!projId) {
      setSelectedSiteId(null);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/sites?project_id=${projId}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) {
          setSites(prev => {
            const others = prev.filter(s => String(s.project_id) !== String(projId));
            return [...others, ...data];
          });
          if (data.length > 0) {
            setSelectedSiteId(data[0].id);
          } else {
            setSelectedSiteId(null);
          }
        }
      }
    } catch (_) {}
  };

  useEffect(() => {
    if (loggedInUser) fetchProjects();
  }, [loggedInUser]);

  useEffect(() => {
    if (selectedProjectId) {
      fetchSitesForProject(selectedProjectId);
    }
  }, [selectedProjectId]);

  // Auth Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);

    if (isRegister) {
      if (password !== confirmPassword) {
        setMessage({ type: 'error', text: 'Passwords do not match.' });
        return;
      }
      if (password.length < 6) {
        setMessage({ type: 'error', text: 'Password must be at least 6 characters long.' });
        return;
      }
    }

    setLoading(true);
    const endpoint = isRegister ? `${API_BASE}/api/auth/register` : `${API_BASE}/api/auth/login`;
    const payload = isRegister 
      ? { name: name.trim(), email: email.trim().toLowerCase(), password, confirm_password: confirmPassword, role }
      : { email: email.trim().toLowerCase(), password, role };

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access_token || 'demo-token');
        setLoggedInUser({ name: data.name || name || 'User', role: data.role || role, email: data.email || email });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Authentication failed' });
      }
    } catch (err) {
      setLoggedInUser({ name: name || 'Planner', role: role, email: email });
    } finally {
      setLoading(false);
    }
  };

  // Submit Handler for New Project Portfolio
  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;

    const newProject = {
      id: `p-${Date.now()}`,
      name: newProjectName.trim(),
      description: newProjectDesc.trim() || 'Scope, regional target, or feasibility notes',
      status: 'Planning'
    };

    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProject)
      });
      if (res.ok) {
        const created = await res.json();
        setProjects(prev => [created, ...prev]);
        setSelectedProjectId(created.id);
      } else {
        setProjects(prev => [newProject, ...prev]);
        setSelectedProjectId(newProject.id);
      }
    } catch (_) {
      setProjects(prev => [newProject, ...prev]);
      setSelectedProjectId(newProject.id);
    }

    setNewProjectName('');
    setNewProjectDesc('');
    setIsNewProjectModalOpen(false);
  };

  // Callback when user picks a location on the real-time Leaflet Map
  const handleLocationPickedFromMap = (locationData) => {
    setSiteLat(locationData.lat);
    setSiteLong(locationData.long);
    setIsLiveMapOpen(false);
  };

  // Submit Handler for Adding Site under Currently Open Project
  const handleAddSiteSubmit = async (e) => {
    e.preventDefault();
    
    const currentActiveProjId = selectedProjectId || (projects.length > 0 ? projects[0].id : null);
    if (!currentActiveProjId) {
      alert('Please create or select a project first!');
      setIsAddSiteModalOpen(false);
      setIsNewProjectModalOpen(true);
      return;
    }

    const sitesUnderCurrent = sites.filter(s => String(s.project_id) === String(currentActiveProjId));
    const cleanName = siteIdentifier.trim() || `Site ${sitesUnderCurrent.length + 1}`;
    
    let badgeType = 'SO';
    if (siteTech.includes('Wind')) badgeType = 'WI';
    if (siteTech.includes('Hybrid')) badgeType = 'HY';

    const newSite = {
      id: `s-${Date.now()}`,
      project_id: currentActiveProjId,
      type: badgeType,
      name: cleanName,
      lat: parseFloat(Number(siteLat).toFixed(4)),
      long: parseFloat(Number(siteLong).toFixed(4)),
      elevation: 25,
      tech: siteTech,
      solar_irradiance: (Math.random() * 1.5 + 5.0).toFixed(2),
      temperature_avg: (Math.random() * 4 + 27).toFixed(1),
      rainfall: (Math.random() * 50 + 90).toFixed(1),
      cloud_cover: (Math.random() * 20 + 55).toFixed(1),
      capacity_factor: (Math.random() * 8 + 42).toFixed(1),
      est_yield: (Math.random() * 200 + 1550).toFixed(1),
      suitability_score: (Math.random() * 1.5 + 8.0).toFixed(1)
    };

    try {
      const res = await fetch(`${API_BASE}/api/sites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSite)
      });
      if (res.ok) {
        const created = await res.json();
        setSites(prev => [created, ...prev]);
        setSelectedSiteId(created.id);
      } else {
        setSites(prev => [newSite, ...prev]);
        setSelectedSiteId(newSite.id);
      }
    } catch (_) {
      setSites(prev => [newSite, ...prev]);
      setSelectedSiteId(newSite.id);
    }

    setSiteIdentifier('');
    setIsAddSiteModalOpen(false);
  };

  // Handler for Deleting a Site
  const handleDeleteSite = async (e, siteId) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to remove this site?')) return;

    try {
      await fetch(`${API_BASE}/api/sites/${siteId}`, {
        method: 'DELETE'
      });
    } catch (_) {}

    setSites(prev => prev.filter(s => String(s.id) !== String(siteId)));
    if (selectedSiteId === siteId) {
      setSelectedSiteId(null);
    }
  };

  const handleCopyEmail = () => {
    if (loggedInUser?.email) {
      navigator.clipboard.writeText(loggedInUser.email);
      setEmailCopied(true);
      setTimeout(() => setEmailCopied(false), 2000);
    }
  };

  const handleConfirmSignOut = () => {
    localStorage.removeItem('token');
    setLoggedInUser(null);
    setMessage(null);
    setIsUserMenuOpen(false);
    setShowSignOutConfirm(false);
  };

  const activeProject = projects.find(p => String(p.id) === String(selectedProjectId)) || projects[0] || { name: 'Active Project', description: '' };
  const currentProjectSites = sites.filter(s => String(s.project_id) === String(selectedProjectId));
  const currentSiteData = currentProjectSites.find(s => String(s.id) === String(selectedSiteId)) || currentProjectSites[0] || null;

  // =========================================================================
  // VIEW: AUTHENTICATED DASHBOARD
  // =========================================================================
  if (loggedInUser) {
    return (
      <div className="flex flex-col h-screen w-full bg-slate-950 text-slate-200 font-sans antialiased overflow-hidden selection:bg-emerald-500 selection:text-white">
        
        {/* Ambient Glow */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
          <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/10 rounded-full filter blur-[100px] animate-pulse"></div>
          <div className="absolute top-1/3 -right-40 w-[30rem] h-[30rem] bg-sky-500/10 rounded-full filter blur-[120px] animate-pulse delay-1000"></div>
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-20"></div>
        </div>

        {/* Top Header */}
        <header className="bg-slate-900/90 border-b border-slate-800/80 backdrop-blur-xl px-8 py-3.5 flex items-center justify-between sticky top-0 z-30 shadow-lg shadow-slate-950/20 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 bg-emerald-500/10 text-emerald-400 p-2 rounded-2xl border border-emerald-500/20 shadow-inner">
              <Sun className="w-5 h-5 text-amber-400 animate-spin" style={{ animationDuration: '24s' }} />
              <Wind className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-bold text-white leading-tight tracking-wide">Solar &amp; Wind Intelligence</h1>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Deployment &amp; Feasibility Platform</p>
            </div>
          </div>

          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center space-x-3 p-1.5 pr-3.5 rounded-2xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 transition duration-200 backdrop-blur-md cursor-pointer"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-slate-950 font-bold text-xs flex items-center justify-center shadow-sm">
                {(loggedInUser.name || 'U').charAt(0).toUpperCase()}
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-xs font-semibold text-slate-200 leading-tight">{loggedInUser.name}</p>
                <span className="text-[10px] text-emerald-400 font-medium">{loggedInUser.role}</span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 py-3.5 px-4 z-50 backdrop-blur-2xl animate-in fade-in slide-in-from-top-2 duration-150">
                <div className="pb-3 border-b border-slate-800">
                  <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Signed in account</p>
                  <p className="text-sm font-bold text-white mt-0.5">{loggedInUser.name}</p>
                  
                  <div className="mt-2.5 flex items-center justify-between bg-slate-950 border border-slate-800 rounded-xl p-2 text-xs">
                    <div className="flex items-center space-x-2 truncate mr-2 text-slate-300">
                      <Mail className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
                      <span className="truncate">{loggedInUser.email}</span>
                    </div>
                    <button
                      onClick={handleCopyEmail}
                      title="Copy Email"
                      className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition cursor-pointer"
                    >
                      {emailCopied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                <div className="py-2.5 border-b border-slate-800 space-y-2 text-xs text-slate-400">
                  <div className="flex items-center justify-between">
                    <span>Role:</span>
                    <span className="font-medium text-emerald-300 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 text-[10px]">
                      {loggedInUser.role}
                    </span>
                  </div>
                </div>

                <div className="pt-2.5">
                  <button
                    onClick={() => {
                      setIsUserMenuOpen(false);
                      setShowSignOutConfirm(true);
                    }}
                    className="w-full flex items-center justify-center space-x-2 text-xs font-semibold text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 p-2.5 rounded-xl border border-rose-500/20 transition duration-150 cursor-pointer"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Main Workspace Body */}
        <div className="flex-1 flex overflow-hidden z-10">
          <aside className="w-56 bg-slate-900/80 border-r border-slate-800/80 backdrop-blur-xl flex flex-col justify-between p-6 flex-shrink-0">
            <div>
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-3">Workspace</p>
              <nav className="space-y-2">
                {[
                  { id: 'projects', label: 'Projects & Sites' },
                  { id: 'map', label: 'Map View' },
                  { id: 'analytics', label: 'Analytics' },
                  { id: 'users', label: 'User Management' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveNav(item.id);
                      if (item.id === 'map') setIsLiveMapOpen(true);
                    }}
                    className={`w-full text-left text-xs transition-colors cursor-pointer py-1.5 px-2 rounded-lg block ${
                      activeNav === item.id 
                        ? 'font-bold text-emerald-400 bg-slate-800/60 border-l-2 border-emerald-400' 
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </nav>
            </div>
            <div className="text-[11px] text-slate-500 font-mono">v2.4 &middot; Feasibility Core</div>
          </aside>

          <main className="flex-1 flex flex-col overflow-y-auto px-10 py-8">
            <div className="mb-6">
              <p className="text-[9px] font-semibold tracking-wider text-slate-500 uppercase">
                ADMINISTRATOR &middot; SYSTEM GOVERNANCE
              </p>
              <h2 className="text-2xl font-serif font-bold text-white mt-1">Projects &amp; Sites</h2>
            </div>

            <div className="grid grid-cols-12 gap-8 items-start">
              {/* Column 1: Projects */}
              <div className="col-span-12 lg:col-span-4 space-y-3">
                <div className="flex items-center justify-between pb-1">
                  <span className="text-[10px] font-bold tracking-wider text-slate-400 uppercase">
                    PROJECT PORTFOLIOS ({projects.length})
                  </span>
                  <button 
                    onClick={() => setIsNewProjectModalOpen(true)}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-medium px-2.5 py-0.5 rounded transition shadow-sm cursor-pointer"
                  >
                    + New
                  </button>
                </div>

                <div className="space-y-2.5">
                  {projects.map((proj) => {
                    const isSelected = String(proj.id) === String(selectedProjectId);
                    const countUnderProject = sites.filter(s => String(s.project_id) === String(proj.id)).length;

                    return (
                      <div
                        key={proj.id}
                        onClick={() => setSelectedProjectId(proj.id)}
                        className={`relative p-4 rounded-xl transition cursor-pointer border ${
                          isSelected
                            ? 'bg-slate-900/90 border-emerald-500/50 shadow-md shadow-emerald-950/20'
                            : 'bg-slate-900/40 border-slate-800/80 hover:border-slate-700'
                        }`}
                      >
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            const remProjects = projects.filter(p => p.id !== proj.id);
                            setProjects(remProjects);
                            setSites(sites.filter(s => s.project_id !== proj.id));
                            if (selectedProjectId === proj.id && remProjects.length > 0) {
                              setSelectedProjectId(remProjects[0].id);
                            }
                          }}
                          className="absolute top-3 right-3 text-slate-500 hover:text-rose-400 text-xs transition cursor-pointer"
                        >
                          ✕
                        </button>
                        <h3 className="text-xs font-bold text-white pr-5">{proj.name}</h3>
                        <p className="text-[11px] text-slate-400 mt-1 leading-snug">{proj.description}</p>
                        <div className="mt-3 flex items-center justify-between">
                          <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                            {proj.status || 'Planning'}
                          </span>
                          <span className="text-[10px] text-slate-500">
                            {countUnderProject} {countUnderProject === 1 ? 'Site' : 'Sites'}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Column 2: Sites under active project */}
              <div className="col-span-12 lg:col-span-8 space-y-4">
                <div className="flex items-start justify-between pb-3 border-b border-slate-800">
                  <div>
                    <h3 className="text-base font-bold text-white">{activeProject.name}</h3>
                    <p className="text-xs text-slate-400 mt-0.5">{activeProject.description}</p>
                  </div>
                  <button 
                    onClick={() => {
                      if (!selectedProjectId) {
                        alert('Please create or select a project first!');
                        setIsNewProjectModalOpen(true);
                        return;
                      }
                      setIsAddSiteModalOpen(true);
                    }}
                    className="bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium px-3 py-1.5 rounded transition shadow-sm cursor-pointer"
                  >
                    + Add Site
                  </button>
                </div>

                <div className="space-y-2.5">
                  {currentProjectSites.length === 0 ? (
                    <div className="p-10 text-center text-xs text-slate-500 bg-slate-900/30 rounded-2xl border border-dashed border-slate-800/80">
                      No candidate sites registered under <strong className="text-white">&ldquo;{activeProject.name}&rdquo;</strong> yet.<br />
                      Click <strong className="text-emerald-400">&ldquo;+ Add Site&rdquo;</strong> to choose locations from the map.
                    </div>
                  ) : (
                    currentProjectSites.map((site) => {
                      const isSiteSelected = currentSiteData?.id === site.id;

                      return (
                        <div
                          key={site.id}
                          onClick={() => setSelectedSiteId(site.id)}
                          className={`p-3.5 bg-slate-900/60 rounded-xl border transition cursor-pointer ${
                            isSiteSelected ? 'border-emerald-500/50 shadow-sm' : 'border-slate-800/80 hover:border-slate-700'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3.5">
                              <span className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold text-[10px]">
                                {site.type}
                              </span>
                              <div>
                                <h4 className="text-xs font-bold text-white leading-none">{site.name}</h4>
                                <p className="text-[10px] text-slate-400 font-mono mt-1">
                                  {site.tech ? site.tech.toLowerCase() : 'solar'} &middot; {site.lat}&deg;, {site.long}&deg; &middot; {site.elevation}m
                                </p>
                              </div>
                            </div>

                            <div className="flex items-center space-x-2.5">
                              <span className="text-[10px] font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                                {site.suitability_score} / 10
                              </span>
                              
                              {/* Delete site button */}
                              <button
                                type="button"
                                onClick={(e) => handleDeleteSite(e, site.id)}
                                title="Remove Site"
                                className="p-1 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition cursor-pointer"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>

                              <span className="text-slate-500 text-xs">
                                {isSiteSelected ? '▲' : '▼'}
                              </span>
                            </div>
                          </div>

                          {isSiteSelected && (
                            <div className="mt-3 pt-3 border-t border-slate-800 grid grid-cols-3 sm:grid-cols-6 gap-2 text-center text-[10px] animate-in fade-in duration-150">
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <span className="text-slate-500 block">Solar (GHI)</span>
                                <span className="font-bold text-amber-400">{site.solar_irradiance} kWh/m&sup2;</span>
                              </div>
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <span className="text-slate-500 block">Avg Temp</span>
                                <span className="font-bold text-slate-300">{site.temperature_avg} &deg;C</span>
                              </div>
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <span className="text-slate-500 block">Rainfall</span>
                                <span className="font-bold text-sky-400">{site.rainfall} mm</span>
                              </div>
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <span className="text-slate-500 block">Cloud Cover</span>
                                <span className="font-bold text-slate-300">{site.cloud_cover} %</span>
                              </div>
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <span className="text-slate-500 block">Capacity Factor</span>
                                <span className="font-bold text-emerald-400">{site.capacity_factor} %</span>
                              </div>
                              <div className="bg-slate-950/60 p-2 rounded-lg border border-slate-800/60">
                                <span className="text-slate-500 block">Est Yield</span>
                                <span className="font-bold text-teal-300">{site.est_yield}</span>
                              </div>
                            </div>
                          )}
                        </div>
                      );
                    })
                  )}
                </div>
              </div>
            </div>
          </main>
        </div>

        {/* Sign Out Confirmation Modal */}
        {showSignOutConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-sm w-full shadow-2xl text-center backdrop-blur-xl animate-in zoom-in-95 duration-150">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-4 text-rose-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Sign Out Confirmation</h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Are you sure you want to sign out of the <span className="font-medium text-emerald-400">Solar &amp; Wind Intelligence Platform</span>?
              </p>
              
              <div className="mt-6 flex items-center space-x-3">
                <button
                  type="button"
                  onClick={() => setShowSignOutConfirm(false)}
                  className="flex-1 px-4 py-2.5 text-xs font-semibold text-slate-300 bg-slate-800/80 hover:bg-slate-800 rounded-xl transition border border-slate-700/60 cursor-pointer"
                >
                  No, Stay
                </button>
                <button
                  type="button"
                  onClick={handleConfirmSignOut}
                  className="flex-1 px-4 py-2.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-xl transition shadow-lg shadow-rose-600/20 cursor-pointer"
                >
                  Yes, Sign Out
                </button>
              </div>
            </div>
          </div>
        )}

        {/* New Project Portfolio Modal */}
        {isNewProjectModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl backdrop-blur-xl relative z-10 animate-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-base font-bold text-white">New Project Portfolio</h3>
                <button 
                  onClick={() => setIsNewProjectModalOpen(false)} 
                  className="text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateProject} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Portfolio / Project Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Tamil Nadu Coastal Solar & Wind Phase 1"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>

                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Description &amp; Objective</label>
                  <textarea
                    rows={3}
                    placeholder="Scope, regional target, or feasibility notes"
                    value={newProjectDesc}
                    onChange={(e) => setNewProjectDesc(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsNewProjectModalOpen(false)}
                    className="px-4 py-2 text-slate-400 hover:text-slate-200 rounded-xl cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2 rounded-xl shadow-md transition cursor-pointer"
                  >
                    Create Project
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Add Site Dialog */}
        {isAddSiteModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-lg w-full shadow-2xl backdrop-blur-xl relative z-10 max-h-[90vh] overflow-y-auto animate-in zoom-in-95 duration-150">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <h3 className="text-base font-bold text-white">Add Site to &ldquo;{activeProject.name}&rdquo;</h3>
                <button 
                  onClick={() => setIsAddSiteModalOpen(false)} 
                  className="text-slate-400 hover:text-white text-xs cursor-pointer"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleAddSiteSubmit} className="space-y-4 text-xs">
                {/* Site Identifier Box */}
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Site Identifier *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Ramanathapuram Sector 4"
                    value={siteIdentifier}
                    onChange={(e) => setSiteIdentifier(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>

                {/* Choose Site From Map Button */}
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Geographic Selection</label>
                  <button
                    type="button"
                    onClick={() => setIsLiveMapOpen(true)}
                    className="w-full py-2.5 px-4 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-xl font-bold flex items-center justify-center space-x-2 transition cursor-pointer"
                  >
                    <MapPin className="w-4 h-4" />
                    <span>Choose Site From Map (Search Place or Move Pin)</span>
                  </button>
                </div>

                {/* Latitude & Longitude Inputs (Auto-filled from map) */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-400 font-semibold mb-1">Latitude</label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={siteLat}
                      onChange={(e) => setSiteLat(parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-400 font-semibold mb-1">Longitude</label>
                    <input
                      type="number"
                      step="any"
                      required
                      value={siteLong}
                      onChange={(e) => setSiteLong(parseFloat(e.target.value) || 0)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none font-mono"
                    />
                  </div>
                </div>

                {/* Technology Focus */}
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Technology Focus</label>
                  <select
                    value={siteTech}
                    onChange={(e) => setSiteTech(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none cursor-pointer"
                  >
                    <option value="Solar PV">Solar PV</option>
                    <option value="Wind Turbine">Wind Turbine</option>
                    <option value="Hybrid (Solar + Wind)">Hybrid (Solar + Wind)</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsAddSiteModalOpen(false)}
                    className="px-4 py-2 text-slate-400 hover:text-slate-200 rounded-xl cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-5 py-2 rounded-xl shadow-md transition cursor-pointer"
                  >
                    Detect Location &amp; Add Site
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Real-time Map Picker Modal */}
        {isLiveMapOpen && (
          <MapPickerModal
            isOpen={isLiveMapOpen}
            onClose={() => setIsLiveMapOpen(false)}
            onSelectLocation={handleLocationPickedFromMap}
            initialLat={siteLat}
            initialLong={siteLong}
          />
        )}

      </div>
    );
  }

  // =========================================================================
  // VIEW: AUTHENTICATION
  // =========================================================================
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-slate-200 font-sans relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/25 rounded-full filter blur-[100px] animate-pulse"></div>
        <div className="absolute top-1/2 -right-24 w-[30rem] h-[30rem] bg-sky-500/25 rounded-full filter blur-[110px] animate-pulse delay-1000"></div>
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-35"></div>
      </div>

      <div className="max-w-md w-full bg-slate-900/80 rounded-3xl shadow-2xl border border-slate-800/80 p-8 backdrop-blur-2xl relative z-10">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex items-center justify-center space-x-2 bg-emerald-500/10 text-emerald-400 p-3.5 rounded-2xl border border-emerald-500/20 mb-3 shadow-inner">
            <Sun className="w-6 h-6 text-amber-400" />
            <Wind className="w-6 h-6 text-sky-400" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Solar &amp; Wind Intelligence Platform</h1>
          <p className="text-xs text-slate-400 mt-1">Renewable Energy Deployment &amp; Feasibility Analysis</p>
        </div>

        <div className="flex bg-slate-950/80 p-1.5 rounded-2xl mb-6 border border-slate-800/80">
          <button
            type="button"
            onClick={() => { setIsRegister(false); setMessage(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition duration-200 cursor-pointer ${
              !isRegister ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setIsRegister(true); setMessage(null); }}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition duration-200 cursor-pointer ${
              isRegister ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Register Account
          </button>
        </div>

        {message && (
          <div className={`p-3 rounded-xl text-xs font-medium mb-5 flex items-start space-x-2 border ${
            message.type === 'success' 
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
              : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
          }`}>
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{message.text}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Display Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  placeholder="Sakshi Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Platform Role</label>
            <div className="relative">
              <UserCheck className="w-4 h-4 text-slate-500 absolute left-3 top-3.5 pointer-events-none" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-8 py-2.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 cursor-pointer appearance-none"
              >
                {roles.map((r) => (
                  <option key={r} value={r} className="bg-slate-900 text-slate-200">
                    {r}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-slate-500 absolute right-3 top-3.5 pointer-events-none" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                placeholder="planner@energy.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1.5">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-10 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 focus:outline-none cursor-pointer"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1.5">Confirm Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-10 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-3 text-slate-500 hover:text-slate-300 focus:outline-none cursor-pointer"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold py-3 rounded-xl text-xs shadow-lg shadow-emerald-500/20 transition duration-200 ease-in-out mt-2 disabled:opacity-50 active:scale-[0.98] cursor-pointer"
          >
            {loading ? 'Processing...' : (isRegister ? 'Register & Sign In' : 'Sign In')}
          </button>
        </form>
      </div>
    </div>
  );
}
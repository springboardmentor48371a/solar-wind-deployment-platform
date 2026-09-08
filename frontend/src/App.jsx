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
  MapPin, 
  Compass, 
  Layers, 
  Zap, 
  ArrowRight, 
  LogOut, 
  AlertCircle, 
  PlusCircle, 
  Activity, 
  AlertTriangle,
  ChevronDown,
  Copy,
  Check,
  Globe2,
  FolderGit2,
  FolderPlus,
  Trash2,
  TrendingUp,
  FileText,
  Sparkles,
  RotateCw,
  Clock,
  CheckCircle2,
  PlayCircle
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

  // Profile Dropdown states
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [showSignOutConfirm, setShowSignOutConfirm] = useState(false);
  const [emailCopied, setEmailCopied] = useState(false);
  const dropdownRef = useRef(null);

  // Dashboard Navigation Tabs
  const [activeTab, setActiveTab] = useState('select-site');

  // Projects State
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [isNewProjectModalOpen, setIsNewProjectModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectDesc, setNewProjectDesc] = useState('');
  const [newProjectStatus, setNewProjectStatus] = useState('Planning');

  // Sites State
  const [sites, setSites] = useState([]);
  const [selectedSiteId, setSelectedSiteId] = useState(null);
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [storedSitesFilter, setStoredSitesFilter] = useState('all');

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
        setProjects(data);
        if (data.length > 0 && !selectedProjectId) {
          setSelectedProjectId(data[0].id);
        }
      }
    } catch (_) {}
  };

  // Fetch Sites for selected project
  const fetchSitesForProject = async (projId) => {
    if (!projId) {
      setSites([]);
      setSelectedSiteId(null);
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/sites?project_id=${projId}`);
      if (res.ok) {
        const data = await res.json();
        setSites(data);
        if (data.length > 0) {
          setSelectedSiteId(data[0].id);
        } else {
          setSelectedSiteId(null);
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

  // Auth Handler
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
        setLoggedInUser({ name: data.name, role: data.role, email: data.email });
      } else {
        if (response.status === 404 || data.detail?.includes('User not registered')) {
          setMessage({ type: 'error', text: 'User not registered. Please register first to continue!' });
          setIsRegister(true);
        } else {
          setMessage({ type: 'error', text: data.detail || 'Authentication failed' });
        }
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Unable to connect to backend server (http://127.0.0.1:8000)' });
    } finally {
      setLoading(false);
    }
  };

  // Create Project
  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/api/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          name: newProjectName.trim(), 
          description: newProjectDesc.trim(),
          status: newProjectStatus
        })
      });
      if (res.ok) {
        const created = await res.json();
        setProjects(prev => [created, ...prev]);
        setSelectedProjectId(created.id);
        setNewProjectName('');
        setNewProjectDesc('');
        setNewProjectStatus('Planning');
        setIsNewProjectModalOpen(false);
        fetchSitesForProject(created.id);
      }
    } catch (_) {}
  };

  // Update Project Status in Real Time
  const handleUpdateProjectStatus = async (newStatus) => {
    if (!selectedProjectId) return;
    try {
      const res = await fetch(`${API_BASE}/api/projects/${selectedProjectId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) {
        const updated = await res.json();
        setProjects(prev => prev.map(p => p.id === updated.id ? updated : p));
      }
    } catch (_) {
      // Fallback local update if backend patch is not yet added
      setProjects(prev => prev.map(p => p.id === selectedProjectId ? { ...p, status: newStatus } : p));
    }
  };

  // Add Site From Map Modal
  const handleConfirmMapSite = async (siteMeta) => {
    if (!selectedProjectId) {
      alert('Please create or select a project first!');
      setIsNewProjectModalOpen(true);
      return;
    }

    const rawLat = typeof siteMeta.rawLat === 'number' ? siteMeta.rawLat : parseFloat(siteMeta.lat) || 26.9;
    const rawLng = typeof siteMeta.rawLng === 'number' ? siteMeta.rawLng : parseFloat(siteMeta.long) || 75.8;

    const payload = {
      project_id: selectedProjectId,
      name: siteMeta.name || `Site ${sites.length + 1}`,
      lat: rawLat,
      long: rawLng,
      region: siteMeta.region || 'Selected Corridor',
      elevation: parseFloat(String(siteMeta.elevation || 12)) || 12.0
    };

    try {
      const res = await fetch(`${API_BASE}/api/sites`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const createdSite = await res.json();
        setSites(prev => [createdSite, ...prev]);
        setSelectedSiteId(createdSite.id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsMapModalOpen(false);
      setActiveTab('select-site');
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

  const activeProject = projects.find(p => String(p.id) === String(selectedProjectId)) || projects[0] || null;

  const currentSiteData = sites.find(s => String(s.id) === String(selectedSiteId)) || sites[0] || {
    id: 'preview-site',
    name: 'Ramanathapuram Solar Site',
    lat: 9.3639,
    long: 78.8395,
    solar_irradiance: 5.69,
    peak_sun_hours: 5.69,
    temperature_avg: 29.34,
    rainfall: 133.8,
    cloud_cover: 70.2,
    elevation: 12,
    days_recorded: 30,
    suitability_score: 8.6,
    suitability_category: 'Excellent',
    capacity_factor: 46.4,
    est_yield: 1618.5
  };

  const score10 = Number(currentSiteData.suitability_score || 8.6) > 10 
    ? (Number(currentSiteData.suitability_score) / 10).toFixed(1) 
    : Number(currentSiteData.suitability_score || 8.6).toFixed(1);

  // Status visual mapping helper
  const getStatusBadge = (status) => {
    switch (status) {
      case 'Active':
        return {
          bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
          dot: 'bg-emerald-400',
          icon: <PlayCircle className="w-3.5 h-3.5 mr-1" />
        };
      case 'Completed':
        return {
          bg: 'bg-sky-500/10 border-sky-500/30 text-sky-400',
          dot: 'bg-sky-400',
          icon: <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
        };
      default:
        return {
          bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
          dot: 'bg-amber-400',
          icon: <Clock className="w-3.5 h-3.5 mr-1" />
        };
    }
  };

  // =========================================================================
  // VIEW: AUTHENTICATED DASHBOARD WITH ACTIVE PROJECT AND REAL-TIME STATUS
  // =========================================================================
  if (loggedInUser) {
    const statusMeta = getStatusBadge(activeProject?.status || 'Planning');

    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col selection:bg-emerald-500 selection:text-white relative overflow-hidden">
        
        {/* Animated Background Fluid Orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
          <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/20 rounded-full mix-blend-screen filter blur-[90px] animate-pulse duration-7000"></div>
          <div className="absolute top-1/3 -right-40 w-[30rem] h-[30rem] bg-sky-500/20 rounded-full mix-blend-screen filter blur-[100px] animate-pulse duration-10000 delay-1000"></div>
          <div className="absolute -bottom-40 left-1/3 w-[28rem] h-[28rem] bg-amber-500/15 rounded-full mix-blend-screen filter blur-[90px] animate-pulse duration-8000 delay-2000"></div>
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-30"></div>
        </div>

        {/* Modal: Create New Project */}
        {isNewProjectModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full shadow-2xl backdrop-blur-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <FolderPlus className="w-5 h-5" />
                  <h3 className="text-base font-bold text-white">Create New Project</h3>
                </div>
                <button onClick={() => setIsNewProjectModalOpen(false)} className="text-slate-400 hover:text-white">
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreateProject} className="space-y-4 text-xs">
                <div>
                  <label className="block text-slate-300 font-medium mb-1">Project Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Tamil Nadu Solar & Wind Farm"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Initial Project Status</label>
                  <select
                    value={newProjectStatus}
                    onChange={(e) => setNewProjectStatus(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 cursor-pointer"
                  >
                    <option value="Planning">Planning (Feasibility & Screening)</option>
                    <option value="Active">Active (Ongoing Deployment)</option>
                    <option value="Completed">Completed (Commissioned)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-300 font-medium mb-1">Description / Regional Scope</label>
                  <textarea
                    rows={3}
                    placeholder="e.g. Large scale utility deployment across southern Tamil Nadu plains"
                    value={newProjectDesc}
                    onChange={(e) => setNewProjectDesc(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsNewProjectModalOpen(false)}
                    className="px-4 py-2 text-slate-400 hover:bg-slate-800 rounded-xl cursor-pointer"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 font-bold px-5 py-2 rounded-xl shadow-md cursor-pointer"
                  >
                    Create Project
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Sign Out Confirmation */}
        {showSignOutConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-sm w-full shadow-2xl text-center backdrop-blur-xl animate-in zoom-in-95 duration-150">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center mx-auto mb-4 text-rose-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Sign Out Confirmation</h3>
              <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                Are you sure you want to sign out of the <span className="font-medium text-emerald-400">Solar & Wind Intelligence Platform</span>?
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

        {/* Top Header */}
        <header className="bg-slate-900/80 border-b border-slate-800/80 backdrop-blur-xl px-6 py-3.5 flex items-center justify-between sticky top-0 z-30 shadow-lg shadow-slate-950/20">
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-1.5 bg-emerald-500/10 text-emerald-400 p-2 rounded-2xl border border-emerald-500/20 shadow-inner">
              <Sun className="w-5 h-5 text-amber-400 animate-spin" style={{ animationDuration: '24s' }} />
              <Wind className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-bold text-white leading-tight tracking-wide">Solar & Wind Intelligence</h1>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
              </div>
              <p className="text-[11px] text-slate-400">Deployment & Feasibility Platform</p>
            </div>
          </div>

          {/* User Profile Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center space-x-3 p-1.5 pr-3.5 rounded-2xl bg-slate-800/50 hover:bg-slate-800/90 border border-slate-700/60 hover:border-slate-600 transition duration-200 backdrop-blur-md cursor-pointer"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-slate-950 font-bold text-xs flex items-center justify-center shadow-sm">
                {loggedInUser.name.charAt(0).toUpperCase()}
              </div>
              <div className="text-left hidden sm:block">
                <p className="text-xs font-semibold text-slate-200 leading-tight">{loggedInUser.name}</p>
                <span className="text-[10px] text-emerald-400 font-medium">{loggedInUser.role}</span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {isUserMenuOpen && (
              <div className="absolute right-0 mt-2 w-72 bg-slate-900 rounded-2xl shadow-2xl border border-slate-800 py-3.5 px-4 z-40 backdrop-blur-2xl animate-in fade-in slide-in-from-top-2 duration-150">
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

        {/* Dashboard Body with Left Navigation */}
        <div className="flex-1 flex overflow-hidden z-10">
          
          {/* Left Sidebar */}
          <aside className="w-64 bg-slate-900/70 border-r border-slate-800/80 flex flex-col justify-between p-4 backdrop-blur-xl flex-shrink-0">
            <div className="space-y-6">
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2">
                  Navigation Menu
                </p>
                <nav className="space-y-1.5">
                  <button
                    onClick={() => setActiveTab('select-site')}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'select-site'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <MapPin className="w-4 h-4 text-emerald-400" />
                    <span>Select New Site</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('stored-sites')}
                    className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'stored-sites'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <Layers className="w-4 h-4 text-sky-400" />
                      <span>Stored Sites</span>
                    </div>
                    <span className="text-[10px] bg-slate-800 px-2 py-0.5 rounded-full text-slate-300 font-mono">
                      {sites.length}
                    </span>
                  </button>

                  <button
                    onClick={() => setActiveTab('analytics')}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'analytics'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <TrendingUp className="w-4 h-4 text-indigo-400" />
                    <span>Site Analytics</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('reports')}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'reports'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <FileText className="w-4 h-4 text-teal-400" />
                    <span>Feasibility Report</span>
                  </button>
                </nav>
              </div>

              {/* Sidebar Active Project Card */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-2xl p-3.5 space-y-2">
                <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider block">
                  Current Open Project
                </span>
                <p className="text-xs font-bold text-white truncate">
                  {activeProject ? activeProject.name : 'No Project Selected'}
                </p>

                {activeProject && (
                  <div className="flex items-center space-x-2 pt-1">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold border ${statusMeta.bg}`}>
                      {statusMeta.icon}
                      {activeProject.status || 'Planning'}
                    </span>
                  </div>
                )}

                <button
                  onClick={() => setIsNewProjectModalOpen(true)}
                  className="mt-2 w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold py-1.5 rounded-xl border border-slate-700 cursor-pointer transition"
                >
                  + Add New Project
                </button>
              </div>
            </div>
          </aside>

          {/* Main Dashboard Panel */}
          <main className="flex-1 p-6 overflow-y-auto space-y-6">

            {/* ========================================================================= */}
            {/* ACTIVE PROJECT BANNER WITH REAL-TIME STATUS SWITCHER                      */}
            {/* ========================================================================= */}
            <div className="bg-slate-900/80 border border-slate-800/80 rounded-3xl p-6 backdrop-blur-xl shadow-xl space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/60">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                      Active Project Corridor
                    </span>
                    <span className="text-xs text-slate-500">•</span>
                    <span className="text-xs text-slate-400">
                      ID: <span className="font-mono">{activeProject?.id?.slice(0, 8) || 'proj-1'}</span>
                    </span>
                  </div>

                  <h2 className="text-2xl font-black text-white tracking-tight">
                    {activeProject ? activeProject.name : 'Select or Create a Project'}
                  </h2>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
                    {activeProject?.description || 'No project description entered. Select a registered project or click "+ New Project" to initialize a regional deployment corridor.'}
                  </p>
                </div>

                {/* Real-time Project Selector & Status Switcher */}
                <div className="flex flex-wrap items-center gap-3 bg-slate-950/80 p-3 rounded-2xl border border-slate-800">
                  <div className="text-left">
                    <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                      Switch Project:
                    </label>
                    <select
                      value={selectedProjectId || ''}
                      onChange={(e) => setSelectedProjectId(e.target.value)}
                      className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer min-w-[180px]"
                    >
                      {projects.length === 0 ? (
                        <option value="">No projects registered</option>
                      ) : (
                        projects.map(p => (
                          <option key={p.id} value={p.id}>{p.name} ({p.status || 'Planning'})</option>
                        ))
                      )}
                    </select>
                  </div>

                  {activeProject && (
                    <div className="text-left border-l border-slate-800 pl-3">
                      <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                        Real-World Status:
                      </label>
                      <select
                        value={activeProject.status || 'Planning'}
                        onChange={(e) => handleUpdateProjectStatus(e.target.value)}
                        className={`border rounded-xl px-3 py-1.5 text-xs font-bold focus:outline-none cursor-pointer ${statusMeta.bg}`}
                      >
                        <option value="Planning" className="bg-slate-900 text-amber-400">🟡 Planning (Screening)</option>
                        <option value="Active" className="bg-slate-900 text-emerald-400">🟢 Active (In Progress)</option>
                        <option value="Completed" className="bg-slate-900 text-sky-400">🔵 Completed (Built)</option>
                      </select>
                    </div>
                  )}
                </div>
              </div>

              {/* Action Bar for Adding Sites under Open Project */}
              <div className="flex flex-wrap items-center justify-between gap-4 pt-1">
                <div className="flex items-center space-x-2 text-xs text-slate-400">
                  <FolderGit2 className="w-4 h-4 text-emerald-400" />
                  <span>Enrolled Candidate Sites: <strong className="text-white">{sites.length}</strong></span>
                </div>

                <div className="flex items-center space-x-3">
                  <button
                    onClick={() => setIsNewProjectModalOpen(true)}
                    className="bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-700 cursor-pointer transition"
                  >
                    + New Project
                  </button>

                  <button
                    onClick={() => {
                      if (!selectedProjectId) {
                        alert('Please register or select a Project first!');
                        setIsNewProjectModalOpen(true);
                        return;
                      }
                      setIsMapModalOpen(true);
                    }}
                    className="flex items-center space-x-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs shadow-md shadow-emerald-500/20 active:scale-95 cursor-pointer transition"
                  >
                    <Globe2 className="w-4 h-4" />
                    <span>Add Site to Project via Map</span>
                  </button>
                </div>
              </div>
            </div>

            {/* TAB 1: SITE OVERVIEW & TELEMETRY */}
            {activeTab === 'select-site' && (
              <div className="space-y-6">

                {/* Candidate Sites Switcher */}
                <div className="flex items-center space-x-2 overflow-x-auto pb-1">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex-shrink-0">Sites:</span>
                  {sites.length === 0 ? (
                    <span className="text-xs text-slate-500">No sites added yet under this project. Click "Add Site to Project via Map"</span>
                  ) : (
                    sites.map(s => (
                      <button
                        key={s.id}
                        onClick={() => setSelectedSiteId(s.id)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                          currentSiteData.id === s.id
                            ? 'bg-slate-800 text-emerald-400 border border-emerald-500/40 shadow-sm'
                            : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
                        }`}
                      >
                        {s.name}
                      </button>
                    ))
                  )}
                </div>

                {/* Environmental Ribbon */}
                <div className="bg-slate-900/70 border border-slate-800/80 rounded-3xl p-5 backdrop-blur-xl">
                  <div className="flex items-center justify-between mb-3 border-b border-slate-800/60 pb-2.5">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Environmental Data</span>
                      <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-semibold">
                        Live Feed
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-400 font-mono">
                      {currentSiteData.name} ({currentSiteData.lat?.toFixed ? currentSiteData.lat.toFixed(4) : currentSiteData.lat}°N, {currentSiteData.long?.toFixed ? currentSiteData.long.toFixed(4) : currentSiteData.long}°E)
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-7 gap-3 text-center">
                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Solar Irradiance</p>
                      <p className="text-lg font-black text-amber-400 mt-1">{currentSiteData.solar_irradiance || '5.69'}</p>
                      <p className="text-[10px] text-slate-500">kWh/m²</p>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Peak Sun Hours</p>
                      <p className="text-lg font-black text-amber-300 mt-1">{currentSiteData.peak_sun_hours || '5.69'}</p>
                      <p className="text-[10px] text-slate-500">hours/day</p>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Avg Temp</p>
                      <p className="text-lg font-black text-slate-200 mt-1">{currentSiteData.temperature_avg || '29.34'}</p>
                      <p className="text-[10px] text-slate-500">°C</p>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Total Rainfall</p>
                      <p className="text-lg font-black text-sky-400 mt-1">{currentSiteData.rainfall || '133.8'}</p>
                      <p className="text-[10px] text-slate-500">mm</p>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Cloud Cover</p>
                      <p className="text-lg font-black text-slate-300 mt-1">{currentSiteData.cloud_cover || '70.2'}</p>
                      <p className="text-[10px] text-slate-500">%</p>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Elevation</p>
                      <p className="text-lg font-black text-teal-300 mt-1">{currentSiteData.elevation || 12}</p>
                      <p className="text-[10px] text-slate-500">m (DEM)</p>
                    </div>

                    <div className="bg-slate-950/60 p-3 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase">Data Days</p>
                      <p className="text-lg font-black text-indigo-400 mt-1">{currentSiteData.days_recorded || 30}</p>
                      <p className="text-[10px] text-slate-500">days</p>
                    </div>
                  </div>
                </div>

                {/* Suitability Score Bar (0 to 10 Scale) */}
                <div className="bg-slate-900/70 border border-slate-800/80 rounded-3xl p-6 backdrop-blur-xl space-y-4">
                  <div className="flex items-baseline justify-between">
                    <div className="flex items-baseline space-x-2">
                      <span className="text-4xl font-extrabold text-emerald-300">{score10}</span>
                      <span className="text-sm font-bold text-slate-500">/ 10</span>
                      <span className="text-xs font-semibold text-emerald-400 ml-2">
                        Overall Suitability ({currentSiteData.suitability_category || 'Excellent'})
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-400">{(Number(score10) * 10).toFixed(0)}%</span>
                  </div>

                  <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
                    <div 
                      className="h-full bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-300 rounded-full transition-all duration-700 shadow-sm shadow-emerald-500/50"
                      style={{ width: `${Math.min(100, Number(score10) * 10)}%` }}
                    />
                  </div>

                  <div className="flex flex-wrap gap-4 text-xs text-slate-300 pt-2">
                    <span>Capacity Factor: <strong className="text-white">{currentSiteData.capacity_factor || '46.4'}%</strong></span>
                    <span>Yield: <strong className="text-white">{currentSiteData.est_yield || '1618.5'} kWh/kWp/yr</strong></span>
                    <span>Substations: <strong className="text-white">&lt; 2 km (Optimal)</strong></span>
                  </div>
                </div>

              </div>
            )}

            {/* TAB 2: STORED SITES */}
            {activeTab === 'stored-sites' && (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h2 className="text-xl font-bold text-white">Stored Candidate Sites</h2>
                    <p className="text-xs text-slate-400 mt-1">Sites enrolled under current project: <span className="text-emerald-400 font-semibold">{activeProject?.name}</span></p>
                  </div>
                  <button
                    onClick={() => setIsMapModalOpen(true)}
                    className="bg-emerald-500 text-slate-950 text-xs font-bold px-4 py-2 rounded-xl cursor-pointer"
                  >
                    + Add Site via Map
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                  {sites.length === 0 ? (
                    <div className="col-span-full py-12 text-center text-slate-500 text-xs border border-dashed border-slate-800 rounded-3xl">
                      No candidate sites registered under this project yet. Click "+ Add Site via Map" above!
                    </div>
                  ) : (
                    sites.map(site => (
                      <div key={site.id} className="bg-slate-900/80 border border-slate-800/80 rounded-3xl p-5 space-y-3">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="text-sm font-bold text-white">{site.name}</h4>
                            <p className="text-[11px] text-slate-400">{site.lat}°N, {site.long}°E</p>
                          </div>
                        </div>

                        <div className="bg-slate-950/80 border border-slate-800 p-3 rounded-2xl flex justify-between items-center">
                          <span className="text-xs text-slate-400 font-medium">Suitability Score:</span>
                          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-lg">
                            {Number(site.suitability_score || 8.6) > 10 ? (site.suitability_score / 10).toFixed(1) : Number(site.suitability_score || 8.6).toFixed(1)} / 10
                          </span>
                        </div>

                        <button
                          onClick={() => {
                            setSelectedSiteId(site.id);
                            setActiveTab('select-site');
                          }}
                          className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 rounded-xl border border-slate-700 cursor-pointer transition"
                        >
                          View Full Telemetry
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* TAB 3 & 4 */}
            {activeTab === 'analytics' && (
              <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 text-center text-slate-400 space-y-2">
                <Activity className="w-8 h-8 text-emerald-400 mx-auto" />
                <h3 className="text-base font-bold text-white">Comparative Energy Analytics</h3>
                <p className="text-xs max-w-md mx-auto">Evaluating solar radiation, wind speeds, and elevation profile for {activeProject?.name}.</p>
              </div>
            )}

            {activeTab === 'reports' && (
              <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 text-center text-slate-400 space-y-2">
                <FileText className="w-8 h-8 text-teal-400 mx-auto" />
                <h3 className="text-base font-bold text-white">Project Feasibility Report</h3>
                <p className="text-xs max-w-md mx-auto">Exportable summary for {activeProject?.name} covering candidate site coordinates and multi-criteria scores.</p>
              </div>
            )}

          </main>
        </div>

        {/* Integrated Leaflet Map Modal */}
        <MapPickerModal
          isOpen={isMapModalOpen}
          onClose={() => setIsMapModalOpen(false)}
          onConfirmSite={handleConfirmMapSite}
          activeProjectName={activeProject?.name || 'Selected Project'}
        />
      </div>
    );
  }

  // =========================================================================
  // VIEW: AUTHENTICATION (DARK ANIMATED SCREEN)
  // =========================================================================
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-slate-200 font-sans relative overflow-hidden">
      
      {/* Drifting Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/25 rounded-full filter blur-[100px] animate-pulse"></div>
        <div className="absolute top-1/2 -right-24 w-[30rem] h-[30rem] bg-sky-500/25 rounded-full filter blur-[110px] animate-pulse delay-1000"></div>
        <div className="absolute -bottom-24 left-1/3 w-96 h-96 bg-amber-500/20 rounded-full filter blur-[100px] animate-pulse delay-2000"></div>
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-35"></div>
      </div>

      <div className="max-w-md w-full bg-slate-900/80 rounded-3xl shadow-2xl border border-slate-800/80 p-8 backdrop-blur-2xl relative z-10">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex items-center justify-center space-x-2 bg-emerald-500/10 text-emerald-400 p-3.5 rounded-2xl border border-emerald-500/20 mb-3 shadow-inner">
            <Sun className="w-6 h-6 text-amber-400" />
            <Wind className="w-6 h-6 text-sky-400" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Solar & Wind Intelligence Platform</h1>
          <p className="text-xs text-slate-400 mt-1">Renewable Energy Deployment & Feasibility Analysis</p>
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
              <UserCheck className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              >
                {roles.map((r) => (<option key={r} value={r} className="bg-slate-900 text-slate-200">{r}</option>))}
              </select>
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
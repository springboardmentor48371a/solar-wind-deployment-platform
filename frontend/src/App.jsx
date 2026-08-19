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
  Sparkles,
  TrendingUp,
  FileText,
  FolderGit2,
  Download
} from 'lucide-react';
import MapPickerModal from './components/MapPickerModal';

const DEFAULT_SITES = [
  {
    id: 1,
    name: 'Bhadla Solar Park Extension',
    region: 'Rajasthan, India',
    lat: 27.5381,
    long: 71.9161,
    site_type: 'Solar PV',
    area: '45.2 km²',
    solar_potential: '5.8 kWh/m²/day',
    wind_speed: '4.2 m/s',
    grid_proximity: '1.8 km',
    suitability_score: 94
  },
  {
    id: 2,
    name: 'Muppandal Wind Corridor',
    region: 'Tamil Nadu, India',
    lat: 8.2588,
    long: 77.5484,
    site_type: 'Wind Farm',
    area: '62.0 km²',
    solar_potential: '4.9 kWh/m²/day',
    wind_speed: '8.7 m/s',
    grid_proximity: '3.4 km',
    suitability_score: 91
  },
  {
    id: 3,
    name: 'Kutch Hybrid Energy Zone',
    region: 'Gujarat, India',
    lat: 23.7337,
    long: 69.8597,
    site_type: 'Hybrid (Solar + Wind)',
    area: '88.5 km²',
    solar_potential: '5.6 kWh/m²/day',
    wind_speed: '7.4 m/s',
    grid_proximity: '0.9 km',
    suitability_score: 96
  }
];

export default function App() {
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('Renewable Energy Planner');
  const [rememberMe, setRememberMe] = useState(true);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [loggedInUser, setLoggedInUser] = useState(null);

  // Sidebar navigation state: 'select-site' | 'stored-sites' | 'compare-sites' | 'view-report'
  const [activeTab, setActiveTab] = useState('select-site');

  // Map Modal & User Dropdown States
  const [isMapModalOpen, setIsMapModalOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [showSignOutConfirm, setShowSignOutConfirm] = useState(false);
  const [emailCopied, setEmailCopied] = useState(false);
  const dropdownRef = useRef(null);

  // Persistent Candidate Sites State
  const [sites, setSites] = useState(DEFAULT_SITES);
  const [selectedSiteId, setSelectedSiteId] = useState(DEFAULT_SITES[0].id);

  const currentSiteData = sites.find((s) => String(s.id) === String(selectedSiteId)) || sites[0] || DEFAULT_SITES[0];

  const roles = [
    'Renewable Energy Planner',
    'GIS Analyst',
    'Project Manager',
    'Administrator'
  ];

  // Fetch persistent sites from backend on load
  useEffect(() => {
    const fetchPersistedSites = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/sites');
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setSites(data);
            setSelectedSiteId(data[0].id);
          }
        }
      } catch (err) {
        console.warn('Backend database not reachable, using fallback sites state.');
      }
    };

    fetchPersistedSites();
  }, []);

  // Load remembered credentials on startup
  useEffect(() => {
    const savedEmail = localStorage.getItem('saved_email');
    const savedPassword = localStorage.getItem('saved_password');
    const savedRemember = localStorage.getItem('remember_me');

    if (savedRemember === 'true' && savedEmail) {
      setEmail(savedEmail);
      if (savedPassword) {
        setPassword(savedPassword);
      }
      setRememberMe(true);
    } else if (savedRemember === 'false') {
      setRememberMe(false);
    }
  }, []);

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
    const endpoint = isRegister 
      ? 'http://127.0.0.1:8000/api/auth/register' 
      : 'http://127.0.0.1:8000/api/auth/login';

    const payload = isRegister 
      ? { name, email, password, confirm_password: confirmPassword, role }
      : { email, password, role };

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access_token);

        if (rememberMe) {
          localStorage.setItem('saved_email', email);
          localStorage.setItem('saved_password', password);
          localStorage.setItem('remember_me', 'true');
        } else {
          localStorage.removeItem('saved_email');
          localStorage.removeItem('saved_password');
          localStorage.setItem('remember_me', 'false');
        }

        setLoggedInUser({ name: data.name, role: data.role, email: data.email });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Authentication failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Unable to connect to backend server (http://127.0.0.1:8000)' });
    } finally {
      setLoading(false);
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

    const savedEmail = localStorage.getItem('saved_email');
    const savedPassword = localStorage.getItem('saved_password');
    const savedRemember = localStorage.getItem('remember_me');

    if (savedRemember === 'true' && savedEmail) {
      setEmail(savedEmail);
      if (savedPassword) setPassword(savedPassword);
    } else {
      setPassword('');
    }
  };

  // Register and persist site returned from map picker to FastAPI DB
  const handleConfirmMapSite = async (siteMeta) => {
    const rawLat = typeof siteMeta.rawLat === 'number' ? siteMeta.rawLat : parseFloat(siteMeta.lat) || 25.0;
    const rawLng = typeof siteMeta.rawLng === 'number' ? siteMeta.rawLng : parseFloat(siteMeta.long) || 75.0;
    const solarVal = `${(Math.random() * 1.8 + 4.6).toFixed(1)} kWh/m²/day`;
    const windVal = `${(Math.random() * 3.2 + 5.2).toFixed(1)} m/s`;
    const scoreVal = Math.floor(Math.random() * 12 + 86);

    const payload = {
      name: siteMeta.name || `Custom Site ${sites.length + 1}`,
      region: siteMeta.region || 'Selected Region',
      lat: rawLat,
      long: rawLng,
      site_type: 'Hybrid (Solar + Wind)',
      area: siteMeta.area || '30.0 km²',
      solar_potential: solarVal,
      wind_speed: windVal,
      grid_proximity: siteMeta.gridProximity || '2.0 km',
      elevation: siteMeta.elevation || '250 m',
      suitability_score: scoreVal
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/api/sites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const savedSite = await response.json();
        setSites((prev) => [savedSite, ...prev]);
        setSelectedSiteId(savedSite.id);
      } else {
        const fallbackSite = { ...payload, id: Date.now() };
        setSites((prev) => [fallbackSite, ...prev]);
        setSelectedSiteId(fallbackSite.id);
      }
    } catch (err) {
      const fallbackSite = { ...payload, id: Date.now() };
      setSites((prev) => [fallbackSite, ...prev]);
      setSelectedSiteId(fallbackSite.id);
    } finally {
      setIsMapModalOpen(false);
      setActiveTab('select-site');
    }
  };

  const formatCoord = (val, dirPos, dirNeg) => {
    if (typeof val === 'number') {
      return `${Math.abs(val).toFixed(4)}° ${val >= 0 ? dirPos : dirNeg}`;
    }
    return String(val || '');
  };

  // ----------------------------------------------------
  // AUTHENTICATED DASHBOARD
  // ----------------------------------------------------
  if (loggedInUser) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col selection:bg-emerald-500 selection:text-white">

        {/* Sign Out Confirmation Modal Dialog */}
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
                <p className="text-xs font-semibold text-slate-200 leading-tight">
                  {loggedInUser.name}
                </p>
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

        {/* Dashboard Body with Sidebar */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* ======================= SIDEBAR ======================= */}
          <aside className="w-64 bg-slate-900/70 border-r border-slate-800/80 flex flex-col justify-between p-4 backdrop-blur-xl flex-shrink-0">
            <div className="space-y-6">
              
              <div>
                <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider px-3 mb-2">
                  Navigation Menu
                </p>
                <nav className="space-y-1.5">
                  
                  {/* Option 1: Select / Register New Site */}
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

                  {/* Option 2: View Stored Sites */}
                  <button
                    onClick={() => setActiveTab('stored-sites')}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'stored-sites'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <FolderGit2 className="w-4 h-4 text-sky-400" />
                    <span>View Stored Sites</span>
                    <span className="ml-auto text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700 font-mono">
                      {sites.length}
                    </span>
                  </button>

                  {/* Option 3: Compare Sites */}
                  <button
                    onClick={() => setActiveTab('compare-sites')}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'compare-sites'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <TrendingUp className="w-4 h-4 text-amber-400" />
                    <span>Compare Sites</span>
                  </button>

                  {/* Option 4: View Report */}
                  <button
                    onClick={() => setActiveTab('view-report')}
                    className={`w-full flex items-center space-x-3 px-3.5 py-2.5 rounded-2xl text-xs font-semibold transition duration-200 cursor-pointer ${
                      activeTab === 'view-report'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-sm'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <FileText className="w-4 h-4 text-purple-400" />
                    <span>View Feasibility Report</span>
                  </button>

                </nav>
              </div>

              {/* Quick Map Launcher Card */}
              <div className="bg-slate-950/80 border border-slate-800/80 rounded-2xl p-3.5 text-center">
                <Globe2 className="w-6 h-6 text-emerald-400 mx-auto mb-2 animate-pulse" />
                <p className="text-xs font-bold text-white">GIS Map Picker</p>
                <p className="text-[10px] text-slate-400 mt-1 mb-3">Drop pins and auto-extract coordinates on OpenStreetMap.</p>
                <button
                  onClick={() => setIsMapModalOpen(true)}
                  className="w-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold py-2 rounded-xl transition shadow-sm flex items-center justify-center space-x-1.5 cursor-pointer"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>Launch Map</span>
                </button>
              </div>

            </div>

            {/* Platform Status Info */}
            <div className="bg-slate-950/50 rounded-2xl p-3 border border-slate-800/60 text-[11px] text-slate-400">
              <div className="flex items-center justify-between mb-1">
                <span>Active Target:</span>
                <span className="font-semibold text-emerald-400 truncate max-w-[100px]">{currentSiteData.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Suitability:</span>
                <span className="font-bold text-white">{currentSiteData.suitability_score || currentSiteData.suitabilityScore}/100</span>
              </div>
            </div>

          </aside>

          {/* ======================= MAIN CONTENT VIEW ======================= */}
          <main className="flex-1 overflow-y-auto p-6 md:p-8 space-y-6">

            {/* VIEW 1: SELECT / EVALUATE NEW SITE */}
            {activeTab === 'select-site' && (
              <div className="space-y-6 animate-in fade-in duration-200">
                
                {/* Active Deployment Hero Card */}
                <div className="bg-slate-900/70 border border-slate-800/80 rounded-3xl p-6 md:p-8 backdrop-blur-xl shadow-2xl">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800/60">
                    <div>
                      <div className="flex items-center space-x-2 text-emerald-400 mb-1.5">
                        <Sparkles className="w-4 h-4" />
                        <span className="text-[11px] font-bold uppercase tracking-wider">Site Intelligence & Selection</span>
                      </div>
                      <h2 className="text-xl font-bold text-white tracking-tight">Active Deployment Target Zone</h2>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Evaluating <span className="text-emerald-400 font-semibold">{currentSiteData.name}</span> ({currentSiteData.region}).
                      </p>
                    </div>

                    <div className="flex items-center space-x-3">
                      <select
                        value={selectedSiteId}
                        onChange={(e) => setSelectedSiteId(e.target.value)}
                        className="bg-slate-950 border border-slate-800 text-slate-200 rounded-2xl px-4 py-2.5 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-emerald-500/50 cursor-pointer"
                      >
                        {sites.map((site) => (
                          <option key={site.id} value={site.id}>
                            {site.name} ({site.region})
                          </option>
                        ))}
                      </select>

                      <button 
                        onClick={() => setIsMapModalOpen(true)}
                        className="flex items-center space-x-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 text-xs font-bold px-4 py-2.5 rounded-2xl transition shadow-lg shadow-emerald-500/20 active:scale-95 cursor-pointer"
                      >
                        <Globe2 className="w-4 h-4" />
                        <span>Register Site on Map</span>
                      </button>
                    </div>
                  </div>

                  {/* Selected Site Details */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                    <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Coordinates</p>
                      <p className="text-sm font-bold text-slate-200 mt-1 flex items-center space-x-1.5">
                        <Compass className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span className="truncate">{formatCoord(currentSiteData.lat, 'N', 'S')}, {formatCoord(currentSiteData.long, 'E', 'W')}</span>
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">Area: {currentSiteData.area || 'N/A'}</p>
                    </div>

                    <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Solar GHI Potential</p>
                      <p className="text-sm font-bold text-amber-400 mt-1 flex items-center space-x-1.5">
                        <Sun className="w-4 h-4 text-amber-400 flex-shrink-0" />
                        <span>{currentSiteData.solar_potential || currentSiteData.solarPotential || '5.5 kWh/m²/day'}</span>
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">NASA POWER Feed</p>
                    </div>

                    <div className="bg-slate-950/60 p-4 rounded-2xl border border-slate-800/80">
                      <p className="text-[10px] font-medium text-slate-500 uppercase tracking-wider">Mean Wind (100m)</p>
                      <p className="text-sm font-bold text-sky-400 mt-1 flex items-center space-x-1.5">
                        <Wind className="w-4 h-4 text-sky-400 flex-shrink-0" />
                        <span>{currentSiteData.wind_speed || currentSiteData.windSpeed || '6.8 m/s'}</span>
                      </p>
                      <p className="text-[11px] text-slate-500 mt-1">Global Wind Atlas</p>
                    </div>

                    <div className="bg-emerald-950/30 p-4 rounded-2xl border border-emerald-500/30">
                      <p className="text-[10px] font-medium text-emerald-400 uppercase tracking-wider">Suitability Index</p>
                      <p className="text-base font-extrabold text-emerald-300 mt-0.5 flex items-center space-x-1.5">
                        <Activity className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span>{currentSiteData.suitability_score || currentSiteData.suitabilityScore || 90} / 100</span>
                      </p>
                      <p className="text-[11px] text-emerald-400/80 mt-1">Grid Distance: {currentSiteData.grid_proximity || currentSiteData.gridProximity || '2.0 km'}</p>
                    </div>
                  </div>
                </div>

                {/* Action Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-slate-900/60 p-6 rounded-3xl border border-slate-800/80 hover:border-emerald-500/40 transition">
                    <div className="w-11 h-11 bg-emerald-500/10 text-emerald-400 rounded-2xl flex items-center justify-center mb-4">
                      <Layers className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-white">GIS Elevation & Terrain</h3>
                    <p className="text-xs text-slate-400 mt-1.5 mb-5 leading-relaxed">
                      Analyze digital elevation models (DEM), slope gradients, and infrastructure proximity buffers.
                    </p>
                    <button 
                      onClick={() => setIsMapModalOpen(true)}
                      className="flex items-center space-x-1.5 text-xs font-bold text-emerald-400 hover:text-emerald-300 cursor-pointer"
                    >
                      <span>Open Map Picker</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="bg-slate-900/60 p-6 rounded-3xl border border-slate-800/80 hover:border-amber-500/40 transition">
                    <div className="w-11 h-11 bg-amber-500/10 text-amber-400 rounded-2xl flex items-center justify-center mb-4">
                      <Zap className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-white">Yield Prediction Engine</h3>
                    <p className="text-xs text-slate-400 mt-1.5 mb-5 leading-relaxed">
                      Simulate annual generation (MWh) and Capacity Utilization Factor (CUF) with ML algorithms.
                    </p>
                    <button 
                      onClick={() => setActiveTab('view-report')}
                      className="flex items-center space-x-1.5 text-xs font-bold text-amber-400 hover:text-amber-300 cursor-pointer"
                    >
                      <span>Simulate Yield</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <div className="bg-slate-900/60 p-6 rounded-3xl border border-slate-800/80 hover:border-sky-500/40 transition">
                    <div className="w-11 h-11 bg-sky-500/10 text-sky-400 rounded-2xl flex items-center justify-center mb-4">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-white">Multi-Site Comparison</h3>
                    <p className="text-xs text-slate-400 mt-1.5 mb-5 leading-relaxed">
                      Benchmark candidate sites across irradiance, wind speed, CAPEX, and grid connectivity.
                    </p>
                    <button 
                      onClick={() => setActiveTab('compare-sites')}
                      className="flex items-center space-x-1.5 text-xs font-bold text-sky-400 hover:text-sky-300 cursor-pointer"
                    >
                      <span>Compare Sites</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

              </div>
            )}

            {/* VIEW 2: VIEW STORED SITES */}
            {activeTab === 'stored-sites' && (
              <div className="space-y-6 animate-in fade-in duration-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white">Stored Candidate Sites</h2>
                    <p className="text-xs text-slate-400 mt-1">All persistent geographic boundaries and project corridors in your database.</p>
                  </div>
                  <button 
                    onClick={() => setIsMapModalOpen(true)}
                    className="flex items-center space-x-1.5 bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold px-4 py-2.5 rounded-2xl transition cursor-pointer"
                  >
                    <PlusCircle className="w-4 h-4" />
                    <span>Register Another Site</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                  {sites.map((s) => (
                    <div 
                      key={s.id} 
                      className={`bg-slate-900/80 p-5 rounded-3xl border transition duration-200 ${
                        String(s.id) === String(selectedSiteId) ? 'border-emerald-500 shadow-lg shadow-emerald-500/10' : 'border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
                          {s.site_type || s.type || 'Hybrid'}
                        </span>
                        <span className="text-xs font-extrabold text-emerald-300">
                          {s.suitability_score || s.suitabilityScore || 90}/100 Score
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-white">{s.name}</h3>
                      <p className="text-xs text-slate-400 mb-4">{s.region}</p>

                      <div className="space-y-2 text-xs text-slate-300 border-t border-slate-800/80 pt-3 mb-4">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Coordinates:</span>
                          <span className="font-mono text-slate-200">{formatCoord(s.lat, 'N', 'S')}, {formatCoord(s.long, 'E', 'W')}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Solar (GHI):</span>
                          <span className="text-amber-400 font-semibold">{s.solar_potential || s.solarPotential}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Wind (100m):</span>
                          <span className="text-sky-400 font-semibold">{s.wind_speed || s.windSpeed}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Grid Distance:</span>
                          <span className="text-slate-300 font-semibold">{s.grid_proximity || s.gridProximity}</span>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          setSelectedSiteId(s.id);
                          setActiveTab('select-site');
                        }}
                        className={`w-full py-2 text-xs font-bold rounded-xl transition cursor-pointer ${
                          String(s.id) === String(selectedSiteId) 
                            ? 'bg-emerald-500 text-slate-950' 
                            : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
                        }`}
                      >
                        {String(s.id) === String(selectedSiteId) ? 'Currently Active Target' : 'Set as Active Target'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* VIEW 3: COMPARE SITES */}
            {activeTab === 'compare-sites' && (
              <div className="space-y-6 animate-in fade-in duration-200">
                <div>
                  <h2 className="text-xl font-bold text-white">Multi-Site Comparison Matrix</h2>
                  <p className="text-xs text-slate-400 mt-1">Side-by-side evaluation of registered database sites against resource, infrastructure, and suitability benchmarks.</p>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-slate-300">
                      <thead className="bg-slate-950 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                        <tr>
                          <th className="px-6 py-4">Site Name & Region</th>
                          <th className="px-6 py-4">Type</th>
                          <th className="px-6 py-4">Solar Potential (GHI)</th>
                          <th className="px-6 py-4">Wind Speed (100m)</th>
                          <th className="px-6 py-4">Land Area</th>
                          <th className="px-6 py-4">Grid Proximity</th>
                          <th className="px-6 py-4">Suitability</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {sites.map((s) => (
                          <tr key={s.id} className="hover:bg-slate-800/30 transition">
                            <td className="px-6 py-4 font-semibold text-white">
                              {s.name}
                              <span className="block text-[11px] text-slate-400 font-normal">{s.region}</span>
                            </td>
                            <td className="px-6 py-4">{s.site_type || s.type}</td>
                            <td className="px-6 py-4 font-semibold text-amber-400">{s.solar_potential || s.solarPotential}</td>
                            <td className="px-6 py-4 font-semibold text-sky-400">{s.wind_speed || s.windSpeed}</td>
                            <td className="px-6 py-4">{s.area}</td>
                            <td className="px-6 py-4">{s.grid_proximity || s.gridProximity}</td>
                            <td className="px-6 py-4">
                              <span className="px-3 py-1 rounded-full text-[11px] font-extrabold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                                {s.suitability_score || s.suitabilityScore} / 100
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* VIEW 4: VIEW FEASIBILITY REPORT */}
            {activeTab === 'view-report' && (
              <div className="space-y-6 animate-in fade-in duration-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-bold text-white">Executive Feasibility Report</h2>
                    <p className="text-xs text-slate-400 mt-1">Generated deployment assessment for <span className="text-emerald-400 font-semibold">{currentSiteData.name}</span>.</p>
                  </div>
                  <button 
                    onClick={() => window.print()}
                    className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold px-4 py-2.5 rounded-2xl transition border border-slate-700 cursor-pointer"
                  >
                    <Download className="w-4 h-4" />
                    <span>Export Report</span>
                  </button>
                </div>

                <div className="bg-slate-900/80 border border-slate-800 rounded-3xl p-8 space-y-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-6 border-b border-slate-800 gap-4">
                    <div>
                      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest">DEPLOYMENT READINESS</span>
                      <h3 className="text-2xl font-black text-white mt-1">{currentSiteData.name}</h3>
                      <p className="text-xs text-slate-400">{currentSiteData.region} • Coordinates: {formatCoord(currentSiteData.lat, 'N', 'S')}, {formatCoord(currentSiteData.long, 'E', 'W')}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Overall Index</p>
                      <p className="text-3xl font-extrabold text-emerald-400">{currentSiteData.suitability_score || currentSiteData.suitabilityScore}<span className="text-sm text-slate-400">/100</span></p>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Estimated Annual Generation</p>
                      <p className="text-lg font-bold text-white mt-1">142,800 MWh/yr</p>
                      <p className="text-[10px] text-emerald-400 mt-0.5">XGBoost Yield Model</p>
                    </div>
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Capacity Utilization Factor (CUF)</p>
                      <p className="text-lg font-bold text-amber-400 mt-1">28.4 %</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">Solar + Wind Colocation</p>
                    </div>
                    <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800">
                      <p className="text-[10px] text-slate-400 uppercase font-semibold">Grid Interconnection Cost</p>
                      <p className="text-lg font-bold text-sky-400 mt-1">Low ({currentSiteData.grid_proximity || currentSiteData.gridProximity || '1.8 km'} to Substation)</p>
                      <p className="text-[10px] text-slate-500 mt-0.5">OSM Substation Buffer</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

          </main>
        </div>

        {/* Integrated Map Modal */}
        <MapPickerModal
          isOpen={isMapModalOpen}
          onClose={() => setIsMapModalOpen(false)}
          onConfirmSite={handleConfirmMapSite}
        />
      </div>
    );
  }

  // ----------------------------------------------------
  // LOGIN / REGISTER VIEW (UNAUTHENTICATED)
  // ----------------------------------------------------
  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-6 text-slate-200 font-sans relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-20 -left-20 w-80 h-80 bg-emerald-500/20 rounded-full blur-[80px] animate-pulse"></div>
        <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-sky-500/20 rounded-full blur-[80px] animate-pulse delay-1000"></div>
      </div>

      <div className="max-w-md w-full bg-slate-900/80 rounded-3xl shadow-2xl border border-slate-800 p-8 backdrop-blur-2xl relative z-10">
        <div className="flex flex-col items-center text-center mb-6">
          <div className="flex items-center justify-center space-x-2 bg-emerald-500/10 text-emerald-400 p-3.5 rounded-2xl border border-emerald-500/20 mb-3 shadow-inner">
            <Sun className="w-6 h-6 text-amber-400" />
            <Wind className="w-6 h-6 text-sky-400" />
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            Solar & Wind Intelligence Platform
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Renewable Energy Deployment & Feasibility Analysis
          </p>
        </div>

        <div className="flex bg-slate-950/80 p-1 rounded-2xl mb-6 border border-slate-800">
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
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Display Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type="text"
                  required
                  placeholder="Sakshi Sharma"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Platform Role
            </label>
            <div className="relative">
              <UserCheck className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition cursor-pointer"
              >
                {roles.map((r) => (
                  <option key={r} value={r} className="bg-slate-900 text-slate-200">{r}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                placeholder="planner@energy.org"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              {isRegister ? 'Create Password (at least 6 characters)' : 'Password'}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-10 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition"
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
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3 top-3.5" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-slate-950/90 border border-slate-800 rounded-xl pl-9 pr-10 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 transition"
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

          {/* Remember Me Checkbox */}
          <div className="flex items-center justify-between py-1">
            <label className="flex items-center space-x-2 text-xs text-slate-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded bg-slate-950 border-slate-800 text-emerald-500 focus:ring-emerald-500/50 cursor-pointer"
              />
              <span>Remember email & password</span>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold py-3 rounded-xl text-xs shadow-lg shadow-emerald-500/20 transition duration-200 ease-in-out mt-2 disabled:opacity-50 active:scale-[0.98] cursor-pointer"
          >
            {loading 
              ? (isRegister ? 'Creating Account...' : 'Authenticating...') 
              : (isRegister ? 'Register & Sign In' : 'Sign In')
            }
          </button>
        </form>
      </div>
    </div>
  );
}
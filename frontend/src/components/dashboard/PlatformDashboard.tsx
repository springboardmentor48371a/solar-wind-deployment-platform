import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { 
  Sun, Wind, LogOut, CheckCircle2, User, Mail, 
  Calculator, Activity, PlusCircle, History, Landmark, Compass, AlertTriangle, MapPin, Ruler
} from 'lucide-react';
import { SiteMapPicker, type LocationData } from './SiteMapPicker';

interface SiteAssessment {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  region: string;
  land_area: number;
  land_ownership: string;
  
  // Predictions
  predicted_irradiance: number;
  predicted_wind_speed: number;
  predicted_temp: number;
  predicted_cloud_cover: number;
  predicted_elevation: number;
  predicted_slope: number;
  
  // Scores
  resource_score: number;
  geographic_score: number;
  infrastructure_score: number;
  environmental_score: number;
  economic_score: number;
  overall_score: number;
  suitability_class: string;
  created_at: string;
}

export const PlatformDashboard: React.FC = () => {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<'assess' | 'settings'>('assess');
  
  // Form States - with sensible default candidate location
  const [name, setName] = useState('Jaipur Solar & Wind Park Phase I');
  const [latitude, setLatitude] = useState('26.9124');
  const [longitude, setLongitude] = useState('75.7873');
  const [region, setRegion] = useState('Rajasthan');
  const [district, setDistrict] = useState('Jaipur District');
  const [landArea, setLandArea] = useState('150000');
  const [landOwnership, setLandOwnership] = useState('Government Lease');

  // Real-time Area & Spatial Geometry states
  const [areaDimensions, setAreaDimensions] = useState<{
    areaLengthM: number;
    areaWidthM: number;
    radiusM: number;
    acres: number;
    hectares: number;
  }>({
    areaLengthM: 387,
    areaWidthM: 387,
    radiusM: 219,
    acres: 37.07,
    hectares: 15.0,
  });
  
  // Status States
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assessmentResult, setAssessmentResult] = useState<SiteAssessment | null>(null);
  const [historyList, setHistoryList] = useState<SiteAssessment[]>([]);

  // Coordinate presets for quick demonstration
  const presets = [
    { name: "Jaipur, Rajasthan", lat: 26.9124, lon: 75.7873, reg: "Rajasthan", district: "Jaipur District", area: 150000, own: "Government Lease" },
    { name: "Kanyakumari Coast, TN", lat: 8.0883, lon: 77.5385, reg: "Tamil Nadu", district: "Kanyakumari District", area: 250000, own: "Government Lease" },
    { name: "Leh Mountain, Ladakh", lat: 34.1526, lon: 77.5771, reg: "Ladakh", district: "Leh District", area: 180000, own: "Government Lease" },
    { name: "Shillong Hills, Meghalaya", lat: 25.5788, lon: 91.8933, reg: "Meghalaya", district: "East Khasi Hills", area: 90000, own: "Private Purchase" }
  ];

  const applyPreset = (preset: typeof presets[0]) => {
    setName(`${preset.name} Renewable Project`);
    setLatitude(preset.lat.toString());
    setLongitude(preset.lon.toString());
    setRegion(preset.reg);
    setDistrict(preset.district);
    setLandArea(preset.area.toString());
    setLandOwnership(preset.own);
    const radiusM = Math.round(Math.sqrt(preset.area / Math.PI));
    const sideM = Math.round(Math.sqrt(preset.area));
    setAreaDimensions({
      areaLengthM: sideM,
      areaWidthM: sideM,
      radiusM,
      acres: parseFloat((preset.area * 0.000247105).toFixed(2)),
      hectares: parseFloat((preset.area / 10000).toFixed(2)),
    });
  };

  // Callback when user clicks or selects a point anywhere on the interactive GIS map
  const handleMapLocationSelect = (loc: LocationData) => {
    setLatitude(loc.lat.toString());
    setLongitude(loc.lon.toString());
    setRegion(loc.state);
    setDistrict(loc.district);
    setAreaDimensions({
      areaLengthM: loc.areaLengthM,
      areaWidthM: loc.areaWidthM,
      radiusM: loc.radiusM,
      acres: loc.acres,
      hectares: loc.hectares,
    });
    // Auto-update project title if using standard naming
    if (!name || name.includes('Solar') || name.includes('Wind') || name.includes('Project') || name.includes('Park')) {
      setName(`${loc.district} Renewable Energy Site`);
    }
  };

  // Callback when user modifies or clicks quick area presets
  const handleAreaSelect = (newArea: number) => {
    setLandArea(newArea.toString());
    const radiusM = Math.round(Math.sqrt(newArea / Math.PI));
    const sideM = Math.round(Math.sqrt(newArea));
    setAreaDimensions({
      areaLengthM: sideM,
      areaWidthM: sideM,
      radiusM,
      acres: parseFloat((newArea * 0.000247105).toFixed(2)),
      hectares: parseFloat((newArea / 10000).toFixed(2)),
    });
  };

  const fetchHistory = async () => {
    try {
      const response = await api.get<SiteAssessment[]>('/api/sites/');
      setHistoryList(response.data);
    } catch (err: any) {
      console.error("Failed to fetch assessment history", err);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleAssessSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    
    try {
      const payload = {
        name,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        region,
        land_area: parseFloat(landArea),
        land_ownership: landOwnership
      };
      
      const response = await api.post<SiteAssessment>('/api/sites/assess', payload);
      setAssessmentResult(response.data);
      fetchHistory(); // Refresh history table
    } catch (err: any) {
      setError(err.response?.data?.detail || "An error occurred during site assessment.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSuitabilityColor = (suitClass: string) => {
    switch (suitClass) {
      case 'Excellent': return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
      case 'Good': return 'text-green-400 border-green-500/30 bg-green-500/10';
      case 'Moderate': return 'text-amber-400 border-amber-500/30 bg-amber-500/10';
      default: return 'text-rose-400 border-rose-500/30 bg-rose-500/10';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex flex-col relative overflow-hidden">
      
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />

      {/* Navbar Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-amber-500">
              <Sun className="w-5 h-5 animate-spin-slow" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-snug">
                Solar & Wind Deployment Intelligence Platform
              </h1>
              <p className="text-xs text-amber-400 font-semibold tracking-wide">
                AI-Powered Renewable Energy Intelligence
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={() => setActiveTab(activeTab === 'assess' ? 'settings' : 'assess')}
              className="px-3.5 py-1.5 rounded-lg border border-slate-800 hover:border-slate-700 bg-slate-900 text-xs font-semibold text-slate-300 transition-all"
            >
              {activeTab === 'assess' ? 'Show Account Settings' : 'Back to Assessment'}
            </button>
            <button
              onClick={logout}
              className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-rose-950/20 hover:bg-rose-900/30 border border-rose-800/40 text-rose-300 text-sm font-bold transition-all shadow-sm"
            >
              <LogOut className="w-4 h-4" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 z-10">
        
        {activeTab === 'assess' ? (
          <>
            {/* Intro Welcome Banner */}
            <div className="glass-card rounded-3xl p-6 sm:p-8 mb-8 border border-slate-800 shadow-xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
                <Wind className="w-48 h-48 text-emerald-500" />
              </div>
              <div className="relative z-10">
                <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/35 text-emerald-400 text-xs font-bold mb-4 shadow-sm">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Milestone 2 - Core Intelligence Module Active</span>
                </div>
                <h2 className="text-3xl font-extrabold text-white mb-2">
                  Solar & Wind Site Suitability Assessment
                </h2>
                <p className="text-slate-300 text-sm max-w-3xl leading-relaxed">
                  Enter geographic coordinates below to run our **scikit-learn machine learning regressor models**. 
                  The platform predicts weather, climate, and terrain features for the location, and then calculates deployment suitability rankings using our weighted math formula.
                </p>
              </div>
            </div>

            {/* Interactive GIS Map & Site Dimension Explorer */}
            <SiteMapPicker
              latitude={latitude ? parseFloat(latitude) : null}
              longitude={longitude ? parseFloat(longitude) : null}
              landArea={landArea ? parseFloat(landArea) : 150000}
              onLocationSelect={handleMapLocationSelect}
              onAreaSelect={handleAreaSelect}
            />

            {/* Assessment Dashboard Section */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-8">
              
              {/* Left Column: Assessment Input Form (Grid size: 5) */}
              <div className="lg:col-span-5 flex flex-col space-y-6">
                <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-lg">
                  <h3 className="text-md font-bold text-white mb-4 flex items-center space-x-2">
                    <PlusCircle className="w-5 h-5 text-amber-500" />
                    <span>Candidate Site Coordinates</span>
                  </h3>
                  
                  {/* Preset quick buttons */}
                  <div className="mb-5">
                    <span className="text-xs font-semibold text-slate-400 block mb-2">Demonstration Location Presets:</span>
                    <div className="grid grid-cols-2 gap-2">
                      {presets.map((preset, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => applyPreset(preset)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-[11px] font-bold text-slate-300 text-left truncate transition-all"
                        >
                          📍 {preset.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleAssessSubmit} className="space-y-4">
                    <div>
                      <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Site / Project Name</label>
                      <input
                        type="text" required
                        placeholder="e.g. Rajasthan Solar Park Phase I"
                        value={name} onChange={(e) => setName(e.target.value)}
                        className="glass-input w-full px-3 py-2 text-sm"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Latitude</label>
                        <input
                          type="number" step="any" required
                          placeholder="e.g. 26.9124"
                          value={latitude} onChange={(e) => setLatitude(e.target.value)}
                          className="glass-input w-full px-3 py-2 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Longitude</label>
                        <input
                          type="number" step="any" required
                          placeholder="e.g. 75.7873"
                          value={longitude} onChange={(e) => setLongitude(e.target.value)}
                          className="glass-input w-full px-3 py-2 text-sm"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Region / State</label>
                        <input
                          type="text" required
                          placeholder="e.g. Rajasthan"
                          value={region} onChange={(e) => setRegion(e.target.value)}
                          className="glass-input w-full px-3 py-2 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Land Area (m²)</label>
                        <input
                          type="number" required min="1"
                          placeholder="e.g. 150000"
                          value={landArea} onChange={(e) => setLandArea(e.target.value)}
                          className="glass-input w-full px-3 py-2 text-sm"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-1">Land Ownership</label>
                      <select
                        value={landOwnership} onChange={(e) => setLandOwnership(e.target.value)}
                        className="glass-input w-full px-3 py-2 text-sm bg-slate-950"
                      >
                        <option value="Government Lease">Government Lease</option>
                        <option value="Private Purchase">Private Purchase</option>
                        <option value="Community Land">Community Land</option>
                      </select>
                    </div>

                    {/* Live GIS & Boundary Derived Metadata Card */}
                    <div className="bg-slate-950/70 rounded-xl p-3 border border-slate-800/80 space-y-2 text-xs">
                      <div className="flex items-center justify-between text-slate-400">
                        <span className="font-semibold flex items-center space-x-1">
                          <MapPin className="w-3.5 h-3.5 text-amber-500" />
                          <span>Detected District:</span>
                        </span>
                        <span className="font-bold text-white truncate max-w-[200px]">{district}</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400 border-t border-slate-850 pt-1.5">
                        <span className="font-semibold flex items-center space-x-1">
                          <Ruler className="w-3.5 h-3.5 text-cyan-400" />
                          <span>Estimated Plot Span:</span>
                        </span>
                        <span className="font-mono text-cyan-300 font-semibold">~{areaDimensions.areaLengthM}m × {areaDimensions.areaWidthM}m</span>
                      </div>
                      <div className="flex items-center justify-between text-slate-400 border-t border-slate-850 pt-1.5">
                        <span className="font-semibold">Equivalent Land Scale:</span>
                        <span className="font-bold text-amber-300">{areaDimensions.acres} Acres ({areaDimensions.hectares} Ha)</span>
                      </div>
                    </div>

                    {error && (
                      <div className="p-3 bg-rose-950/20 border border-rose-800/40 text-rose-300 text-xs rounded-xl flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                        <span>{error}</span>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-sm transition-all shadow-md flex items-center justify-center space-x-2 disabled:opacity-50"
                    >
                      <Calculator className="w-4 h-4" />
                      <span>{isSubmitting ? 'Running ML Models...' : 'Run AI Suitability Assessment'}</span>
                    </button>
                  </form>
                </div>
              </div>

              {/* Right Column: Results Display Panel (Grid size: 7) */}
              <div className="lg:col-span-7 flex flex-col">
                <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-lg flex-1 flex flex-col justify-between">
                  {assessmentResult ? (
                    <div className="space-y-6">
                      
                      {/* Overall Assessment Score Header */}
                      <div className="flex items-center justify-between border-b border-slate-800/60 pb-4">
                        <div>
                          <h4 className="text-slate-400 text-xs font-bold uppercase tracking-wider">Overall Assessment</h4>
                          <h3 className="text-2xl font-black text-white mt-0.5">{assessmentResult.name}</h3>
                          <p className="text-xs text-slate-400 mt-0.5">Coordinates: Lat {assessmentResult.latitude}, Lon {assessmentResult.longitude}</p>
                        </div>
                        <div className={`px-4 py-2 rounded-2xl border text-center ${getSuitabilityColor(assessmentResult.suitability_class)}`}>
                          <span className="text-2xl font-black block tracking-tight">{assessmentResult.overall_score}%</span>
                          <span className="text-[10px] font-bold uppercase tracking-widest">{assessmentResult.suitability_class}</span>
                        </div>
                      </div>

                      {/* Part 1: ML Model Predictions */}
                      <div>
                        <h4 className="text-amber-500 text-xs font-bold uppercase tracking-wider mb-3 flex items-center space-x-2">
                          <Activity className="w-4 h-4" />
                          <span>AI Machine Learning Predictions</span>
                        </h4>
                        
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                          <div className="bg-slate-950/65 rounded-xl p-3 border border-slate-800/60">
                            <span className="text-slate-400 text-[10px] font-bold uppercase block tracking-wider">Solar Irradiance</span>
                            <span className="text-md font-extrabold text-white mt-1 block">🌞 {assessmentResult.predicted_irradiance} <span className="text-xs font-medium text-slate-400">kWh/m²</span></span>
                          </div>
                          <div className="bg-slate-950/65 rounded-xl p-3 border border-slate-800/60">
                            <span className="text-slate-400 text-[10px] font-bold uppercase block tracking-wider">Wind Speed</span>
                            <span className="text-md font-extrabold text-white mt-1 block">💨 {assessmentResult.predicted_wind_speed} <span className="text-xs font-medium text-slate-400">m/s</span></span>
                          </div>
                          <div className="bg-slate-950/65 rounded-xl p-3 border border-slate-800/60">
                            <span className="text-slate-400 text-[10px] font-bold uppercase block tracking-wider">Temperature</span>
                            <span className="text-md font-extrabold text-white mt-1 block">🌡️ {assessmentResult.predicted_temp} <span className="text-xs font-medium text-slate-400">°C</span></span>
                          </div>
                          <div className="bg-slate-950/65 rounded-xl p-3 border border-slate-800/60">
                            <span className="text-slate-400 text-[10px] font-bold uppercase block tracking-wider">Cloud Cover</span>
                            <span className="text-md font-extrabold text-white mt-1 block">☁️ {assessmentResult.predicted_cloud_cover} <span className="text-xs font-medium text-slate-400">%</span></span>
                          </div>
                          <div className="bg-slate-950/65 rounded-xl p-3 border border-slate-800/60">
                            <span className="text-slate-400 text-[10px] font-bold uppercase block tracking-wider">Elevation</span>
                            <span className="text-md font-extrabold text-white mt-1 block">🏔️ {assessmentResult.predicted_elevation} <span className="text-xs font-medium text-slate-400">m</span></span>
                          </div>
                          <div className="bg-slate-950/65 rounded-xl p-3 border border-slate-800/60">
                            <span className="text-slate-400 text-[10px] font-bold uppercase block tracking-wider">Land Slope (Derived)</span>
                            <span className="text-md font-extrabold text-white mt-1 block">📐 {assessmentResult.predicted_slope} <span className="text-xs font-medium text-slate-400">°</span></span>
                          </div>
                        </div>
                      </div>

                      {/* Part 2: Math Scoring Progress Bars */}
                      <div className="border-t border-slate-800/60 pt-4">
                        <h4 className="text-amber-500 text-xs font-bold uppercase tracking-wider mb-4 flex items-center space-x-2">
                          <Landmark className="w-4 h-4" />
                          <span>Weighted Suitability Breakdown</span>
                        </h4>

                        <div className="space-y-3">
                          {/* Resource 35% */}
                          <div>
                            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                              <span>Resource Availability (35% Weight)</span>
                              <span>{assessmentResult.resource_score} / 100</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div className="bg-amber-500 h-full rounded-full" style={{ width: `${assessmentResult.resource_score}%` }} />
                            </div>
                          </div>

                          {/* Geographic 25% */}
                          <div>
                            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                              <span>Geographic Suitability (25% Weight)</span>
                              <span>{assessmentResult.geographic_score} / 100</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div className="bg-amber-500 h-full rounded-full" style={{ width: `${assessmentResult.geographic_score}%` }} />
                            </div>
                          </div>

                          {/* Infrastructure 15% */}
                          <div>
                            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                              <span>Infrastructure Accessibility (15% Weight)</span>
                              <span>{assessmentResult.infrastructure_score} / 100</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div className="bg-amber-500 h-full rounded-full" style={{ width: `${assessmentResult.infrastructure_score}%` }} />
                            </div>
                          </div>

                          {/* Environmental 15% */}
                          <div>
                            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                              <span>Environmental Impact (15% Weight)</span>
                              <span>{assessmentResult.environmental_score} / 100</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div className="bg-amber-500 h-full rounded-full" style={{ width: `${assessmentResult.environmental_score}%` }} />
                            </div>
                          </div>

                          {/* Economic 10% */}
                          <div>
                            <div className="flex justify-between text-xs font-semibold text-slate-300 mb-1">
                              <span>Economic Feasibility (10% Weight)</span>
                              <span>{assessmentResult.economic_score} / 100</span>
                            </div>
                            <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                              <div className="bg-amber-500 h-full rounded-full" style={{ width: `${assessmentResult.economic_score}%` }} />
                            </div>
                          </div>
                        </div>
                      </div>

                    </div>
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                      <div className="p-4 rounded-full bg-slate-900 border border-slate-800 text-slate-500 mb-4 animate-pulse">
                        <Compass className="w-12 h-12" />
                      </div>
                      <h4 className="text-lg font-bold text-white mb-2">No Site Selected</h4>
                      <p className="text-slate-400 text-sm max-w-sm">
                        Apply one of the geographic coordinates presets on the left or enter a custom coordinate, then click **Assess** to run the prediction pipeline.
                      </p>
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* Assessment History Table */}
            <div className="glass-card rounded-2xl p-6 border border-slate-800 shadow-md">
              <h3 className="text-md font-bold text-white mb-4 flex items-center space-x-2">
                <History className="w-5 h-5 text-amber-500" />
                <span>Assessed Sites History ({historyList.length})</span>
              </h3>

              {historyList.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300 border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-bold uppercase tracking-wider">
                        <th className="py-3 px-4">Site Name</th>
                        <th className="py-3 px-4">Coordinates (Lat / Lon)</th>
                        <th className="py-3 px-4">Region</th>
                        <th className="py-3 px-4">Land Area</th>
                        <th className="py-3 px-4">Solar Irrad.</th>
                        <th className="py-3 px-4">Wind Speed</th>
                        <th className="py-3 px-4 text-center">Score</th>
                        <th className="py-3 px-4 text-center">Suitability</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40">
                      {historyList.map((site) => (
                        <tr
                          key={site.id}
                          onClick={() => setAssessmentResult(site)}
                          className="hover:bg-slate-900/45 cursor-pointer transition-all"
                        >
                          <td className="py-3.5 px-4 font-bold text-white">{site.name}</td>
                          <td className="py-3.5 px-4 font-mono">{site.latitude.toFixed(4)}, {site.longitude.toFixed(4)}</td>
                          <td className="py-3.5 px-4">{site.region}</td>
                          <td className="py-3.5 px-4">{site.land_area.toLocaleString()} m²</td>
                          <td className="py-3.5 px-4">🌞 {site.predicted_irradiance}</td>
                          <td className="py-3.5 px-4">💨 {site.predicted_wind_speed}</td>
                          <td className="py-3.5 px-4 text-center font-extrabold text-amber-400">{site.overall_score}%</td>
                          <td className="py-3.5 px-4 text-center">
                            <span className={`inline-block px-2 py-0.5 rounded-full border text-[10px] font-bold ${getSuitabilityColor(site.suitability_class)}`}>
                              {site.suitability_class}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-6 text-slate-500 font-medium">
                  No site assessments found. Complete your first coordinate assessment above to see details here.
                </div>
              )}
            </div>
          </>
        ) : (
          /* Settings Tab / Page (Original Dashboard details) */
          <div className="space-y-8">
            <div className="glass-card rounded-3xl p-6 sm:p-8 border border-slate-800 shadow-xl relative overflow-hidden">
              <div className="relative z-10">
                <div className="inline-flex items-center space-x-2 px-3.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/35 text-emerald-400 text-xs font-bold mb-4">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Authentication Session Active</span>
                </div>
                <h2 className="text-3xl font-extrabold text-white mb-2">
                  Account Details & Security Audit
                </h2>
                <p className="text-slate-300 text-sm max-w-2xl font-medium leading-relaxed">
                  Your identity and API access keys are managed client-side using secure JWT authentication contexts.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="glass-card rounded-2xl p-6 border border-slate-800 flex items-start space-x-4">
                <div className="p-3 rounded-xl bg-slate-900 text-amber-500 border border-slate-800">
                  <User className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">User Identity</span>
                  <p className="text-lg font-bold text-white mt-1">{user?.full_name}</p>
                  <p className="text-xs text-slate-400 font-medium mt-0.5">Account ID: {user?.id?.substring(0, 13)}...</p>
                </div>
              </div>

              <div className="glass-card rounded-2xl p-6 border border-slate-800 flex items-start space-x-4">
                <div className="p-3 rounded-xl bg-slate-900 text-emerald-400 border border-slate-800">
                  <Mail className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Authenticated Email</span>
                  <p className="text-lg font-bold text-white mt-1">{user?.email}</p>
                  <p className="text-xs text-slate-400 font-medium mt-0.5">Verified Primary Account</p>
                </div>
              </div>

              {/* Card 3: Total Assessed Sites */}
              <div className="glass-card rounded-2xl p-6 border border-slate-800 flex items-start space-x-4 shadow-sm">
                <div className="p-3 rounded-xl bg-slate-900 text-amber-500 border border-slate-800">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Platform Activity</span>
                  <p className="text-lg font-bold text-white mt-1">{historyList.length} Sites</p>
                  <p className="text-xs text-slate-400 font-medium mt-0.5">Assessed Locations</p>
                </div>
              </div>

            </div>

            {/* User Profile Panel */}
            <div className="glass-card rounded-2xl p-6 sm:p-8 border border-slate-800 shadow-sm">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                <User className="w-5 h-5 text-amber-500" />
                <span>User Profile</span>
              </h3>

              <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 text-sm text-slate-300 space-y-4 shadow-inner">
                <div className="flex justify-between border-b border-slate-850 pb-2.5">
                  <span className="text-slate-400 font-bold">Full Name</span>
                  <span className="text-white font-semibold">{user?.full_name}</span>
                </div>
                <div className="flex justify-between border-b border-slate-850 pb-2.5">
                  <span className="text-slate-400 font-bold">Email Address</span>
                  <span className="text-white font-semibold">{user?.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 font-bold">Member Since</span>
                  <span className="text-white font-semibold">
                    {user?.created_at ? new Date(user.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500 font-medium z-10">
        Solar & Wind Deployment Intelligence Platform &copy; 2026. All rights reserved.
      </footer>
    </div>
  );
};

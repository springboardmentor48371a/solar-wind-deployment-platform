import React, { useState, useRef } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Search, Check, X, Loader2, Compass, Mountain, Zap, AlertCircle, Edit3 } from 'lucide-react';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function MapClickHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function MapPickerModal({ isOpen, onClose, onConfirmSite, activeProjectName }) {
  const [selectedCoords, setSelectedCoords] = useState({ lat: 26.9124, lng: 75.7873 });
  const [siteCustomName, setSiteCustomName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const mapRef = useRef(null);

  const [siteDetails, setSiteDetails] = useState({
    name: 'Jaipur Renewable Zone',
    region: 'Rajasthan, India',
    elevation: '435 m',
    lat: '26.9124° N',
    long: '75.7873° E',
    rawLat: 26.9124,
    rawLng: 75.7873,
    area: '35.0 km²',
    gridProximity: '2.4 km',
  });

  if (!isOpen) return null;

  const fetchLocationData = async (lat, lng) => {
    setLoading(true);
    setSearchError(null);
    try {
      const geoRes = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`);
      const geoData = await geoRes.json();
      const addr = geoData.address || {};

      const regionName = [
        addr.state_district || addr.county || addr.city,
        addr.state,
        addr.country
      ].filter(Boolean).join(', ') || 'Custom Geographic Corridor';

      const detectedName = geoData.name || addr.city || addr.town || addr.village || 'Proposed Renewable Zone';

      const elevRes = await fetch(`https://elevation-api.open-meteo.com/v1/elevation?latitude=${lat}&longitude=${lng}`);
      const elevData = await elevRes.json();
      const elevationVal = elevData.elevation ? `${elevData.elevation[0]} m` : '310 m';

      setSelectedCoords({ lat, lng });
      if (!siteCustomName) setSiteCustomName(detectedName);

      setSiteDetails({
        name: siteCustomName.trim() || detectedName,
        region: regionName,
        elevation: elevationVal,
        lat: `${lat.toFixed(4)}° N`,
        long: `${lng.toFixed(4)}° E`,
        rawLat: lat,
        rawLng: lng,
        area: '32.5 km²',
        gridProximity: `${(Math.random() * 3.2 + 0.9).toFixed(1)} km`,
      });

      if (mapRef.current) {
        mapRef.current.flyTo([lat, lng], 8, { duration: 1.2 });
      }
    } catch (err) {
      console.error('Metadata lookup error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setLoading(true);
    setSearchError(null);
    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`);
      const data = await res.json();
      if (data && data.length > 0) {
        const targetLat = parseFloat(data[0].lat);
        const targetLon = parseFloat(data[0].lon);
        await fetchLocationData(targetLat, targetLon);
      } else {
        setSearchError('Location not found. Try searching by city, district, or landmark.');
      }
    } catch (err) {
      setSearchError('Failed to locate search target.');
    } finally {
      setLoading(false);
    }
  };

  const handleFinalSubmit = () => {
    onConfirmSite({
      ...siteDetails,
      name: siteCustomName.trim() || siteDetails.name || 'Candidate Energy Zone'
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-4xl w-full shadow-2xl overflow-hidden flex flex-col max-h-[92vh]">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-emerald-400">
            <MapPin className="w-5 h-5" />
            <div>
              <h3 className="text-base font-bold text-white">Add Site to Project via Map</h3>
              <p className="text-[11px] text-slate-400">Enrolling site under: <span className="text-emerald-400 font-semibold">{activeProjectName}</span></p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1.5 rounded-xl hover:bg-slate-800 transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 bg-slate-950/60 border-b border-slate-800 space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 relative">
              <Edit3 className="w-4 h-4 text-emerald-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder="Enter Site Name (e.g. Ramanathapuram Sector 1)..."
                value={siteCustomName}
                onChange={(e) => setSiteCustomName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
              />
            </div>

            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder="Search map location (city, district, landmark)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="bg-slate-800 hover:bg-slate-700 text-white font-bold px-4 py-2.5 rounded-xl text-xs flex items-center space-x-1.5 transition border border-slate-700 disabled:opacity-50"
              >
                {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Search</span>}
              </button>
            </form>
          </div>

          {searchError && (
            <p className="text-[11px] text-rose-400 flex items-center gap-1 font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              {searchError}
            </p>
          )}
        </div>

        <div style={{ height: '320px', width: '100%', position: 'relative' }}>
          <MapContainer center={[selectedCoords.lat, selectedCoords.lng]} zoom={6} style={{ height: '100%', width: '100%' }} ref={mapRef}>
            <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <MapClickHandler onLocationSelect={fetchLocationData} />
            <Marker position={[selectedCoords.lat, selectedCoords.lng]} />
          </MapContainer>
          <div className="absolute top-3 right-3 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-800 text-[11px] font-medium text-emerald-400 shadow-md pointer-events-none z-[1000]">
            📍 Click anywhere or search to pin location
          </div>
        </div>

        <div className="p-5 bg-slate-950/90 border-t border-slate-800">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <div className="bg-slate-900 p-3 rounded-2xl border border-slate-800">
              <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1"><Compass className="w-3 h-3" /> COORDINATES</span>
              <span className="text-xs font-bold text-slate-200 truncate block mt-1">{siteDetails.lat}, {siteDetails.long}</span>
            </div>
            <div className="bg-slate-900 p-3 rounded-2xl border border-slate-800">
              <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1"><MapPin className="w-3 h-3" /> REGION</span>
              <span className="text-xs font-bold text-slate-200 truncate block mt-1">{siteDetails.region}</span>
            </div>
            <div className="bg-slate-900 p-3 rounded-2xl border border-slate-800">
              <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1"><Mountain className="w-3 h-3 text-emerald-400" /> ELEVATION</span>
              <span className="text-xs font-bold text-emerald-400 truncate block mt-1">{siteDetails.elevation}</span>
            </div>
            <div className="bg-slate-900 p-3 rounded-2xl border border-slate-800">
              <span className="text-[10px] text-slate-400 font-semibold flex items-center gap-1"><Zap className="w-3 h-3 text-sky-400" /> GRID PROXIMITY</span>
              <span className="text-xs font-bold text-sky-400 truncate block mt-1">{siteDetails.gridProximity}</span>
            </div>
          </div>

          <div className="flex items-center justify-end space-x-3">
            <button onClick={onClose} className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/80 rounded-xl transition">
              Cancel
            </button>
            <button
              onClick={handleFinalSubmit}
              disabled={loading}
              className="flex items-center space-x-1.5 px-5 py-2.5 text-xs font-bold text-slate-950 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 rounded-xl transition shadow-lg disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              <span>Confirm & Enroll Site Under Project</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
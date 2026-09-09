import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Search, Check, X, Loader2, AlertCircle } from 'lucide-react';

// Fix Leaflet icon resolution
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

export default function MapPickerModal({ isOpen, onClose, onSelectLocation, initialLat, initialLong }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);

  const [coords, setCoords] = useState({
    lat: parseFloat(initialLat) || 26.9124,
    lng: parseFloat(initialLong) || 75.7873,
  });
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [regionName, setRegionName] = useState('Selected Coordinates');

  // Initialize and mount pure Leaflet map when modal is open
  useEffect(() => {
    if (!isOpen) return;

    const lat = parseFloat(initialLat) || 26.9124;
    const lng = parseFloat(initialLong) || 75.7873;
    setCoords({ lat, lng });

    // Slight timeout ensures modal DOM container is fully mounted with pixel height
    const timer = setTimeout(() => {
      if (!mapContainerRef.current) return;

      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
      }

      const map = L.map(mapContainerRef.current).setView([lat, lng], 7);
      mapInstanceRef.current = map;

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
      }).addTo(map);

      const marker = L.marker([lat, lng], { draggable: true }).addTo(map);
      markerRef.current = marker;

      // Handle map click
      map.on('click', (e) => {
        const newLat = e.latlng.lat;
        const newLng = e.latlng.lng;
        marker.setLatLng([newLat, newLng]);
        setCoords({ lat: newLat, lng: newLng });
        lookupGeocode(newLat, newLng);
      });

      // Handle marker drag
      marker.on('dragend', () => {
        const pos = marker.getLatLng();
        setCoords({ lat: pos.lat, lng: pos.lng });
        lookupGeocode(pos.lat, pos.lng);
      });

      // Recalculate dimensions so tiles render without gray/blank areas
      map.invalidateSize();
      lookupGeocode(lat, lng);
    }, 150);

    return () => {
      clearTimeout(timer);
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [isOpen]);

  const lookupGeocode = async (lat, lng) => {
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=en`
      );
      const data = await res.json();
      const addr = data.address || {};
      const detected = [
        addr.city || addr.town || addr.village || addr.county || addr.state_district,
        addr.state,
        addr.country,
      ].filter(Boolean).join(', ') || 'Selected Location';
      setRegionName(detected);
    } catch (_) {
      setRegionName('Selected Location');
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setLoading(true);
    setSearchError(null);

    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&accept-language=en`
      );
      const data = await res.json();
      if (data && data.length > 0) {
        const targetLat = parseFloat(data[0].lat);
        const targetLng = parseFloat(data[0].lon);

        setCoords({ lat: targetLat, lng: targetLng });
        if (mapInstanceRef.current && markerRef.current) {
          mapInstanceRef.current.flyTo([targetLat, targetLng], 9, { duration: 1.2 });
          markerRef.current.setLatLng([targetLat, targetLng]);
        }
        lookupGeocode(targetLat, targetLng);
      } else {
        setSearchError('Place not found. Try searching for a specific city or district.');
      }
    } catch (_) {
      setSearchError('Search failed. Please check internet connectivity.');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = () => {
    if (onSelectLocation) {
      onSelectLocation({
        lat: parseFloat(coords.lat.toFixed(4)),
        long: parseFloat(coords.lng.toFixed(4)),
        region: regionName,
      });
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 animate-in fade-in duration-150">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-3xl w-full shadow-2xl overflow-hidden flex flex-col">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2 text-emerald-400">
            <MapPin className="w-5 h-5" />
            <h3 className="text-sm font-bold text-white">Select Site Coordinates from Map</h3>
          </div>
          <button 
            type="button" 
            onClick={onClose} 
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 bg-slate-950/70 border-b border-slate-800 space-y-2">
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search place, city or district (e.g. Jodhpur, Ramanathapuram)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-slate-800 hover:bg-slate-700 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center space-x-1.5 border border-slate-700 disabled:opacity-50 transition cursor-pointer"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <span>Search</span>}
            </button>
          </form>

          {searchError && (
            <p className="text-[11px] text-rose-400 flex items-center gap-1 font-medium">
              <AlertCircle className="w-3.5 h-3.5" />
              {searchError}
            </p>
          )}
        </div>

        {/* Map Container */}
        <div className="relative w-full" style={{ height: '360px', backgroundColor: '#0f172a' }}>
          <div ref={mapContainerRef} className="w-full h-full" style={{ height: '360px' }} />
          <div className="absolute top-2 right-2 bg-slate-900/90 backdrop-blur-md px-3 py-1 rounded-lg border border-slate-800 text-[11px] text-emerald-400 z-[1000] pointer-events-none shadow-md">
            📍 Click anywhere or drag the blue pin to position
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950/90 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center space-x-3 text-xs font-mono">
            <div className="bg-slate-900 px-3 py-2 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-sans">Coordinates</span>
              <span className="font-bold text-white">{coords.lat.toFixed(4)}° N, {coords.lng.toFixed(4)}° E</span>
            </div>
            <div className="bg-slate-900 px-3 py-2 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block font-sans">Region</span>
              <span className="font-bold text-emerald-400 truncate max-w-[200px] block">{regionName}</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button 
              type="button" 
              onClick={onClose} 
              className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white bg-slate-800 rounded-xl transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              className="flex items-center space-x-1.5 px-5 py-2 text-xs font-bold text-slate-950 bg-emerald-500 hover:bg-emerald-400 rounded-xl shadow-lg transition cursor-pointer"
            >
              <Check className="w-4 h-4" />
              <span>Use This Location</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
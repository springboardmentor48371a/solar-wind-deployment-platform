import React, { useState, useRef, useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Search, Loader2, Compass, AlertCircle } from 'lucide-react';

// Fix leaflet default icon missing issue
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function MapEventsHandler({ onLocationSelect }) {
  useMapEvents({
    click(e) {
      onLocationSelect(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function EmbeddedMapPicker({ lat, lng, onCoordsChange }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  
  const mapRef = useRef(null);
  const markerRef = useRef(null);

  // Invalidate map size on render to prevent gray/blue tile glitch
  useEffect(() => {
    const timer = setTimeout(() => {
      if (mapRef.current) {
        mapRef.current.invalidateSize();
      }
    }, 200);
    return () => clearTimeout(timer);
  }, []);

  const handleLocationUpdate = (newLat, newLng, shouldFly = false) => {
    onCoordsChange(newLat, newLng);
    if (shouldFly && mapRef.current) {
      mapRef.current.flyTo([newLat, newLng], 10, { duration: 1.2 });
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setLoading(true);
    setSearchError(null);
    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`
      );
      const data = await res.json();
      if (data && data.length > 0) {
        const targetLat = parseFloat(data[0].lat);
        const targetLon = parseFloat(data[0].lon);
        handleLocationUpdate(targetLat, targetLon, true);
      } else {
        setSearchError('Location not found. Try searching by city, district or state.');
      }
    } catch (_) {
      setSearchError('Failed to search location.');
    } finally {
      setLoading(false);
    }
  };

  const eventHandlers = useMemo(
    () => ({
      dragend() {
        const marker = markerRef.current;
        if (marker != null) {
          const newPos = marker.getLatLng();
          handleLocationUpdate(newPos.lat, newPos.lng, false);
        }
      },
    }),
    []
  );

  return (
    <div className="space-y-2">
      {/* Location Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search place, city or district (e.g. Ramanathapuram)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-emerald-500/50"
          />
        </div>
        <button
          type="button"
          onClick={handleSearch}
          disabled={loading}
          className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-1.5 rounded-xl border border-slate-700 transition cursor-pointer disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Search'}
        </button>
      </div>

      {searchError && (
        <p className="text-[10px] text-rose-400 flex items-center gap-1 font-medium">
          <AlertCircle className="w-3 h-3" /> {searchError}
        </p>
      )}

      {/* Map Surface */}
      <div className="relative h-48 w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
        <MapContainer
          center={[lat || 9.3639, lng || 78.8395]}
          zoom={6}
          style={{ height: '100%', width: '100%' }}
          ref={mapRef}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapEventsHandler onLocationSelect={(clickLat, clickLng) => handleLocationUpdate(clickLat, clickLng, false)} />
          <Marker
            draggable={true}
            eventHandlers={eventHandlers}
            position={[lat || 9.3639, lng || 78.8395]}
            ref={markerRef}
          />
        </MapContainer>
        <div className="absolute top-2 right-2 bg-slate-900/90 backdrop-blur-md px-2.5 py-1 rounded-lg border border-slate-800 text-[10px] font-medium text-emerald-400 shadow-md pointer-events-none z-[1000]">
          📍 Drag pin or click map to pick site
        </div>
      </div>
    </div>
  );
}
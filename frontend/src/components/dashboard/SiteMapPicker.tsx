import React, { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import { MapPin, Compass, Layers, Maximize2, Loader2 } from 'lucide-react';

export interface LocationData {
  lat: number;
  lon: number;
  district: string;
  state: string;
  displayName: string;
  areaSizeM2: number;
  areaLengthM: number; // approximate square side length or diameter
  areaWidthM: number;
  radiusM: number;
  acres: number;
  hectares: number;
}

interface SiteMapPickerProps {
  latitude: number | null;
  longitude: number | null;
  landArea: number; // in m2
  onLocationSelect: (data: LocationData) => void;
  onAreaSelect?: (areaM2: number) => void;
}

// Custom modern SVG marker to eliminate broken Leaflet default asset 404s
const createCustomMarker = () => {
  return L.divIcon({
    className: 'custom-site-marker',
    html: `
      <div style="position: relative; display: flex; align-items: center; justify-content: center; width: 42px; height: 42px; transform: translate(-50%, -50%);">
        <div style="position: absolute; width: 38px; height: 38px; background: rgba(245, 158, 11, 0.35); border-radius: 50%; animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
        <div style="position: relative; width: 28px; height: 28px; background: linear-gradient(135deg, #f59e0b, #d97706); border: 2.5px solid #ffffff; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(0,0,0,0.6);">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0f172a" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="4"/>
            <path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>
          </svg>
        </div>
      </div>
    `,
    iconSize: [42, 42],
    iconAnchor: [21, 21],
  });
};

// Component to handle smooth map panning when coordinates change externally (e.g. preset buttons)
const MapController: React.FC<{ center: [number, number]; zoom?: number }> = ({ center, zoom = 9 }) => {
  const map = useMap();
  useEffect(() => {
    if (center[0] && center[1]) {
      map.flyTo(center, Math.max(map.getZoom(), zoom), { duration: 1.2 });
    }
  }, [center[0], center[1]]);
  return null;
};

// Component to capture map clicks and reverse geocode
const MapClickHandler: React.FC<{
  onMapClick: (lat: number, lon: number) => void;
}> = ({ onMapClick }) => {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
};

export const SiteMapPicker: React.FC<SiteMapPickerProps> = ({
  latitude,
  longitude,
  landArea,
  onLocationSelect,
  onAreaSelect,
}) => {
  const initialPos: [number, number] = latitude && longitude ? [latitude, longitude] : [26.9124, 75.7873]; // Jaipur fallback

  const [position, setPosition] = useState<[number, number]>(initialPos);
  const [district, setDistrict] = useState<string>('Jaipur District');
  const [state, setState] = useState<string>('Rajasthan');
  const [displayName, setDisplayName] = useState<string>('Jaipur, Rajasthan, India');
  const [isGeocoding, setIsGeocoding] = useState<boolean>(false);
  const [tileStyle, setTileStyle] = useState<'streets' | 'satellite'>('streets');

  // Synchronize when external coordinates change (e.g., presets)
  useEffect(() => {
    if (latitude && longitude && (latitude !== position[0] || longitude !== position[1])) {
      setPosition([latitude, longitude]);
      reverseGeocode(latitude, longitude, landArea);
    }
  }, [latitude, longitude]);

  // Dimension calculations derived mathematically from Land Area
  const dimensions = useMemo(() => {
    const area = landArea > 0 ? landArea : 150000;
    // Equivalent circular radius R = sqrt(Area / pi)
    const radiusM = Math.round(Math.sqrt(area / Math.PI));
    // Equivalent square plot side length S = sqrt(Area)
    const sideM = Math.round(Math.sqrt(area));
    // Diameter / maximum span across the site
    const diameterM = radiusM * 2;
    // Acres (1 m2 = 0.000247105 acres)
    const acres = parseFloat((area * 0.000247105).toFixed(2));
    // Hectares (1 ha = 10,000 m2)
    const hectares = parseFloat((area / 10000).toFixed(2));

    return {
      areaSizeM2: area,
      radiusM,
      areaLengthM: sideM,
      areaWidthM: sideM,
      diameterM,
      acres,
      hectares,
    };
  }, [landArea]);

  // Reverse Geocoding via OpenStreetMap Nominatim
  const reverseGeocode = async (lat: number, lon: number, currentArea: number) => {
    setIsGeocoding(true);
    try {
      const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=12&addressdetails=1`;
      const response = await fetch(url, {
        headers: {
          'Accept-Language': 'en',
          'User-Agent': 'SolarWindDeploymentPlatform/1.0',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const address = data.address || {};

        const extractedDistrict =
          address.state_district ||
          address.district ||
          address.county ||
          address.city ||
          address.municipality ||
          address.town ||
          'Candidate District';

        const extractedState =
          address.state ||
          address.region ||
          address.province ||
          'Candidate Region';

        const extractedName =
          data.display_name?.split(',').slice(0, 3).join(', ') ||
          `${extractedDistrict}, ${extractedState}`;

        setDistrict(extractedDistrict);
        setState(extractedState);
        setDisplayName(extractedName);

        // Notify parent callback with complete geographic & area package
        onLocationSelect({
          lat: parseFloat(lat.toFixed(4)),
          lon: parseFloat(lon.toFixed(4)),
          district: extractedDistrict,
          state: extractedState,
          displayName: extractedName,
          areaSizeM2: currentArea,
          areaLengthM: dimensions.areaLengthM,
          areaWidthM: dimensions.areaWidthM,
          radiusM: dimensions.radiusM,
          acres: dimensions.acres,
          hectares: dimensions.hectares,
        });
      }
    } catch (err) {
      console.warn('Reverse geocoding unavailable, using coordinate fallbacks:', err);
    } finally {
      setIsGeocoding(false);
    }
  };

  const handleMapClick = (lat: number, lon: number) => {
    setPosition([lat, lon]);
    reverseGeocode(lat, lon, landArea);
  };

  const markerIcon = useMemo(() => createCustomMarker(), []);

  // Quick area preset buttons
  const areaPresets = [
    { label: '50k m²', value: 50000, desc: 'Small (12.4 ac)' },
    { label: '150k m²', value: 150000, desc: 'Medium (37.1 ac)' },
    { label: '300k m²', value: 300000, desc: 'Large (74.1 ac)' },
    { label: '600k m²', value: 600000, desc: 'Utility Park (148 ac)' },
  ];

  return (
    <div className="glass-card rounded-2xl overflow-hidden border border-slate-800 shadow-xl mb-6">
      {/* Map Header and Quick Stats HUD */}
      <div className="p-4 sm:p-5 border-b border-slate-800 bg-slate-950/60 backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
              <Compass className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <span>Interactive GIS Site Explorer</span>
                {isGeocoding && (
                  <span className="inline-flex items-center space-x-1 text-[11px] font-medium text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    <span>Resolving location...</span>
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400">
                Click anywhere on the map to pinpoint candidate site coordinates, district, and land boundary dimensions.
              </p>
            </div>
          </div>

          {/* Map Layer Switcher */}
          <div className="flex items-center space-x-2">
            <span className="text-[11px] font-semibold text-slate-400 flex items-center space-x-1">
              <Layers className="w-3.5 h-3.5" />
              <span>Layer:</span>
            </span>
            <div className="inline-flex p-0.5 rounded-lg bg-slate-900 border border-slate-800">
              <button
                type="button"
                onClick={() => setTileStyle('streets')}
                className={`px-2.5 py-1 text-[11px] font-bold rounded-md transition-all ${
                  tileStyle === 'streets'
                    ? 'bg-amber-500 text-slate-950 shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Topographic
              </button>
              <button
                type="button"
                onClick={() => setTileStyle('satellite')}
                className={`px-2.5 py-1 text-[11px] font-bold rounded-md transition-all ${
                  tileStyle === 'satellite'
                    ? 'bg-amber-500 text-slate-950 shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Satellite / Terrain
              </button>
            </div>
          </div>
        </div>

        {/* Real-Time Telemetry Bar (Coordinates, District, State, Length, Area) */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-2 border-t border-slate-850">
          {/* Coordinates */}
          <div className="bg-slate-900/90 rounded-xl p-2.5 border border-slate-800/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Coordinates</span>
            <p className="text-xs font-mono font-bold text-amber-400 mt-0.5 truncate">
              {position[0].toFixed(4)}°, {position[1].toFixed(4)}°
            </p>
          </div>

          {/* District */}
          <div className="bg-slate-900/90 rounded-xl p-2.5 border border-slate-800/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">District</span>
            <p className="text-xs font-bold text-white mt-0.5 truncate" title={district}>
              📍 {district}
            </p>
          </div>

          {/* State / Region */}
          <div className="bg-slate-900/90 rounded-xl p-2.5 border border-slate-800/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">State / Region</span>
            <p className="text-xs font-bold text-emerald-400 mt-0.5 truncate" title={state}>
              🏛️ {state}
            </p>
          </div>

          {/* Site Length & Width (Span) */}
          <div className="bg-slate-900/90 rounded-xl p-2.5 border border-slate-800/80">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Area Length × Width</span>
            <p className="text-xs font-bold text-cyan-300 mt-0.5 truncate">
              📐 ~{dimensions.areaLengthM}m × {dimensions.areaWidthM}m
            </p>
          </div>

          {/* Area Footprint */}
          <div className="bg-slate-900/90 rounded-xl p-2.5 border border-slate-800/80 col-span-2 sm:col-span-1">
            <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Land Area Size</span>
            <p className="text-xs font-bold text-amber-300 mt-0.5 truncate">
              ⚡ {dimensions.areaSizeM2.toLocaleString()} m² <span className="text-[10px] text-slate-400">({dimensions.acres} ac)</span>
            </p>
          </div>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div className="relative h-80 sm:h-96 w-full z-0 bg-slate-950">
        <MapContainer
          center={position}
          zoom={8}
          scrollWheelZoom={true}
          className="h-full w-full"
          style={{ background: '#090d16' }}
        >
          {/* Tile Layer (Topographic OSM vs Esri World Imagery Satellite) */}
          {tileStyle === 'streets' ? (
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          ) : (
            <TileLayer
              attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          )}

          <MapController center={position} zoom={10} />
          <MapClickHandler onMapClick={handleMapClick} />

          {/* Interactive Marker on clicked coordinates */}
          <Marker position={position} icon={markerIcon}>
            <Popup className="custom-leaflet-popup">
              <div className="p-1 text-slate-900 text-xs">
                <p className="font-extrabold text-amber-600 mb-0.5">📍 {displayName}</p>
                <p className="text-[11px] text-slate-600 font-mono">
                  Lat: {position[0].toFixed(4)}, Lon: {position[1].toFixed(4)}
                </p>
                <div className="mt-1 pt-1 border-t border-slate-200 text-[10px] text-slate-700 space-y-0.5">
                  <p><strong>District:</strong> {district}</p>
                  <p><strong>State:</strong> {state}</p>
                  <p><strong>Plot Span:</strong> ~{dimensions.diameterM} meters</p>
                  <p><strong>Footprint:</strong> {dimensions.areaSizeM2.toLocaleString()} m² ({dimensions.acres} Acres)</p>
                </div>
              </div>
            </Popup>
          </Marker>

          {/* Visual Land Area Boundary Circle */}
          <Circle
            center={position}
            radius={dimensions.radiusM}
            pathOptions={{
              color: '#f59e0b',
              fillColor: '#f59e0b',
              fillOpacity: 0.22,
              weight: 2,
              dashArray: '4, 6',
            }}
          />
        </MapContainer>

        {/* Quick Hint Overlay */}
        <div className="absolute bottom-3 left-3 z-[400] bg-slate-950/85 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-800 text-[11px] text-slate-300 pointer-events-none shadow-lg flex items-center space-x-2">
          <MapPin className="w-3.5 h-3.5 text-amber-400 animate-bounce" />
          <span>Click anywhere to reposition site boundary & detect district/state</span>
        </div>
      </div>

      {/* Area Dimension Selector Controls */}
      <div className="p-3 sm:p-4 bg-slate-950/80 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center space-x-2 text-slate-400">
          <Maximize2 className="w-4 h-4 text-amber-500" />
          <span className="font-semibold text-slate-300">Quick Plot Scale:</span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {areaPresets.map((preset) => {
            const isSelected = landArea === preset.value;
            return (
              <button
                key={preset.value}
                type="button"
                onClick={() => onAreaSelect && onAreaSelect(preset.value)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all border ${
                  isSelected
                    ? 'bg-amber-500 border-amber-400 text-slate-950 shadow-md scale-105'
                    : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                {preset.label} <span className="text-[10px] font-normal opacity-80">({preset.desc})</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

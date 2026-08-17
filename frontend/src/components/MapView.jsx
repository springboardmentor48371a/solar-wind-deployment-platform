import React from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Polyline, Polygon, useMapEvents } from 'react-leaflet'

// Color map for suitability categories
const CATEGORY_COLORS = {
  "Excellent": "#10b981",   // Emerald Green
  "High": "#34d399",        // Light Emerald
  "Moderate": "#fbbf24",    // Amber
  "Low": "#f97316",         // Orange
  "Unsuitable": "#ef4444"   // Red
}

// Map Click Listener component
function MapClickListener({ onClick }) {
  useMapEvents({
    click(e) {
      onClick(e.latlng)
    }
  })
  return null
}

export default function MapView({ sites, infraData, activeSite, onSiteSelect, onMapClick }) {
  // Center of Gujarat/Rajasthan (Western India)
  const defaultPosition = [25.0, 71.0]
  const defaultZoom = 6

  return (
    <MapContainer 
      center={defaultPosition} 
      zoom={defaultZoom} 
      style={{ height: '100%', width: '100%' }}
      zoomControl={true}
    >
      {/* Dark CartoDB Map Tiles for premium aesthetic */}
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      />

      {/* Map Click Listener */}
      <MapClickListener onClick={onMapClick} />

      {/* Render Protected Exclusion Zones */}
      {infraData?.protected_zones?.features.map((feature, idx) => {
        const coords = feature.geometry.coordinates[0].map(c => [c[1], c[0]]) // GeoJSON [lng, lat] to Leaflet [lat, lng]
        return (
          <Polygon
            key={`protected-${idx}`}
            positions={coords}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.18,
              weight: 1.5,
              dashArray: '4'
            }}
          >
            <Popup>
              <div style={{ color: '#fca5a5', fontWeight: 'bold' }}>{feature.properties.name}</div>
              <div style={{ fontSize: '11px', marginTop: '4px' }}>Environmental Exclusion Zone. Building renewable projects here is legally prohibited.</div>
            </Popup>
          </Polygon>
        )
      })}

      {/* Render Grid Transmission Lines */}
      {infraData?.transmission_lines?.features.map((feature, idx) => {
        const coords = feature.geometry.coordinates.map(c => [c[1], c[0]])
        return (
          <Polyline
            key={`line-${idx}`}
            positions={coords}
            pathOptions={{
              color: '#f59e0b',
              weight: 2,
              dashArray: '6, 8',
              opacity: 0.8
            }}
          >
            <Popup>
              <div style={{ color: '#fcd34d', fontWeight: 'bold' }}>{feature.properties.name}</div>
              <div style={{ fontSize: '11px' }}>High Voltage Grid Interconnector segment.</div>
            </Popup>
          </Polyline>
        )
      })}

      {/* Render Grid Substations */}
      {infraData?.substations?.features.map((feature, idx) => {
        const [lng, lat] = feature.geometry.coordinates
        return (
          <CircleMarker
            key={`sub-${idx}`}
            center={[lat, lng]}
            radius={6}
            pathOptions={{
              color: '#f59e0b',
              fillColor: '#f59e0b',
              fillOpacity: 0.9,
              weight: 2
            }}
          >
            <Popup>
              <div style={{ color: '#fcd34d', fontWeight: 'bold' }}>{feature.properties.name}</div>
              <div style={{ fontSize: '11px' }}>Grid Substation Interconnection Point. Proximity improves economic score.</div>
            </Popup>
          </CircleMarker>
        )
      })}

      {/* Render Candidate Sites */}
      {sites.map((site) => {
        const latestAssess = site.assessments?.[0]
        const score = latestAssess?.suitability_score ?? 50.0
        const category = latestAssess?.suitability_category ?? "Moderate"
        const color = CATEGORY_COLORS[category] || "#94a3b8"
        const isActive = activeSite?.site_id === site.site_id

        return (
          <CircleMarker
            key={site.site_id}
            center={[parseFloat(site.latitude), parseFloat(site.longitude)]}
            radius={isActive ? 11 : 8}
            pathOptions={{
              color: isActive ? '#ffffff' : color,
              fillColor: color,
              fillOpacity: 0.85,
              weight: isActive ? 3 : 1.5,
            }}
            eventHandlers={{
              click: () => onSiteSelect(site)
            }}
          >
            <Popup>
              <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '2px' }}>{site.site_name}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '11px', marginBottom: '8px' }}>Region: {site.region}</div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', borderTop: '1px solid var(--glass-border)', paddingTop: '6px' }}>
                <div>
                  <span style={{ fontSize: '9px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Score</span>
                  <div style={{ fontSize: '14px', fontWeight: 'bold', color: color }}>{score}/100</div>
                </div>
                <div>
                  <span style={{ fontSize: '9px', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Type</span>
                  <div style={{ fontSize: '11px', fontWeight: 'bold' }}>{latestAssess?.deployment_type || 'N/A'}</div>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </MapContainer>
  )
}

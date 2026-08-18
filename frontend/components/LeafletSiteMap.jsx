'use client'

import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

// Free OpenStreetMap tiles — no API key, no token, works immediately.
// (Matches the tech stack's "Leaflet.js" entry; Mapbox needs a paid/free
// account token which most people trying this out won't have yet, so
// Leaflet is the map that's guaranteed to actually render.)
const TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const TILE_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

export default function LeafletSiteMap({ sites, categoryColor }) {
  const center = sites.length
    ? [sites[0].latitude, sites[0].longitude]
    : [17.6868, 83.2185] // sensible regional default

  return (
    <MapContainer
      center={center}
      zoom={sites.length ? 6 : 3}
      style={{ height: 480, width: '100%' }}
      scrollWheelZoom
    >
      <TileLayer url={TILE_URL} attribution={TILE_ATTRIBUTION} />
      {sites.map((s) => (
        <CircleMarker
          key={s.site_id}
          center={[s.latitude, s.longitude]}
          radius={8}
          pathOptions={{
            color: '#ffffff',
            weight: 2,
            fillColor: categoryColor[s.category] || categoryColor.Unscored,
            fillOpacity: 1,
          }}
        >
          <Popup>
            <div className="text-[13px] text-ink">
              <strong>{s.site_name}</strong>
              <br />
              Project: {s.project_name}
              <br />
              Elevation: {s.elevation_m ?? '—'} m
              <br />
              Score: {s.overall_score ?? '—'}{' '}
              <span
                style={{ color: categoryColor[s.category] || categoryColor.Unscored, fontWeight: 600 }}
              >
                ({s.category})
              </span>
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}

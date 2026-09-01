import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getPrediction } from '../api'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const CATEGORY_COLORS = {
  'Excellent':           '#16a34a',
  'Highly Suitable':     '#65a30d',
  'Moderately Suitable': '#ca8a04',
  'Low Suitability':     '#ea580c',
  'Unsuitable':          '#dc2626',
}

function coloredIcon(color) {
  return L.divIcon({
    className: '',
    html: `<div style="width:14px;height:14px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
    popupAnchor: [0, -10],
  })
}

function SitePopup({ site }) {
  const [pred, setPred] = useState(null)

  useEffect(() => {
    getPrediction(site.id).then(r => setPred(r.data)).catch(() => {})
  }, [site.id])

  const catColor = pred ? (CATEGORY_COLORS[pred.suitability_category] || '#6b7280') : '#6b7280'

  return (
    <div style={{ minWidth: 180, fontFamily: 'Segoe UI, sans-serif' }}>
      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>{site.name}</div>
      <div style={{ fontSize: 11, color: '#6b7280', marginBottom: 6 }}>
        {site.energy_type} · {site.status.replace(/_/g, ' ')}
      </div>
      {pred ? (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: catColor }}>{Math.round(pred.suitability_score ?? 0)}</div>
            <div>
              <div style={{ fontSize: 10, color: '#9ca3af' }}>Suitability</div>
              <div style={{ fontSize: 11, fontWeight: 600, color: catColor }}>{pred.suitability_category}</div>
            </div>
          </div>
          <div style={{ fontSize: 11, color: '#6b7280' }}>
            {pred.solar_score != null && <div>☀️ Solar: <strong>{Math.round(pred.solar_score)}</strong></div>}
            {pred.wind_score != null && <div>💨 Wind: <strong>{Math.round(pred.wind_score)}</strong></div>}
            {pred.land_cover_class && <div>🌍 Land: <strong style={{ textTransform: 'capitalize' }}>{pred.land_cover_class}</strong></div>}
          </div>
        </>
      ) : (
        <div style={{ fontSize: 11, color: '#9ca3af' }}>No predictions yet</div>
      )}
      <div style={{ fontSize: 10, color: '#d1d5db', marginTop: 6 }}>
        {site.latitude.toFixed(4)}, {site.longitude.toFixed(4)}
        {site.elevation && ` · ${site.elevation}m`}
      </div>
    </div>
  )
}

export default function MapView({ sites = [] }) {
  const [predictions, setPredictions] = useState({})

  useEffect(() => {
    sites.forEach(site => {
      getPrediction(site.id)
        .then(r => setPredictions(prev => ({ ...prev, [site.id]: r.data })))
        .catch(() => {})
    })
  }, [sites])

  const center = sites.length > 0 ? [sites[0].latitude, sites[0].longitude] : [20, 78]

  return (
    <MapContainer center={center} zoom={sites.length > 0 ? 8 : 4}
      style={{ height: 'calc(100vh - 40px)', width: '100%', borderRadius: 8, border: '1px solid #e5e7eb' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {sites.map(site => {
        const pred = predictions[site.id]
        const color = pred ? (CATEGORY_COLORS[pred.suitability_category] || '#6b7280') : '#6b7280'
        return (
          <Marker key={site.id} position={[site.latitude, site.longitude]} icon={coloredIcon(color)}>
            <Popup><SitePopup site={site} /></Popup>
          </Marker>
        )
      })}
    </MapContainer>
  )
}

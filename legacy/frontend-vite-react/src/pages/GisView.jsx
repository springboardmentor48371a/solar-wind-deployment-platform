import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import api from '../api'
import Navbar from '../components/Navbar'

// Leaflet's default marker icons reference image paths that don't resolve
// correctly under Vite's bundler — this fixes broken marker icons.
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const categoryColor = {
  Excellent: '#1e6f4c',
  'Highly Suitable': '#227a8f',
  'Moderately Suitable': '#a5670c',
  'Low Suitability': '#c26b2c',
  Unsuitable: '#b3261e',
  Unscored: '#8a988f',
}

const catClass = {
  Excellent: 'cat-excellent',
  'Highly Suitable': 'cat-highly-suitable',
  'Moderately Suitable': 'cat-moderately-suitable',
  'Low Suitability': 'cat-low-suitability',
  Unsuitable: 'cat-unsuitable',
}

export default function GisView() {
  const [sites, setSites] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/gis/sites').then((res) => setSites(res.data)).finally(() => setLoading(false))
  }, [])

  const center = sites.length
    ? [sites[0].latitude, sites[0].longitude]
    : [17.6868, 83.2185] // sensible regional default

  return (
    <div>
      <Navbar />
      <div className="container">
        <div className="page-header">
          <div>
            <h2>GIS Site Intelligence</h2>
            <p className="page-subtitle">
              {loading ? 'Loading sites…' : `${sites.length} site${sites.length === 1 ? '' : 's'} plotted, colored by suitability category`}
            </p>
          </div>
          <div className="btn-row">
            {Object.entries(categoryColor).filter(([k]) => k !== 'Unscored').map(([label, color]) => (
              <span key={label} className={`badge ${catClass[label]}`}>
                <span className="badge-dot" style={{ background: color }} />
                {label}
              </span>
            ))}
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <MapContainer center={center} zoom={6} style={{ height: 480, width: '100%' }}>
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {sites.map((s) => (
              <CircleMarker
                key={s.site_id}
                center={[s.latitude, s.longitude]}
                radius={9}
                pathOptions={{
                  color: '#fff',
                  weight: 2,
                  fillColor: categoryColor[s.category] || categoryColor.Unscored,
                  fillOpacity: 0.9,
                }}
              >
                <Popup>
                  <strong>{s.site_name}</strong>
                  <br />
                  Project: {s.project_name}
                  <br />
                  Elevation: {s.elevation_m ?? '—'} m
                  <br />
                  Score: {s.overall_score ?? '—'}{' '}
                  <span style={{ color: categoryColor[s.category] || categoryColor.Unscored, fontWeight: 600 }}>
                    ({s.category})
                  </span>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        <div className="card">
          <div className="card-header"><h3>All plotted sites</h3></div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Project</th>
                  <th>Coordinates</th>
                  <th>Category</th>
                </tr>
              </thead>
              <tbody>
                {sites.map((s) => (
                  <tr key={s.site_id}>
                    <td>{s.site_name}</td>
                    <td>{s.project_name}</td>
                    <td className="mono">{s.latitude.toFixed(4)}, {s.longitude.toFixed(4)}</td>
                    <td>
                      <span className={`badge ${catClass[s.category] || 'cat-unscored'}`}>{s.category}</span>
                    </td>
                  </tr>
                ))}
                {sites.length === 0 && !loading && (
                  <tr><td colSpan={4}><div className="empty-state">No sites to display yet.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { getPrediction } from '../api'
import './MapView.css'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

function coloredIcon(energyType) {
  const type = (energyType || 'solar').toLowerCase()
  const variant = type === 'wind' ? 'wind' : type === 'hybrid' ? 'hybrid' : 'solar'
  return L.divIcon({
    className: '',
    html: `<div class="editorial-map-marker editorial-map-marker--${variant}"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9],
    popupAnchor: [0, -12],
  })
}

function SitePopup({ site }) {
  const [pred, setPred] = useState(null)

  useEffect(() => {
    getPrediction(site.id)
      .then((r) => setPred(r.data))
      .catch(() => {})
  }, [site.id])

  const cat = pred?.suitability_category || ''
  const isPositive = cat === 'Excellent' || cat === 'Highly Suitable'
  const isNegative = cat === 'Unsuitable'
  const pillClass = isPositive
    ? 'map-popup__score-badge--positive'
    : isNegative
    ? 'map-popup__score-badge--negative'
    : 'map-popup__score-badge--neutral'

  return (
    <div className="map-popup">
      <div className="map-popup__title">{site.name}</div>
      <div className="map-popup__subtitle">
        {site.energy_type} &middot; {site.status.replace(/_/g, ' ')}
      </div>

      {pred ? (
        <>
          <div className="map-popup__score-row">
            <div>
              <div className="map-popup__score-val">
                {Math.round(pred.suitability_score ?? 0)}
              </div>
              <div className="map-popup__score-label">Suitability</div>
            </div>
            <div style={{ marginLeft: 'auto' }}>
              <span
                className={`map-popup__score-badge ${pillClass}`}
                style={{
                  background: isPositive
                    ? 'var(--color-pill-green-bg)'
                    : isNegative
                    ? 'var(--color-pill-red-bg)'
                    : 'var(--color-pill-peach-bg)',
                  color: isPositive
                    ? 'var(--color-pill-green-text)'
                    : isNegative
                    ? 'var(--color-pill-red-text)'
                    : 'var(--color-pill-peach-text)',
                }}
              >
                {pred.suitability_category}
              </span>
            </div>
          </div>

          <div className="map-popup__details">
            {pred.solar_score != null && (
              <div>
                Solar Score: <strong>{Math.round(pred.solar_score)}</strong>
              </div>
            )}
            {pred.wind_score != null && (
              <div>
                Wind Score: <strong>{Math.round(pred.wind_score)}</strong>
              </div>
            )}
            {pred.land_cover_class && (
              <div>
                Land Cover:{' '}
                <strong style={{ textTransform: 'capitalize' }}>
                  {pred.land_cover_class}
                </strong>
              </div>
            )}
          </div>
        </>
      ) : (
        <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>
          No predictions available yet
        </div>
      )}

      <div className="map-popup__coords">
        {site.latitude.toFixed(4)}&deg;, {site.longitude.toFixed(4)}&deg;
        {site.elevation && ` · ${site.elevation}m`}
      </div>
    </div>
  )
}

export default function MapView({ sites = [] }) {
  const [filterType, setFilterType] = useState('all')

  const filteredSites =
    filterType === 'all'
      ? sites
      : sites.filter(
          (s) => (s.energy_type || '').toLowerCase() === filterType.toLowerCase()
        )

  const center =
    sites.length > 0 ? [sites[0].latitude, sites[0].longitude] : [20.5937, 78.9629]

  return (
    <div className="map-view">
      {/* Panel header sits OUTSIDE/ABOVE the map panel */}
      <div className="map-view__panel-header">
        <div className="map-view__panel-title">
          Site Geography &amp; Resource Distribution ({filteredSites.length} active sites)
        </div>

        {/* Legend Chips / Filter Chips */}
        <div className="map-view__legend">
          <button
            type="button"
            className={`map-view__legend-chip ${
              filterType === 'all' ? 'map-view__legend-chip--active' : ''
            }`}
            onClick={() => setFilterType('all')}
          >
            All Sites ({sites.length})
          </button>
          <button
            type="button"
            className={`map-view__legend-chip ${
              filterType === 'solar' ? 'map-view__legend-chip--active' : ''
            }`}
            onClick={() => setFilterType(filterType === 'solar' ? 'all' : 'solar')}
          >
            <span className="map-view__legend-dot map-view__legend-dot--solar" />
            Solar ({sites.filter((s) => s.energy_type === 'solar').length})
          </button>
          <button
            type="button"
            className={`map-view__legend-chip ${
              filterType === 'wind' ? 'map-view__legend-chip--active' : ''
            }`}
            onClick={() => setFilterType(filterType === 'wind' ? 'all' : 'wind')}
          >
            <span className="map-view__legend-dot map-view__legend-dot--wind" />
            Wind ({sites.filter((s) => s.energy_type === 'wind').length})
          </button>
          <button
            type="button"
            className={`map-view__legend-chip ${
              filterType === 'hybrid' ? 'map-view__legend-chip--active' : ''
            }`}
            onClick={() => setFilterType(filterType === 'hybrid' ? 'all' : 'hybrid')}
          >
            <span className="map-view__legend-dot map-view__legend-dot--hybrid" />
            Hybrid ({sites.filter((s) => s.energy_type === 'hybrid').length})
          </button>
        </div>
      </div>

      {/* Map visualization panel */}
      <div className="map-view__container">
        <MapContainer
          center={center}
          zoom={sites.length > 0 ? 7 : 5}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {filteredSites.map((site) => (
            <Marker
              key={site.id}
              position={[site.latitude, site.longitude]}
              icon={coloredIcon(site.energy_type)}
            >
              <Popup>
                <SitePopup site={site} />
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}

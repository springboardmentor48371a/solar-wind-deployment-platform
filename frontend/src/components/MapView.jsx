import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix default marker icons broken by Vite
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

export default function MapView({ sites = [] }) {
  const center = sites.length > 0
    ? [sites[0].latitude, sites[0].longitude]
    : [20, 78] // default center India

  return (
    <MapContainer center={center} zoom={sites.length > 0 ? 8 : 4} style={{ height: 'calc(100vh - 40px)', width: '100%', borderRadius: 8, border: '1px solid #e5e7eb' }}>
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {sites.map(site => (
        <Marker key={site.id} position={[site.latitude, site.longitude]}>
          <Popup>
            <strong>{site.name}</strong><br />
            Type: {site.energy_type}<br />
            Status: {site.status}<br />
            Lat: {site.latitude}, Lon: {site.longitude}
            {site.land_area && <><br />Area: {site.land_area} ha</>}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}

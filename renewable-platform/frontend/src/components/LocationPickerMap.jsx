import React, { useState, useEffect, useRef } from 'react'
import L from 'leaflet'

// Fix default marker icon issues in Leaflet when bundled with Vite
if (typeof window !== 'undefined' && L && L.Icon && L.Icon.Default && L.Icon.Default.prototype) {
  try {
    delete L.Icon.Default.prototype._getIconUrl
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    })
  } catch (e) {
    console.warn('Leaflet default icon patch skipped:', e)
  }
}

export default function LocationPickerMap({ initialLat = 28.6139, initialLon = 77.2090, onLocationSelect }) {
  const [lat, setLat] = useState(initialLat)
  const [lon, setLon] = useState(initialLon)
  const [searchQuery, setSearchQuery] = useState('')
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState('')
  const mapRef = useRef(null)
  const leafletMapInstance = useRef(null)
  const markerInstance = useRef(null)

  useEffect(() => {
    if (!mapRef.current) return
    if (leafletMapInstance.current) return // initialized once

    const map = L.map(mapRef.current).setView([lat, lon], 12)
    leafletMapInstance.current = map

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map)

    const marker = L.marker([lat, lon], { draggable: true }).addTo(map)
    markerInstance.current = marker

    marker.on('dragend', (e) => {
      const position = marker.getLatLng()
      setLat(position.lat)
      setLon(position.lng)
      if (onLocationSelect) {
        onLocationSelect(position.lat, position.lng)
      }
    })

    map.on('click', (e) => {
      const { lat: clickedLat, lng: clickedLon } = e.latlng
      setLat(clickedLat)
      setLon(clickedLon)
      marker.setLatLng([clickedLat, clickedLon])
      if (onLocationSelect) {
        onLocationSelect(clickedLat, clickedLon)
      }
    })

    return () => {
      map.remove()
      leafletMapInstance.current = null
    }
  }, [])

  const updateMapPosition = (newLat, newLon) => {
    setLat(newLat)
    setLon(newLon)
    if (markerInstance.current) {
      markerInstance.current.setLatLng([newLat, newLon])
    }
    if (leafletMapInstance.current) {
      leafletMapInstance.current.setView([newLat, newLon], 13)
    }
    if (onLocationSelect) {
      onLocationSelect(newLat, newLon)
    }
  }

  const handleSearch = async (e) => {
    if (e) e.preventDefault()
    if (!searchQuery.trim()) return
    setSearching(true)
    setSearchError('')

    try {
      const res = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}`
      )
      const data = await res.json()
      if (data && data.length > 0) {
        const first = data[0]
        const foundLat = parseFloat(first.lat)
        const foundLon = parseFloat(first.lon)
        updateMapPosition(foundLat, foundLon)
      } else {
        setSearchError('Location not found. Try entering a city, landmark, or region.')
      }
    } catch (err) {
      setSearchError('Failed to geocode location. Please try again or click directly on the map.')
    } finally {
      setSearching(false)
    }
  }

  return (
    <div className="location-picker-container">
      <div className="search-bar-row">
        <input
          type="text"
          className="search-input"
          placeholder="🔍 Search location (e.g. 'Delhi Site 1' or 'Bawana, Delhi')..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch(e)}
        />
        <button type="button" className="btn-primary btn-search" onClick={handleSearch} disabled={searching}>
          {searching ? 'Locating...' : 'Search Location'}
        </button>
      </div>

      {searchError && <p className="error-text small">{searchError}</p>}

      <div ref={mapRef} className="map-picker-viewport" style={{ height: '320px', borderRadius: '8px', marginTop: '10px' }} />

      <div className="coords-readout">
        <div>
          <span>Latitude: </span><strong>{lat ? lat.toFixed(6) : '—'}</strong>
        </div>
        <div>
          <span>Longitude: </span><strong>{lon ? lon.toFixed(6) : '—'}</strong>
        </div>
        <div className="hint-pill">💡 Drag marker or click map to adjust exact site location</div>
      </div>
    </div>
  )
}

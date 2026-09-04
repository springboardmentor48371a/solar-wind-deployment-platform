import React, { useEffect, useRef } from 'react'
import L from 'leaflet'

const CATEGORY_COLORS = {
  'Excellent': '#0f9d58',
  'Highly Suitable': '#2b6cb0',
  'Moderately Suitable': '#dd6b20',
  'Low Suitability': '#e53e3e',
  'Unsuitable': '#718096'
}

export default function ProjectMap({ sites = [], ranking = [], onSelectSite }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)

  useEffect(() => {
    if (!mapRef.current || sites.length === 0) return

    if (mapInstance.current) {
      mapInstance.current.remove()
      mapInstance.current = null
    }

    const firstSite = sites[0]
    const map = L.map(mapRef.current).setView([firstSite.latitude, firstSite.longitude], 10)
    mapInstance.current = map

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map)

    const bounds = L.latLngBounds()

    sites.forEach(site => {
      const siteRank = ranking.find(r => r.site_id === site.id) || {}
      const category = siteRank.category || 'Moderately Suitable'
      const color = CATEGORY_COLORS[category] || '#2b6cb0'

      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `<div style="background-color:${color}; width:24px; height:24px; border-radius:50%; border:2px solid white; box-shadow:0 2px 5px rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:center; color:white; font-size:11px; font-weight:bold;">${siteRank.overall_score ? Math.round(siteRank.overall_score) : '•'}</div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      })

      const marker = L.marker([site.latitude, site.longitude], { icon: customIcon }).addTo(map)
      bounds.extend([site.latitude, site.longitude])

      const popupContent = `
        <div style="font-family:Inter, sans-serif; padding:4px;">
          <h4 style="margin:0 0 4px 0; font-size:14px;">${site.name}</h4>
          <p style="margin:0 0 4px 0; font-size:12px; color:#4a5568;">Score: <strong>${siteRank.overall_score ? siteRank.overall_score.toFixed(1) : 'N/A'}</strong> (${category})</p>
          <p style="margin:0 0 6px 0; font-size:12px; color:#4a5568;">Recommended: <strong>${siteRank.recommended_technology || site.site_type}</strong></p>
        </div>
      `
      marker.bindPopup(popupContent)

      if (onSelectSite) {
        marker.on('click', () => onSelectSite(site.id))
      }
    })

    if (sites.length > 1) {
      map.fitBounds(bounds, { padding: [30, 30] })
    }

    return () => {
      if (mapInstance.current) {
        mapInstance.current.remove()
        mapInstance.current = null
      }
    }
  }, [sites, ranking])

  return (
    <div className="project-map-container card">
      <h2>🗺️ GIS Project Sites Map</h2>
      <div ref={mapRef} style={{ height: '340px', borderRadius: '8px', marginTop: '10px' }} />
    </div>
  )
}

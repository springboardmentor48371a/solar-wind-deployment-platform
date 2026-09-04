import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api.js'

export default function SiteComparison() {
  const { projectId } = useParams()
  const [sites, setSites] = useState([])
  const [selectedSiteIds, setSelectedSiteIds] = useState([])
  const [siteDetails, setSiteDetails] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/projects/${projectId}/sites`).then(({ data }) => {
      setSites(data)
      if (data.length > 0) {
        // Preselect up to 3 sites
        const initial = data.slice(0, 3).map(s => s.id)
        setSelectedSiteIds(initial)
      }
      setLoading(false)
    })
  }, [projectId])

  useEffect(() => {
    // Fetch details for selected sites if not already loaded
    selectedSiteIds.forEach(id => {
      if (!siteDetails[id]) {
        api.get(`/projects/${projectId}/sites/${id}`).then(({ data }) => {
          setSiteDetails(prev => ({ ...prev, [id]: data }))
        })
      }
    })
  }, [selectedSiteIds, projectId])

  const toggleSiteSelect = (id) => {
    if (selectedSiteIds.includes(id)) {
      if (selectedSiteIds.length > 1) {
        setSelectedSiteIds(selectedSiteIds.filter(sId => sId !== id))
      }
    } else {
      if (selectedSiteIds.length < 3) {
        setSelectedSiteIds([...selectedSiteIds, id])
      }
    }
  }

  if (loading) return <div className="page"><p>Loading comparison data…</p></div>

  const selectedDetails = selectedSiteIds.map(id => siteDetails[id]).filter(Boolean)

  // Determine optimal site based on highest overall score
  let bestSiteId = null
  let maxScore = -1
  selectedDetails.forEach(d => {
    const s = d.score?.overall_score || 0
    if (s > maxScore) {
      maxScore = s
      bestSiteId = d.site.id
    }
  })

  return (
    <div className="page">
      <Link to={`/projects/${projectId}`} className="back-link">← Back to project</Link>
      <div className="section-header">
        <div>
          <h1>📊 Multi-Site Comparative Analysis</h1>
          <p className="page-subtitle">Select 2 to 3 sites to compare side-by-side and evaluate trade-offs.</p>
        </div>
      </div>

      <div className="card">
        <h3>Select Sites to Compare</h3>
        <div className="site-checkbox-group">
          {sites.map(s => (
            <label key={s.id} className={`chip-select ${selectedSiteIds.includes(s.id) ? 'active' : ''}`}>
              <input
                type="checkbox"
                checked={selectedSiteIds.includes(s.id)}
                onChange={() => toggleSiteSelect(s.id)}
              />
              {s.name}
            </label>
          ))}
        </div>
      </div>

      {selectedDetails.length > 0 && (
        <div className="card comparison-table-card">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Attribute / Metric</th>
                {selectedDetails.map(d => (
                  <th key={d.site.id} className={d.site.id === bestSiteId ? 'best-site-header' : ''}>
                    {d.site.name}
                    {d.site.id === bestSiteId && <span className="winner-badge">🏆 Best Choice</span>}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Location</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.site.latitude.toFixed(4)}°, {d.site.longitude.toFixed(4)}°</td>
                ))}
              </tr>
              <tr>
                <td><strong>Land Area</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.site.land_area_hectares} ha</td>
                ))}
              </tr>
              <tr>
                <td><strong>Solar Irradiance</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.environmental?.solar_irradiance_kwh_m2_day || '—'} kWh/m²/day</td>
                ))}
              </tr>
              <tr>
                <td><strong>Avg Wind Speed</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.environmental?.wind_speed_avg_ms || '—'} m/s</td>
                ))}
              </tr>
              <tr>
                <td><strong>Solar Capacity Factor</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.solar?.capacity_factor_pct || '—'}%</td>
                ))}
              </tr>
              <tr>
                <td><strong>Wind Capacity Factor</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.wind?.capacity_factor_pct || '—'}%</td>
                ))}
              </tr>
              <tr>
                <td><strong>Solar Output (Year 1)</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.solar?.expected_energy_output_mwh_year || '—'} MWh</td>
                ))}
              </tr>
              <tr>
                <td><strong>Wind Output (Year 1)</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.wind?.expected_annual_energy_mwh || '—'} MWh</td>
                ))}
              </tr>
              <tr className="highlight-row">
                <td><strong>Suitability Score</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}><strong>{d.score?.overall_score?.toFixed(1) || '—'}</strong> / 100</td>
                ))}
              </tr>
              <tr>
                <td><strong>Category</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.score?.category || '—'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Recommendation</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id} className="tech-cell">{d.score?.recommended_technology?.toUpperCase() || '—'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Payback Period</strong></td>
                {selectedDetails.map(d => (
                  <td key={d.site.id}>{d.forecast?.payback_period_years != null ? `${d.forecast.payback_period_years} years` : '—'}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

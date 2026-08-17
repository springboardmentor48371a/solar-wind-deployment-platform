import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line, CartesianGrid, Legend } from 'recharts'
import api from '../api.js'
import ScoreBadge from '../components/ScoreBadge.jsx'

export default function SiteDetail() {
  const { projectId, siteId } = useParams()
  const [detail, setDetail] = useState(null)

  useEffect(() => {
    api.get(`/projects/${projectId}/sites/${siteId}`).then(({ data }) => setDetail(data))
  }, [projectId, siteId])

  if (!detail) return <div className="page"><p>Loading…</p></div>

  const { site, environmental, solar, wind, score, forecast } = detail

  const scoreBreakdown = score ? [
    { name: 'Resource', value: score.resource_score },
    { name: 'Geographic', value: score.geographic_score },
    { name: 'Infrastructure', value: score.infrastructure_score },
    { name: 'Environmental', value: score.environmental_score },
    { name: 'Economic', value: score.economic_score },
  ] : []

  const energyComparison = solar && wind ? [
    { name: 'Solar', 'Capacity Factor %': solar.capacity_factor_pct, 'Output (MWh/yr)': solar.expected_energy_output_mwh_year },
    { name: 'Wind', 'Capacity Factor %': wind.capacity_factor_pct, 'Output (MWh/yr)': wind.expected_annual_energy_mwh },
  ] : []

  const forecastSeries = forecast ? [
    { year: 'Year 1', mwh: forecast.year1_mwh },
    { year: 'Year 5', mwh: forecast.year5_mwh },
    { year: 'Year 10', mwh: forecast.year10_mwh },
    { year: 'Year 25', mwh: forecast.year25_mwh },
  ] : []

  return (
    <div className="page">
      <Link to={`/projects/${projectId}`} className="back-link">← Back to project</Link>
      <div className="section-header">
        <div>
          <h1>{site.name}</h1>
          <p className="page-subtitle">{site.latitude.toFixed(4)}, {site.longitude.toFixed(4)} · {site.region || 'Region not set'}</p>
        </div>
        {score && <ScoreBadge category={score.category} score={score.overall_score} />}
      </div>

      {score && (
        <div className="card">
          <h2>Deployment Suitability</h2>
          <p className="muted">Recommended technology: <strong>{score.recommended_technology}</strong></p>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={scoreBreakdown}>
              <PolarGrid />
              <PolarAngleAxis dataKey="name" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} />
              <Radar name="Score" dataKey="value" stroke="#0f9d58" fill="#0f9d58" fillOpacity={0.4} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="two-col">
        {solar && (
          <div className="card">
            <h2>☀️ Solar Potential</h2>
            <dl className="metric-list">
              <div><dt>Annual Irradiance</dt><dd>{solar.annual_irradiance_kwh_m2} kWh/m²</dd></div>
              <div><dt>Peak Sun Hours</dt><dd>{solar.peak_sun_hours} hrs/day</dd></div>
              <div><dt>Panel Efficiency</dt><dd>{solar.panel_efficiency_pct}%</dd></div>
              <div><dt>Performance Ratio</dt><dd>{solar.performance_ratio}</dd></div>
              <div><dt>Capacity Factor</dt><dd>{solar.capacity_factor_pct}%</dd></div>
              <div><dt>Expected Output</dt><dd>{solar.expected_energy_output_mwh_year} MWh/yr</dd></div>
            </dl>
          </div>
        )}
        {wind && (
          <div className="card">
            <h2>🌬️ Wind Potential</h2>
            <dl className="metric-list">
              <div><dt>Avg Wind Speed</dt><dd>{wind.avg_wind_speed_ms} m/s</dd></div>
              <div><dt>Power Density</dt><dd>{wind.wind_power_density_w_m2} W/m²</dd></div>
              <div><dt>Turbulence Intensity</dt><dd>{wind.turbulence_intensity_pct}%</dd></div>
              <div><dt>Turbine Suitability</dt><dd>{wind.turbine_suitability}</dd></div>
              <div><dt>Capacity Factor</dt><dd>{wind.capacity_factor_pct}%</dd></div>
              <div><dt>Expected Output</dt><dd>{wind.expected_annual_energy_mwh} MWh/yr</dd></div>
            </dl>
          </div>
        )}
      </div>

      {energyComparison.length > 0 && (
        <div className="card">
          <h2>Solar vs Wind Comparison</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={energyComparison}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Capacity Factor %" fill="#4caf50" />
              <Bar dataKey="Output (MWh/yr)" fill="#2b6cb0" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {forecast && (
        <div className="card">
          <h2>📈 Energy Generation Forecast</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={forecastSeries}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="mwh" name="MWh" stroke="#0f9d58" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
          <dl className="metric-list">
            <div><dt>Estimated CAPEX</dt><dd>${forecast.estimated_capex_usd.toLocaleString()}</dd></div>
            <div><dt>Est. Annual Revenue</dt><dd>${forecast.estimated_annual_revenue_usd.toLocaleString()}</dd></div>
            <div><dt>Payback Period</dt><dd>{forecast.payback_period_years} years</dd></div>
          </dl>
        </div>
      )}

      {environmental && (
        <div className="card">
          <h2>🌍 Environmental & Site Factors</h2>
          <dl className="metric-list">
            <div><dt>Solar Irradiance</dt><dd>{environmental.solar_irradiance_kwh_m2_day} kWh/m²/day</dd></div>
            <div><dt>Wind Speed</dt><dd>{environmental.wind_speed_avg_ms} m/s</dd></div>
            <div><dt>Temperature</dt><dd>{environmental.temperature_avg_c} °C</dd></div>
            <div><dt>Rainfall</dt><dd>{environmental.rainfall_mm_year} mm/yr</dd></div>
            <div><dt>Cloud Cover</dt><dd>{environmental.cloud_cover_pct}%</dd></div>
            <div><dt>Land Slope</dt><dd>{environmental.land_slope_pct}%</dd></div>
            <div><dt>Distance to Road</dt><dd>{environmental.distance_to_road_km} km</dd></div>
            <div><dt>Distance to Transmission</dt><dd>{environmental.distance_to_transmission_km} km</dd></div>
            <div><dt>Distance to Substation</dt><dd>{environmental.distance_to_substation_km} km</dd></div>
            <div><dt>Protected Zone</dt><dd>{environmental.in_protected_zone ? 'Yes ⚠️' : 'No'}</dd></div>
          </dl>
        </div>
      )}
    </div>
  )
}

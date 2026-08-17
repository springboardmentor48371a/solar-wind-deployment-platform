import React from 'react'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { MapPin, Zap, Calendar, TrendingUp, AlertTriangle } from 'lucide-react'

export default function SiteDetails({ site, weights }) {
  const env = site.environmental_data
  const assess = site.assessments?.[0]
  if (!assess) return null

  // Calculate CapEx and ROI lifecycle (Synthetic estimation)
  // Let's assume typical Indian costs: Solar installation is ~₹4.5 Crores per MW, Wind is ~₹6.5 Crores per MW
  // CapEx in Lakhs (1 Lakh = ₹100,000, 1 Crore = 100 Lakhs)
  const capSolarMW = site.land_area / 4.0
  const capWindMW = site.land_area / 8.0

  let initialCapEx = 0
  if (assess.deployment_type === 'Solar') {
    initialCapEx = capSolarMW * 450 // Lakhs
  } else if (assess.deployment_type === 'Wind') {
    initialCapEx = capWindMW * 650 // Lakhs
  } else { // Hybrid
    initialCapEx = (capSolarMW * 450) + (capWindMW * 650) // Lakhs
  }

  // Net annual operational earnings (Revenue - 2% O&M) in Lakhs
  const annualRevLakhs = (assess.revenue_estimate) / 100000.0 // Convert INR to Lakhs
  const annualOpCost = initialCapEx * 0.015 // 1.5% O&M
  const netAnnualEarnings = Math.max(0.1, annualRevLakhs - annualOpCost)

  // Generate 25-year cumulative cash flow timeline
  const cashFlowData = []
  let cumulativeValue = -initialCapEx
  
  for (let year = 0; year <= 25; year++) {
    if (year > 0) {
      cumulativeValue += netAnnualEarnings
    }
    cashFlowData.push({
      year: `Yr ${year}`,
      'Cumulative Cash Flow': Math.round(cumulativeValue)
    })
  }

  const paybackPeriod = netAnnualEarnings > 0 ? (initialCapEx / netAnnualEarnings).toFixed(1) : 'N/A'

  // Radar/Bar chart data for scores breakdown
  const scoringBreakdown = [
    { subject: 'Resource', score: Math.round((assess.solar_capacity_factor * 0.5 + assess.wind_capacity_factor * 0.5) * 200) || 50 },
    { subject: 'Geographic', score: env?.terrain_slope <= 3.0 ? 100 : env?.terrain_slope <= 5.0 ? 80 : 50 },
    { subject: 'Infrastructure', score: env?.nearest_substation_distance <= 5.0 ? 100 : env?.nearest_substation_distance <= 10.0 ? 80 : 50 },
    { subject: 'Environmental', score: env?.protected_area ? 0 : 100 },
    { subject: 'Economic', score: site.land_area >= 100 ? 100 : site.land_area >= 50 ? 80 : 50 }
  ]

  // Recalculate resource score specifically based on type
  if (assess.deployment_type === 'Solar') {
    scoringBreakdown[0].score = Math.round(assess.solar_capacity_factor * 100 * (1 / 0.75) * 10)
  } else if (assess.deployment_type === 'Wind') {
    scoringBreakdown[0].score = Math.round(assess.wind_capacity_factor * 100 * (100 / 35))
  } else {
    scoringBreakdown[0].score = Math.round(((assess.solar_capacity_factor * 1.33) + (assess.wind_capacity_factor * 2.85)) / 2 * 100)
  }
  
  // Clip scores to 100 max
  scoringBreakdown.forEach(item => {
    item.score = Math.min(100, Math.max(0, item.score))
  })

  // Color mappings
  let suitColor = '#ef4444' // red
  if (assess.suitability_score >= 85) suitColor = '#10b981' // emerald
  else if (assess.suitability_score >= 70) suitColor = '#34d399' // lime emerald
  else if (assess.suitability_score >= 50) suitColor = '#fbbf24' // amber
  else if (assess.suitability_score >= 30) suitColor = '#f97316' // orange

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', overflowY: 'auto', maxHeight: '460px', paddingRight: '4px' }}>
      
      {/* Title Header */}
      <div style={{ borderBottom: '1px solid var(--glass-border)', paddingBottom: '12px' }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-primary)' }}>{site.site_name}</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
          <MapPin size={14} color="var(--solar)" />
          <span>Coordinates: {parseFloat(site.latitude).toFixed(4)}°N, {parseFloat(site.longitude).toFixed(4)}°E</span>
        </div>
      </div>

      {/* Grid: Stats left, Score ring right */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.3fr 1fr', gap: '20px', alignItems: 'center' }}>
        
        {/* Site Details attributes list */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.8125rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Land Area:</span>
            <span style={{ fontWeight: '600' }}>{site.land_area} Acres</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Elevation:</span>
            <span style={{ fontWeight: '600' }}>{site.elevation} meters</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Land Type:</span>
            <span style={{ fontWeight: '600' }}>{site.land_type || 'Barren'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Ownership:</span>
            <span style={{ fontWeight: '600' }}>{site.ownership || 'Government'}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Grid Distance:</span>
            <span style={{ fontWeight: '600', color: env?.nearest_substation_distance <= 5.0 ? 'var(--eco)' : 'var(--text-primary)' }}>
              {env?.nearest_substation_distance} km
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Road Proximity:</span>
            <span style={{ fontWeight: '600' }}>{env?.road_distance} km</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Sanctuary Reserve:</span>
            <span style={{ fontWeight: '600', color: env?.protected_area ? 'var(--risk)' : 'var(--eco)' }}>
              {env?.protected_area ? 'YES (Prohibited)' : 'NO (Clear)'}
            </span>
          </div>
        </div>

        {/* Suitability Score Radial representation */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '15px', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
          <div style={{ position: 'relative', width: '90px', height: '90px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '50%', border: `4px solid ${suitColor}`, boxShadow: `0 0 15px ${suitColor}25` }}>
            <div style={{ textAlign: 'center' }}>
              <span style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--text-primary)' }}>{assess.suitability_score}</span>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '-2px' }}>Score</p>
            </div>
          </div>
          <span style={{ color: suitColor, fontWeight: '700', fontSize: '0.875rem', marginTop: '10px' }}>
            {assess.suitability_category}
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', marginTop: '2px', fontWeight: '500' }}>
            Recommended: <strong style={{ color: '#fff' }}>{assess.deployment_type}</strong>
          </span>
        </div>

      </div>

      {/* AI recommendation notes */}
      <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px 16px', borderRadius: '8px', borderLeft: `3px solid ${suitColor}` }}>
        <p style={{ fontSize: '0.78125rem', lineHeight: '1.4', color: 'var(--text-secondary)' }}>
          <strong>Intelligence Report:</strong> {assess.recommendation}
        </p>
      </div>

      {/* Resource & Yield forecasts table */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
        
        {/* Solar estimates */}
        <div className="glass-card" style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.01)' }}>
          <h4 style={{ fontSize: '0.8125rem', color: 'var(--solar)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Sun size={14} /> Solar Yield (1 MWp)
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Avg Irradiance:</span>
              <span style={{ fontWeight: '500' }}>{env?.solar_irradiance} kWh/m²</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Capacity Factor:</span>
              <span style={{ fontWeight: '500' }}>{Math.round(assess.solar_capacity_factor * 100)}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Annual Energy:</span>
              <span style={{ fontWeight: '600' }}>{assess.solar_energy_prediction} MWh</span>
            </div>
          </div>
        </div>

        {/* Wind estimates */}
        <div className="glass-card" style={{ padding: '12px 16px', background: 'rgba(255,255,255,0.01)' }}>
          <h4 style={{ fontSize: '0.8125rem', color: 'var(--wind)', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Wind size={14} /> Wind Yield (1 MW)
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontSize: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Avg Wind Speed:</span>
              <span style={{ fontWeight: '500' }}>{env?.wind_speed} m/s</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Capacity Factor:</span>
              <span style={{ fontWeight: '500' }}>{Math.round(assess.wind_capacity_factor * 100)}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}>Annual Energy:</span>
              <span style={{ fontWeight: '600' }}>{assess.wind_energy_prediction} MWh</span>
            </div>
          </div>
        </div>

      </div>

      {/* Economic Forecasting and Payback Curve */}
      <div className="glass-card" style={{ padding: '15px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h4 style={{ fontSize: '0.875rem', fontWeight: '600' }}>25-Year Lifecycle ROI Curve</h4>
          <span style={{ fontSize: '11px', color: 'var(--solar)', fontWeight: '600' }}>Payback: {paybackPeriod} Years</span>
        </div>
        
        {/* Cost stats brief */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '12px', background: 'rgba(0,0,0,0.1)', padding: '8px', borderRadius: '6px' }}>
          <div>
            Est CapEx
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--text-primary)', marginTop: '2px' }}>₹{initialCapEx.toFixed(0)} Lakhs</div>
          </div>
          <div>
            Annual Net Earn
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--eco)', marginTop: '2px' }}>₹{netAnnualEarnings.toFixed(1)} L/Yr</div>
          </div>
          <div>
            Expected Generation
            <div style={{ fontSize: '12px', fontWeight: 'bold', color: 'var(--wind)', marginTop: '2px' }}>{assess.energy_forecast.toFixed(0)} MWh/Y</div>
          </div>
        </div>

        <div style={{ width: '100%', height: '140px', fontSize: '9px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={cashFlowData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="year" stroke="var(--text-muted)" tickLine={false} />
              <YAxis stroke="var(--text-muted)" tickLine={false} />
              <ChartTooltip 
                contentStyle={{ 
                  backgroundColor: 'var(--bg-secondary)', 
                  borderColor: 'var(--glass-border)',
                  color: '#fff',
                  borderRadius: '6px'
                }} 
              />
              <Line type="monotone" dataKey="Cumulative Cash Flow" stroke="var(--eco)" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Scores breakdown polar radar chart */}
      <div className="glass-card" style={{ padding: '15px' }}>
        <h4 style={{ fontSize: '0.875rem', fontWeight: '600', marginBottom: '10px' }}>Multi-Criteria Suitability Breakdown</h4>
        <div style={{ width: '100%', height: '150px', fontSize: '9px', display: 'flex', justify: 'center' }}>
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" radius="70%" data={scoringBreakdown}>
              <PolarGrid stroke="rgba(255,255,255,0.05)" />
              <PolarAngleAxis dataKey="subject" stroke="var(--text-secondary)" fontSize={10} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--text-muted)" fontSize={8} />
              <Radar name="Site Parameter" dataKey="score" stroke={suitColor} fill={suitColor} fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  )
}

import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Activity, ShieldAlert, Award, Grid3X3 } from 'lucide-react'

export default function Dashboard({ sites }) {
  // Aggregate stats
  const totalSites = sites.length
  
  const scores = sites
    .map(s => s.assessments?.[0]?.suitability_score)
    .filter(val => val !== undefined && val !== null)
    
  const avgScore = scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1) : 0.0

  const solarCount = sites.filter(s => s.assessments?.[0]?.deployment_type === 'Solar').length
  const windCount = sites.filter(s => s.assessments?.[0]?.deployment_type === 'Wind').length
  const hybridCount = sites.filter(s => s.assessments?.[0]?.deployment_type === 'Hybrid').length

  // Prep chart data
  const chartData = sites.map(s => {
    const assess = s.assessments?.[0]
    return {
      name: s.site_name.length > 15 ? s.site_name.substring(0, 15) + '...' : s.site_name,
      'Suitability Score': assess?.suitability_score || 0,
      'Solar Capacity (%)': assess?.solar_capacity_factor ? Math.round(assess.solar_capacity_factor * 100) : 0,
      'Wind Capacity (%)': assess?.wind_capacity_factor ? Math.round(assess.wind_capacity_factor * 100) : 0
    }
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Quick stats cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
        
        {/* Card 1: Total Sites */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ padding: '10px', background: 'rgba(255,255,255,0.04)', borderRadius: '12px' }}>
            <Activity size={24} color="var(--solar)" />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Evaluated Sites</span>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginTop: '2px' }}>{totalSites}</h3>
          </div>
        </div>

        {/* Card 2: Average Score */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ padding: '10px', background: 'rgba(255,255,255,0.04)', borderRadius: '12px' }}>
            <Award size={24} color="var(--eco)" />
          </div>
          <div>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Average Score</span>
            <h3 style={{ fontSize: '1.5rem', fontWeight: '700', marginTop: '2px' }}>{avgScore}<span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>/100</span></h3>
          </div>
        </div>

        {/* Card 3: Recommendations Breakdown */}
        <div className="glass-card" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ padding: '10px', background: 'rgba(255,255,255,0.04)', borderRadius: '12px' }}>
            <Grid3X3 size={24} color="var(--wind)" />
          </div>
          <div style={{ flex: 1 }}>
            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Resource Recommendations</span>
            <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '0.875rem', fontWeight: '600' }}>
              <span style={{ color: 'var(--solar)' }}>☀️ {solarCount}</span>
              <span style={{ color: 'var(--wind)' }}>💨 {windCount}</span>
              <span style={{ color: 'var(--hybrid)' }}>⚡ {hybridCount}</span>
            </div>
          </div>
        </div>
        
      </div>

      {/* Grid Comparison Chart */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: '600', marginBottom: '15px' }}>Site Suitability & Capacity Breakdown</h3>
        {chartData.length === 0 ? (
          <div style={{ height: '220px', display: 'flex', alignItems: 'center', justify: 'center', color: 'var(--text-muted)' }}>
            No site data available. Click on the map to evaluate candidate locations.
          </div>
        ) : (
          <div style={{ width: '100%', height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: 'var(--bg-secondary)', 
                    borderColor: 'var(--glass-border)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)'
                  }} 
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="Suitability Score" fill="var(--solar)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Solar Capacity (%)" fill="rgba(245, 158, 11, 0.4)" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Wind Capacity (%)" fill="var(--wind)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

    </div>
  )
}

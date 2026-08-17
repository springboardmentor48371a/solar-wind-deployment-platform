import { useState } from 'react'
import { collectEnvData, getEnvSummary } from '../api'

const Card = ({ label, value, unit, color }) => (
  <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: '14px 16px', minWidth: 130 }}>
    <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700, color: color || '#111' }}>{value ?? '—'}</div>
    {unit && <div style={{ fontSize: 11, color: '#9ca3af' }}>{unit}</div>}
  </div>
)

export default function EnvSummary({ siteId }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(false)
  const [collecting, setCollecting] = useState(false)
  const [error, setError] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getEnvSummary(siteId)
      setSummary(res.data)
    } catch {
      setError('No data yet. Click Collect Data first.')
    } finally {
      setLoading(false)
    }
  }

  const collect = async () => {
    setCollecting(true)
    setError('')
    try {
      await collectEnvData(siteId, 30)
      await load()
    } catch {
      setError('Failed to collect data. Check your connection.')
    } finally {
      setCollecting(false)
    }
  }

  const windColor = (v) => !v ? '#111' : v >= 6 ? '#16a34a' : v >= 3 ? '#ca8a04' : '#dc2626'
  const solarColor = (v) => !v ? '#111' : v >= 5 ? '#16a34a' : v >= 3 ? '#ca8a04' : '#dc2626'

  return (
    <div style={{ marginTop: 16 }}>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
        <span style={{ fontSize: 13, fontWeight: 600 }}>Environmental Data</span>
        <button onClick={collect} disabled={collecting} style={{ padding: '5px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff' }}>
          {collecting ? 'Collecting...' : 'Collect Data'}
        </button>
        {!summary && !loading && (
          <button onClick={load} style={{ padding: '5px 12px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff' }}>Load Summary</button>
        )}
      </div>

      {error && <p style={{ fontSize: 12, color: '#dc2626', marginBottom: 8 }}>{error}</p>}
      {loading && <p style={{ fontSize: 12, color: '#9ca3af' }}>Loading...</p>}

      {summary && summary.total_days > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
          <Card label="Avg Solar Irradiance" value={summary.avg_solar_irradiance} unit="W/m²" color={solarColor(summary.avg_peak_sun_hours)} />
          <Card label="Peak Sun Hours" value={summary.avg_peak_sun_hours} unit="hrs/day" color={solarColor(summary.avg_peak_sun_hours)} />
          <Card label="Avg Wind Speed" value={summary.avg_wind_speed} unit="m/s (10m)" color={windColor(summary.avg_wind_speed)} />
          <Card label="Wind Speed 50m" value={summary.avg_wind_speed_50m} unit="m/s (50m)" color={windColor(summary.avg_wind_speed_50m)} />
          <Card label="Avg Temperature" value={summary.avg_temperature} unit="°C" />
          <Card label="Total Rainfall" value={summary.total_rainfall} unit="mm" />
          <Card label="Avg Cloud Cover" value={summary.avg_cloud_cover} unit="%" />
          <Card label="Elevation" value={summary.elevation} unit="m" />
          <Card label="Data Days" value={summary.total_days} unit="days" />
        </div>
      )}
    </div>
  )
}

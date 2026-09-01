import { useState, useEffect } from 'react'
import { collectEnvData, getEnvSummary } from '../api'

const Card = ({ label, value, unit, color }) => (
  <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: '12px 14px', minWidth: 120 }}>
    <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 18, fontWeight: 700, color: color || '#111' }}>{value ?? '—'}</div>
    {unit && <div style={{ fontSize: 11, color: '#9ca3af' }}>{unit}</div>}
  </div>
)

export default function EnvSummary({ siteId, energyType }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { load() }, [siteId])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getEnvSummary(siteId)
      setSummary(res.data.total_days > 0 ? res.data : null)
      if (res.data.total_days === 0) setError('No data yet.')
    } catch {
      setError('No environmental data yet.')
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    setRefreshing(true)
    setError('')
    try {
      await collectEnvData(siteId, 30)
      await load()
    } catch {
      setError('Failed to fetch data. Check your connection.')
    } finally {
      setRefreshing(false)
    }
  }

  const windColor = (v) => !v ? '#111' : v >= 6 ? '#16a34a' : v >= 3 ? '#ca8a04' : '#dc2626'
  const solarColor = (v) => !v ? '#111' : v >= 5 ? '#16a34a' : v >= 3 ? '#ca8a04' : '#dc2626'

  return (
    <div style={{ marginTop: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: '#6b7280' }}>Environmental Data</span>
        <button onClick={refresh} disabled={refreshing}
          style={{ padding: '3px 10px', fontSize: 11, border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer', background: '#fff', color: '#6b7280' }}>
          {refreshing ? 'Fetching...' : 'Refresh'}
        </button>
      </div>

      {loading && <p style={{ fontSize: 12, color: '#9ca3af' }}>Loading environmental data...</p>}
      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <p style={{ fontSize: 12, color: '#9ca3af' }}>{error}</p>
          <button onClick={refresh} disabled={refreshing}
            style={{ padding: '3px 10px', fontSize: 11, border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer', background: '#fff' }}>
            {refreshing ? 'Fetching...' : 'Fetch Now'}
          </button>
        </div>
      )}

      {summary && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
          {(energyType === 'solar' || energyType === 'hybrid') && (
            <>
              <Card label="Solar Irradiance" value={summary.avg_solar_irradiance} unit="W/m²" color={solarColor(summary.avg_peak_sun_hours)} />
              <Card label="Peak Sun Hours" value={summary.avg_peak_sun_hours} unit="hrs/day" color={solarColor(summary.avg_peak_sun_hours)} />
            </>
          )}
          {(energyType === 'wind' || energyType === 'hybrid') && (
            <>
              <Card label="Wind Speed 10m" value={summary.avg_wind_speed} unit="m/s" color={windColor(summary.avg_wind_speed)} />
              <Card label="Wind Speed 50m" value={summary.avg_wind_speed_50m} unit="m/s" color={windColor(summary.avg_wind_speed_50m)} />
            </>
          )}
          <Card label="Avg Temperature" value={summary.avg_temperature} unit="°C" />
          <Card label="Total Rainfall" value={summary.total_rainfall} unit="mm" />
          <Card label="Cloud Cover" value={summary.avg_cloud_cover} unit="%" />
          <Card label="Elevation" value={summary.elevation} unit="m" />
          <Card label="Data Days" value={summary.total_days} unit="days" />
        </div>
      )}
    </div>
  )
}

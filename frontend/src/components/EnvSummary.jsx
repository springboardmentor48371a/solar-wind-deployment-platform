import { useState, useEffect, useCallback } from 'react'
import { collectEnvData, getEnvSummary } from '../api'
import './EnvSummary.css'

function EnvCard({ label, value, unit, variant }) {
  const numClass = variant ? `env-card__value--${variant}` : ''
  return (
    <div className="env-card">
      <div className="env-card__label">{label}</div>
      <div className={`env-card__value ${numClass}`}>
        {value != null ? value : '—'}
      </div>
      {unit && <div className="env-card__unit">{unit}</div>}
    </div>
  )
}

export default function EnvSummary({ siteId, energyType }) {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getEnvSummary(siteId)
      setSummary(res.data.total_days > 0 ? res.data : null)
      if (res.data.total_days === 0) setError('No environmental readings collected yet.')
    } catch {
      setError('No environmental data available yet.')
    } finally {
      setLoading(false)
    }
  }, [siteId])

  useEffect(() => {
    load()
  }, [load])

  const refresh = async () => {
    setRefreshing(true)
    setError('')
    try {
      await collectEnvData(siteId, 30)
      await load()
    } catch {
      setError('Failed to fetch data from satellite/weather providers.')
    } finally {
      setRefreshing(false)
    }
  }

  const isSolar = energyType === 'solar' || energyType === 'hybrid'
  const isWind = energyType === 'wind' || energyType === 'hybrid'

  return (
    <div className="env-summary">
      <div className="env-summary__header">
        <span className="env-summary__title">Environmental Baseline</span>
        <button
          type="button"
          onClick={refresh}
          disabled={refreshing}
          className="env-summary__btn"
        >
          {refreshing ? 'Syncing...' : 'Sync Satellite Data'}
        </button>
      </div>

      {loading && (
        <div className="env-summary__status">
          <span className="env-summary__spinner" />
          Loading baseline data...
        </div>
      )}

      {!loading && error && (
        <div className="env-summary__status">
          <span>{error}</span>
          <button
            type="button"
            onClick={refresh}
            disabled={refreshing}
            className="env-summary__btn"
          >
            {refreshing ? 'Syncing...' : 'Fetch Now'}
          </button>
        </div>
      )}

      {summary && (
        <div className="env-summary__grid">
          {isSolar && (
            <>
              <EnvCard
                label="Solar Irradiance"
                value={summary.avg_solar_irradiance}
                unit="W/m²"
                variant="solar"
              />
              <EnvCard
                label="Peak Sun Hours"
                value={summary.avg_peak_sun_hours}
                unit="hrs/day"
                variant="solar"
              />
            </>
          )}

          {isWind && (
            <>
              <EnvCard
                label="Wind Speed 10m"
                value={summary.avg_wind_speed}
                unit="m/s"
                variant="wind"
              />
              <EnvCard
                label="Wind Speed 50m"
                value={summary.avg_wind_speed_50m}
                unit="m/s"
                variant="wind"
              />
            </>
          )}

          <EnvCard
            label="Avg Temperature"
            value={summary.avg_temperature}
            unit="°C"
          />
          <EnvCard
            label="Total Rainfall"
            value={summary.total_rainfall}
            unit="mm"
          />
          <EnvCard
            label="Cloud Cover"
            value={summary.avg_cloud_cover}
            unit="%"
          />
          <EnvCard
            label="Elevation"
            value={summary.elevation}
            unit="m"
          />
          <EnvCard
            label="Sample Window"
            value={summary.total_days}
            unit="days"
            variant="olive"
          />
        </div>
      )}
    </div>
  )
}

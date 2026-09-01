import { useState, useEffect } from 'react'
import { getPrediction, runPrediction } from '../api'

const CATEGORY_COLORS = {
  'Excellent':           '#16a34a',
  'Highly Suitable':     '#65a30d',
  'Moderately Suitable': '#ca8a04',
  'Low Suitability':     '#ea580c',
  'Unsuitable':          '#dc2626',
}

const ScoreBar = ({ value, color }) => (
  <div style={{ height: 6, background: '#e5e7eb', borderRadius: 3, marginTop: 4 }}>
    <div style={{ height: '100%', width: `${Math.min(value ?? 0, 100)}%`, background: color || '#6b7280', borderRadius: 3, transition: 'width 0.4s' }} />
  </div>
)

const ScoreCard = ({ label, value, color, unit = 'pts' }) => (
  <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: '10px 12px', minWidth: 110 }}>
    <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 2 }}>{label}</div>
    <div style={{ fontSize: 20, fontWeight: 700, color: color || '#111' }}>
      {value != null ? Math.round(value) : '—'}
      {value != null && <span style={{ fontSize: 11, fontWeight: 400, color: '#9ca3af', marginLeft: 2 }}>{unit}</span>}
    </div>
    {value != null && <ScoreBar value={value} color={color} />}
  </div>
)

const LandCoverBadge = ({ cls }) => {
  const colors = { vegetation: '#16a34a', cropland: '#65a30d', barren: '#ca8a04', urban: '#6b7280', water: '#2563eb' }
  const color = colors[cls] || '#6b7280'
  return (
    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12, background: color + '20', color, fontWeight: 600, textTransform: 'capitalize' }}>
      {cls || '—'}
    </span>
  )
}

export default function PredictionPanel({ siteId, energyType }) {
  const [pred, setPred] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { load() }, [siteId])

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getPrediction(siteId)
      setPred(res.data)
    } catch (e) {
      if (e.response?.status === 404) setError('No predictions yet.')
      else setError('Failed to load predictions.')
    } finally {
      setLoading(false)
    }
  }

  const run = async () => {
    setRunning(true)
    setError('')
    try {
      const res = await runPrediction(siteId)
      setPred(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Prediction failed.')
    } finally {
      setRunning(false)
    }
  }

  const catColor = pred ? (CATEGORY_COLORS[pred.suitability_category] || '#6b7280') : '#6b7280'

  return (
    <div style={{ marginTop: 14, borderTop: '1px solid #e5e7eb', paddingTop: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: '#6b7280' }}>ML Predictions</span>
        <button onClick={run} disabled={running}
          style={{ padding: '3px 10px', fontSize: 11, border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer', background: '#fff', color: '#6b7280' }}>
          {running ? 'Running...' : pred ? 'Re-run' : 'Run Now'}
        </button>
      </div>

      {loading && <p style={{ fontSize: 12, color: '#9ca3af' }}>Loading predictions...</p>}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <p style={{ fontSize: 12, color: '#9ca3af' }}>{error}</p>
          <button onClick={run} disabled={running}
            style={{ padding: '3px 10px', fontSize: 11, border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer', background: '#fff' }}>
            {running ? 'Running...' : 'Run Predictions'}
          </button>
        </div>
      )}

      {pred && (
        <div>
          {/* Suitability header */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, padding: '10px 14px', background: catColor + '10', border: `1px solid ${catColor}40`, borderRadius: 8 }}>
            <div>
              <div style={{ fontSize: 11, color: '#6b7280' }}>Overall Suitability</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: catColor, lineHeight: 1.1 }}>
                {pred.suitability_score != null ? Math.round(pred.suitability_score) : '—'}
                <span style={{ fontSize: 13, fontWeight: 400, color: '#9ca3af', marginLeft: 2 }}>/100</span>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: catColor }}>{pred.suitability_category || '—'}</span>
              <ScoreBar value={pred.suitability_score} color={catColor} />
            </div>
          </div>

          {/* Resource scores */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 10 }}>
            {(energyType === 'solar' || energyType === 'hybrid') && (
              <ScoreCard label="Solar Score" value={pred.solar_score} color="#f59e0b" />
            )}
            {(energyType === 'wind' || energyType === 'hybrid') && (
              <ScoreCard label="Wind Score" value={pred.wind_score} color="#3b82f6" />
            )}
            <ScoreCard label="Land Cover" value={pred.land_cover_score} color="#10b981" />
          </div>

          {/* Solar details */}
          {pred.solar_capacity_factor != null && (energyType === 'solar' || energyType === 'hybrid') && (
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>
              ☀️ Capacity Factor: <strong>{(pred.solar_capacity_factor * 100).toFixed(1)}%</strong>
              {' · '}Est. Yield: <strong>{pred.solar_yield_kwh?.toFixed(1)} kWh/day</strong> per kWp
            </div>
          )}

          {/* Wind details */}
          {pred.wind_power_kw != null && (energyType === 'wind' || energyType === 'hybrid') && (
            <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>
              💨 Power Output: <strong>{pred.wind_power_kw?.toFixed(0)} kW</strong>
              {' · '}Capacity Factor: <strong>{(pred.wind_capacity_factor * 100).toFixed(1)}%</strong>
            </div>
          )}

          {/* Land cover */}
          <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 10 }}>
            🌍 Land Cover: <LandCoverBadge cls={pred.land_cover_class} />
            {pred.vegetation_index != null && <span style={{ marginLeft: 8 }}>NDVI: <strong>{pred.vegetation_index?.toFixed(2)}</strong></span>}
            {pred.land_slope != null && <span style={{ marginLeft: 8 }}>Slope: <strong>{pred.land_slope?.toFixed(1)}°</strong></span>}
          </div>

          {/* Sub-scores breakdown */}
          <div style={{ fontSize: 11, color: '#9ca3af', marginBottom: 6, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Score Breakdown</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {[
              { label: 'Resource (35%)',       value: pred.resource_score,        color: '#f59e0b' },
              { label: 'Geographic (25%)',     value: pred.geographic_score,      color: '#8b5cf6' },
              { label: 'Infrastructure (15%)', value: pred.infrastructure_score,  color: '#6b7280' },
              { label: 'Environmental (15%)',  value: pred.environmental_score,   color: '#10b981' },
              { label: 'Economic (10%)',       value: pred.economic_score,        color: '#3b82f6' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 6, padding: '6px 10px', minWidth: 130 }}>
                <div style={{ fontSize: 10, color: '#9ca3af' }}>{label}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color }}>{value != null ? Math.round(value) : '—'}</div>
                <ScoreBar value={value} color={color} />
              </div>
            ))}
          </div>

          <div style={{ fontSize: 10, color: '#d1d5db', marginTop: 8 }}>
            Last predicted: {pred.predicted_at ? new Date(pred.predicted_at).toLocaleString() : '—'}
          </div>
        </div>
      )}
    </div>
  )
}

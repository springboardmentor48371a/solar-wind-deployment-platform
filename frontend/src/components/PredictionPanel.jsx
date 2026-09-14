import { useState, useEffect, useCallback } from 'react'
import { getPrediction, runPrediction } from '../api'
import './PredictionPanel.css'

function ProgressBar({ value, variant = 'rust' }) {
  const pct = Math.min(Math.max(value ?? 0, 0), 100)
  return (
    <div style={{ height: '4px', background: 'var(--color-border)', borderRadius: 'var(--radius-pill)', width: '100%', marginTop: '6px', overflow: 'hidden' }}>
      <div
        style={{
          height: '100%',
          width: `${pct}%`,
          background: variant === 'olive' ? 'var(--color-accent-olive)' : variant === 'steel' ? 'var(--color-accent-steel)' : 'var(--color-accent-rust)',
          borderRadius: 'var(--radius-pill)',
          transition: 'width 250ms ease',
        }}
      />
    </div>
  )
}

export default function PredictionPanel({ siteId, energyType }) {
  const [pred, setPred] = useState(null)
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await getPrediction(siteId)
      setPred(res.data)
    } catch (e) {
      if (e.response?.status === 404) setError('No ML predictions calculated yet.')
      else setError('Failed to retrieve predictions.')
    } finally {
      setLoading(false)
    }
  }, [siteId])

  useEffect(() => {
    load()
  }, [load])

  const run = async () => {
    setRunning(true)
    setError('')
    try {
      const res = await runPrediction(siteId)
      setPred(res.data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Inference engine failed. Check coordinates.')
    } finally {
      setRunning(false)
    }
  }

  const isSolar = energyType === 'solar' || energyType === 'hybrid'
  const isWind = energyType === 'wind' || energyType === 'hybrid'

  const cat = pred?.suitability_category || ''
  const isGreen = cat === 'Excellent' || cat === 'Highly Suitable'
  const isRed = cat === 'Unsuitable'
  const tierClass = isGreen
    ? 'pred-panel__hero-tier--green'
    : isRed
    ? 'pred-panel__hero-tier--red'
    : 'pred-panel__hero-tier--peach'

  const scoreVariant = isGreen ? 'olive' : isRed ? 'rust' : 'rust'

  return (
    <div className="pred-panel">
      <div className="pred-panel__header">
        <span className="pred-panel__title">ML Suitability Assessment</span>
        <button
          type="button"
          onClick={run}
          disabled={running}
          className="pred-panel__btn"
        >
          {running ? 'Running ML Models...' : pred ? 'Recalculate' : 'Run Model'}
        </button>
      </div>

      {loading && (
        <div style={{ padding: '12px 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          Retrieving suitability metrics...
        </div>
      )}

      {!loading && error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 0', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
          <span>{error}</span>
          <button
            type="button"
            onClick={run}
            disabled={running}
            className="pred-panel__btn"
          >
            {running ? 'Running...' : 'Generate Prediction'}
          </button>
        </div>
      )}

      {pred && (
        <div>
          {/* Overall Hero Banner */}
          <div className="pred-panel__hero">
            <div className="pred-panel__hero-score">
              <span className={`pred-panel__hero-number ${isGreen ? 'pred-panel__hero-number--olive' : ''}`}>
                {pred.suitability_score != null ? Math.round(pred.suitability_score) : '—'}
              </span>
              <span className="pred-panel__hero-total">/100</span>
            </div>
            <div className="pred-panel__hero-info">
              <span className={`pred-panel__hero-tier ${tierClass}`}>
                {pred.suitability_category || 'Assessed'}
              </span>
              <ProgressBar value={pred.suitability_score} variant={scoreVariant} />
            </div>
          </div>

          {/* Primary Factor Cards */}
          <div className="pred-panel__scores-grid">
            {isSolar && (
              <div className="pred-panel__score-card">
                <div className="pred-panel__score-card-label">Solar Resource</div>
                <div className="pred-panel__score-card-val pred-panel__score-card-val--solar">
                  {pred.solar_score != null ? Math.round(pred.solar_score) : '—'}
                </div>
                <ProgressBar value={pred.solar_score} variant="rust" />
              </div>
            )}
            {isWind && (
              <div className="pred-panel__score-card">
                <div className="pred-panel__score-card-label">Wind Resource</div>
                <div className="pred-panel__score-card-val pred-panel__score-card-val--wind">
                  {pred.wind_score != null ? Math.round(pred.wind_score) : '—'}
                </div>
                <ProgressBar value={pred.wind_score} variant="steel" />
              </div>
            )}
            <div className="pred-panel__score-card">
              <div className="pred-panel__score-card-label">Terrain &amp; Land</div>
              <div className="pred-panel__score-card-val pred-panel__score-card-val--olive">
                {pred.land_cover_score != null ? Math.round(pred.land_cover_score) : '—'}
              </div>
              <ProgressBar value={pred.land_cover_score} variant="olive" />
            </div>
          </div>

          {/* Environmental and Engineering Details */}
          <div className="pred-panel__details">
            {isSolar && pred.solar_capacity_factor != null && (
              <div>
                Solar Capacity Factor: <strong>{(pred.solar_capacity_factor * 100).toFixed(1)}%</strong>
                {' · '}Estimated Yield: <strong>{pred.solar_yield_kwh?.toFixed(1)} kWh/day</strong> per kWp
              </div>
            )}
            {isWind && pred.wind_power_kw != null && (
              <div>
                Wind Turbine Potential: <strong>{pred.wind_power_kw?.toFixed(0)} kW</strong>
                {' · '}Capacity Factor: <strong>{(pred.wind_capacity_factor * 100).toFixed(1)}%</strong>
              </div>
            )}
            <div>
              Land Classification:{' '}
              <strong style={{ textTransform: 'capitalize' }}>
                {pred.land_cover_class || 'General'}
              </strong>
              {pred.vegetation_index != null && (
                <span> &middot; NDVI: <strong>{pred.vegetation_index.toFixed(2)}</strong></span>
              )}
              {pred.land_slope != null && (
                <span> &middot; Slope: <strong>{pred.land_slope.toFixed(1)}&deg;</strong></span>
              )}
            </div>
          </div>

          {/* Weighted Sub-Scores Breakdown */}
          <div className="pred-panel__breakdown-title">Multi-Criteria Score Breakdown</div>
          <div className="pred-panel__breakdown-grid">
            {(energyType === 'solar'
              ? [
                  { label: 'Resource (43%)', val: pred.resource_score, variant: 'rust' },
                  { label: 'Geographic (19%)', val: pred.geographic_score, variant: 'steel' },
                  { label: 'Infrastructure (16%)', val: pred.infrastructure_score, variant: 'olive' },
                  { label: 'Environmental (12%)', val: pred.environmental_score, variant: 'olive' },
                  { label: 'Economic (10%)', val: pred.economic_score, variant: 'steel' },
                ]
              : energyType === 'wind'
              ? [
                  { label: 'Resource (36%)', val: pred.resource_score, variant: 'rust' },
                  { label: 'Geographic (31%)', val: pred.geographic_score, variant: 'steel' },
                  { label: 'Infrastructure (19%)', val: pred.infrastructure_score, variant: 'olive' },
                  { label: 'Environmental (4%)', val: pred.environmental_score, variant: 'olive' },
                  { label: 'Economic (10%)', val: pred.economic_score, variant: 'steel' },
                ]
              : [
                  { label: 'Resource (40%)', val: pred.resource_score, variant: 'rust' },
                  { label: 'Geographic (25%)', val: pred.geographic_score, variant: 'steel' },
                  { label: 'Infrastructure (18%)', val: pred.infrastructure_score, variant: 'olive' },
                  { label: 'Environmental (8%)', val: pred.environmental_score, variant: 'olive' },
                  { label: 'Economic (10%)', val: pred.economic_score, variant: 'steel' },
                ]
            ).map((item) => (
              <div key={item.label} className="pred-panel__breakdown-item">
                <div className="pred-panel__breakdown-label">{item.label}</div>
                <div className="pred-panel__breakdown-val">
                  {item.val != null ? Math.round(item.val) : '—'}
                </div>
                <ProgressBar value={item.val} variant={item.variant} />
              </div>
            ))}
          </div>

          {pred.updated_at && (
            <div className="pred-panel__timestamp">
              Last calculated {new Date(pred.updated_at).toLocaleDateString()} at {new Date(pred.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

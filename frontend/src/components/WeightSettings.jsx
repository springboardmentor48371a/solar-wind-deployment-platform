import React, { useState, useEffect } from 'react'
import { X, RefreshCw, AlertTriangle } from 'lucide-react'

export default function WeightSettings({ weights, onSave, onClose }) {
  const [resW, setResW] = useState(Math.round(weights.weight_resource * 100))
  const [geoW, setGeoW] = useState(Math.round(weights.weight_geographic * 100))
  const [infW, setInfW] = useState(Math.round(weights.weight_infrastructure * 100))
  const [envW, setEnvW] = useState(Math.round(weights.weight_environment * 100))
  const [ecoW, setEcoW] = useState(Math.round(weights.weight_economic * 100))

  const total = resW + geoW + infW + envW + ecoW
  const isValid = total === 100

  const handleNormalize = () => {
    const sum = resW + geoW + infW + envW + ecoW
    if (sum === 0) return
    setResW(Math.round((resW / sum) * 100))
    setGeoW(Math.round((geoW / sum) * 100))
    setInfW(Math.round((infW / sum) * 100))
    setEnvW(Math.round((envW / sum) * 100))
    setEcoW(Math.round((ecoW / sum) * 100))
  }

  const handleSave = () => {
    if (!isValid) return
    onSave({
      weight_resource: resW / 100,
      weight_geographic: geoW / 100,
      weight_infrastructure: infW / 100,
      weight_environment: envW / 100,
      weight_economic: ecoW / 100
    })
  }

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.6)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000, padding: '20px' }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '440px', padding: '30px', background: 'var(--bg-secondary)', border: '1px solid var(--glass-border-hover)' }}>
        
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '25px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700' }}>Suitability Matrix Weights</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', outline: 'none' }}>
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          Adjust weights to dynamically prioritize factors during renewable site evaluation. The weights must sum to exactly 100%.
        </p>

        {/* Sliders */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', marginBottom: '24px' }}>
          
          {/* Resource Quality */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: '500', marginBottom: '6px' }}>
              <span>Renewable Resource Quality</span>
              <span style={{ color: 'var(--solar)' }}>{resW}%</span>
            </div>
            <input type="range" min="0" max="100" value={resW} onChange={e => setResW(parseInt(e.target.value))} />
          </div>

          {/* Geographic Terrain */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: '500', marginBottom: '6px' }}>
              <span>Geographic Terrain & Slope</span>
              <span style={{ color: 'var(--eco)' }}>{geoW}%</span>
            </div>
            <input type="range" min="0" max="100" value={geoW} onChange={e => setGeoW(parseInt(e.target.value))} />
          </div>

          {/* Grid Proximity */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: '500', marginBottom: '6px' }}>
              <span>Grid & Infrastructure Proximity</span>
              <span style={{ color: 'var(--wind)' }}>{infW}%</span>
            </div>
            <input type="range" min="0" max="100" value={infW} onChange={e => setInfW(parseInt(e.target.value))} />
          </div>

          {/* Environmental Risks */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: '500', marginBottom: '6px' }}>
              <span>Environmental Constraints</span>
              <span style={{ color: 'var(--risk)' }}>{envW}%</span>
            </div>
            <input type="range" min="0" max="100" value={envW} onChange={e => setEnvW(parseInt(e.target.value))} />
          </div>

          {/* Economic ROI */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', fontWeight: '500', marginBottom: '6px' }}>
              <span>Economic Feasibility (Area/Type)</span>
              <span style={{ color: 'var(--text-primary)' }}>{ecoW}%</span>
            </div>
            <input type="range" min="0" max="100" value={ecoW} onChange={e => setEcoW(parseInt(e.target.value))} />
          </div>

        </div>

        {/* Validation total indicator */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: isValid ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)', border: `1px solid ${isValid ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`, borderRadius: '8px', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.875rem' }}>
            {!isValid && <AlertTriangle size={16} color="var(--risk)" />}
            <span style={{ color: isValid ? 'var(--eco)' : '#fca5a5' }}>
              {isValid ? 'Weights balance successfully!' : `Sum of weights: ${total}% (Requires 100%)`}
            </span>
          </div>
          {!isValid && (
            <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '0.75rem', display: 'flex', gap: '4px' }} onClick={handleNormalize}>
              <RefreshCw size={12} /> Auto-Balance
            </button>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <button className="btn btn-primary" onClick={handleSave} disabled={!isValid} style={{ opacity: isValid ? 1 : 0.5, cursor: isValid ? 'pointer' : 'not-allowed' }}>
            Apply Weights
          </button>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
        </div>

      </div>
    </div>
  )
}

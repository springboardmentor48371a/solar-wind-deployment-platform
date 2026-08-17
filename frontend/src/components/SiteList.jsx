import React, { useState } from 'react'
import { Search, Compass, Sun, Wind, Activity } from 'lucide-react'

// Color map for suitability categories
const CATEGORY_COLORS = {
  "Excellent": "badge-eco",
  "High": "badge-eco",
  "Moderate": "badge-solar",
  "Low": "badge-wind",
  "Unsuitable": "badge-risk"
}

export default function SiteList({ sites, activeSite, onSelect }) {
  const [search, setSearch] = useState('')
  const [techFilter, setTechFilter] = useState('All')
  const [ratingFilter, setRatingFilter] = useState('All')

  // Filter pipeline
  const filteredSites = sites.filter(site => {
    const assess = site.assessments?.[0]
    const matchesSearch = site.site_name.toLowerCase().includes(search.toLowerCase())
    const matchesTech = techFilter === 'All' || assess?.deployment_type === techFilter
    const matchesRating = ratingFilter === 'All' || assess?.suitability_category === ratingFilter
    return matchesSearch && matchesTech && matchesRating
  })

  const getTechIcon = (type) => {
    switch (type) {
      case 'Solar':
        return <Sun size={14} style={{ color: 'var(--solar)' }} />
      case 'Wind':
        return <Wind size={14} style={{ color: 'var(--wind)' }} />
      case 'Hybrid':
        return <Activity size={14} style={{ color: 'var(--hybrid)' }} />
      default:
        return <Compass size={14} />
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, overflow: 'hidden' }}>
      
      {/* Search Input */}
      <div style={{ position: 'relative' }}>
        <Search size={16} style={{ position: 'absolute', left: '10px', top: '11px', color: 'var(--text-muted)' }} />
        <input 
          className="form-input" 
          style={{ paddingLeft: '32px', fontSize: '0.8125rem' }} 
          type="text" 
          placeholder="Search site name..." 
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Filters selectors */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <select className="form-input" style={{ fontSize: '0.75rem', padding: '6px' }} value={techFilter} onChange={e => setTechFilter(e.target.value)}>
          <option value="All">All Tech</option>
          <option value="Solar">Solar</option>
          <option value="Wind">Wind</option>
          <option value="Hybrid">Hybrid</option>
        </select>
        <select className="form-input" style={{ fontSize: '0.75rem', padding: '6px' }} value={ratingFilter} onChange={e => setRatingFilter(e.target.value)}>
          <option value="All">All Ratings</option>
          <option value="Excellent">Excellent</option>
          <option value="High">High</option>
          <option value="Moderate">Moderate</option>
          <option value="Low">Low</option>
          <option value="Unsuitable">Unsuitable</option>
        </select>
      </div>

      {/* Sites List scrollbox */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px', paddingRight: '2px' }}>
        {filteredSites.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 10px', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
            No candidate sites found matching criteria.
          </div>
        ) : (
          filteredSites.map((site) => {
            const latestAssess = site.assessments?.[0]
            const score = latestAssess?.suitability_score ?? 0.0
            const category = latestAssess?.suitability_category ?? 'Moderate'
            const tech = latestAssess?.deployment_type ?? 'Solar'
            const isSelected = activeSite?.site_id === site.site_id
            
            const badgeClass = CATEGORY_COLORS[category] || "badge-solar"

            return (
              <div 
                key={site.site_id} 
                onClick={() => onSelect(site)}
                style={{ 
                  padding: '12px', 
                  borderRadius: '10px',
                  background: isSelected ? 'var(--bg-tertiary)' : 'rgba(255,255,255,0.01)',
                  border: `1px solid ${isSelected ? 'var(--solar)' : 'var(--glass-border)'}`,
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)'
                }}
                className="interactive"
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <h4 style={{ fontSize: '0.875rem', fontWeight: '600', color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)', maxLength: '15px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '170px' }}>
                    {site.site_name}
                  </h4>
                  <span className={`badge ${badgeClass}`} style={{ fontSize: '10px', padding: '2px 6px' }}>
                    {score}
                  </span>
                </div>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    {getTechIcon(tech)}
                    <span style={{ fontWeight: '500' }}>{tech}</span>
                  </div>
                  <span>{site.land_area} Acres</span>
                </div>
              </div>
            )
          })
        )}
      </div>

    </div>
  )
}

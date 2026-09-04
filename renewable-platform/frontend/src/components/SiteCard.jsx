import React from 'react'
import { Link } from 'react-router-dom'
import ScoreBadge from './ScoreBadge.jsx'

export default function SiteCard({ projectId, site, score }) {
  return (
    <Link to={`/projects/${projectId}/sites/${site.id}`} className="site-card">
      <div className="site-card-header">
        <h4>{site.name}</h4>
        {score && <ScoreBadge category={score.category} score={score.overall_score} />}
      </div>
      <div className="site-card-meta">
        <span>{site.latitude.toFixed(3)}, {site.longitude.toFixed(3)}</span>
        <span className="dot">•</span>
        <span>{site.site_type}</span>
        {site.land_area_hectares && <>
          <span className="dot">•</span>
          <span>{site.land_area_hectares} ha</span>
        </>}
        {site.attributes_source && (
          <>
            <span className="dot">•</span>
            <span className={site.attributes_source === 'live' ? 'tag-live' : 'tag-fallback'}>
              {site.attributes_source === 'live' ? 'Live data' : 'Estimated'}
            </span>
          </>
        )}
      </div>
    </Link>
  )
}

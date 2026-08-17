import React from 'react'

const CATEGORY_COLORS = {
  'Excellent': '#0f9d58',
  'Highly Suitable': '#4caf50',
  'Moderately Suitable': '#f5a623',
  'Low Suitability': '#e67e22',
  'Unsuitable': '#d64545',
}

export default function ScoreBadge({ category, score }) {
  const color = CATEGORY_COLORS[category] || '#888'
  return (
    <span className="score-badge" style={{ backgroundColor: color }}>
      {score != null ? `${score.toFixed(1)} · ` : ''}{category}
    </span>
  )
}

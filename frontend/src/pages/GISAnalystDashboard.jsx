import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import ProjectsView from '../components/ProjectsView'
import MapView from '../components/MapView'
import AnalyticsView from '../components/AnalyticsView'
import { listProjects, listSites } from '../api'
import './GISAnalystDashboard.css'

const PAGE_META = {
  map: {
    eyebrow: 'GIS Analyst · Spatial Intelligence',
    title: 'Geographic Map View',
  },
  projects: {
    eyebrow: 'GIS Analyst · Site Inventory',
    title: 'Site Assessments',
  },
  analytics: {
    eyebrow: 'GIS Analyst · Suitability Modeling',
    title: 'Site Analytics & Rankings',
  },
}

export default function GISAnalystDashboard({ user, onLogout }) {
  const [page, setPage] = useState('map')
  const [allSites, setAllSites] = useState([])

  useEffect(() => {
    loadAllSites()
  }, [])

  const loadAllSites = async () => {
    try {
      const res = await listProjects()
      const sitesArr = await Promise.all(
        res.data.map((p) => listSites(p.id).then((r) => r.data))
      )
      setAllSites(sitesArr.flat())
    } catch {
      // Handled gracefully in child components
    }
  }

  const meta = PAGE_META[page] || PAGE_META.map

  return (
    <Layout
      user={user}
      onLogout={onLogout}
      activePage={page}
      onNavigate={setPage}
      eyebrow={meta.eyebrow}
      title={meta.title}
    >
      <div className="gis-analyst-dashboard">
        {page === 'map' && <MapView sites={allSites} />}
        {page === 'projects' && <ProjectsView user={user} />}
        {page === 'analytics' && <AnalyticsView />}
      </div>
    </Layout>
  )
}

import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import ProjectsView from '../components/ProjectsView'
import MapView from '../components/MapView'
import AnalyticsView from '../components/AnalyticsView'
import { listProjects, listSites } from '../api'
import './EnergyPlannerDashboard.css'

const PAGE_META = {
  projects: {
    eyebrow: 'Energy Planner · Portfolio Planning',
    title: 'Projects & Sites',
  },
  map: {
    eyebrow: 'Energy Planner · Spatial Intelligence',
    title: 'Resource & Site Map',
  },
  analytics: {
    eyebrow: 'Energy Planner · Suitability Evaluation',
    title: 'Site Analytics & Rankings',
  },
}

export default function EnergyPlannerDashboard({ user, onLogout }) {
  const [page, setPage] = useState('projects')
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

  const meta = PAGE_META[page] || PAGE_META.projects

  return (
    <Layout
      user={user}
      onLogout={onLogout}
      activePage={page}
      onNavigate={setPage}
      eyebrow={meta.eyebrow}
      title={meta.title}
    >
      <div className="energy-planner-dashboard">
        {page === 'projects' && <ProjectsView user={user} />}
        {page === 'map' && <MapView sites={allSites} />}
        {page === 'analytics' && <AnalyticsView />}
      </div>
    </Layout>
  )
}

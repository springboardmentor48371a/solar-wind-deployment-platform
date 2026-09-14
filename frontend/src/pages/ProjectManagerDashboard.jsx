import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import ProjectsView from '../components/ProjectsView'
import MapView from '../components/MapView'
import AnalyticsView from '../components/AnalyticsView'
import { listProjects, listSites } from '../api'
import './ProjectManagerDashboard.css'

const PAGE_META = {
  projects: {
    eyebrow: 'Project Manager · Deployment Execution',
    title: 'Projects & Sites',
  },
  map: {
    eyebrow: 'Project Manager · Field Operations',
    title: 'Infrastructure Map',
  },
  analytics: {
    eyebrow: 'Project Manager · Performance Metrics',
    title: 'Site Analytics & Rankings',
  },
}

export default function ProjectManagerDashboard({ user, onLogout }) {
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
      <div className="project-manager-dashboard">
        {page === 'projects' && <ProjectsView user={user} />}
        {page === 'map' && <MapView sites={allSites} />}
        {page === 'analytics' && <AnalyticsView />}
      </div>
    </Layout>
  )
}

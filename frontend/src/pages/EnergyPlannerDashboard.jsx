import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import ProjectsView from '../components/ProjectsView'
import MapView from '../components/MapView'
import AnalyticsView from '../components/AnalyticsView'
import { listProjects, listSites } from '../api'

export default function EnergyPlannerDashboard({ user, onLogout }) {
  const [page, setPage] = useState('projects')
  const [allSites, setAllSites] = useState([])

  useEffect(() => { loadAllSites() }, [])

  const loadAllSites = async () => {
    const res = await listProjects()
    const sitesArr = await Promise.all(res.data.map(p => listSites(p.id).then(r => r.data)))
    setAllSites(sitesArr.flat())
  }

  return (
    <Layout user={user} onLogout={onLogout} activePage={page} onNavigate={setPage}>
      {page === 'projects' && <ProjectsView user={user} />}
      {page === 'map' && <MapView sites={allSites} />}
      {page === 'analytics' && <AnalyticsView />}
    </Layout>
  )
}

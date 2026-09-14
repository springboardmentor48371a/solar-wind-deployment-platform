import { useState, useEffect } from 'react'
import Layout from '../components/Layout'
import UsersView from '../components/UsersView'
import './AdminDashboard.css'

const PAGE_META = {
  projects: {
    eyebrow: 'Administrator · System Governance',
    title: 'Projects & Sites',
  },
  map: {
    eyebrow: 'Administrator · Global Coverage',
    title: 'Asset Map',
  },
  analytics: {
    eyebrow: 'Administrator · Enterprise Intelligence',
    title: 'Site Analytics & Rankings',
  },
  users: {
    eyebrow: 'Administrator · Access Governance',
    title: 'User Management',
  },
}

export default function AdminDashboard({ user, onLogout }) {
  const [page, setPage] = useState('users')
  const meta = PAGE_META[page] || PAGE_META.users

  return (
    <Layout
      user={user}
      onLogout={onLogout}
      activePage={page}
      onNavigate={setPage}
      eyebrow={meta.eyebrow}
      title={meta.title}
    >
      <div className="admin-dashboard">
        {page === 'users' && <UsersView />}
      </div>
    </Layout>
  )
}

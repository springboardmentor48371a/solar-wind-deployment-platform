'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '../lib/AuthContext'

const links = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/projects', label: 'Projects & Sites', icon: '🗂️' },
  { href: '/gis', label: 'GIS View', icon: '🗺️' },
  { href: '/alerts', label: 'Alerts', icon: '🔔' },
  { href: '/reports', label: 'Report Builder', icon: '📄' },
  { href: '/financial-analysis', label: 'Financial Analysis', icon: '💰' },
]

const adminLinks = [
  { href: '/admin/users', label: 'Users', icon: '👥' },
  { href: '/admin/integrations', label: 'Integrations', icon: '🔌' },
  { href: '/admin/audit-log', label: 'Audit Log', icon: '📋' },
]

const initials = (name = '') =>
  name.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('') || '?'

export default function Sidebar() {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const router = useRouter()

  if (!user) return null

  const isActive = (href) => pathname === href || pathname?.startsWith(href + '/')

  return (
    <nav className="fixed top-0 left-0 bottom-0 w-[236px] z-10 flex flex-col p-3.5 text-white bg-gradient-to-b from-[#0f2e1e] via-[#123a26] to-[#0f2e1e]">
      <div className="flex items-center gap-2.5 px-2 pb-5">
        <div className="w-8 h-8 rounded-[9px] bg-gradient-to-br from-[#3fae7c] to-brand flex items-center justify-center text-base shadow">☀️</div>
        <div className="font-bold text-[14.5px] leading-tight">
          Solstice OS
          <span className="block font-medium text-[10.5px] text-[#9dc2ac] uppercase tracking-wider">Deployment Intelligence</span>
        </div>
      </div>

      <div className="text-[10.5px] uppercase tracking-wider text-[#6f9c81] font-bold px-3 pt-3.5 pb-1.5">Overview</div>
      <div className="flex flex-col gap-0.5">
        {links.map((l) => (
          <Link key={l.href} href={l.href} className={`sidebar-link ${isActive(l.href) ? 'active' : ''}`}>
            <span>{l.icon}</span> {l.label}
          </Link>
        ))}
      </div>

      {user.role === 'Administrator' && (
        <>
          <div className="text-[10.5px] uppercase tracking-wider text-[#6f9c81] font-bold px-3 pt-3.5 pb-1.5">Administration</div>
          <div className="flex flex-col gap-0.5">
            {adminLinks.map((l) => (
              <Link key={l.href} href={l.href} className={`sidebar-link ${isActive(l.href) ? 'active' : ''}`}>
                <span>{l.icon}</span> {l.label}
              </Link>
            ))}
          </div>
        </>
      )}

      <div className="text-[10.5px] uppercase tracking-wider text-[#6f9c81] font-bold px-3 pt-3.5 pb-1.5">Account</div>
      <div className="flex flex-col gap-0.5">
        <Link href="/settings" className={`sidebar-link ${isActive('/settings') ? 'active' : ''}`}>
          <span>⚙️</span> Settings
        </Link>
      </div>

      <div className="mt-auto pt-3.5 border-t border-white/10">
        <div className="flex items-center gap-2.5 p-2 rounded-sm">
          <div className="w-[30px] h-[30px] rounded-full bg-white/10 flex items-center justify-center text-[12.5px] font-bold flex-shrink-0">
            {initials(user.full_name)}
          </div>
          <div className="min-w-0">
            <div className="text-[12.5px] font-semibold truncate">{user.full_name}</div>
            <div className="text-[11px] text-[#9dc2ac] truncate">{user.role}</div>
          </div>
        </div>
        <button
          className="btn-secondary btn-sm w-full mt-2.5 flex items-center justify-center gap-1.5"
          onClick={() => {
            logout()
            router.push('/login')
          }}
        >
          🚪 Sign out
        </button>
      </div>
    </nav>
  )
}

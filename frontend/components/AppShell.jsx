'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../lib/AuthContext'
import Sidebar from './Sidebar'

export default function AppShell({ title, subtitle, actions, children }) {
  const { user, loading, isImpersonating, adminStashUser, returnToAdmin } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  if (loading) {
    return <div className="max-w-5xl mx-auto px-7 py-14 text-ink-muted">Loading…</div>
  }
  if (!user) return null

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 min-w-0 ml-[236px]">
        {isImpersonating && (
          <div className="bg-amber text-white px-7 py-2.5 flex items-center justify-between gap-3 flex-wrap sticky top-0 z-30">
            <span className="text-[13px] font-medium">
              👁️ Viewing as <strong>{user.full_name}</strong> ({user.role})
              {adminStashUser && <> — signed in as {adminStashUser.full_name}</>}
            </span>
            <button
              className="text-[12.5px] font-semibold bg-white/20 hover:bg-white/30 transition rounded-sm px-3 py-1"
              onClick={async () => {
                await returnToAdmin()
                router.push('/admin/users')
              }}
            >
              ← Return to admin account
            </button>
          </div>
        )}
        <div className="max-w-[1080px] mx-auto px-7 pt-7 pb-14">
          {(title || actions) && (
            <div className="flex items-end justify-between gap-4 flex-wrap mb-5">
              <div>
                {title && <h2 className="text-[22px]">{title}</h2>}
                {subtitle && <p className="text-ink-muted text-[13.5px] mt-0.5">{subtitle}</p>}
              </div>
              {actions && <div className="flex gap-2.5 flex-wrap">{actions}</div>}
            </div>
          )}
          {children}
        </div>
      </div>
    </div>
  )
}

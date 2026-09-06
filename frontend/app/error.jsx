'use client'

import { useEffect } from 'react'
import Link from 'next/link'

export default function GlobalError({ error, reset }) {
  useEffect(() => {
    // Log to the browser console at minimum so the actual error isn't
    // silently swallowed — a real backend logging integration (Sentry,
    // etc.) can hook in here later without changing this component.
    console.error('Unhandled application error:', error)
  }, [error])

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[radial-gradient(1000px_500px_at_15%_-10%,#eaf5ee_0%,transparent_55%),radial-gradient(900px_500px_at_100%_110%,#e4f2ea_0%,transparent_55%)] bg-bg">
      <div className="text-center max-w-[440px]">
        <div className="w-[64px] h-[64px] rounded-2xl bg-red-50 border border-red-100 flex items-center justify-center text-3xl mx-auto mb-5">⚠️</div>
        <h1 className="text-2xl mb-2">Something went wrong</h1>
        <p className="text-ink-muted text-[14.5px] mb-6">
          An unexpected error occurred while loading this page. This has been logged —
          try again, or head back to your dashboard.
        </p>
        <div className="flex gap-2.5 justify-center flex-wrap">
          <button className="btn" onClick={() => reset()}>Try Again</button>
          <Link href="/dashboard"><button className="btn-secondary">Go to Dashboard</button></Link>
        </div>
      </div>
    </div>
  )
}

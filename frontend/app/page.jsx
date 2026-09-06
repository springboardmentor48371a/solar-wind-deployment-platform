'use client'

import Link from 'next/link'
import { useAuth } from '../lib/AuthContext'

const roles = [
  { name: 'Renewable Energy Planner', desc: 'Create projects, review recommended sites, and get investment guidance.' },
  { name: 'GIS Analyst', desc: 'Run terrain and environmental analysis, compare sites.' },
  { name: 'Project Manager', desc: 'Track every project\u2019s progress, feasibility, and timelines.' },
  { name: 'Investor / Developer', desc: 'Read-only portfolio visibility for investment decisions.' },
  { name: 'Government / Regulator', desc: 'Read-only compliance visibility across projects.' },
  { name: 'Administrator', desc: 'Manage users and oversee the full portfolio.' },
]

const whatYouCanDo = [
  'Register a site and get automatic environmental, terrain, and infrastructure analysis',
  'See a clear suitability score and category for every site \u2014 no guesswork',
  'Compare candidate sites side by side and export a report',
]

export default function Landing() {
  const { user } = useAuth()

  return (
    <div>
      <header className="sticky top-0 z-20 bg-white/90 backdrop-blur border-b border-border">
        <div className="max-w-[1120px] mx-auto px-7 py-3.5 flex items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-[34px] h-[34px] rounded-[9px] bg-gradient-to-br from-[#3fae7c] to-brand flex items-center justify-center text-base shadow">☀️</div>
            <div className="font-extrabold text-[15px] leading-tight">
              Solstice OS
              <span className="block font-medium text-[11px] text-ink-muted">Solar &amp; Wind Deployment Intelligence</span>
            </div>
          </div>

          <div className="flex gap-2 items-center">
            {user ? (
              <Link href="/dashboard"><button className="btn">Go to Dashboard</button></Link>
            ) : (
              <>
                <Link href="/login"><button className="btn-secondary btn-sm">Login</button></Link>
                <Link href="/register"><button className="btn btn-sm">Register</button></Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="py-16">
        <div className="max-w-[1120px] mx-auto px-7 grid md:grid-cols-2 gap-12 items-center">
          <div>
            <h1 className="text-[40px] leading-[1.12] mt-3.5 mb-4 tracking-tight">
              Find the best ground for your next solar &amp; wind project.
            </h1>
            <p className="text-ink-muted text-base leading-relaxed max-w-[560px]">
              Register a site and Solstice OS automatically analyzes weather, terrain, and
              infrastructure to give you a clear suitability score \u2014 so you can decide faster,
              with evidence behind every recommendation.
            </p>
            <ul className="mt-5 space-y-2">
              {whatYouCanDo.map((item) => (
                <li key={item} className="text-[13.5px] text-ink-muted flex gap-2">
                  <span className="text-brand">✓</span> {item}
                </li>
              ))}
            </ul>
            <div className="flex gap-3 mt-6 flex-wrap">
              {user ? (
                <Link href="/dashboard"><button className="btn px-6 py-3 text-sm">Open your dashboard →</button></Link>
              ) : (
                <>
                  <Link href="/register"><button className="btn px-6 py-3 text-sm">Create a free account</button></Link>
                  <Link href="/login"><button className="btn-secondary px-6 py-3 text-sm">Sign in</button></Link>
                </>
              )}
            </div>
          </div>

          <div className="card p-6">
            <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Example: Deployment Suitability Score</div>
            <div className="flex flex-col gap-2.5 mt-3">
              {[
                ['Renewable Resource Availability', 35],
                ['Geographic Suitability', 25],
                ['Infrastructure Accessibility', 15],
                ['Environmental Impact', 15],
                ['Economic Feasibility', 10],
              ].map(([label, pct]) => (
                <div key={label} className="grid grid-cols-[1fr_90px_34px] items-center gap-2.5 text-[12.5px] text-ink-muted">
                  <span>{label}</span>
                  <div className="h-2 bg-surface-2 rounded-full overflow-hidden border border-border">
                    <div className="h-full bg-gradient-to-r from-[#3fae7c] to-brand" style={{ width: `${pct}%` }} />
                  </div>
                  <b className="text-ink">{pct}%</b>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap gap-1.5 mt-4">
              <span className="badge cat-excellent">Excellent</span>
              <span className="badge cat-highly-suitable">Highly Suitable</span>
              <span className="badge cat-moderately-suitable">Moderate</span>
              <span className="badge cat-low-suitability">Low</span>
              <span className="badge cat-unsuitable">Unsuitable</span>
            </div>
          </div>
        </div>
      </section>

      <section id="roles" className="py-14 bg-surface border-y border-border">
        <div className="max-w-[1120px] mx-auto px-7">
          <h2 className="text-2xl">Pick the role that matches what you do</h2>
          <p className="text-ink-muted text-[14.5px] mb-6 mt-1">You'll choose one of these when you register.</p>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3.5">
            {roles.map((r) => (
              <div className="card-hover" key={r.name}>
                <h3 className="text-[14.5px]">{r.name}</h3>
                <p className="text-ink-muted text-[13.5px] mt-1.5">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="py-9 border-t border-border mt-5">
        <div className="max-w-[1120px] mx-auto px-7 flex items-center justify-between flex-wrap gap-3">
          <div className="text-ink-muted text-[13px]">© {new Date().getFullYear()} Solstice OS — Solar &amp; Wind Deployment Intelligence</div>
          {!user && (
            <div className="flex gap-2.5 flex-wrap">
              <Link href="/login"><button className="btn-secondary btn-sm">Login</button></Link>
              <Link href="/register"><button className="btn btn-sm">Register</button></Link>
            </div>
          )}
        </div>
      </footer>
    </div>
  )
}

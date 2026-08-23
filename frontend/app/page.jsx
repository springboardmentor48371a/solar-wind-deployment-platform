'use client'

import Link from 'next/link'
import { useAuth } from '../lib/AuthContext'

const roles = [
  { name: 'Renewable Energy Planner', desc: 'Creates projects, reviews recommended sites, generation forecasts, and investment guidance to decide where projects go next.' },
  { name: 'GIS Analyst', desc: 'Runs terrain, environmental, and infrastructure-proximity analysis on any project; produces comparison and terrain reports. Analysis-only — doesn\u2019t create or delete projects.' },
  { name: 'Project Manager', desc: 'Creates and tracks projects portfolio-wide: progress, feasibility reports, cost-benefit context, and deployment timelines.' },
  { name: 'Investor / Developer', desc: 'Read-only portfolio visibility across every project, for investment decisions.' },
  { name: 'Government / Regulator', desc: 'Read-only compliance visibility across every project.' },
  { name: 'Administrator', desc: 'Full portfolio access, user management, audit trail, and the ability to view the app as any other user.' },
]

const engines = [
  { name: 'Environmental Data Engine', desc: 'Live solar irradiance, temperature, rainfall and cloud-cover series from NASA POWER for every registered site.' },
  { name: 'Geographic Intelligence Engine', desc: 'Terrain via Rasterio/GDAL & Open-Elevation, plus roads, substations and transmission lines via OpenStreetMap, measured with GeoPandas/Shapely.' },
  { name: 'Site Suitability Scoring Engine', desc: 'A transparent, weighted rule-based score — Resource 35%, Geographic 25%, Infrastructure 15%, Environmental 15%, Economic 10%.' },
  { name: 'ML-Assisted Solar & Wind Prediction', desc: 'Random Forest models trained on real measured data — real Indian solar plant generation/weather sensors (Kaggle) and real Kelmarsh wind farm SCADA telemetry (Zenodo) — shown alongside, never replacing, the physics-based estimates above.' },
  { name: 'Suitability Quick-Classifier', desc: 'An ML model trained directly on the validated scoring formula gives an instant rough category estimate from ballpark inputs, before a site is even registered — a triage tool, not a replacement for the real score.' },
]

const dataSources = [
  'NASA POWER API — solar irradiance & climate',
  'NASA SRTM / Rasterio (GDAL) / Open-Elevation — terrain & elevation',
  'OpenStreetMap (Overpass API) — roads, substations, transmission lines',
  'PostgreSQL + PostGIS — structured, geospatial storage',
  'MongoDB — raw external-API payload archive',
]

const actions = [
  'Create projects & register sites', 'Run environmental & terrain analysis', 'Compare multiple sites side by side',
  'View suitability scores & rankings', 'Generate PDF / Excel reports', 'Manage users & review audit logs',
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

          <div className="hidden md:flex gap-5">
            <a href="#platform" className="text-ink-muted text-[13.5px] font-semibold hover:text-brand">Platform</a>
            <a href="#roles" className="text-ink-muted text-[13.5px] font-semibold hover:text-brand">Roles</a>
            <a href="#architecture" className="text-ink-muted text-[13.5px] font-semibold hover:text-brand">Architecture</a>
            <a href="#data" className="text-ink-muted text-[13.5px] font-semibold hover:text-brand">Data Sources</a>
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
            <span className="badge">Physics engine + ML-assisted predictions</span>
            <h1 className="text-[40px] leading-[1.12] mt-3.5 mb-4 tracking-tight">
              Find the best ground for your next solar &amp; wind project.
            </h1>
            <p className="text-ink-muted text-base leading-relaxed max-w-[560px]">
              Solstice OS is a Solar &amp; Wind Deployment Intelligence Platform that recommends
              optimal renewable energy sites by analyzing environmental, geographic, climatic, and
              infrastructure data — combining a transparent physics engine with a trained ML-assisted
              prediction layer — so planners, analysts, and investors can make faster, defensible
              decisions.
            </p>
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
            <div className="mt-5 text-[12.5px] text-ink-faint max-w-[520px] leading-relaxed">
              Built for renewable energy companies, government agencies, utility providers,
              environmental organizations, infrastructure planners, and sustainability consultants.
            </div>
          </div>

          <div className="card p-6">
            <div className="text-xs font-semibold uppercase tracking-wide text-ink-muted mb-1">Deployment Suitability Score</div>
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

      <section id="platform" className="py-14 bg-surface border-y border-border">
        <div className="max-w-[1120px] mx-auto px-7">
          <h2 className="text-2xl">What the platform does</h2>
          <p className="text-ink-muted text-[14.5px] mb-6 max-w-xl mt-1">
            Register a project and its candidate sites, and Solstice OS automatically gathers the
            environmental and geographic signal that matters for renewable deployment — then scores,
            ranks, and reports on it.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
            {engines.map((e) => (
              <div className="card-hover" key={e.name}>
                <div className="flex items-center justify-between">
                  <h3 className="text-[14.5px]">{e.name}</h3>
                  {e.beta && <span className="badge badge-amber">Beta</span>}
                </div>
                <p className="text-ink-muted text-[13.5px] mt-1.5">{e.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="roles" className="py-14">
        <div className="max-w-[1120px] mx-auto px-7">
          <h2 className="text-2xl">Users &amp; roles</h2>
          <p className="text-ink-muted text-[14.5px] mb-6 mt-1">Role-based access control keeps every user scoped to what they need.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5">
            {roles.map((r) => (
              <div className="card-hover" key={r.name}>
                <h3 className="text-[14.5px]">{r.name}</h3>
                <p className="text-ink-muted text-[13.5px] mt-1.5">{r.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="architecture" className="py-14 bg-surface border-y border-border">
        <div className="max-w-[1120px] mx-auto px-7">
          <h2 className="text-2xl">How it&apos;s built</h2>
          <p className="text-ink-muted text-[14.5px] mb-6 mt-1">Every layer from the architecture diagram, wired end-to-end.</p>
          <div className="grid md:grid-cols-2 gap-3.5">
            <div className="card">
              <h3>Access channels &amp; user actions</h3>
              <p className="text-ink-muted text-[13.5px]">
                Available today via the web application, with a documented API for third-party integrations. Typical actions:
              </p>
              <ul className="list-disc pl-[18px] text-ink-muted text-[13.5px] leading-loose mt-2">
                {actions.map((a) => <li key={a}>{a}</li>)}
              </ul>
            </div>
            <div className="card">
              <h3>Platform layers</h3>
              <ul className="list-disc pl-[18px] text-ink-muted text-[13.5px] leading-loose">
                <li><b className="text-ink">API Gateway</b> — FastAPI, JWT auth, rate limiting, CORS, security headers</li>
                <li><b className="text-ink">Microservices</b> — user &amp; access, project &amp; site, environmental data, GIS/spatial, suitability &amp; scoring, alerts, reports</li>
                <li><b className="text-ink">Data layer</b> — PostgreSQL + PostGIS (primary, structured/geospatial) and MongoDB (secondary, raw payload archive)</li>
                <li><b className="text-ink">ML-assisted prediction layer</b> — 3 trained Random Forest models: solar and wind trained on real measured plant/turbine data (Kaggle, Zenodo), suitability quick-classifier trained on the platform's own validated formula, all run alongside the deterministic physics engine above</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section id="data" className="py-14">
        <div className="max-w-[1120px] mx-auto px-7">
          <h2 className="text-2xl">External services &amp; data sources</h2>
          <p className="text-ink-muted text-[14.5px] mb-6 mt-1">Real, live pipelines — not mock data.</p>
          <div className="card">
            <ul className="list-disc pl-[18px] text-ink-muted text-[13.5px] leading-loose columns-1 sm:columns-2">
              {dataSources.map((d) => <li key={d}>{d}</li>)}
            </ul>
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

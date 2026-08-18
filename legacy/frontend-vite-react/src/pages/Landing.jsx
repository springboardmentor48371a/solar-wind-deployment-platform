import React from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../AuthContext'

const Section = ({ id, children, alt }) => (
  <section id={id} className={`land-section${alt ? ' land-section-alt' : ''}`}>
    <div className="land-wrap">{children}</div>
  </section>
)

const roles = [
  {
    name: 'Renewable Energy Planner',
    desc: 'Reviews recommended sites, generation forecasts, and investment guidance to decide where projects go next.',
  },
  {
    name: 'GIS Analyst',
    desc: 'Runs terrain, environmental, and infrastructure-proximity analysis; produces comparison and terrain reports.',
  },
  {
    name: 'Project Manager',
    desc: 'Tracks project progress, feasibility reports, cost-benefit context, and deployment timelines.',
  },
  {
    name: 'Administrator',
    desc: 'Manages users and roles, monitors platform activity, data sources, and the security audit trail.',
  },
]

const engines = [
  { name: 'Environmental Data Engine', desc: 'Pulls live solar irradiance, temperature, rainfall and cloud-cover series from NASA POWER for every registered site.' },
  { name: 'Geographic Intelligence Engine', desc: 'Terrain (elevation, slope) via NASA/Open-Elevation, plus roads, substations, transmission lines and water bodies via OpenStreetMap/Overpass.' },
  { name: 'Site Suitability Scoring Engine', desc: 'A transparent, weighted rule-based score — Resource 35%, Geographic 25%, Infrastructure 15%, Environmental 15%, Economic 10% — sorting sites into Excellent → Unsuitable.' },
  { name: 'Deployment Optimization & Forecasting', desc: 'Reserved for the AI/ML phase — solar & wind prediction models, energy forecasting, and hybrid deployment optimization plug in here next.', comingSoon: true },
]

const dataSources = [
  'NASA POWER API — solar irradiance & climate',
  'NASA SRTM / Open-Elevation — terrain & elevation',
  'OpenStreetMap (Overpass API) — roads, substations, transmission lines',
  'Global Wind Atlas & OpenWeather — wind & weather (roadmap)',
  'Copernicus Sentinel Hub — satellite land-cover (roadmap)',
]

const actions = [
  'Create projects & register sites', 'Run environmental & terrain analysis', 'Compare multiple sites side by side',
  'View suitability scores & rankings', 'Generate PDF / Excel reports', 'Manage users & review audit logs',
]

export default function Landing() {
  const { user } = useAuth()

  return (
    <div className="land">
      <header className="land-nav">
        <div className="land-nav-inner">
          <div className="land-brand">
            <div className="land-brand-mark">☀️</div>
            <div className="land-brand-text">
              Solstice OS
              <span>Solar &amp; Wind Deployment Intelligence</span>
            </div>
          </div>

          <div className="land-nav-links">
            <a href="#platform">Platform</a>
            <a href="#roles">Roles</a>
            <a href="#architecture">Architecture</a>
            <a href="#data">Data Sources</a>
          </div>

          <div className="land-nav-auth">
            {user ? (
              <Link to="/dashboard"><button>Go to Dashboard</button></Link>
            ) : (
              <>
                <Link to="/login"><button className="secondary sm">Login</button></Link>
                <Link to="/register"><button className="sm">Register</button></Link>
              </>
            )}
          </div>
        </div>
      </header>

      <section className="land-hero">
        <div className="land-wrap land-hero-grid">
          <div>
            <span className="badge">Pre-AI phase &middot; AI/ML forecasting layer coming next</span>
            <h1>Find the best ground for your next solar &amp; wind project.</h1>
            <p className="land-lead">
              Solstice OS is an AI-ready Solar &amp; Wind Deployment Intelligence Platform that recommends
              optimal renewable energy sites by analyzing environmental, geographic, climatic, and
              infrastructure data — so planners, analysts, and investors can make faster, defensible
              decisions.
            </p>
            <div className="land-cta-row">
              {user ? (
                <Link to="/dashboard"><button>Open your dashboard →</button></Link>
              ) : (
                <>
                  <Link to="/register"><button>Create a free account</button></Link>
                  <Link to="/login"><button className="secondary">Sign in</button></Link>
                </>
              )}
            </div>
            <div className="land-audience">
              Built for renewable energy companies, government agencies, utility providers,
              environmental organizations, infrastructure planners, and sustainability consultants.
            </div>
          </div>

          <div className="land-hero-card card">
            <div className="stat-label">Deployment Suitability Score</div>
            <div className="land-score-bars">
              <div className="land-score-row"><span>Renewable Resource Availability</span><div className="land-bar"><div style={{ width: '35%' }} /></div><b>35%</b></div>
              <div className="land-score-row"><span>Geographic Suitability</span><div className="land-bar"><div style={{ width: '25%' }} /></div><b>25%</b></div>
              <div className="land-score-row"><span>Infrastructure Accessibility</span><div className="land-bar"><div style={{ width: '15%' }} /></div><b>15%</b></div>
              <div className="land-score-row"><span>Environmental Impact</span><div className="land-bar"><div style={{ width: '15%' }} /></div><b>15%</b></div>
              <div className="land-score-row"><span>Economic Feasibility</span><div className="land-bar"><div style={{ width: '10%' }} /></div><b>10%</b></div>
            </div>
            <div className="land-cats">
              <span className="badge cat-excellent">Excellent</span>
              <span className="badge cat-highly-suitable">Highly Suitable</span>
              <span className="badge cat-moderately-suitable">Moderate</span>
              <span className="badge cat-low-suitability">Low</span>
              <span className="badge cat-unsuitable">Unsuitable</span>
            </div>
          </div>
        </div>
      </section>

      <Section id="platform" alt>
        <h2>What the platform does</h2>
        <p className="land-sub">
          Register a project and its candidate sites, and Solstice OS automatically gathers the
          environmental and geographic signal that matters for renewable deployment — then scores,
          ranks, and reports on it.
        </p>
        <div className="grid grid-4 land-engine-grid">
          {engines.map((e) => (
            <div className="card land-engine-card" key={e.name}>
              <div className="row-between">
                <h3>{e.name}</h3>
                {e.comingSoon && <span className="badge badge-amber">AI phase</span>}
              </div>
              <p className="muted" style={{ fontSize: 13.5 }}>{e.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="roles">
        <h2>Users &amp; roles</h2>
        <p className="land-sub">Role-based access control keeps every user scoped to what they need.</p>
        <div className="grid grid-4">
          {roles.map((r) => (
            <div className="card" key={r.name}>
              <h3>{r.name}</h3>
              <p className="muted" style={{ fontSize: 13.5 }}>{r.desc}</p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="architecture" alt>
        <h2>How it's built</h2>
        <p className="land-sub">Every layer from the architecture diagram, wired end-to-end.</p>
        <div className="grid grid-2">
          <div className="card">
            <h3>Access channels &amp; user actions</h3>
            <p className="muted" style={{ fontSize: 13.5 }}>
              Available today via the web application, with a documented API for third-party
              integrations. Typical actions:
            </p>
            <ul className="land-list">
              {actions.map((a) => <li key={a}>{a}</li>)}
            </ul>
          </div>
          <div className="card">
            <h3>Platform layers</h3>
            <ul className="land-list">
              <li><b>API Gateway</b> — FastAPI, JWT auth, rate limiting, CORS, security headers</li>
              <li><b>Microservices</b> — user &amp; access, project &amp; site, environmental data, GIS/spatial, suitability &amp; scoring, alerts, reports</li>
              <li><b>Data layer</b> — PostgreSQL/PostGIS (or SQLite for local dev), with an audit log for every sensitive action</li>
              <li><b>AI/ML layer</b> — reserved interface for the upcoming prediction &amp; optimization models</li>
            </ul>
          </div>
        </div>
      </Section>

      <Section id="data">
        <h2>External services &amp; data sources</h2>
        <p className="land-sub">Real, live pipelines — not mock data.</p>
        <div className="card">
          <ul className="land-list land-list-2col">
            {dataSources.map((d) => <li key={d}>{d}</li>)}
          </ul>
        </div>
      </Section>

      <footer className="land-footer">
        <div className="land-wrap row-between">
          <div className="muted" style={{ fontSize: 13 }}>© {new Date().getFullYear()} Solstice OS — Solar &amp; Wind Deployment Intelligence</div>
          {!user && (
            <div className="btn-row">
              <Link to="/login"><button className="secondary sm">Login</button></Link>
              <Link to="/register"><button className="sm">Register</button></Link>
            </div>
          )}
        </div>
      </footer>
    </div>
  )
}

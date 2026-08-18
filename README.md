# Solstice OS — Solar & Wind Deployment Intelligence Platform

A full-stack platform that helps identify, evaluate, and rank locations
for solar and wind energy projects by combining real geospatial,
climate, terrain, infrastructure, and financial data — built to the
specification in `AI_Solar___Wind_Deployment_Intelligence_Platform.pdf`.

**Scope note:** every module in the spec is implemented **except the
AI/ML prediction layer** (XGBoost / TensorFlow / PyTorch forecasting
models), which was intentionally left out of this phase. Everywhere the
spec called for a prediction, this platform uses deterministic,
explainable formulas instead (e.g. a weighted suitability score, a
physics-based power-output simulation, a standard NPV/IRR/LCOE financial
model) — real calculations against real data, just not machine-learned
ones.

---

## What's actually implemented

### 1. Authentication & Access Control
- JWT authentication (access + refresh tokens, automatic silent refresh)
- Role-based access control across 6 roles, each with a genuinely
  different action set — not the same buttons re-labeled per role
- Self-service registration for Renewable Energy Planner, Investor /
  Developer, and Government / Regulator
- Staff-PIN-gated registration and login for GIS Analyst, Project
  Manager, and Administrator (a shared secret on top of each person's
  own password — see **Security** below)
- Admin "view as" — impersonate any non-admin user to reproduce a
  support issue, fully audit-logged

### 2. Project & Site Management
- Project creation, site registration, region management (a real
  entity with a bounding box, not a free-text field), site comparison,
  full ingestion-log visibility per site
- Site fields matching the spec exactly: coordinates, land area,
  elevation, existing infrastructure notes, land ownership, region

### 3. Environmental & Geographic Data Collection (all real, live APIs)
| Source | Provides |
|---|---|
| NASA POWER | Solar irradiance, wind speed (10m + 50m), temperature, rainfall, cloud cover |
| OpenStreetMap (Overpass) | Roads, transmission lines, substations, urban areas, water bodies |
| Open-Elevation / SRTM-style terrain | Elevation, land slope |
| Copernicus Sentinel Hub | Satellite imagery summary, land cover, NDVI, cloud cover (optional — needs a free API key) |
| World Bank Open Data | Country demographic/economic context (population density, GDP per capita) |
| OpenWeather + NOAA | Live current-conditions weather cross-check, kept separate from the historical NASA POWER data used for scoring |

Every connector degrades gracefully: missing credentials or an upstream
outage never crashes a request, it just reports "not configured" or
skips that step.

### 4. Solar & Wind Potential Engines
- Solar: panel efficiency, shading loss, peak sun hours, capacity
  factor, expected annual output
- Wind: turbine class suitability, turbulence intensity, capacity
  factor, expected annual energy production (AEP)

### 5. Site Suitability Intelligence Engine
The spec's exact weighted formula:

```
Deployment Suitability Score =
  Renewable Resource Availability   35%
  Geographic Suitability            25%
  Infrastructure Accessibility      15%
  Environmental Impact              15%
  Economic Feasibility              10%
```
mapped to 5 categories: Excellent, Highly Suitable, Moderately
Suitable, Low Suitability, Unsuitable.

### 6. Investment Analytics
Real financial modeling: NPV, IRR, LCOE, and payback period, computed
from user-supplied CapEx/OpEx/tariff assumptions plus the site's
computed energy output.

### 7. Power System Simulation
Deterministic hourly output-profile generator (solar: sine-shaped
diurnal curve; wind: capacity-factor-driven with realistic variance) —
"what would this site produce," without needing anything actually built
yet.

### 8. SCADA / IoT Telemetry
Ingestion endpoint for live operational readings from a deployed site's
own monitoring system, plus a query API by metric/time range.

### 9. Integrations
Generic webhook connectors for the 5 categories the spec lists
(financial modeling, project management, SCADA/IoT, power simulation,
third-party analytics) — register any compatible endpoint, and it fires
automatically on real platform events (a new suitability score, a new
alert), not just on manual test.

### 10. Custom Report Builder
Pick-your-own-sections PDF reports, a fixed executive-summary template,
and saved/reusable report templates — on top of the original fixed-format
PDF/Excel site-assessment exports.

### 11. Dashboards — genuinely different per role
- **Planner**: ranked recommended sites, energy forecasts, investment signal
- **GIS Analyst**: GIS map, terrain maps, environmental analytics, site comparison report
- **Project Manager**: portfolio-wide feasibility & cost-benefit (NPV/IRR/LCOE)
- **Administrator**: connector health, warehouse refresh, user/integration/audit management
- **Investor/Developer & Government/Regulator**: read-only portfolio oversight

### 12. Notifications & Alerts
Weather alerts, suitability-score-change alerts, automatically dispatched
to any connected integration webhook.

### 13. Infrastructure & Platform Engineering
- **PostgreSQL + PostGIS** (primary DB) and **MongoDB** (raw payload archive)
- **Redis** cache (graceful in-process fallback if unreachable)
- **TimescaleDB** hypertables for time-series data (auto-enabled if the extension is available)
- **S3-compatible data lake** for durable raw-payload archival (optional)
- **Data warehouse** — a denormalized rollup table + optional Parquet export for BI queries
- **Prometheus `/metrics`** endpoint + optional Sentry error tracking
- **Automated backups** (Postgres `pg_dump` + Mongo per-collection export, daily, with retention pruning)
- **Audit logging** on every sensitive action
- **Rate limiting** and security headers on every response
- Full **Docker Compose** deployment — one command, 6 containers

---

## Roles & Permissions

| Role | Create/edit projects | Run analysis | Read scope |
|---|---|---|---|
| Renewable Energy Planner | Own projects only | Own projects only | Own projects only |
| GIS Analyst | No | **Any** project | Every project |
| Project Manager | Any project | Any project | Every project |
| Administrator | Any project | Any project | Every project + user/integration/audit management |
| Investor / Developer | No | No | Every project (read-only) |
| Government / Regulator | No | No | Every project (read-only) |

Every one of these rules is enforced **server-side** on every request —
the frontend hiding a button is a UX nicety, not the actual security
boundary.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | JavaScript, Next.js, Tailwind CSS |
| Primary database | PostgreSQL + PostGIS (+ TimescaleDB) |
| Secondary database | MongoDB |
| Cache | Redis |
| GIS & Remote Sensing | GDAL, Rasterio, GeoPandas, Shapely, PyProj |
| Data analytics | Pandas, NumPy, PyArrow |
| Visualization | Plotly, Leaflet.js |
| Auth | JWT (access + refresh) |
| Monitoring | Prometheus, optional Sentry |
| DevOps | Docker, Docker Compose |

---

## Getting Started (Docker — recommended)

Requires Docker Desktop with WSL2 (Windows) or Docker Desktop (Mac/Linux).

```bash
# .env is already included with generated secrets — just run:
docker compose up --build
```

This starts 6 containers: `db` (Postgres+PostGIS), `mongo`, `redis`,
`backend` (FastAPI on `http://localhost:8000`, docs at `/docs`),
`frontend` (Next.js on `http://localhost:3000`), and `backup`.

Register an account at `http://localhost:3000/register`. For a staff
role (GIS Analyst / Project Manager / Administrator), you'll need the
staff PIN — see `STAFF_PIN` in your `.env` file.

Optional external connectors (satellite imagery, live weather
cross-check, S3 archival) are documented in `.env.example` — the
platform runs fully without any of them.

---

## Project Structure

```
backend/app/
  main.py              FastAPI app, middleware, router wiring
  models.py             SQLAlchemy models (PostGIS-aware)
  schemas.py             Pydantic request/response schemas
  auth.py / authz.py / security.py    JWT auth, per-request ownership checks, rate limiting
  services/               One file per data connector / calculation engine
    environmental.py, terrain.py, infrastructure.py, satellite.py,
    land_data.py, supplemental_weather.py   → data collection
    solar_engine.py, wind_engine.py, scoring.py, financial.py,
    power_simulation.py                     → calculation engines
    alerting.py, integration_dispatch.py    → notifications & webhooks
  routers/                One file per resource (projects, sites, gis,
                           reports, integrations, analytics, admin, ...)
  data_lake.py, warehouse.py     S3 archival + BI rollup layer

frontend/app/            Next.js App Router pages
  dashboard/              Role-specific dashboards
  projects/, gis/, reports/, alerts/, admin/
frontend/lib/             API client, auth context, role permission helpers
frontend/components/      Shared layout, Leaflet map
```

---

## Testing

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Covers auth, RBAC/IDOR protection, the suitability-scoring formula, the
newly-wired site intelligence pipeline (satellite/environmental/solar/
wind/financial), integration event dispatch, report generation, and the
data-source health check — all against an isolated SQLite DB per test
run with deterministic stand-ins for every external API, so it needs no
network access to run.

---

## Security

- Staff roles require a shared PIN (`STAFF_PIN`) on top of each
  person's own password, both at registration and every login —
  **change the default value before any real deployment**
- Every project/site-scoped endpoint checks per-request ownership
  server-side (prevents IDOR — one user reading/writing another user's
  data by guessing an ID)
- Passwords hashed with bcrypt; login uses a constant-time comparison
  path to avoid timing-based email enumeration
- Containers run as a non-root user
- Security headers (clickjacking/MIME-sniffing protection) on both the
  API and the Next.js frontend
- Rate limiting on auth endpoints
- MongoDB and Postgres both require credentials (no anonymous access)

---

## Acknowledgments

This project was built with the assistance of **Claude** (Anthropic),
used as an AI pair-programmer throughout development — architecture
decisions, implementation, debugging real Docker/build failures, and
this documentation were all done collaboratively with Claude across the
course of the project.

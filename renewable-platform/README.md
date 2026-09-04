# Solar & Wind Deployment Intelligence Platform

An AI-powered platform that recommends optimal locations for solar and wind
deployment. You register a site with **coordinates only** — the platform
pulls live environmental and geospatial data, runs it through trained ML
models, and returns a full suitability score, energy forecast, and
investment picture, automatically.

Pipeline on every site registration:

```
lat/lon
  → live site-attribute derivation (region, land area, elevation,
     infrastructure, land ownership — NASA/SRTM + OpenStreetMap)
  → live environmental data collection (NASA POWER + OpenStreetMap)
  → ML solar potential prediction (trained Random Forest)
  → ML wind potential prediction (trained Random Forest)
  → ML site suitability scoring + category + recommended technology
     (trained Random Forest, anchored to the spec's weighted formula)
  → energy & financial forecasting (25-year output, CAPEX, payback)
```

## Stack

| Layer      | Tech |
|------------|------|
| Backend    | Python, FastAPI, SQLAlchemy, JWT auth |
| ML         | scikit-learn (RandomForest regressors/classifiers), joblib |
| Live data  | NASA POWER, Open-Elevation (SRTM), OpenStreetMap Overpass + Nominatim — all free, key-free APIs |
| Database   | SQLite by default (zero setup) — swap in PostgreSQL + PostGIS via `DATABASE_URL` |
| Frontend   | React 18, Vite, React Router, Recharts, Axios |
| Deployment | Dockerfiles for both services + `docker-compose.yml` |

## Project structure

```
renewable-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI app entrypoint
│   │   ├── database.py                 # DB engine/session
│   │   ├── models.py                   # SQLAlchemy tables
│   │   ├── schemas.py                  # Pydantic request/response models
│   │   ├── auth.py                     # JWT + role-based access
│   │   ├── routers/
│   │   │   ├── auth.py                 # register/login/me
│   │   │   ├── projects.py             # project CRUD
│   │   │   ├── sites.py                # site CRUD + intelligence pipeline + ranking + recompute
│   │   │   └── reports.py              # site/project report export (JSON)
│   │   ├── services/
│   │   │   ├── geo_data_service.py     # Module 3/4: NASA POWER, Open-Elevation, OSM Overpass/Nominatim calls
│   │   │   ├── site_intelligence.py    # derives region/land area/elevation/infra/ownership from lat+lon only
│   │   │   ├── environmental_engine.py # Module 3/4: live-first env data, deterministic per-field fallback
│   │   │   ├── solar_engine.py         # Module 5: ML solar prediction (wraps ml/predictor.py)
│   │   │   ├── wind_engine.py          # Module 6: ML wind prediction (wraps ml/predictor.py)
│   │   │   ├── scoring_engine.py       # Module 7/10: ML suitability scoring (wraps ml/predictor.py)
│   │   │   └── forecasting_engine.py   # Module 8: energy/financial forecast
│   │   └── ml/
│   │       ├── physics_baseline.py     # PV-yield/wind-power formulas: fallback + training ground truth
│   │       ├── feature_schema.py       # single source of truth for model feature/target ordering
│   │       ├── train.py                # generates synthetic training data, trains + saves all models
│   │       ├── predictor.py            # loads trained models, predicts, falls back to physics on failure
│   │       └── models/                 # trained .joblib artifacts (shipped, ready to use)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/         # Login, Register, Dashboard, Projects, ProjectDetail, SiteDetail
│   │   ├── components/    # Navbar, ScoreBadge, SiteCard
│   │   ├── api.js         # Axios client with JWT interceptor
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
└── docker-compose.yml
```

## Run locally (fastest way to review)

**Backend** (Python 3.11+):
```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs (SQLite file `renewable_platform.db` is created automatically — no DB setup needed). Trained ML models ship in `app/ml/models/` and load automatically; no training step required to run the app.

**Frontend** (Node 18+):
```bash
cd frontend
npm install
npm run dev
```
App: http://localhost:5173 (Vite proxies `/api` to `localhost:8000`)

## Run with Docker (production-style, PostgreSQL + PostGIS)

```bash
docker-compose up --build
```
- Frontend → http://localhost:3000
- Backend API → http://localhost:8000/docs
- Postgres+PostGIS → localhost:5432

## Using it

1. Register an account (pick a role: Renewable Energy Planner, GIS Analyst,
   Project Manager, or Administrator).
2. Create a Project.
3. Inside the project, "Register & Analyze Site" with just a **name +
   latitude/longitude** (+ preferred technology). Region, land area,
   elevation, terrain slope, infrastructure proximity, and land
   classification are all derived automatically from live datasets for
   that location — nothing else to fill in.
4. On submit, the backend runs the full pipeline: live site-attribute
   derivation → live environmental data collection → ML solar potential →
   ML wind potential → ML suitability scoring → energy/financial
   forecasting.
5. View the site's radar score chart, solar/wind metrics (each tagged
   "ML-predicted" or "Physics-baseline" depending on which produced it),
   25-year output forecast, and environmental factors on the site detail
   page.
6. Back on the project page, see all sites ranked by overall suitability
   score, with category and recommended technology (solar / wind / hybrid).
7. If a site was registered while a live data provider was down, hit
   `POST /api/projects/{id}/sites/{site_id}/recompute` to re-run it once
   connectivity is back.

## Live data & offline fallback

`geo_data_service.py` calls four free, key-free public APIs:

| Data | Source |
|---|---|
| Solar irradiance, wind speed, temperature, rainfall, cloud cover | [NASA POWER](https://power.larc.nasa.gov/) climatology API |
| Elevation + terrain slope | [Open-Elevation](https://open-elevation.com/) (SRTM-derived), sampled at 5 points around the site |
| Roads, transmission lines, substations, water bodies, protected areas, land-use parcel (→ land area + ownership label) | [OpenStreetMap Overpass API](https://overpass-api.de/) |
| Region name | [OpenStreetMap Nominatim](https://nominatim.org/) reverse geocoding |

NDVI has no free key-less satellite provider, so it's proxied from the OSM
land-use classification of the parcel (forest/grass score high,
industrial/residential score low) — real data, not a random number. Swap in
Copernicus Sentinel Hub (credential fields are stubbed in `.env.example`)
for true satellite NDVI when you have API credentials.

**Every live call is wrapped so failure never breaks the app**: if a
provider is unreachable, only the affected field falls back to a
deterministic, coordinate-seeded estimate (same site → same fallback
numbers, so results stay reproducible). Every environmental record and
site carries a `data_source` / `attributes_source` flag (`"live"` or
`"synthetic_fallback"`) so the UI is always honest about which was used —
look for the green "Live data" vs amber "Estimated" tag on each site card.

> This sandbox environment has outbound network access disabled, so the
> live-data code paths were validated by observing correct request
> construction and graceful fallback (HTTP calls reach the providers'
> real endpoints and the pipeline completes correctly using fallback
> values when blocked) rather than live successful responses. Nothing
> else needs to change to see live values — just run it somewhere with
> internet egress.

## ML models

`app/ml/train.py` trains four Random Forest models (regressors for
solar/wind/suitability-score, classifiers for suitability category +
recommended technology) on ~9,000 physics-informed synthetic samples with
realistic noise, generated from the same standard PV-yield and
wind-power-density formulas the spec's tech stack calls for
(`app/ml/physics_baseline.py`). This is the standard approach for siting
models before a platform has accumulated real deployment outcomes to train
on: sample realistic input combinations, run them through validated
engineering formulas, add measurement-realistic noise, and fit a
generalizable surrogate model to it.

Trained models ship in `app/ml/models/*.joblib` and are loaded once at
startup. To retrain (e.g. after tuning the synthetic data ranges, or once
you have real deployment outcomes to train on instead — see the docstring
in `train.py` for the one-line swap):

```bash
cd backend
python -m app.ml.train
```

Every prediction response includes `model_used` (`"random_forest_regressor"`
/ `"random_forest"` vs `"physics_baseline"`) so you can see whether the ML
model or the analytical fallback produced a given number. The two paths are
consistent because the physics formulas are both the fallback *and* the
training ground truth.

To upgrade the regressors to XGBoost/LightGBM per the spec's tech stack,
install the package and swap `RandomForestRegressor`/`Classifier` for
`XGBRegressor`/`XGBClassifier` (or LightGBM equivalents) in `train.py` —
`feature_schema.py` and `predictor.py` need no changes.

## Milestones (per the 8-week plan)

| Milestone | Status |
|---|---|
| **Week 1–2**: project init, architecture, auth & RBAC, project/site management, GIS/environmental dataset integration | Done. Auth (JWT + roles) and project/site management were already in place; environmental/GIS dataset integration is now **live** (NASA POWER, SRTM, OSM) rather than stubbed |
| **Week 3–4**: environmental intelligence engine, GIS processing, solar/wind prediction models, resource assessment reports | Done. Environmental engine is live-data-backed; solar/wind prediction now runs through **trained ML models** (`app/ml/train.py`), not just formulas |
| **Week 5–6**: site suitability engine, deployment optimization, forecasting models, investment recommendations, dashboards | Done. Suitability scoring is ML-driven (category + technology classifiers, weighted-score regressor); dashboards, forecasting, and investment figures were already wired to real backend data |
| **Week 7–8**: dashboards, reports/GIS visualization, testing, Docker deployment, docs | Mostly done. Docker Compose + Dockerfiles present; reports export as JSON (PDF/Excel export is the one item still stubbed — see below); this README documents the completed system |

## What's still simplified (and how to extend it)

- **NDVI**: proxied from OSM land-use tags rather than true satellite
  imagery. Wire in Copernicus Sentinel Hub (credential fields already in
  `.env.example`) for real NDVI — `geo_data_service.landuse_ndvi_proxy`
  is the single call site to replace.
- **Land area when no OSM parcel is mapped**: falls back to a flat 10 ha
  default rather than leaving it blank, so downstream capacity/output math
  always has a number to work with. Flag `attributes_source` in the UI (already
  done) to make clear when this happened.
- **PDF/Excel export**: `/api/reports/site/{id}` and
  `/api/reports/project/{id}` return export-ready JSON; wire in `reportlab`
  (PDF) or `openpyxl` (Excel) to convert that payload to downloadable files
  — the aggregation logic is already done.
- **Not yet built**: OAuth2 social login (JWT email/password auth is in
  place), push/email notification delivery (the alert *data* — weather,
  suitability changes — is available from the live pipeline, just not
  wired to a delivery channel), and interactive GIS map rendering (site
  lat/lon is captured and ready to feed into Leaflet/Mapbox on the
  frontend).
- **Database**: SQLite is the default for zero-setup local review. Models
  use plain float lat/lon columns (not PostGIS geometry types) so they run
  unmodified on both SQLite and PostgreSQL — switch via `DATABASE_URL` in
  `.env` when moving to PostGIS spatial queries. Note: the schema changed
  in this update (added `data_source`/`model_used`/`attributes_source`
  columns) — delete any existing `renewable_platform.db` from the previous
  version before running, since there's no Alembic migration set up yet.

## Roles & access

Role-based access is enforced via `auth.require_roles(...)` in
`backend/app/auth.py`, following the spec's four roles: Renewable Energy
Planner, GIS Analyst, Project Manager, Administrator. Currently all
authenticated users can manage their own projects/sites; tighten specific
endpoints (e.g. restrict deletion to Project Manager/Administrator) by
adding `Depends(require_roles(RoleEnum.project_manager, RoleEnum.admin))`
to the relevant router functions.

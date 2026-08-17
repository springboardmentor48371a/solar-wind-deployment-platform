# Solar & Wind Deployment Intelligence Platform

A working scaffold of the AI-powered renewable energy deployment platform,
built from the workflow spec: user auth → project/site creation →
environmental & GIS data → solar/wind prediction → suitability scoring →
energy forecasting → deployment recommendations & dashboards.

This is a **functional MVP**, not a stub — every screen calls real backend
endpoints, and every site you register runs through a live scoring pipeline
end to end. It's meant as a foundation to review and build on, not a final
production system (see "What's simplified" below).

## Stack

| Layer      | Tech |
|------------|------|
| Backend    | Python, FastAPI, SQLAlchemy, JWT auth |
| Database   | SQLite by default (zero setup) — swap in PostgreSQL + PostGIS via `DATABASE_URL` |
| Frontend   | React 18, Vite, React Router, Recharts, Axios |
| Deployment | Dockerfiles for both services + `docker-compose.yml` |

## Project structure

```
renewable-platform/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app entrypoint
│   │   ├── database.py           # DB engine/session
│   │   ├── models.py             # SQLAlchemy tables
│   │   ├── schemas.py            # Pydantic request/response models
│   │   ├── auth.py               # JWT + role-based access
│   │   ├── routers/
│   │   │   ├── auth.py           # register/login/me
│   │   │   ├── projects.py       # project CRUD
│   │   │   ├── sites.py          # site CRUD + intelligence pipeline + ranking
│   │   │   └── reports.py        # site/project report export (JSON)
│   │   └── services/
│   │       ├── environmental_engine.py  # Module 3/4 data collection
│   │       ├── solar_engine.py          # Module 5 solar prediction
│   │       ├── wind_engine.py           # Module 6 wind prediction
│   │       ├── scoring_engine.py        # Module 7/10 weighted scoring
│   │       └── forecasting_engine.py    # Module 8 energy/financial forecast
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
API docs: http://localhost:8000/docs (SQLite file `renewable_platform.db` is created automatically — no DB setup needed)

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
3. Inside the project, "Register & Analyze Site" with a name + lat/lon
   (+ optional land area, elevation, technology preference).
4. On submit, the backend runs the full pipeline automatically:
   environmental data collection → solar potential → wind potential →
   weighted suitability scoring → energy/financial forecasting.
5. View the site's radar score chart, solar/wind metrics, 25-year output
   forecast, and environmental factors on the site detail page.
6. Back on the project page, see all sites ranked by overall suitability
   score, with category and recommended technology (solar / wind / hybrid).

## What's simplified vs. the full spec (and how to extend it)

This scaffold implements the full **workflow shape** end-to-end so you can
review architecture and UX, but some modules use transparent heuristics
instead of production data sources / trained models:

- **Environmental data** (`services/environmental_engine.py`): currently
  generates deterministic synthetic values seeded by site coordinates, so
  the same site always returns the same numbers. Swap in real calls to
  NASA POWER, Global Wind Atlas, NASA SRTM, OpenStreetMap, and Copernicus
  Sentinel Hub (API key fields are already stubbed in `.env.example`) —
  nothing downstream needs to change since the function's return shape is
  fixed.
- **Solar/Wind prediction** (`services/solar_engine.py`,
  `services/wind_engine.py`): use standard PV-yield and wind-power-density
  physics formulas rather than trained ML models. Swap in a trained
  XGBoost/LightGBM/TensorFlow model by replacing the `predict_*` function
  bodies — the interface (env dict in → metrics dict out) is model-agnostic.
- **Site scoring**: implements the exact weighted formula from the spec
  (Resource 35% / Geographic 25% / Infrastructure 15% / Environmental 15% /
  Economic 10%).
- **Reports**: `/api/reports/site/{id}` and `/api/reports/project/{id}`
  return export-ready JSON. Wire in `reportlab` (PDF) or `openpyxl` (Excel)
  to convert that payload to downloadable files — the aggregation logic is
  already done.
- **Not yet built**: OAuth2 social login (JWT email/password auth is in
  place), notification/alert system, satellite imagery visualization, and
  GIS map rendering (site lat/lon is captured and ready to feed into
  Leaflet/Mapbox on the frontend).
- **Database**: SQLite is the default for zero-setup local review. The
  models use plain float lat/lon columns (not PostGIS geometry types) so
  they run unmodified on both SQLite and PostgreSQL — switch via
  `DATABASE_URL` in `.env` when you're ready to move to PostGIS spatial
  queries.

## Roles & access

Role-based access is enforced via `auth.require_roles(...)` in
`backend/app/auth.py`, following the spec's four roles: Renewable Energy
Planner, GIS Analyst, Project Manager, Administrator. Currently all
authenticated users can manage their own projects/sites; tighten specific
endpoints (e.g. restrict deletion to Project Manager/Administrator) by
adding `Depends(require_roles(RoleEnum.project_manager, RoleEnum.admin))`
to the relevant router functions.

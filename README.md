# ☀️ 💨 Solar & Wind Deployment Intelligence Platform

An AI-powered decision support platform that identifies, evaluates, and ranks optimal geographic locations for utility-scale solar, wind, and hybrid energy installations. The platform ingests real-time climatic data, executes spatial proximity scans, runs machine-learning-based generation forecasts with physics derating, and computes multi-criteria decision-making (MCDM) suitability scores and financial returns.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React.js (Vite), React-Leaflet, Leaflet, Recharts, Vanilla CSS / Tailwind CSS, SheetJS (`xlsx`), jsPDF, jsPDF-Autotable |
| **Backend API** | Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Python-JOSE (JWT), Passlib / Argon2 / Bcrypt |
| **Database & ORM** | SQLite (Dev) / PostgreSQL + PostGIS (Production), SQLAlchemy ORM |
| **Geospatial & Mapping** | OpenStreetMap Overpass API, Open-Meteo Elevation API, Leaflet Interactive Drag-and-Drop Map, NASA SRTM DEM |
| **AI / ML & Modeling** | Scikit-Learn (Random Forest Regression), Hellman Power Law Wind Shear Scaling, Physics PV Cell Derating |
| **External Data APIs** | NASA POWER API (Solar GHI & Meteorological telemetry), Copernicus Sentinel-2 (NDVI Vegetation Index) |
| **DevOps & Containerization** | Docker, Docker Compose, Linux Alpine |

---

## 👥 Default Accounts

Pre-configured role-based access control (RBAC) credentials seeded via `seed.py` for testing and evaluation:

| Role | Email | Password | Permissions & Operational Scope |
| :--- | :--- | :--- | :--- |
| **Renewable Energy Planner** | `planner@energygrid.gov` | `planner123` | Create project portfolios, register candidate sites, trigger NASA climatology sync, execute Solar & Wind ML models, run multi-site comparisons. |
| **GIS Analyst** | `gis@energygrid.gov` | `gis123` | Register sites, execute OpenStreetMap grid scans, edit spatial coordinates and terrain parameters (slope, elevation, NDVI). |
| **Project Manager** | `pm@energygrid.gov` | `pm123` | Create portfolios, review feasibility metrics, issue final deployment approvals (`/approval`), export PDF and Excel reports. |
| **Administrator** | `admin@energygrid.gov` | `admin123` | Full system oversight, registered user governance table, access auditing, and unrestricted platform operations. |

---

## 📊 Module Progress

| # | Module | Status | Capabilities Delivered |
| :---: | :--- | :---: | :--- |
| **1** | User Authentication & RBAC | ✅ Complete | JWT authentication, salted password hashing, 4-tier role enforcement. |
| **2** | Project & Site Management | ✅ Complete | Two-column portfolio manager, candidate site registration, interactive map drag picker. |
| **3** | Environmental Data Collection | ✅ Complete | Live integration with NASA POWER API for solar irradiance (GHI), temperature, precipitation, and cloud cover. |
| **4** | Geographic Intelligence Engine | ✅ Complete | OpenStreetMap Overpass spatial queries computing distances to substations, transmission lines, and access roads. |
| **5** | Solar Potential Prediction | ✅ Complete | Machine-learning solar capacity factor prediction with thermal cell derating losses. |
| **6** | Wind Potential Prediction | ✅ Complete | Hellman Power Law shear extrapolation (50m to 100m hub-height), wind power density, and annual yield. |
| **7** | Site Suitability Engine | ✅ Complete | 5-factor weighted Multi-Criteria Decision-Making (MCDM) scoring engine (0–10 scale). |
| **8** | Energy Forecasting Engine | ✅ Complete | Dynamic 12-month generation dispatch curves for Solar, Wind, and Hybrid combined systems. |
| **9** | Deployment Optimization Engine | ✅ Complete | Dynamic site-specific technology selection (Hybrid vs. Solar vs. Wind), LCOE ($/MWh), dynamic CAPEX, and payback periods. |
| **10** | Site Scoring Engine | ✅ Complete | Multi-site side-by-side comparison matrix evaluating competing sites across resource, terrain, and economic metrics. |
| **11** | Dashboard & Analytics | ✅ Complete | Interactive Recharts dashboard visualizing generation profiles, CAPEX vs. LCOE tradeoffs, and MCDM factor breakdown. |
| **12** | Notification & Alert System | ✅ Complete | Real-time threshold monitoring and environmental anomaly warnings. |
| **13** | Reports & Export System | ✅ Complete | Client-side export of comprehensive feasibility reports to PDF (jsPDF-Autotable) and Excel workbooks (`xlsx`). |
| **14** | Final Integration & Deployment | ✅ Complete | Multi-stage Dockerization (`Dockerfile`, `docker-compose.yml`), container networking, volume mounting, and database seeding. |

---

## 🚀 Getting Started

### Run with Docker (Recommended)

1. Build and start the platform:
   ```bash
   docker compose up --build

2. In a separate terminal, seed default RBAC accounts:
   ```bash
   docker exec -it solar_wind_backend python -c "import sys; sys.path.insert(0, '.'); from app.models.user import engine, Base, SessionLocal, User, UserRole; from app.core.security import get_password_hash; import app.models.project_site; Base.metadata.create_all(bind=engine); db = SessionLocal(); users = [('admin@energygrid.gov', 'System Administrator', 'admin123', UserRole.ADMIN.value), ('planner@energygrid.gov', 'Elena Rostova', 'planner123', UserRole.PLANNER.value), ('gis@energygrid.gov', 'Marcus Chen', 'gis123', UserRole.GIS_ANALYST.value), ('pm@energygrid.gov', 'Sarah Jenkins', 'pm123', UserRole.PROJECT_MANAGER.value)]; [db.add(User(email=e, full_name=n, hashed_password=get_password_hash(p), role=r, organization='National Renewable Energy Grid', department='Geospatial Division')) for e, n, p, r in users if not db.query(User).filter(User.email == e).first()]; db.commit(); db.close(); print('Database seeded successfully in Docker!')"

3. Open in browser:

Frontend App: http://localhost:5173

FastAPI Swagger Docs: http://localhost:8000/docs

--- 

### Local Development Setup (Without Docker)

## Backend Setup
   ```bash
   cd backend
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


## Frontend Setup

   ```bash
    cd frontend
    npm install
    npm run dev

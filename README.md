# Solar & Wind Deployment Intelligence Platform

A production-grade, AI-powered renewable energy platform designed to identify, evaluate, optimize, and forecast deployment sites for solar, wind, and hybrid projects.

---

## Key Features

1. **Geospatial & Multi-Factor Suitability Scoring**:
   - Evaluates sites according to:
     $$\text{Score} = (0.35 \times \text{Resource}) + (0.25 \times \text{Geographic}) + (0.15 \times \text{Infrastructure}) + (0.15 \times \text{Environmental}) + (0.10 \times \text{Economic})$$
   - Threshold categories: *Excellent (90-100)*, *Highly Suitable (75-89)*, *Moderately Suitable (60-74)*, *Low Suitability (40-59)*, *Unsuitable (0-39)*.
2. **Machine Learning Potential Engines**:
   - **Solar ML**: Predicts annual GHI irradiance, peak sun hours, capacity factor, and annual expected MWh yield with feature importances.
   - **Wind ML**: Predicts hub-height wind speed, aerodynamic power density, turbulence intensity, and turbine capacity factor.
3. **Deployment Optimization & Explainable AI**:
   - Recommends optimal location, capacity, and technology selection (Solar vs. Wind vs. Hybrid).
   - Generates transparent, human-readable reasoning points.
4. **Energy Generation & Revenue Forecasting**:
   - Multi-horizon forward projections: Daily (30-day), Monthly (12-month), Seasonal (Q1-Q4), and 10-year production degradation curves with confidence intervals.
   - Dynamic offtake power tariff slider (`electricity_price_per_kwh`).
5. **Investment Intelligence**:
   - 25-year discounted cash flow modeling, LCOE, NPV, IRR, and payback period calculations.
6. **Interactive GIS Map**:
   - Leaflet interactive map with vector layers: substations, transmission lines, heavy haul roads, protected reserves, water bodies, and agricultural plots.
   - Color-coded pins, site boundaries, and suitability heatmaps.
7. **Role-Based Access Control (RBAC)**:
   - 4 Pre-configured roles: *Renewable Energy Planner*, *GIS Analyst*, *Project Manager*, and *Administrator*.
8. **Automated PDF & Excel Reporting**:
   - Generates multi-page PDF executive dossiers and formatted multi-sheet Excel financial models.

---

## Tech Stack

- **Frontend**: React 18, Vite, Tailwind CSS, Leaflet, React-Leaflet, Lucide Icons, Recharts, Axios.
- **Backend**: Python 3.11/3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, GeoAlchemy2, Uvicorn, Passlib/Bcrypt, Python-Jose (JWT).
- **Databases**: PostgreSQL 16 + PostGIS, MongoDB (flexible unstructured document store), SQLite fallback for standalone local execution.
- **Machine Learning & GIS**: Scikit-learn, XGBoost/Gradient Boosting, Random Forest, NumPy, Pandas, Shapely, ReportLab, OpenPyXL.
- **DevOps**: Docker, Docker Compose, Nginx.

---

## Demo Login Credentials

| Role | Email | Password | Scope & Permissions |
| :--- | :--- | :--- | :--- |
| **Renewable Energy Planner** | `planner@example.com` | `Planner123!` | View recommendations, compare candidate sites, forecast energy, investment intelligence |
| **GIS Analyst** | `analyst@example.com` | `Analyst123!` | GIS interactive map, environmental layer controls, terrain analysis, retrain ML models |
| **Project Manager** | `manager@example.com` | `Manager123!` | Project & site CRUD, budget/capacity allocation, deployment timelines |
| **Administrator** | `admin@example.com` | `Admin123!` | User management, external dataset ingestion status, system health telemetry |

> *Note: These credentials are seeded automatically on first startup for demonstration purposes.*

---

## Quick Start (Docker Compose)

The entire multi-tier stack (PostgreSQL + PostGIS, MongoDB, FastAPI Backend, React Frontend) can be launched with:

```bash
# 1. Clone repository and copy environment variables
cp .env.example .env

# 2. Build and start all services
docker compose up --build
```

- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI REST API**: `http://localhost:8000`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/docs`

---

## Local Development (Native Execution)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Run migrations and seed default data
python scripts/seed_database.py

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:3000`.

---

## Running Automated Tests

Run the complete test suite with `pytest`:

```bash
cd backend
python -m pytest tests/ -v
```

The test suite validates:
- Password hashing and JWT generation
- Multi-factor site suitability exact scoring and category thresholds
- Solar and Wind ML prediction pipelines and metrics
- Monthly and seasonal forecasting
- Discounted cash flow, LCOE, NPV, and IRR calculations
- GIS spatial distance, Haversine formulas, and polygon boundaries
- PDF and Excel export generation

---

## External Data Integration & Resiliency

The platform supports external API integrations:
- `NASA_POWER_API_KEY`: Global horizontal and direct normal solar irradiance.
- `OPENWEATHER_API_KEY`: Real-time atmospheric conditions.
- `SENTINEL_HUB_CLIENT_ID` & `SENTINEL_HUB_CLIENT_SECRET`: Copernicus land cover and NDVI.

**Resilient Fallback**: If external API keys are omitted or endpoints are unreachable, the platform activates the **High-Fidelity Physics-Based Demo Generator** (`[DEMO DATA MODE]`), ensuring zero crash or downtime.

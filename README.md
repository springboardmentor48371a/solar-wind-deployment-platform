# Solar & Wind Deployment Intelligence Platform

An AI-powered platform that recommends optimal locations for renewable energy projects by analyzing environmental, geographic, climatic, and infrastructure-related factors.



---

## 🛠️ Tech Stack

- **Frontend:** React 19, Vite, TailwindCSS, Lucide Icons, Leaflet / React-Leaflet, `jsPDF`.
- **Backend:** FastAPI, Uvicorn, SQLAlchemy ORM, SQLite / PostgreSQL, Pydantic.
- **Data Science & ML:** XGBoost, Scikit-learn (Random Forest), PyTorch (ResNet-18), NumPy, Pandas, Joblib.
- **External Data Sources:** NASA POWER API, Open-Meteo Weather API, OpenStreetMap (Nominatim), SRTM 30m DEM.
- **DevOps:** Git, Docker, Docker Compose.

## 🚀 Project Overview & Architecture

The platform integrates real-time satellite earth observations, NASA meteorological APIs, digital elevation models (DEM), and machine learning regression models to evaluate renewable energy sites across India and globally.

```text
[ Frontend: React 19 + Vite + TailwindCSS + Leaflet + jsPDF ]
                         │  (HTTP / JSON REST)
                         ▼
[ Backend: FastAPI + Uvicorn + SQLAlchemy ORM (SQLite / PostgreSQL) ]
       │                      │                      │
       ├─ NASA POWER API      ├─ Terrain GIS Engine   ├─ ML Inference Pipelines
       │  (Solar GHI, Temp)   │  (30m DEM Slope)     │  (XGBoost + Random Forest)
       │                      │                      │
       ├─ Open-Meteo API      ├─ Exclusion Screening └─ AHP Multi-Criteria Engine
          (100m Hellmann Wind)   (EuroSAT ResNet-18)    (5-Factor Siting Index)


---

## Project Structure

```text
solar-wind-deployment-platform/
├── backend/
│   ├── app/
│   │   ├── core/         # config, security, dependencies
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── routers/      # API endpoint handlers
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # External API callers & calculations
│   │   └── main.py       # FastAPI application entry point
│   ├── tests/            # pytest suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # UI & Map components
│   │   ├── pages/        # Dashboard & view pages
│   │   ├── services/     # API client functions
│   │   ├── App.jsx       # Routing & main app wrapper
│   │   └── main.jsx
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── DATABASE_SCHEMA.md
│   ├── PROJECT_SPEC.md
│   └── WORKFLOWS.md
├── docker-compose.yml
├── .env.example
└── README.md
```
---

## 📊 Milestone Progress Summary

| Milestone Phase | Scope | Status | Implemented Capabilities |
| :--- | :--- | :---: | :--- |
| **Milestone 1** (Weeks 1–2) | Platform Foundation, RBAC, GIS Mapping & Relational Storage | **100% Complete** ✅ | JWT bearer authentication, Bcrypt password hashing, 4-role RBAC (`energy_planner`, `gis_analyst`, `project_manager`, `administrator`), Leaflet draggable GIS map picker modal, English reverse-geocoding, and persistent SQLAlchemy database models. |
| **Milestone 2** (Weeks 3–4) | Climate Ingestion, Terrain Analysis & Resource ML Modeling | **100% Complete** ✅ | Automated background task ingestion for NASA POWER and Open-Meteo with 24-hr caching; Hellmann's 100m wind extrapolation; Horn's 30m DEM slope analysis; in-memory streaming XGBoost solar model (`solar_aep_xgb.pkl`, $R^2 = 0.9955$); in-memory Random Forest wind model (`wind_aep_rf.pkl`); and EuroSAT ResNet-18 exclusion screening. |
| **Milestone 3** (Weeks 5–6) | Siting, Co-Location & Multi-Criteria Decision Scoring | **100% Complete** ✅ | Dedicated optimization service; 5-factor weighted AHP decision matrix (Resource 35%, Geographic 25%, Grid 15%, Environmental 15%, Economic 10%); and hybrid $5D \times 7D$ turbine wake-loss spacing & solar co-location density estimation. |
| **Milestone 4** (Weeks 7–8) | Analytics Dashboard, Hazard Alerts, PDF Export & DevOps | **95% Complete** 🔄 | Benchmark comparison matrix with dynamic top-performer badges; aggregate portfolio KPI summary bar; real-time operational risk and weather hazard alerts; client-side binary PDF feasibility dossier generation (`jsPDF`); and multi-container Docker configuration. |

---

## 🧩 Module Breakdown (All 14 Modules)

- **Module 1: User Authentication & Role-Based Access Control (100% ✅)**  
  Secure user registration, authentication, duplicate email prevention, Bcrypt hashing, and JWT bearer token issuance. Includes 4 operational role profiles, account switcher dropdown, copy-email tool, remember-me persistence, and sign-out confirmation dialogs.
- **Module 2: Project & Site Management (100% ✅)**  
  Interactive Leaflet GIS map picker modal (`MapPickerModal.jsx`) supporting click-to-pin coordinate extraction, elevation retrieval, English place-name geocoding, and persistent relational SQLite storage (`solar_wind.db`).
- **Module 3: Environmental Data Collection Engine (100% ✅)**  
  Asynchronous FastAPI `BackgroundTasks` automating climate collection from NASA POWER ($GHI$ irradiance, ambient temperature) and Open-Meteo. Uses Hellmann's Power Law to extrapolate 10m wind speeds to standard 100m turbine hub heights. Card metrics short-poll and update live upon background completion.
- **Module 4: Geographic Intelligence & Terrain Slope Analysis (100% ✅)**  
  Horn's 5-point DEM terrain slope kernel in `gis_engine.py` calculating ground slope degrees and construction viability thresholds ($< 5^\circ$ for solar PV, $< 12^\circ$ for wind turbines). Displayed as dynamic gradient badges on dashboard cards.
- **Module 5: Solar Potential Prediction Engine (100% ✅)**  
  Zero-unzip in-memory streaming XGBoost regression pipeline (`train_solar_stream.py`) trained on solar generation data ($R^2 = 0.9955$). Model artifact `solar_aep_xgb.pkl` deployed to live endpoint `POST /api/predict/yield`.
- **Module 6: Wind Potential Prediction Engine (100% ✅)**  
  In-memory Random Forest wind yield model (`train_wind_stream.py`) trained on standard IEC 61400 turbine power curves ($R^2 \approx 0.99$). Model artifact `wind_aep_rf.pkl` integrated into `yield_service.py` to evaluate aerodynamic power output.
- **Module 7: Environmental Exclusion & Satellite Screening (100% ✅)**  
  Deep learning PyTorch EuroSAT ResNet-18 satellite vision classifier identifying water bodies, protected wetlands, and dense forestry to flag legal exclusion conflicts.
- **Module 8: Energy Forecasting Engine (100% ✅)**  
  Live Annual Energy Production ($AEP$ in MWh/yr) and Capacity Utilization Factor ($CUF$ %) calculations across Solar PV, Wind, and Hybrid co-location archetypes.
- **Module 9: Deployment & Co-Location Optimization Engine (100% ✅)**  
  Calculates available land footprint capacity, maximum allowable 2.5 MW turbines using $5D \times 7D$ wake deficit buffer spacing, and ground-mounted bifacial PV density per $\text{km}^2$. Exposed via `POST /api/optimization/colocation`.
- **Module 10: Multi-Criteria Site Scoring Engine (100% ✅)**  
  Official 5-factor weighted AHP decision engine calculating a 0–100 suitability score:
  $$\text{Suitability Score} = (\text{Resource} \times 35\%) + (\text{Geographic} \times 25\%) + (\text{Infrastructure} \times 15\%) + (\text{Environmental} \times 15\%) + (\text{Economic} \times 10\%)$$
  Exposed via `POST /api/scoring/multicriteria` with visual subscore breakdown in the UI.
- **Module 11: Analytics Dashboard & Multi-Site Benchmark Matrix (100% ✅)**  
  Dark-themed dashboard with candidate category filter tabs (All, Active, Completed), candidate deletion, 4 aggregate portfolio KPI metrics cards, dynamic highlight badges (`Best` Solar, `Best` Wind, `Top Ranked` Suitability), and inline row-level target switching.
- **Module 12: Notification & Risk Advisory System (100% ✅)**  
  Automated threshold screening service in `risk_service.py` checking for turbine cut-out ($> 25\text{ m/s}$), solar PV thermal derating ($> 42^\circ\text{C}$), and steep civil slope excavation hazards ($> 5^\circ$ / $> 10^\circ$). Alerts render dynamically in an advisory banner.
- **Module 13: Reports & Export System (100% ✅)**  
  Executive Feasibility Report view featuring dual export triggers: browser-native print layout via `window.print()` and direct client-side binary PDF feasibility dossier generation via `jsPDF`.
- **Module 14: Final Integration, DevOps & Containerization (85% 🔄)**  
  Multi-container Docker orchestration (`docker-compose.yml`) exposing backend (port 8000) and frontend (port 5173).

---
## Module Progress

| Module | Status |
|---|---|
| **1. User Authentication & RBAC** | 🟩 Complete |
| **2. Project & Site Management** | 🟩 Complete |
| **3. Environmental Data Collection** | 🟩 Complete |
| **4. Geographic Intelligence Engine** | 🟩 Complete |
| **5. Solar Potential Prediction** | 🟩 Complete |
| **6. Wind Potential Prediction** | 🟩 Complete |
| **7. Site Suitability Engine** | 🟩 Complete |
| **8. Energy Forecasting Engine** | 🟩 Complete |
| **9. Deployment Optimization Engine** | 🟩 Complete |
| **10. Site Scoring Engine** | 🟩 Complete |
| **11. Dashboard & Analytics** | 🟩 Complete |
| **12. Notification & Alert System** | 🟩 Complete |
| **13. Reports & Export System** | 🟩 Complete |
| **14. Final Integration & Deployment** | 🟨 In Progress |


---

## External Datasets & Connectors

| Dataset / API | Purpose / Data Provided | Source |
| :--- | :--- | :--- |
| **NASA POWER** | Solar irradiance (GHI/DNI), wind speed (10m & 50m), temperature, precipitation. | `power.larc.nasa.gov/api` |
| **Global Wind Atlas / Open-Meteo** | Wind speed velocity at 100m hub height. | `open-meteo.com` |
| **Open-Meteo / SRTM** | Digital Elevation Model (DEM) height above sea level. | `elevation-api.open-meteo.com` |
| **OpenStreetMap (Nominatim)** | Reverse geocoding for automated region, state, and city extraction in English. | `nominatim.openstreetmap.org` |

---

## Multi-Criteria Site Scoring Algorithm

The platform evaluates potential deployment sites using the weighted multi-factor formula:

$$\text{Suitability Score} = (\text{Resource} \times 35\%) + (\text{Geographic} \times 25\%) + (\text{Infrastructure} \times 15\%) + (\text{Environmental} \times 15\%) + (\text{Economic} \times 10\%)$$

### Suitability Tiers
- 🟢 **Excellent:** $\ge 90$ / 100
- 🔵 **Highly Suitable:** $75 - 89$ / 100
- 🟡 **Moderately Suitable:** $60 - 74$ / 100
- 🟠 **Low Suitability:** $40 - 59$ / 100
- 🔴 **Unsuitable:** $< 40$ / 100

---

## Prerequisites

Only two things needed:

* **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — runs everything
* **[Git](https://git-scm.com/)** — to clone the repo

No Node.js, no Python, no pip — Docker handles all of that.

---

## Getting Started

### Step 1. Clone the repository

```bash
git clone [https://github.com/springboardmentor48371a/solar-wind-deployment-platform.git](https://github.com/springboardmentor48371a/solar-wind-deployment-platform.git)
cd solar-wind-deployment-platform
git checkout shruti-mishra
```
### Step 2: Start the FastAPI Backend ServerOpen your first terminal in the project root:PowerShell# Navigate to backend directory
```bash
cd backend

# Create virtual environment

python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1
# macOS / Linux:
# source venv/bin/activate

# Install required Python dependencies

pip install fastapi uvicorn sqlalchemy "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1" pydantic "pydantic[email]" email-validator requests

# Run the backend with live reload
uvicorn main:app --reload --port 8000
```
Backend API Gateway: http://127.0.0.1:8000Interactive Swagger Documentation: http://127.0.0.1:8000/docs
### Step 3: Start the Vite + React Frontend ServerOpen a second terminal in the project root:PowerShell# Navigate to frontend directory
```bash
cd frontend
```
# Install Node dependencies
```bash
npm install
```
# Start Vite development server
```bash
npm run dev
```
Frontend Web Application: http://localhost:5173/

## Testing & Verification Guide

Follow these steps to test and verify the end-to-end functionality of the platform in your browser:

### 1. Launch Application
* Open **`http://localhost:5173/`** in your web browser.

---

### 2. User Registration & Login
* Click on **Register Account**.
* Select your platform role (e.g., *Renewable Energy Planner*, *GIS Analyst*, *Project Manager*, or *Administrator*).
* Enter your display name, email address, and a secure password ($\ge$ 6 characters).
* Click **Register & Sign In** to authenticate and receive your JWT session token.

---

### 3. Register Candidate Sites with Interactive GIS
* On the authenticated dashboard, click **Select Your Site on Map** or **Register Site on Map**.
* Enter a custom **Site / Project Name**.
* Search for any location by name in the search bar or click and drag the blue pin anywhere on the map.
* Verify that the **Coordinates (Lat/Long)**, **Region / State (in English)**, **DEM Elevation**, and **Grid Distance** update automatically in real time.
* Click **Confirm & Send for Feasibility Analysis** to persist the site record to the database.

---

### 4. Multi-Site Analysis & Dashboard Navigation
* **View Stored Sites:** Use the sidebar navigation menu to browse all saved geographical corridors and switch active target zones.
* **Compare Sites:** Benchmark candidate locations side-by-side on Solar GHI, Wind Speed (100m), Area, and Suitability Scores.
* **View Feasibility Report:** Review the estimated Annual Energy Production (AEP in MWh/yr), Capacity Utilization Factor (CUF), and export the dossier.

---




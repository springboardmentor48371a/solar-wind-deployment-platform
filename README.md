# Solar & Wind Deployment Intelligence Platform

An AI-powered platform that recommends optimal locations for renewable energy projects by analyzing environmental, geographic, climatic, and infrastructure-related factors.



---

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI |
| **Frontend** | React.js, Vite |
| **Database** | PostgreSQL 16 |
| **Auth** | JWT, bcrypt, Google OAuth2 |
| **Maps** | Leaflet.js, OpenStreetMap |
| **DevOps** | Docker, Docker Compose |

---

## Comprehensive Module Breakdown (All 14 Modules)

### 1. User Authentication & Role-Based Access (RBAC) ✅
- User registration and login with bcrypt password hashing.
- JWT token generation and session management.
- Multi-role permission system supporting:
  - **Renewable Energy Planner:** Evaluates candidate sites and yield forecasts.
  - **GIS Analyst:** Conducts terrain, elevation, and infrastructure analysis.
  - **Project Manager:** Tracks project progress and site comparison matrices.
  - **Administrator:** Full platform, database, and user management.
- User profile management, password toggles, and secure sign-out modals.

### 2. Project & Site Management ✅
- Dynamic project creation and site registration workflow.
- Interactive **Leaflet GIS Map Picker** with real-time draggable pin extraction.
- Automated reverse-geocoding via **OpenStreetMap Nominatim API** (strictly English names).
- Automated Digital Elevation Model (DEM) lookup via **Open-Meteo Elevation API**.
- Persistent relational database storage via **SQLAlchemy**.

### 3. Environmental Data Collection Engine ✅
- Weather data collection integration via **NASA POWER API**.
- Historical climate data collection via **Open-Meteo API** (relative humidity, temperature ranges).
- Terrain elevation retrieval via **OpenTopoData / Open-Meteo SRTM30m**.
- 24-hour collection caching to minimize external API rate limits.

### 4. Geographic Intelligence Engine 🔜
- Advanced GIS raster and vector data processing with PostGIS / GeoPandas.
- Digital Elevation Model (DEM) contour and terrain slope gradient analysis.
- Automated road network and transmission grid infrastructure proximity buffering.
- Exclusion zone filtering (water bodies, protected forests, urban settlements).

### 5. Solar Potential Prediction Engine 🔜
- Global Horizontal Irradiance (GHI) and Direct Normal Irradiance (DNI) estimation.
- Solar PV panel degradation and conversion efficiency modeling.
- Seasonal solar energy output forecasting.
- Solar resource spatial mapping.

### 6. Wind Potential Prediction Engine 🔜
- Wind speed modeling extrapolated to 50m, 100m, and 120m hub heights.
- Wind turbine power curve matching and wake loss calculations.
- Wind Power Density (WPD) modeling.
- Seasonal and diurnal wind pattern forecasting.

### 7. Site Suitability Intelligence Engine 🔜
- Multi-factor environmental constraint evaluation.
- Machine-learning-based classification (Random Forest / XGBoost) for site viability.
- Environmental impact and risk scoring.

### 8. Energy Forecasting Engine 🔜
- Time-series machine learning models (LSTM / Prophet / XGBoost) for energy generation forecasting.
- Annual Energy Production (AEP in MWh/year) estimation.
- Capacity Utilization Factor (CUF / Capacity Factor) predictions.
- Revenue and economic return forecasting.

### 9. Deployment Optimization Engine 🔜
- Optimal site selection using Genetic Algorithms (GA) / Mixed-Integer Linear Programming (MILP).
- Co-location optimization for **Hybrid Solar-Wind** installations.
- Capacity planning and footprint optimization per square kilometer.

### 10. Site Scoring & Ranking Engine 🔜
- Automated weighted scoring algorithm that evaluates candidate sites on a scale of 0 to 100.
- Multi-criteria breakdown covering resource availability, terrain slope, infrastructure, and financial viability.

### 11. Dashboard & Analytics 🔄
- Role-specific dashboard views tailored for Planners, Analysts, Managers, and Admins.
- Side-by-side **Multi-Site Comparison Matrix**.
- Stored project galleries with quick-action target switching.
- Visual generation analytics and charts.

### 12. Notification & Alert System 🔜
- Severe weather risk alerts.
- Site status change and workflow updates.
- Threshold warning notifications for grid distance and low resource availability.

### 13. Reports & Export System 🔜
- One-click executive site feasibility dossiers.
- Downloadable project assessment reports (PDF and Excel format).
- Customizable executive summary charts and financial ROI breakdowns.

### 14. Final Integration, Testing & Deployment 🔜
- End-to-end API and UI pipeline validation.
- Containerization using **Docker** and **Docker Compose**.
- CI/CD integration with GitHub Actions.
- Cloud hosting deployment on **AWS / Azure**.

---

## Module Progress

| Module | Status |
|---|---|
| **1. User Authentication & RBAC** | 🟩 Complete |
| **2. Project & Site Management** | 🟩 Complete |
| **3. Environmental Data Collection** | 🟩 Complete |
| **4. Geographic Intelligence Engine** | 🟦 Planned |
| **5. Solar Potential Prediction** | 🟦 Planned |
| **6. Wind Potential Prediction** | 🟦 Planned |
| **7. Site Suitability Engine** | 🟦 Planned |
| **8. Energy Forecasting Engine** | 🟦 Planned |
| **9. Deployment Optimization Engine** | 🟦 Planned |
| **10. Site Scoring Engine** | 🟦 Planned |
| **11. Dashboard & Analytics** | 🟨 In Progress |
| **12. Notification & Alert System** | 🟦 Planned |
| **13. Reports & Export System** | 🟦 Planned |
| **14. Final Integration & Deployment** | 🟦 Planned |


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

### 1. Clone the repository

```bash
git clone [https://github.com/springboardmentor48371a/solar-wind-deployment-platform.git](https://github.com/springboardmentor48371a/solar-wind-deployment-platform.git)
cd solar-wind-deployment-platform
git checkout shruti-mishra




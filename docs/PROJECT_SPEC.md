# Project Specification

## Objective

Build an AI-powered Solar & Wind Deployment Intelligence Platform that recommends optimal locations for renewable energy projects by analyzing environmental, geographic, climatic, and infrastructure-related factors.

The platform leverages geospatial analytics, satellite weather data, terrain analysis, machine learning inference, and multi-criteria decision algorithms to evaluate site suitability, estimate renewable generation potential, streamline stakeholder collaboration, and accelerate renewable energy deployment.

**Target Stakeholders:** Renewable energy developers, energy planners, GIS analysts, project managers, utility providers, and infrastructure consultants.

---

## Implemented Capabilities

The platform has been designed, implemented, tested, and deployed with the following core systems:

### 1. Secure Authentication & Role-Based Access Control (RBAC)
- **Multi-Factor Session Security**: JWT-based authentication featuring short-lived access tokens (30 minutes) and secure refresh tokens (7 days).
- **Password Protection**: Industry-standard password hashing using `bcrypt` via Passlib.
- **Federated Authentication**: Google OAuth2 authentication flow with automatic account provisioning and token exchange.
- **Granular Roles & Least Privilege**: Four specialized user personas with strictly enforced backend authorization policies:
  - *Administrator*: System governance, user lifecycle management, role modifications, and account deactivations.
  - *Energy Planner*: Project portfolio creation, site exploration, scenario planning, and yield analysis.
  - *GIS Analyst*: Geospatial map intelligence, coordinate inspection, terrain profiling, and site registration.
  - *Project Manager*: Project governance, resource oversight, multi-site comparison, and exclusive authority to approve or reject site deployment statuses.

### 2. Project Portfolio & Site Asset Management
- **Project Workspaces**: Centralized containerization of renewable energy initiatives tracking lifecycle milestones (`planning`, `active`, `completed`, `on_hold`).
- **Asset Registration**: Detailed site profiling capturing coordinates (latitude/longitude), elevation, land area (hectares), energy technology (`solar`, `wind`, `hybrid`), and land ownership categories.
- **Geographic Auto-Discovery**: Automatic country and regional boundary resolution via Nominatim reverse geocoding on site submission.
- **Site Comparison Matrix**: Side-by-side benchmarking tool enabling multi-site evaluations across key terrain, resource, and prediction metrics.
- **Deployment Audit Trail**: Immutable history log (`deployment_history`) tracking every status transition with reviewer ID, previous status, new status, timestamp, and audit notes.

### 3. Automated Environmental & Climate Data Pipeline
- **Meteorological Ingestion**: Automated data ingestion from NASA POWER API fetching daily solar irradiance ($W/m^2$), peak sun hours, direct normal irradiance (DNI), and ambient temperature ranges.
- **Atmospheric Climate Ingestion**: Integration with the Open-Meteo API for multi-altitude wind vectors (10m and 50m wind speed in $m/s$), wind direction, precipitation, cloud cover, and relative humidity.
- **Terrain Elevation Modeling**: Automatic DEM altitude, slope, and aspect retrieval using OpenTopoData / NASA SRTM.
- **Smart 24-Hour Cache Layer**: Ingestion layer caching that eliminates duplicate external API queries if a site's environmental observations have been refreshed within 24 hours.

### 4. Smart Environmental Visibility Engine
- **Technology-Tailored Metrics**: Dynamic client-side filtering that presents only domain-relevant environmental parameters:
  - *Solar Sites*: Displays solar irradiance, peak sun hours, and temperature metrics; automatically suppresses wind metrics.
  - *Wind Sites*: Displays 10m/50m wind speeds, directional compass, and atmospheric density; automatically suppresses solar irradiance.
  - *Hybrid Sites*: Displays the unified environmental matrix across both solar and wind dimensions.

### 5. AI/ML Site Suitability & Resource Yield Intelligence
- **Microservice Architecture**: Decoupled FastAPI ML service executing asynchronous model inference and scoring.
- **Solar Potential Estimation**: Machine learning estimation of solar capacity factor and daily energy yield ($kWh$).
- **Wind Resource Modeling**: Wind power output prediction ($kW$) integrated with Betz-limit aerodynamic fallbacks for low-wind regimes.
- **Geographic & Land Cover Analysis**: Land classification, vegetation indexing (NDVI), and slope suitability indexing.
- **Multi-Factor Suitability Scoring Engine**:
  $$\text{Composite Score} = 35\% \times \text{Resource} + 25\% \times \text{Geographic} + 15\% \times \text{Infrastructure} + 15\% \times \text{Environmental} + 10\% \times \text{Economic}$$
- **Standardized Categorization**: Automatic qualitative rating classification into *Excellent*, *Highly Suitable*, *Moderately Suitable*, *Low Suitability*, or *Unsuitable*.

### 6. Interactive Geospatial GIS & Role Dashboards
- **Interactive Mapping**: Leaflet.js-powered GIS map with OpenStreetMap basemaps, custom color-coded technology markers, and site radius coverage circles.
- **Real-Time Coordinate Preview**: Live reverse-geocoding preview tool displaying elevation, municipality, state, and country before site commitment.
- **Customized Role Dashboards**: Specialized UI layouts designed specifically around each role's primary mission:
  - *Planner*: Portfolio view, suitability rankings, and site comparisons.
  - *GIS Analyst*: Map-first spatial intelligence, site registration, and coordinate profiling.
  - *Project Manager*: Project health, site approval/rejection controls, and audit logs.
  - *Admin*: User management, access rights, and security oversight.

### 7. Production DevOps & Cloud Deployment
- **Docker Compose Orchestration**: Containerized multi-container environment encompassing PostgreSQL 16, FastAPI Backend Gateway, FastAPI ML Microservice, and an Nginx Alpine SPA.
- **Nginx Reverse Proxying**: Built-in production routing with SPA HTML5 fallback and upstream API gateway proxying.
- **Live Render Deployment**: Fully operational production release on Render across managed static sites, web services, and PostgreSQL databases.

---

## Future Implementation

The following modules represent the strategic development roadmap for upcoming releases of the platform:

### 1. Advanced Energy Forecasting
Provide reliable 30-day and seasonal solar/wind generation forecasts leveraging time-series machine learning models to predict output variability and grid export capacity.

### 2. Deployment Optimization Engine
Recommend the best technology, capacity, and site combination for each project using multi-objective genetic algorithms and spatial optimization to maximize return on investment.

### 3. Financial Feasibility Analysis
Add comprehensive financial intelligence including CAPEX, OPEX, ROI, payback period, levelized cost of energy (LCOE), revenue projections, and energy-cost estimates.

### 4. Automated Feasibility Reports
Generate downloadable, executive-ready PDF and spreadsheet reports incorporating spatial maps, environmental metrics, suitability rankings, ML predictions, and strategic recommendations.

### 5. Notification and Alert System
Notify users about automated data updates, site-status transitions, prediction completions, critical weather anomalies, and system operational issues through in-app and email alerts.

---

## Current Technology Stack

| Layer | Technologies | Purpose |
|---|---|---|
| **Frontend** | React 19, Vite, React Router 7, Axios | Single-Page Web Application |
| **Mapping & GIS** | Leaflet.js, React-Leaflet, OpenStreetMap | Interactive spatial analysis |
| **Backend API** | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0 | High-performance API Gateway |
| **ML Microservice** | FastAPI, Scikit-Learn, XGBoost, Joblib, NumPy, Pandas | Climate inference & suitability scoring |
| **Database** | PostgreSQL 16 | Relational data persistence & spatial indices |
| **Authentication**| JWT (Python-Jose), Passlib (Bcrypt), Google OAuth2 | Secure identity & role management |
| **Web Server** | Nginx (Alpine) | Production SPA hosting & reverse proxy |
| **DevOps & Cloud** | Docker, Docker Compose, Render | Container orchestration & cloud deployment |

---

## External Data Integrations

| Data Source | Integration Type | Parameter Scope |
|---|---|---|
| **NASA POWER API** | REST API | Solar GHI, DNI, peak sun hours, daily ambient temperatures |
| **Open-Meteo API** | REST API | Wind speed at 10m/50m, wind direction, precipitation, cloud cover, humidity |
| **OpenTopoData / NASA SRTM** | REST API | Digital elevation models (DEM), terrain slope, aspect |
| **Nominatim (OpenStreetMap)** | REST API | Reverse geocoding of coordinates to country, state, and administrative region |

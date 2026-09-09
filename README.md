# Solar & Wind Deployment Intelligence Platform

An AI-powered renewable energy planning platform designed to find, evaluate, and recommend optimal locations for solar, wind, and hybrid projects in Western India (Gujarat/Rajasthan) using geospatial analytics, dynamic multi-criteria decision scoring, and machine learning yield predictions.

---

## Key Features
- **Real-Time OpenStreetMap (OSM) Infrastructure**: Uses the Overpass API to fetch real roads and power substations near the site dynamically. Applies grid-based caching (rounded coordinates) to prevent rate limits.
- **Global Wind Atlas Integration**: Queries locally cropped high-resolution GeoTIFFs to provide real mean wind speed (100m) and wind power density.
- **NASA POWER Climatology Integration**: Fetches real solar irradiance (GHI), temperature, rainfall, humidity, and cloud cover metrics for precise climate modeling.
- **Vectorized Geospatial Distance Engine**: Employs GeoPandas and Shapely (projected onto India's UTM coordinate grid **EPSG:32643**) for fast, vectorized calculations of proximity to transmission lines, substations, and intersections with environmental protected wildlife zones (triggering auto-unsuitability overrides).
- **Exact Database Schema Mapping**: Integrates the original 8-table relational schema covering User Roles, Projects, Site Parameters, Environmental averages, Site Assessments, Reports, and System Notifications.
- **JWT Authorization with 4 Roles**: Custom OAuth2/JWT logins for **Planner**, **GIS Analyst**, **Project Manager**, and **Admin** profiles.
- **ML Yield & ROI Forecasting**: Integrates a Scikit-Learn `RandomForestRegressor` mapping climatic inputs to predict yearly capacity factors and GWh energy yields, complemented by a 25-year project cash flow ROI tracker.
- **Thematic Geospatial Dashboard**: A glassmorphic dark-theme dashboard featuring interactive CartoDB Leaflet maps, dynamic suitability weighting sliders, and comparison charts.
- **Demo Mode Flags**: Clearly labels all machine learning outputs with a synthetic indicator badge and distinguishes real API sources from local estimates.

---

## System Architecture

```
                       +----------------------------------+
                       |          React Frontend          |
                       |       (Leaflet & Recharts)       |
                       +----------------+-----------------+
                                        |
                                        | HTTP Requests (REST / JWT)
                                        v
                       +----------------+-----------------+
                       |         FastAPI Backend          |
                       | (Auth, Recalculate, GeoJSON API) |
                       +-------+----------------+---------+
                               |                |
                GIS Analysis   v                v   ML Predictions & Data
         +---------------------+----+      +----+---------------------+
         |    GeoPandas / Shapely   |      | Scikit-learn RandomForest|
         | (UTM 43N - EPSG:32643)   |      |  (Yields, Cash Flow ROI) |
         |   OpenStreetMap Overpass |      |  NASA POWER Climatology  |
         |    Local OSM Grid Cache  |      |   Global Wind Atlas TIFs |
         +---------------------+----+      +--------------------------+
                               |
                               v
                       +-------+--------------------------+
                       |       PostgreSQL Database        |
                       |    (8 Schema Tables Storage)     |
                       +----------------------------------+
```

---

## Database Schema (Foundation Table Mapping)
1. **`roles`**: UUID PK, role name, description, and created timestamp.
2. **`users`**: UUID PK, full name, email (unique), password hash, contact, organization, role FK, status, and update timestamps.
3. **`projects`**: UUID PK, project name, description, region, status, creator user FK, and timestamps.
4. **`sites`**: UUID PK, project FK, site name, latitude, longitude, region, land area (Acres), elevation (meters), land type, and ownership.
5. **`environmental_data`**: UUID PK, site FK, solar irradiance, wind speed/direction, temperature, rainfall, humidity, cloud cover, slope, NDVI veg index, nearest substation distance, road distance, protected area flag, and timestamp.
6. **`site_assessments`**: UUID PK, site FK, expected solar/wind energy predictions, capacity factors, suitability score, rating category, energy forecast, revenue estimate, recommended deployment type, text recommendation, analysis status, and timestamp.
7. **`reports`**: UUID PK, project FK, report type, generator user FK, file path URL, and timestamp.
8. **`notifications`**: UUID PK, user FK, title, message, type (Weather/AI/System), read flag, and timestamp.

---

## Setup & Installation

### Prerequisites
- **Node.js** (v18.0 or newer)
- **Python** (v3.10 to v3.13)
- **PostgreSQL** (Active on port 5432 or 5433)

### 1. Backend Configuration
1. Navigate to the `backend` folder:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows (PowerShell):
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Verify your database settings in `.env`. The database credentials default to:
   - **Host**: `localhost`
   - **Port**: `5433`
   - **User**: `postgres`
   - **Database**: `solar_wind_db`
   - **Password**: Configure this to match your system password.

5. Initialize the database schema and seed the initial corridors, users, and sites in Gujarat/Rajasthan:
   ```bash
   python app/seed.py
   ```

### 2. Running the Backend Server
```bash
python -m uvicorn app.main:app --reload --port 8000
```
The API Swagger documentation will be available at `http://localhost:8000/docs`.

### 3. Frontend Configuration
1. Navigate to the `frontend` folder:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Start the Vite React development server:
   ```bash
   npm run dev
   ```
The frontend portal will launch on **`http://localhost:5173/`**.

---

## Pre-seeded Accounts
Log in using one of the pre-seeded accounts configured for each profile:

| Profile Role | Email Login | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@renewable.in` | `adminpassword` |
| **Planner** | `planner@renewable.in` | `plannerpassword` |
| **GIS Analyst** | `gis@renewable.in` | `gispassword` |
| **Project Manager** | `manager@renewable.in` | `managerpassword` |

---

## Suitability Scoring Matrix Weights
You can customize the following evaluation weights inside the sidebar weights settings drawer:
- **Renewable Resource Availability (35%)**: Evaluates solar irradiance capacity and wind capacity yields.
- **Geographic Suitability (25%)**: Penalizes high slopes and low solar aspects.
- **Infrastructure Accessibility (15%)**: Scores distance to grid connection substations and access roads.
- **Environmental Impact (15%)**: Assesses intersection with park preserves.
- **Economic Feasibility (10%)**: Favors large waste lands.

---

## Data Source Attributions & Licensing

This platform integrates genuine meteorological, infrastructure, and wind resource datasets from international atmospheric, geospatial, and wind energy research centers:

### 1. Global Wind Atlas (GWA)
*   **Metrics**: 100m Hub Height Mean Wind Speed, Mean Wind Power Density.
*   **Attribution**: Wind data is sourced from the Global Wind Atlas, developed by the Technical University of Denmark (DTU) in partnership with the World Bank Group (financed by the Energy Sector Management Assistance Program - ESMAP).
*   **Licensing**: Data is licensed under a [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
*   **Official Resource**: [https://globalwindatlas.info/](https://globalwindatlas.info/)

### 2. NASA POWER Project
*   **Metrics**: Daily Global Horizontal Irradiance (GHI) solar index, Earth air temperature (2m), total annual precipitation (rainfall), relative humidity index (2m), and cloud cover percentage.
*   **Attribution**: Solar and meteorological data is sourced from the NASA Langley Research Center (LaRC) Prediction of Worldwide Energy Resources (POWER) Project, funded by the NASA Earth Science Division Applied Sciences Program.
*   **Official Resource**: [https://power.larc.nasa.gov/](https://power.larc.nasa.gov/)

### 3. OpenStreetMap (OSM) via Overpass API
*   **Metrics**: Dynamic road distance, Substation proximity, Protected Area bounds.
*   **Implementation**: Calculates the shortest geographical distance from the site to the nearest substation (radius: 50 km) and highway (radius: 20 km) excluding footpaths and cycles paths. Uses dynamic bounding box grid caching to minimize external API loads.
*   **Attribution**: Map data © OpenStreetMap contributors.
*   **Licensing**: ODbL License.
*   **Official Resource**: [https://www.openstreetmap.org/](https://www.openstreetmap.org/)

### 4. NASA SRTM
*   **Metrics**: Elevation, Terrain Slope.
*   **Attribution**: Shuttle Radar Topography Mission (SRTM).

### 5. Esri Land Cover
*   **Metrics**: Mapped Land Use classes.
*   **Attribution**: Esri Sentinel-2 10m Land Cover, derived from Copernicus Sentinel-2 imagery.

---

## Machine Learning & Prediction Methodology
The platform implements a **dual-path predictive engine**:
1. **Real Historical ML Predictors**: Evaluated Random Forest regressors mapped on real wind farm datasets.
2. **Synthetic Fallback Estimators**: Safe fallbacks triggered when public API features (such as Module Temperature) are missing.

### Known Limitations & Synthetic Disclosures
- **Solar Validation**: Due to the unavailability of `MODULE_TEMPERATURE` via standard free weather APIs, the platform triggers an algorithmic fallback to evaluate solar energy, keeping predictions physically honest. The Solar UI clearly labels itself as a `Synthetic Fallback`.
- **Wind Model Geo-Validation**: The Wind RF model is trained on the physical parameters of the [Kelmarsh Wind Farm SCADA dataset](https://zenodo.org/record/7331828) (UK). While it accurately models MM92 turbine outputs, its predictive behavior has *not* been fully geographically validated for the atmospheric conditions specific to Gujarat/Rajasthan.

### Model Metrics (Evaluated on Origin Sets)
- **Wind (Random Forest Regressor)**:
    - MAE = 50.70
    - RMSE = 130.93
    - R² = 0.9260

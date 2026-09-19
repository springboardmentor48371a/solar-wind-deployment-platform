# Solar & Wind Deployment Intelligence - Frontend

## Key Features

1. **Role-Based Dashboards**: 
   - **Administrator**: User management, system metrics, role updates.
   - **Energy Planner**: Site comparison, suitability scoring, analytics.
   - **GIS Analyst**: Interactive map visualizations, elevation, slope details.
   - **Project Manager**: Project progress, timelines, sites overview.
2. **Interactive Map View (`MapView`)**: Uses Leaflet.js and OpenStreetMap to render sites with color-coded markers matching their suitability categories (e.g., green for Excellent, red for Unsuitable). Includes popups showing key environmental and resource metrics.
3. **Environment Summary (`EnvSummary`)**: Displays 30-day averaged climate variables (solar irradiance, peak sun hours, wind speed, temperature, rainfall, cloud cover, and elevation).
   * Note: Environmental display is strictly symmetric; wind sites hide solar-related parameters, and solar sites hide wind-related parameters. Hybrid sites display both sets of metrics.
4. **ML Predictions Panel (`PredictionPanel`)**: Renders predictions from the ML models, including solar capacity factor, wind power outputs, land cover predictions, and sub-score breakdowns. Includes a **Run Now / Re-run** button to manually trigger models.
5. **Analytics Ranking (`AnalyticsView`)**: Tabular, sortable ranking of all sites based on suitability scores across all metrics. Includes distribution summary counts of site categories.

## File Structure

```
frontend/
├── public/                → static assets and map icons
├── src/
│   ├── assets/            → react/vite logos
│   ├── components/        → modular UI components
│   │   ├── AnalyticsView.jsx    → global site rankings & score distribution
│   │   ├── Dashboard.jsx        → dashboard layout structure
│   │   ├── EnvSummary.jsx       → climate averages viewer
│   │   ├── Layout.jsx           → layout frame & sidebar routing
│   │   ├── Login.jsx            → sign-in form with styles
│   │   ├── MapView.jsx          → Leaflet GIS map with suitability pins
│   │   ├── PredictionPanel.jsx  → ML model predictor panel with triggers
│   │   ├── ProjectsView.jsx     → projects, sites list, and comparisons
│   │   └── UsersView.jsx        → user management view for Admin
│   ├── pages/             → role-based views mapping components
│   ├── App.jsx            → root router & session authentication guard
│   ├── api.js             → Axios configuration and endpoint mapping
│   └── index.css          → global theme styling & variables
├── package.json           → scripts and dependencies
└── vite.config.js         → vite build config
```

## Running the Frontend

The frontend runs inside a Docker container on port `5173`. When launching via docker-compose:
```bash
docker compose up --build
```
Open **http://localhost:5173** to view the app.

# Solar & Wind Deployment Intelligence - Backend

This is the FastAPI backend service for the Solar & Wind Deployment Intelligence Platform. It manages authentication, project & site details, coordinates geocoding, database triggers, environmental data fetching, and proxies machine learning predictions to the `ml-service`.

## Key Features

1. **Authentication & RBAC**:
   - JWT-based authentication (30-minute access token, 7-day refresh token).
   - Role-based permissions supporting four roles: `energy_planner`, `gis_analyst`, `project_manager`, and `administrator`.
   - Google OAuth2 callback integration.
2. **Project & Site Management**:
   - Location auto-detection: Nominatim API reverse geocoding to determine region (state, country) based on site coordinates.
   - Elevation detection: Auto-fetches elevation from OpenTopoData.
   - Site Comparison API: `GET /sites/compare?ids=...` to compare multiple sites side-by-side.
   - Audit trail tracking: `deployment_history` table automatically logged during site status changes (`under_review` → `approved` / `rejected`).
3. **Environmental Data Aggregation**:
   - Triggers on site creation to fetch 30 days of daily weather, terrain, and climate variables from NASA POWER and Open-Meteo.
4. **Machine Learning Proxy**:
   - Routes prediction requests (`GET /predictions/{site_id}` and manual triggers `POST /predictions/{site_id}/run`) to the `ml-service` to run solar, wind, land cover, and suitability models.

## Folder Structure

```
backend/
├── app/
│   ├── core/          → JWT authentication, security helpers, CORS configurations
│   ├── models/        → SQLAlchemy database declarations (User, Region, Project, Site, etc.)
│   ├── routers/       → API controllers (auth, users, regions, projects, sites, environmental, predictions)
│   ├── schemas/       → Pydantic DTO definitions for inputs and outputs validation
│   ├── services/      → integration with Open-Meteo, NASA POWER, OpenTopoData, Nominatim geocoder
│   ├── database.py    → SQLAlchemy SessionLocal and database engine setup
│   ├── main.py        → FastAPI entry point, lifespan events, router registration
│   └── seed.py        → database seed script with default accounts & mock sites
├── requirements.txt   → python dependencies
└── Dockerfile         → container image definition
```

## Running the Backend

The backend runs inside Docker on port `8000` (API documentation at **http://localhost:8000/docs**).

To seed the database with mock accounts (`admin@solarwind.com`, `planner@solarwind.com`, `gis@solarwind.com`, `manager@solarwind.com`) and sample sites, execute:
```bash
docker exec solar-wind-deployment-platform-backend-1 python app/seed.py
```

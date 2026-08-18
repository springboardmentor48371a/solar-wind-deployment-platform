
# Solar and Wind Prediction — Deployment Intelligence Platform

A working full-stack prototype based on the supplied project brief.

## Included workflow
1. Register account / login
2. Role-based account selection
3. Create renewable energy project
4. Register candidate site
5. Capture environmental, geographic and infrastructure factors
6. Calculate suitability using the brief's weighted model:
   - Resource availability 35%
   - Geographic suitability 25%
   - Infrastructure accessibility 15%
   - Environmental impact 15%
   - Economic feasibility 10%
7. Rank sites and show deployment recommendations
8. View analytics and energy estimates
9. Export a site assessment CSV
10. View profile and sign out

## Why SQLite for this prototype?
The project brief specifies PostgreSQL + PostGIS as the primary production database. This prototype intentionally uses SQLite for authentication and core persistence so registration/login works immediately without PostgreSQL setup or driver/schema issues. The API/database layer is isolated, so PostgreSQL/PostGIS can be introduced later.

## Run backend
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend: http://localhost:8000
Swagger: http://localhost:8000/docs

## Run frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Login test
Create a new account on `/register`. The same email + password are saved and can immediately be used on `/login`. Duplicate email registration returns a clear message instead of creating a broken user.

## Notes
The environmental/energy calculations are transparent prototype heuristics, not a validated engineering model. The brief's production stack includes NASA POWER, Global Wind Atlas, SRTM, OSM and Copernicus Sentinel datasets, plus ML/GIS services; those external integrations can be connected after the core workflow is validated.

# Solar & Wind Deployment Intelligence Platform

Milestone 2 MVP: React frontend + FastAPI backend.

## Features
- JWT authentication
- Site management
- Environmental analysis using a deterministic demo model
- Solar potential prediction
- Wind potential prediction
- Interactive GIS map
- Assessment report dashboard

## Run Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend: http://127.0.0.1:8000/docs

## Run Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

## Demo workflow
1. Register and login.
2. Create a site with latitude, longitude, land area and elevation.
3. Open the site in the dashboard.
4. Run environmental analysis.
5. Run solar and wind predictions.
6. View the GIS map and resource assessment report.

Note: The prediction calculations are MVP/demo calculations. Replace service formulas with trained ML models and real API integrations for the final version.

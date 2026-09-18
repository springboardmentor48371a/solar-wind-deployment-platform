````markdown
# AI-Driven Solar & Wind Prediction Platform

An AI-powered platform that helps users analyse and compare potential locations for solar and wind energy deployment using environmental, geographic, infrastructure, and machine-learning data.

## Key Features

- User registration and login
- Create and manage renewable-energy projects
- Add multiple candidate sites
- Solar and wind energy prediction using Random Forest Regression
- Site suitability scoring
- Site comparison and ranking
- Recommendations for suitable locations
- Analytics and visualisations
- ML model information and evaluation

## Machine Learning

The system uses two Random Forest Regression models:

- **Solar Model** – predicts annual solar energy generation
- **Wind Model** – predicts annual wind energy generation

The models use factors such as solar irradiance, wind speed, temperature, rainfall, cloud cover, elevation, slope, land area, latitude, longitude, vegetation index, and infrastructure distances.

> The current ML development model uses synthetic data for demonstration. Real datasets can be integrated for production use.

## Site Suitability

The overall suitability score considers:

- Renewable Resource Availability – 35%
- Geographic Suitability – 25%
- Infrastructure Accessibility – 15%
- Environmental Impact – 15%
- Economic Feasibility – 10%

## Application Workflow

```text
Login
  ↓
Create Project
  ↓
Add Candidate Sites
  ↓
Enter Site Data
  ↓
ML Prediction
  ↓
Suitability Scoring
  ↓
Site Comparison
  ↓
Recommendation & Analytics
````

## Project Structure

```text
Solar_and_Wind_Prediction/
├── backend/
│   ├── auth.py
│   ├── database.py
│   ├── main.py
│   ├── ml_models.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   └── package-lock.json
│
├── docs/
├── README.md
└── RUN_FIRST.txt
```

## Tech Stack

**Frontend:** React.js, Vite, JavaScript, CSS, Recharts
**Backend:** Python, FastAPI, Uvicorn
**Database:** SQLite
**Machine Learning:** Scikit-learn, Pandas, NumPy, Joblib
**Authentication:** JWT
**Version Control:** Git & GitHub

## How to Run

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Project Outcome

The platform combines **Machine Learning + site suitability analysis + site comparison** to support solar and wind deployment planning and location-based decision making.

```
```



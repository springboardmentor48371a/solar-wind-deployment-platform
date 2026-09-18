# Solar and Wind Prediction

<<<<<<< HEAD
## Renewable Energy Deployment Intelligence Platform

A full-stack web application for renewable-energy site planning. Users can register and log in, create projects, add multiple candidate sites, analyse solar and wind conditions, compare sites, view suitability rankings, and review machine-learning energy predictions.

## Main Features

The application provides secure account registration and login, project management, candidate-site registration, weighted site suitability scoring, site-to-site comparison, dashboard analytics, Random Forest solar and wind energy prediction, recommendations, and CSV reporting.

For each project, multiple sites can be registered. The **Recommendations** page ranks the sites so the highest-scoring candidate is clearly identified as the current best site for that project or across the workspace.

## Machine Learning

The project uses **two Random Forest Regressor models**: one for estimated annual solar energy and one for estimated annual wind energy. The models use site characteristics such as solar irradiance, wind speed, temperature, cloud cover, elevation, slope, land area, coordinates and infrastructure distances.

The ML pipeline is implemented in `backend/ml_models.py`. On first run, it creates a reproducible development dataset, trains the models and stores the generated model files locally. The bundled training data is synthetic and is intended for demonstrating the ML pipeline. For real-world engineering or investment decisions, it must be replaced with validated historical observations.
=======
A renewable energy deployment intelligence platform that helps users analyse potential solar and wind sites, calculate suitability scores, estimate energy generation, and make deployment recommendations.

## Features

* User registration and login
* JWT authentication
* Role-based access
* Project and site management
* Solar and wind resource analysis
* Environmental and geographic analysis
* Site suitability scoring
* Energy generation estimation
* Site recommendations
* Dashboard and analytics
* Site assessment report export

## Technology Stack

**Frontend**

* React.js
* JavaScript
* Vite
* Recharts
* CSS

**Backend**

* Python
* FastAPI
* JWT Authentication

**Database**

* SQLite
>>>>>>> origin/vaishnavi-gokarna

## Project Structure

```text
<<<<<<< HEAD
Solar_and_Wind_Prediction/
=======
solar-wind-deployment-platform/
│
>>>>>>> origin/vaishnavi-gokarna
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
<<<<<<< HEAD
│   ├── ml_models.py
│   ├── requirements.txt
│   └── README.md
=======
│   └── requirements.txt
│
>>>>>>> origin/vaishnavi-gokarna
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
<<<<<<< HEAD
│   └── README.md
=======
│   └── package-lock.json
│
>>>>>>> origin/vaishnavi-gokarna
├── docs/
├── .gitignore
├── README.md
└── RUN_FIRST.txt
```

<<<<<<< HEAD
## How to Run

### 1. Backend

Open a terminal in the project folder:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

### 2. Frontend

Open a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Website: `http://localhost:5173`

Keep both terminals running while using the application.

## Application Workflow
=======
## Suitability Scoring

The platform uses the weighted scoring model from the project specification:

| Factor                          | Weight |
| ------------------------------- | -----: |
| Renewable Resource Availability |    35% |
| Geographic Suitability          |    25% |
| Infrastructure Accessibility    |    15% |
| Environmental Impact            |    15% |
| Economic Feasibility            |    10% |

## Workflow
>>>>>>> origin/vaishnavi-gokarna

```text
Register / Login
      ↓
Dashboard
      ↓
Create Project
      ↓
<<<<<<< HEAD
Add Multiple Candidate Sites
      ↓
Analyse Site Data
      ↓
Random Forest Solar + Wind Prediction
      ↓
Suitability Scoring
      ↓
Compare and Rank Sites
      ↓
Best Site Recommendation
      ↓
Analytics and Reports
```

## Suitability Model

The current suitability model follows the project brief's weighted structure: Renewable Resource Availability (35%), Geographic Suitability (25%), Infrastructure Accessibility (15%), Environmental Impact (15%), and Economic Feasibility (10%).

## Troubleshooting

If the browser shows **Failed to fetch**, make sure the FastAPI backend is running on port 8000. If the website is blank after selecting a feature, refresh once and check the browser console; the current frontend also includes an error boundary so runtime errors are displayed instead of leaving a completely blank screen.

If Python dependencies are missing after updating the project, run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If frontend dependencies are missing, run:

```powershell
cd frontend
npm install
```

## Important Note

The current ML training data is synthetic development data. The Random Forest implementation demonstrates a genuine training, evaluation and prediction pipeline, but the predictions are not validated real-world renewable-energy forecasts. A production version should train on validated historical solar/wind observations and appropriate geographic and environmental datasets.
=======
Add Site
      ↓
Enter Site Data
      ↓
Solar & Wind Analysis
      ↓
Suitability Score
      ↓
Recommendations
      ↓
Analytics & Reports
```

## How to Run

### Backend

Open a terminal:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Start the backend:

```bash
python -m uvicorn main:app --reload
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

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Testing

1. Register a new account.
2. Login using the same email and password.
3. Create a project.
4. Add a candidate site.
5. Enter environmental and geographic information.
6. Analyse the site.
7. View the suitability score and energy estimation.
8. Check recommendations and analytics.
9. Export the site assessment report.

## Future Enhancements

* PostgreSQL + PostGIS
* NASA POWER integration
* Global Wind Atlas integration
* OpenStreetMap integration
* Sentinel satellite data
* GIS mapping
* Machine-learning prediction models
* Advanced forecasting
* Deployment optimization
* Docker and cloud deployment

## Developer

**Vaishnavi Gokarna**

**Project:** Solar and Wind Prediction
>>>>>>> origin/vaishnavi-gokarna

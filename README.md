# Solar and Wind Prediction

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

## Project Structure

```text
solar-wind-deployment-platform/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
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
├── .gitignore
├── README.md
└── RUN_FIRST.txt
```

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

```text
Register / Login
      ↓
Dashboard
      ↓
Create Project
      ↓
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

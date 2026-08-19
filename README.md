Solar & Wind Deployment Intelligence Platform

A full-stack renewable energy analysis platform that helps users
evaluate solar and wind energy potential for a selected location and
available land area.

The platform combines a React frontend, FastAPI backend, PostgreSQL
database, geocoding, and environmental data APIs to calculate
renewable-energy potential and present the results through an
interactive dashboard.

Features

User registration and login

User-specific dashboard

Solar potential analysis

Wind potential analysis

Automatic latitude and longitude retrieval from location

Automatic environmental data retrieval

Land-area based renewable-energy calculations

Solar irradiance and temperature information

Wind-speed and wind-related environmental information

Renewable potential scoring and rating

Site selection module

Energy predictions

Analysis reports

Report download

PostgreSQL database for users and analysis history

FastAPI backend REST APIs

React + Vite frontend

Technology Stack

Frontend

React

JavaScript

Vite

HTML/CSS

Backend

Python

FastAPI

Uvicorn

Database

PostgreSQL

Data Sources / APIs

Geocoding service for converting location names into latitude and
longitude

NASA POWER environmental data API for solar/environmental
information

Backend environmental data retrieval for wind analysis

System Architecture

                    USER
                     |
                     v
             React Frontend
                     |
        +------------+-------------+
        |            |             |
        v            v             v
   Solar Analysis Wind Analysis  Dashboard
        |            |
        +------------+
                     |
                     v
              FastAPI Backend
                     |
          +----------+----------+
          |                     |
          v                     v
     Location /             Environmental
     Geocoding API          Data APIs
          |                     |
          +----------+----------+
                     |
                     v
             Analysis / Scoring
                     |
                     v
              PostgreSQL DB
                     |
                     v
             Results / Reports

Application Workflow

1. User registers an account
          |
          v
2. User logs in
          |
          v
3. Dashboard displays registered user's information
          |
          v
4. User selects Solar or Wind Analysis
          |
          v
5. User enters:
      - Location
      - Available land area
          |
          v
6. Backend converts location into:
      - Latitude
      - Longitude
          |
          v
7. Backend retrieves environmental data
          |
          v
8. Analysis/scoring is performed
          |
          v
9. Results are returned to React
          |
          v
10. Results are displayed and stored
          |
          v
11. User can view Predictions and Reports

Solar Analysis

The user provides:

Location

Land area in acres

The backend automatically determines the geographical coordinates and
retrieves environmental information.

The solar analysis can provide information such as:

Location

Latitude

Longitude

Land area

Solar irradiance

Temperature

Solar capacity

Daily energy

Annual energy

Efficiency

Potential score

Potential rating

Data source

Wind Analysis

The user provides:

Location

Land area in acres

Wind information is retrieved automatically by the backend.

The wind analysis provides information such as:

Location

Latitude

Longitude

Land area

Average wind speed

Wind power density when available

Potential score

Potential rating

Environmental data source

Authentication

The application provides:

Registration

Users register using:

Full name

Email

Password

Login

Users log in using:

Email

Password

After successful login, the frontend stores the logged-in user's
information so the dashboard can display the registered user's name.

Logout

The logout option clears the locally stored user session information and
returns the user to the login page.

Database

PostgreSQL is used to store application data.

The database can contain information related to:

Users

User IDs

Full names

Email addresses

Password hashes

Analysis history

Solar analysis

Wind analysis

Location information

Environmental values

Potential scores

Sensitive credentials such as database passwords and API keys should not
be committed to GitHub.

Frontend Structure

frontend/
├── public/
├── src/
│   ├── assets/
│   ├── App.jsx
│   ├── Dashboard.jsx
│   ├── SolarAnalysis.jsx
│   ├── windanalysis.jsx
│   ├── predictions.jsx
│   ├── reports.jsx
│   ├── siteselection.jsx
│   ├── login.jsx
│   ├── main.jsx
│   ├── App.css
│   ├── dashboard.css
│   ├── login.css
│   ├── predictions.css
│   ├── reports.css
│   └── ...
├── package.json
└── index.html

Backend Structure

backend/
├── main.py
├── database.py
├── models.py
├── schemas.py
├── data_sources.py
└── README.md

Running the Project

1. Start PostgreSQL

Make sure PostgreSQL is running and the project database is available.

2. Start the Backend

Open a terminal:

cd backend

Install dependencies if required:

pip install fastapi uvicorn requests psycopg2-binary pydantic

Start FastAPI:

uvicorn main:app --reload

The backend should be available at:

http://127.0.0.1:8000

FastAPI documentation:

http://127.0.0.1:8000/docs

3. Start the Frontend

Open another terminal:

cd frontend

Install dependencies:

npm install

Start Vite:

npm run dev

The frontend should be available at:

http://localhost:5173

Important Security Notes

Do not upload these files or values to GitHub:

.env
API keys
database passwords
secret tokens
PostgreSQL credentials
node_modules/
__pycache__/

Recommended .gitignore entries:

.env
node_modules/
__pycache__/
*.pyc
venv/
.venv/

Project Modules

Dashboard

Provides an overview of renewable-energy potential and quick access to
the analysis modules.

Solar Analysis

Calculates solar potential using location, land area, and environmental
data.

Wind Analysis

Calculates wind potential using location, land area, and environmental
data.

Site Selection

Provides a module for selecting and evaluating renewable-energy sites.

Predictions

Displays renewable-energy potential forecasts.

Reports

Displays analysis reports and provides download functionality.

Example User Flow

Register
   ↓
Login
   ↓
Dashboard
   ↓
Solar Analysis
   ↓
Enter "Agra"
   ↓
Enter land area
   ↓
Backend finds latitude/longitude
   ↓
Environmental data is retrieved
   ↓
Solar potential is calculated
   ↓
Result displayed
   ↓
Analysis can be used in reports/history

Future Improvements

Machine-learning based renewable-energy prediction

Interactive map-based site selection

More environmental datasets

Real-time weather information

Advanced wind-power forecasting

Satellite and GIS data integration

Cloud deployment

User-specific analysis history

PDF report generation

Improved renewable-site ranking



Project Status

The project is a working prototype demonstrating an end-to-end
renewable-energy deployment workflow with frontend, backend, database,
environmental data retrieval, analysis, predictions, and reporting
modules.

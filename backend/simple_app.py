from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
import json
import requests
import numpy as np
from typing import Dict, Any, List
import joblib

# ============================================
# APP INITIALIZATION
# ============================================
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# DATABASE SETUP
# ============================================
conn = sqlite3.connect('auth.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    role TEXT DEFAULT 'planner',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,
    description TEXT,
    technology TEXT NOT NULL,
    budget REAL DEFAULT 0,
    status TEXT DEFAULT 'DRAFT',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    site_name TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    region TEXT,
    land_area REAL,
    elevation REAL,
    land_ownership TEXT,
    existing_infrastructure TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS environmental_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER UNIQUE,
    solar_irradiance REAL,
    temperature REAL,
    rainfall REAL,
    wind_speed REAL,
    wind_direction REAL,
    cloud_cover REAL,
    slope REAL,
    ndvi REAL,
    land_cover TEXT,
    data_source TEXT,
    fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS solar_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER UNIQUE,
    peak_sun_hours REAL,
    solar_energy_potential REAL,
    capacity_factor REAL,
    performance_ratio REAL,
    monthly_generation TEXT,
    ml_prediction REAL,
    prediction_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS wind_assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER UNIQUE,
    avg_wind_speed REAL,
    wind_power_density REAL,
    capacity_factor REAL,
    annual_energy_production REAL,
    turbine_suitability TEXT,
    ml_prediction REAL,
    prediction_confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS suitability_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER UNIQUE,
    renewable_resource_score REAL,
    geographic_suitability_score REAL,
    infrastructure_accessibility_score REAL,
    environmental_impact_score REAL,
    economic_feasibility_score REAL,
    overall_score REAL,
    category TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()

print("✅ Database initialized!")

SECRET_KEY = "your-secret-key-change-this-in-production"

# ============================================
# ML MODEL LOADING
# ============================================
ML_MODEL_LOADED = False
ml_model = None
ml_scaler = None

def load_ml_models():
    global ml_model, ml_scaler, ML_MODEL_LOADED
    try:
        if os.path.exists('models/suitability_model.pkl') and os.path.exists('models/suitability_scaler.pkl'):
            ml_model = joblib.load('models/suitability_model.pkl')
            ml_scaler = joblib.load('models/suitability_scaler.pkl')
            ML_MODEL_LOADED = True
            print("✅ ML Model loaded successfully!")
        else:
            print("⚠️ ML models not found. Run ml_train_full.py first.")
    except Exception as e:
        print(f"⚠️ Error loading ML models: {e}")

load_ml_models()

# ============================================
# TOKEN EXTRACTION DEPENDENCY
# ============================================
async def get_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    return token

# ============================================
# PYDANTIC MODELS
# ============================================
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "planner"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ProjectCreate(BaseModel):
    project_name: str
    description: str = None
    technology: str = "SOLAR"
    budget: float = 0.0

class SiteCreate(BaseModel):
    project_id: int
    site_name: str
    latitude: float
    longitude: float
    region: str = None
    land_area: float = None
    elevation: float = None
    land_ownership: str = None
    existing_infrastructure: str = None

class MLPredictionRequest(BaseModel):
    solar_irradiance: float = 5.0
    temperature: float = 25.0
    rainfall: float = 800.0
    wind_speed: float = 5.0
    cloud_cover: float = 30.0
    elevation: float = 150.0
    slope: float = 5.0
    ndvi: float = 0.2
    land_area: float = 100.0
    road_dist: float = 2.0
    power_dist: float = 3.0

class LocationPredictionRequest(BaseModel):
    location: str
    land_area: float = 100.0

class GeocodeRequest(BaseModel):
    location: str

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_user_by_email(email):
    cursor.execute("SELECT id, name, email, password_hash, is_active, role FROM users WHERE email = ?", (email,))
    return cursor.fetchone()

def create_token(email):
    return jwt.encode(
        {"sub": email, "exp": datetime.utcnow() + timedelta(days=7)},
        SECRET_KEY,
        algorithm="HS256"
    )

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except:
        return None

# ============================================
# GEOCODING FUNCTIONS
# ============================================
def geocode_location(location: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": location, "format": "json", "limit": 1}
    headers = {"User-Agent": "SolarWindPlatform/1.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None, None

def get_elevation(lat: float, lon: float):
    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("results"):
            return data["results"][0]["elevation"]
    except:
        pass
    return 150.0

# ============================================
# NASA POWER SERVICE
# ============================================
NASA_POWER_API = "https://power.larc.nasa.gov/api/power"

def fetch_environmental_data(lat: float, lon: float) -> Dict[str, Any]:
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    result = {"success": False, "data": {}, "error": None}
    
    try:
        # Solar irradiance
        resp = requests.get(f"{NASA_POWER_API}/daily", params={
            "request": "execute", "parameters": "ALLSKY_SFC_SW_DWN",
            "startDate": start_date, "endDate": end_date,
            "userCommunity": "RE", "format": "JSON",
            "latitude": lat, "longitude": lon
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vals = data.get("properties", {}).get("parameter", {}).get("ALLSKY_SFC_SW_DWN", {})
        irradiance = sum(vals.values())/len(vals) if vals else 5.0

        # Temperature
        resp = requests.get(f"{NASA_POWER_API}/daily", params={
            "request": "execute", "parameters": "T2M",
            "startDate": start_date, "endDate": end_date,
            "userCommunity": "RE", "format": "JSON",
            "latitude": lat, "longitude": lon
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vals = data.get("properties", {}).get("parameter", {}).get("T2M", {})
        temp = sum(vals.values())/len(vals) if vals else 25.0

        # Precipitation
        resp = requests.get(f"{NASA_POWER_API}/daily", params={
            "request": "execute", "parameters": "PRECTOTCORR",
            "startDate": start_date, "endDate": end_date,
            "userCommunity": "RE", "format": "JSON",
            "latitude": lat, "longitude": lon
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vals = data.get("properties", {}).get("parameter", {}).get("PRECTOTCORR", {})
        rainfall = (sum(vals.values())/len(vals) * 365) if vals else 800.0

        # Wind speed
        resp = requests.get(f"{NASA_POWER_API}/daily", params={
            "request": "execute", "parameters": "WS10M",
            "startDate": start_date, "endDate": end_date,
            "userCommunity": "RE", "format": "JSON",
            "latitude": lat, "longitude": lon
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vals = data.get("properties", {}).get("parameter", {}).get("WS10M", {})
        wind = sum(vals.values())/len(vals) if vals else 5.0

        # Cloud cover
        resp = requests.get(f"{NASA_POWER_API}/daily", params={
            "request": "execute", "parameters": "CLOUD_AMT",
            "startDate": start_date, "endDate": end_date,
            "userCommunity": "RE", "format": "JSON",
            "latitude": lat, "longitude": lon
        }, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        vals = data.get("properties", {}).get("parameter", {}).get("CLOUD_AMT", {})
        cloud = sum(vals.values())/len(vals) if vals else 30.0

        result["success"] = True
        result["data"] = {
            "solar_irradiance": round(irradiance, 2),
            "temperature": round(temp, 2),
            "rainfall": round(rainfall, 2),
            "wind_speed": round(wind, 2),
            "cloud_cover": round(cloud, 2),
            "lat": lat,
            "lon": lon,
            "fetch_date": datetime.now().isoformat()
        }
        return result
    except Exception as e:
        result["error"] = str(e)
        return result

# ============================================
# SOLAR ENGINE
# ============================================
class SolarEngine:
    def predict_solar_potential(self, lat, lon, irradiance, temperature, cloud_cover, elevation, slope, ndvi, capacity_mw=1.0):
        peak_sun_hours = irradiance
        performance_ratio = 0.80
        annual_energy = capacity_mw * peak_sun_hours * 365 * performance_ratio
        capacity_factor = (annual_energy / (capacity_mw * 8760)) * 100
        
        quality_score = 0
        quality_score += min(irradiance / 6.0, 1.0) * 0.4
        quality_score += min(1 / (1 + abs(temperature - 25) / 20), 1.0) * 0.2
        quality_score += min(1 / (1 + cloud_cover / 50), 1.0) * 0.2
        quality_score += min(1 / (1 + slope / 30), 1.0) * 0.1
        quality_score += min(1 / (1 + ndvi * 2), 1.0) * 0.1
        quality_score *= 100
        
        monthly = []
        for m in range(1, 13):
            factor = 0.7 + 0.6 * np.sin((m - 3) * np.pi / 6)
            monthly.append({"month": m, "energy_mwh": round((annual_energy/12) * factor, 2)})
        
        return {
            "peak_sun_hours": round(peak_sun_hours, 2),
            "annual_energy_mwh": round(annual_energy, 2),
            "capacity_factor": round(capacity_factor, 2),
            "performance_ratio": performance_ratio,
            "quality_score": round(quality_score, 2),
            "monthly_generation": monthly,
            "recommendations": ["Site shows good solar potential."] if quality_score > 60 else ["Consider other locations."]
        }

solar_engine = SolarEngine()

# ============================================
# WIND ENGINE
# ============================================
class WindEngine:
    def predict_wind_potential(self, lat, lon, wind_speed, temperature, elevation, terrain="flat", capacity_mw=2.0):
        air_density = 1.225
        power_density = 0.5 * air_density * (wind_speed ** 3)
        rotor_diameter = 100
        swept_area = np.pi * (rotor_diameter / 2) ** 2
        theoretical_power = (power_density * swept_area) / 1_000_000
        efficiency = 0.45
        annual_energy = theoretical_power * 8760 * efficiency
        capacity_factor = (annual_energy / (capacity_mw * 8760)) * 100
        
        quality_score = 0
        quality_score += min(wind_speed / 10.0, 1.0) * 0.5
        terrain_bonus = {"flat": 0.2, "hilly": 0.15, "coastal": 0.25, "mountain": 0.1}
        quality_score += terrain_bonus.get(terrain, 0.2)
        quality_score += min(1 / (1 + abs(temperature - 15) / 25), 1.0) * 0.2
        quality_score += min(1 / (1 + elevation / 1000), 1.0) * 0.1
        quality_score *= 100
        
        monthly = []
        for m in range(1, 13):
            factor = 0.6 + 0.6 * np.sin((m - 1) * np.pi / 6)
            monthly.append({"month": m, "energy_mwh": round((annual_energy/12) * factor, 2)})
        
        return {
            "avg_wind_speed": round(wind_speed, 2),
            "power_density": round(power_density, 2),
            "annual_energy_mwh": round(annual_energy, 2),
            "capacity_factor": round(capacity_factor, 2),
            "quality_score": round(quality_score, 2),
            "monthly_generation": monthly,
            "recommendations": ["Good wind potential."] if quality_score > 60 else ["Consider other locations."]
        }

wind_engine = WindEngine()

# ============================================
# SUITABILITY ENGINE
# ============================================
class SuitabilityEngine:
    def calculate_suitability_score(self, solar_score, wind_score, geographic_score, infrastructure_score, environmental_score, economic_score):
        overall = (solar_score + wind_score) / 2 * 0.35 + geographic_score * 0.25 + infrastructure_score * 0.15 + environmental_score * 0.15 + economic_score * 0.10
        overall = min(max(overall, 0), 100)
        if overall >= 90: category = "Excellent"
        elif overall >= 80: category = "Highly Suitable"
        elif overall >= 65: category = "Moderately Suitable"
        elif overall >= 40: category = "Low Suitability"
        else: category = "Unsuitable"
        recommendations = []
        if overall < 40: recommendations.append("❌ Low suitability. Consider alternative sites.")
        if solar_score < 40: recommendations.append("☀️ Low solar potential.")
        if wind_score < 40: recommendations.append("💨 Low wind potential.")
        if overall >= 80: recommendations.append("✅ Highly recommended for deployment.")
        if not recommendations: recommendations.append("Site shows balanced potential.")
        return {
            "overall_score": round(overall, 2),
            "category": category,
            "scores": {
                "renewable_resource": round((solar_score + wind_score)/2, 2),
                "geographic_suitability": round(geographic_score, 2),
                "infrastructure": round(infrastructure_score, 2),
                "environmental": round(environmental_score, 2),
                "economic": round(economic_score, 2)
            },
            "recommendations": recommendations
        }

suitability_engine = SuitabilityEngine()

# ============================================
# ROOT ROUTE
# ============================================
@app.get("/")
def root():
    return {"message": "Solar & Wind Deployment Intelligence Platform API", "version": "2.0.0"}

# ============================================
# AUTH ROUTES
# ============================================
@app.post("/api/auth/register")
def register(user: UserCreate):
    if get_user_by_email(user.email):
        return {"error": "Email already exists"}, 400
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), salt)
    cursor.execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
        (user.name, user.email, hashed.decode('utf-8'), user.role)
    )
    conn.commit()
    return {"message": "User created successfully", "user": {"name": user.name, "email": user.email, "role": user.role}}

@app.post("/api/auth/login")
def login(user: UserLogin):
    result = get_user_by_email(user.email)
    if not result or not bcrypt.checkpw(user.password.encode('utf-8'), result[3].encode('utf-8')):
        return {"error": "Invalid credentials"}, 401
    token = create_token(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": result[0], "name": result[1], "email": result[2], "is_active": bool(result[4]), "role": result[5]}
    }

@app.get("/api/auth/me")
def get_me(token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Invalid token"}, 401
    result = get_user_by_email(email)
    if not result:
        return {"error": "User not found"}, 404
    return {"id": result[0], "name": result[1], "email": result[2], "is_active": bool(result[4]), "role": result[5]}

# ============================================
# PROJECT ROUTES
# ============================================
@app.post("/api/projects")
def create_project(project: ProjectCreate, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    user = get_user_by_email(email)
    if not user:
        return {"error": "User not found"}, 404
    cursor.execute(
        "INSERT INTO projects (project_name, description, technology, budget, created_by) VALUES (?, ?, ?, ?, ?)",
        (project.project_name, project.description, project.technology, project.budget, user[0])
    )
    conn.commit()
    pid = cursor.lastrowid
    cursor.execute("SELECT * FROM projects WHERE id = ?", (pid,))
    row = cursor.fetchone()
    return {"id": row[0], "project_name": row[1], "description": row[2], "technology": row[3], "budget": row[4], "status": row[5], "created_by": row[6], "created_at": row[7]}

@app.get("/api/projects")
def get_projects(token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT * FROM projects")
    rows = cursor.fetchall()
    return [{"id": r[0], "project_name": r[1], "description": r[2], "technology": r[3], "budget": r[4], "status": r[5], "created_by": r[6], "created_at": r[7]} for r in rows]

@app.delete("/api/projects/{project_id}")
def delete_project(project_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    return {"message": "Project deleted"}

# ============================================
# SITE ROUTES
# ============================================
@app.post("/api/sites")
def create_site(site: SiteCreate, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute(
        "INSERT INTO sites (project_id, site_name, latitude, longitude, region, land_area, elevation, land_ownership, existing_infrastructure) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (site.project_id, site.site_name, site.latitude, site.longitude, site.region, site.land_area, site.elevation, site.land_ownership, site.existing_infrastructure)
    )
    conn.commit()
    sid = cursor.lastrowid
    cursor.execute("SELECT * FROM sites WHERE id = ?", (sid,))
    row = cursor.fetchone()
    return {"id": row[0], "project_id": row[1], "site_name": row[2], "latitude": row[3], "longitude": row[4], "region": row[5], "land_area": row[6], "elevation": row[7], "land_ownership": row[8], "existing_infrastructure": row[9], "created_at": row[10]}

@app.get("/api/sites")
def get_sites(project_id: int = None, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    if project_id:
        cursor.execute("SELECT * FROM sites WHERE project_id = ?", (project_id,))
    else:
        cursor.execute("SELECT * FROM sites")
    rows = cursor.fetchall()
    return [{"id": r[0], "project_id": r[1], "site_name": r[2], "latitude": r[3], "longitude": r[4], "region": r[5], "land_area": r[6], "elevation": r[7], "land_ownership": r[8], "existing_infrastructure": r[9], "created_at": r[10]} for r in rows]

@app.get("/api/sites/{site_id}")
def get_site(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT * FROM sites WHERE id = ?", (site_id,))
    row = cursor.fetchone()
    if not row:
        return {"error": "Site not found"}, 404
    return {"id": row[0], "project_id": row[1], "site_name": row[2], "latitude": row[3], "longitude": row[4], "region": row[5], "land_area": row[6], "elevation": row[7], "land_ownership": row[8], "existing_infrastructure": row[9], "created_at": row[10]}

@app.delete("/api/sites/{site_id}")
def delete_site(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("DELETE FROM sites WHERE id = ?", (site_id,))
    conn.commit()
    return {"message": "Site deleted"}

# ============================================
# GEOCODE ENDPOINT
# ============================================
@app.post("/api/geocode")
def geocode(req: GeocodeRequest, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    lat, lon = geocode_location(req.location)
    if lat is None:
        return {"error": "Location not found"}, 404
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    headers = {"User-Agent": "SolarWindPlatform/1.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()
        display_name = data.get("display_name", req.location)
    except:
        display_name = req.location
    return {"latitude": lat, "longitude": lon, "display_name": display_name}

# ============================================
# ENVIRONMENTAL ROUTES
# ============================================
@app.get("/api/environmental/fetch/{site_id}")
def fetch_environmental(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT latitude, longitude FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()
    if not site:
        return {"error": "Site not found"}, 404
    data = fetch_environmental_data(site[0], site[1])
    if not data["success"]:
        return {"error": data.get("error", "Failed to fetch")}, 500
    env = data["data"]
    cursor.execute(
        "INSERT OR REPLACE INTO environmental_data (site_id, solar_irradiance, temperature, rainfall, wind_speed, cloud_cover, data_source) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (site_id, env["solar_irradiance"], env["temperature"], env["rainfall"], env["wind_speed"], env["cloud_cover"], "NASA POWER")
    )
    conn.commit()
    return {"message": "Environmental data fetched and saved", "data": env}

@app.get("/api/environmental/{site_id}")
def get_environmental(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT * FROM environmental_data WHERE site_id = ?", (site_id,))
    row = cursor.fetchone()
    if not row:
        return {"error": "No data found"}, 404
    return {"id": row[0], "site_id": row[1], "solar_irradiance": row[2], "temperature": row[3], "rainfall": row[4], "wind_speed": row[5], "wind_direction": row[6], "cloud_cover": row[7], "slope": row[8], "ndvi": row[9], "land_cover": row[10], "data_source": row[11], "fetch_date": row[12]}

# ============================================
# SOLAR ROUTES
# ============================================
@app.post("/api/solar/analyze/{site_id}")
def analyze_solar(site_id: int, capacity_mw: float = 1.0, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT latitude, longitude, site_name FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()
    if not site:
        return {"error": "Site not found"}, 404
    cursor.execute("SELECT * FROM environmental_data WHERE site_id = ?", (site_id,))
    env = cursor.fetchone()
    if not env:
        return {"error": "Environmental data not found. Fetch first."}, 404
    result = solar_engine.predict_solar_potential(
        lat=site[0], lon=site[1],
        irradiance=env[2] or 5.0,
        temperature=env[3] or 25.0,
        cloud_cover=env[7] or 30.0,
        elevation=0, slope=0, ndvi=0.2,
        capacity_mw=capacity_mw
    )
    cursor.execute(
        "INSERT OR REPLACE INTO solar_assessments (site_id, peak_sun_hours, solar_energy_potential, capacity_factor, performance_ratio, monthly_generation, ml_prediction, prediction_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (site_id, result["peak_sun_hours"], result["annual_energy_mwh"], result["capacity_factor"], result["performance_ratio"], json.dumps(result["monthly_generation"]), result["quality_score"], 0.85)
    )
    conn.commit()
    return {"message": "Solar analysis completed", "result": result}

@app.get("/api/solar/assessment/{site_id}")
def get_solar_assessment(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT * FROM solar_assessments WHERE site_id = ?", (site_id,))
    row = cursor.fetchone()
    if not row:
        return {"error": "No assessment found"}, 404
    return {"id": row[0], "site_id": row[1], "peak_sun_hours": row[2], "annual_energy_mwh": row[3], "capacity_factor": row[4], "performance_ratio": row[5], "monthly_generation": json.loads(row[6]) if row[6] else [], "quality_score": row[7], "created_at": row[9]}

# ============================================
# WIND ROUTES
# ============================================
@app.post("/api/wind/analyze/{site_id}")
def analyze_wind(site_id: int, capacity_mw: float = 2.0, terrain: str = "flat", token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT latitude, longitude, site_name, elevation FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()
    if not site:
        return {"error": "Site not found"}, 404
    cursor.execute("SELECT * FROM environmental_data WHERE site_id = ?", (site_id,))
    env = cursor.fetchone()
    if not env:
        return {"error": "Environmental data not found. Fetch first."}, 404
    result = wind_engine.predict_wind_potential(
        lat=site[0], lon=site[1],
        wind_speed=env[5] or 5.0,
        temperature=env[3] or 25.0,
        elevation=site[3] or 0,
        terrain=terrain,
        capacity_mw=capacity_mw
    )
    cursor.execute(
        "INSERT OR REPLACE INTO wind_assessments (site_id, avg_wind_speed, wind_power_density, capacity_factor, annual_energy_production, turbine_suitability, ml_prediction, prediction_confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (site_id, result["avg_wind_speed"], result["power_density"], result["capacity_factor"], result["annual_energy_mwh"], json.dumps(result["recommendations"]), result["quality_score"], 0.85)
    )
    conn.commit()
    return {"message": "Wind analysis completed", "result": result}

@app.get("/api/wind/assessment/{site_id}")
def get_wind_assessment(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT * FROM wind_assessments WHERE site_id = ?", (site_id,))
    row = cursor.fetchone()
    if not row:
        return {"error": "No assessment found"}, 404
    return {"id": row[0], "site_id": row[1], "avg_wind_speed": row[2], "power_density": row[3], "capacity_factor": row[4], "annual_energy_mwh": row[5], "turbine_suitability": json.loads(row[6]) if row[6] else [], "quality_score": row[7], "created_at": row[9]}

# ============================================
# SUITABILITY ROUTES
# ============================================
@app.post("/api/suitability/analyze/{site_id}")
def analyze_suitability(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT site_name FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()
    if not site:
        return {"error": "Site not found"}, 404
    cursor.execute("SELECT * FROM solar_assessments WHERE site_id = ?", (site_id,))
    solar = cursor.fetchone()
    cursor.execute("SELECT * FROM wind_assessments WHERE site_id = ?", (site_id,))
    wind = cursor.fetchone()
    if not solar or not wind:
        return {"error": "Solar and wind assessments required. Run analyses first."}, 404
    solar_score = solar[7] or 50.0
    wind_score = wind[7] or 50.0
    geographic_score = 70.0
    infrastructure_score = 60.0
    environmental_score = 75.0
    economic_score = 65.0
    result = suitability_engine.calculate_suitability_score(
        solar_score, wind_score, geographic_score, infrastructure_score, environmental_score, economic_score
    )
    cursor.execute(
        "INSERT OR REPLACE INTO suitability_scores (site_id, renewable_resource_score, geographic_suitability_score, infrastructure_accessibility_score, environmental_impact_score, economic_feasibility_score, overall_score, category, recommendations) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (site_id, (solar_score + wind_score)/2, geographic_score, infrastructure_score, environmental_score, economic_score, result["overall_score"], result["category"], " | ".join(result["recommendations"]))
    )
    conn.commit()
    return {"message": "Suitability analysis completed", "result": result}

@app.get("/api/suitability/score/{site_id}")
def get_suitability(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    cursor.execute("SELECT * FROM suitability_scores WHERE site_id = ?", (site_id,))
    row = cursor.fetchone()
    if not row:
        return {"error": "No score found"}, 404
    return {
        "id": row[0], "site_id": row[1],
        "scores": {"renewable_resource": row[2], "geographic_suitability": row[3], "infrastructure": row[4], "environmental": row[5], "economic": row[6]},
        "overall_score": row[7], "category": row[8],
        "recommendations": row[9].split(" | ") if row[9] else [],
        "created_at": row[10]
    }

# ============================================
# OPTIMIZATION ENGINE
# ============================================
@app.get("/api/optimization/recommend")
def recommend_best_sites(project_id: int = None, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    
    if project_id:
        cursor.execute("SELECT id, site_name, latitude, longitude, project_id FROM sites WHERE project_id = ?", (project_id,))
    else:
        cursor.execute("SELECT id, site_name, latitude, longitude, project_id FROM sites")
    sites = cursor.fetchall()
    
    recommendations = []
    for site in sites:
        site_id = site[0]
        cursor.execute("SELECT overall_score, category FROM suitability_scores WHERE site_id = ?", (site_id,))
        score_row = cursor.fetchone()
        if score_row:
            overall_score = score_row[0] or 0
            category = score_row[1] or "Not Analyzed"
            cursor.execute("SELECT solar_energy_potential FROM solar_assessments WHERE site_id = ?", (site_id,))
            solar = cursor.fetchone()
            cursor.execute("SELECT annual_energy_production FROM wind_assessments WHERE site_id = ?", (site_id,))
            wind = cursor.fetchone()
            annual_energy = (solar[0] if solar else 0) + (wind[0] if wind else 0)
            recommendations.append({
                "site_id": site_id,
                "site_name": site[1],
                "latitude": site[2],
                "longitude": site[3],
                "project_id": site[4],
                "overall_score": overall_score,
                "category": category,
                "annual_energy_mwh": round(annual_energy, 2)
            })
    
    recommendations.sort(key=lambda x: x["overall_score"], reverse=True)
    for i, rec in enumerate(recommendations):
        rec["rank"] = i + 1
    
    return {
        "message": f"Found {len(recommendations)} sites",
        "recommendations": recommendations,
        "top_site": recommendations[0] if recommendations else None
    }

# ============================================
# INVESTMENT ANALYSIS
# ============================================
@app.post("/api/investment/analyze/{site_id}")
def analyze_investment(site_id: int, capex_per_mw: float = 1_200_000, opex_percent: float = 2.0, electricity_price: float = 0.08, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    
    cursor.execute("SELECT site_name FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()
    if not site:
        return {"error": "Site not found"}, 404
    
    cursor.execute("SELECT overall_score FROM suitability_scores WHERE site_id = ?", (site_id,))
    score_row = cursor.fetchone()
    if not score_row:
        return {"error": "Suitability score not found. Run suitability analysis first."}, 404
    
    overall_score = score_row[0]
    if overall_score < 40:
        return {"error": "Site has low suitability (<40), investment not recommended."}, 400
    
    cursor.execute("SELECT solar_energy_potential FROM solar_assessments WHERE site_id = ?", (site_id,))
    solar = cursor.fetchone()
    cursor.execute("SELECT annual_energy_production FROM wind_assessments WHERE site_id = ?", (site_id,))
    wind = cursor.fetchone()
    annual_energy = (solar[0] if solar else 0) + (wind[0] if wind else 0)
    if annual_energy == 0:
        return {"error": "Annual energy not estimated. Run solar/wind analysis first."}, 400
    
    capacity_mw = 1.0
    
    total_capex = capex_per_mw * capacity_mw
    annual_opex = total_capex * (opex_percent / 100)
    annual_revenue = annual_energy * 1000 * electricity_price
    annual_net_profit = annual_revenue - annual_opex
    payback_period = total_capex / annual_net_profit if annual_net_profit > 0 else float('inf')
    roi = (annual_net_profit / total_capex) * 100
    
    discount_rate = 0.08
    npv = -total_capex
    for year in range(1, 11):
        npv += annual_net_profit / ((1 + discount_rate) ** year)
    
    return {
        "site_id": site_id,
        "site_name": site[0],
        "overall_score": overall_score,
        "annual_energy_mwh": annual_energy,
        "investment": {
            "capex": round(total_capex, 2),
            "annual_opex": round(annual_opex, 2),
            "annual_revenue": round(annual_revenue, 2),
            "annual_net_profit": round(annual_net_profit, 2),
            "payback_period_years": round(payback_period, 2) if payback_period != float('inf') else ">20 years",
            "roi_percent": round(roi, 2),
            "npv_10yr": round(npv, 2)
        },
        "recommendation": "Strongly recommended" if overall_score > 80 and payback_period < 10 else "Consider with caution" if overall_score > 60 else "Not recommended"
    }

# ============================================
# FORECASTING ENGINE
# ============================================
@app.get("/api/forecasting/site/{site_id}")
def get_energy_forecast(site_id: int, months: int = 12, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    
    cursor.execute("SELECT site_name FROM sites WHERE id = ?", (site_id,))
    site = cursor.fetchone()
    if not site:
        return {"error": "Site not found"}, 404
    
    cursor.execute("SELECT monthly_generation FROM solar_assessments WHERE site_id = ?", (site_id,))
    solar_row = cursor.fetchone()
    cursor.execute("SELECT monthly_generation FROM wind_assessments WHERE site_id = ?", (site_id,))
    wind_row = cursor.fetchone()
    
    solar_months = json.loads(solar_row[0]) if solar_row and solar_row[0] else []
    wind_months = json.loads(wind_row[0]) if wind_row and wind_row[0] else []
    
    combined = []
    for m in range(1, 13):
        solar_val = next((item["energy_mwh"] for item in solar_months if item["month"] == m), 0)
        wind_val = next((item["energy_mwh"] for item in wind_months if item["month"] == m), 0)
        combined.append({
            "month": m,
            "solar_mwh": round(solar_val, 2),
            "wind_mwh": round(wind_val, 2),
            "total_mwh": round(solar_val + wind_val, 2)
        })
    
    forecast = []
    for i in range(months):
        month_idx = i % 12
        forecast.append({
            "month_offset": i + 1,
            "month": combined[month_idx]["month"],
            "total_mwh": round(combined[month_idx]["total_mwh"] * (1 + i * 0.005), 2)
        })
    
    return {
        "site_id": site_id,
        "site_name": site[0],
        "base_monthly": combined,
        "forecast_months": forecast,
        "annual_estimate": round(sum(item["total_mwh"] for item in combined), 2)
    }

# ============================================
# ML PREDICTION ENDPOINTS
# ============================================
@app.post("/api/ml/predict")
def ml_predict(features: MLPredictionRequest, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    if not ML_MODEL_LOADED:
        return {"error": "ML model not loaded. Train first."}, 503
    
    feature_cols = ['solar_irradiance', 'temperature', 'rainfall', 'wind_speed', 'cloud_cover',
                    'elevation', 'slope', 'ndvi', 'land_area', 'road_dist', 'power_dist']
    X = np.array([[getattr(features, f) for f in feature_cols]])
    X_scaled = ml_scaler.transform(X)
    prediction = ml_model.predict(X_scaled)[0]
    if prediction >= 90: category = "Excellent"
    elif prediction >= 80: category = "Highly Suitable"
    elif prediction >= 65: category = "Moderately Suitable"
    elif prediction >= 40: category = "Low Suitability"
    else: category = "Unsuitable"
    return {"suitability_score": round(prediction, 2), "category": category, "features": features.dict()}

@app.post("/api/ml/predict-location")
def predict_by_location(req: LocationPredictionRequest, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    lat, lon = geocode_location(req.location)
    if lat is None:
        return {"error": "Location not found"}, 404
    env_data = fetch_environmental_data(lat, lon)
    if not env_data["success"]:
        return {"error": "Failed to fetch environmental data"}, 500
    env = env_data["data"]
    elevation = get_elevation(lat, lon)
    features = {
        "solar_irradiance": env["solar_irradiance"],
        "temperature": env["temperature"],
        "rainfall": env["rainfall"],
        "wind_speed": env["wind_speed"],
        "cloud_cover": env["cloud_cover"],
        "elevation": elevation,
        "slope": 5.0,
        "ndvi": 0.2,
        "land_area": req.land_area,
        "road_dist": 2.0,
        "power_dist": 3.0
    }
    if not ML_MODEL_LOADED:
        return {"error": "ML model not loaded"}, 503
    feature_cols = ['solar_irradiance', 'temperature', 'rainfall', 'wind_speed', 'cloud_cover',
                    'elevation', 'slope', 'ndvi', 'land_area', 'road_dist', 'power_dist']
    X = np.array([[features[f] for f in feature_cols]])
    X_scaled = ml_scaler.transform(X)
    prediction = ml_model.predict(X_scaled)[0]
    if prediction >= 90: category = "Excellent"
    elif prediction >= 80: category = "Highly Suitable"
    elif prediction >= 65: category = "Moderately Suitable"
    elif prediction >= 40: category = "Low Suitability"
    else: category = "Unsuitable"
    return {
        "location": req.location,
        "latitude": lat,
        "longitude": lon,
        "suitability_score": round(prediction, 2),
        "category": category,
        "environmental_data": env,
        "features_used": features
    }

@app.post("/api/ml/retrain")
def retrain_model(token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401
    user = get_user_by_email(email)
    if user and user[5] != "admin":
        return {"error": "Admin access required"}, 403
    try:
        import subprocess
        result = subprocess.run(['python', 'ml_train_full.py'], capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            load_ml_models()
            return {"message": "Model retrained successfully", "output": result.stdout}
        else:
            return {"error": "Training failed", "output": result.stderr}, 500
    except Exception as e:
        return {"error": str(e)}, 500

# ============================================
# RUN APP
# ============================================
if __name__ == "__main__":
    import uvicorn
    print("="*50)
    print("🚀 Starting Solar & Wind Intelligence API v2.0")
    print("📝 API running on: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🤖 ML Model Loaded:", "✅" if ML_MODEL_LOADED else "❌")
    print("="*50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
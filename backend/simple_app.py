from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
import sqlite3
import bcrypt
import jwt
from datetime import datetime, timedelta
import os
import json
import requests
import numpy as np
import math
from typing import Dict, Any, List, Optional
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
import threading
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auth.db")
_db_local = threading.local()

def _new_connection():
    c = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c

class _ConnectionProxy:
    def _get(self):
        if not hasattr(_db_local, "connection"):
            _db_local.connection = _new_connection()
        return _db_local.connection
    def __getattr__(self, name):
        return getattr(self._get(), name)

class _CursorProxy:
    def _get_conn(self):
        if not hasattr(_db_local, "connection"):
            _db_local.connection = _new_connection()
        return _db_local.connection
    def _get(self):
        if not hasattr(_db_local, "cursor"):
            _db_local.cursor = self._get_conn().cursor()
        return _db_local.cursor
    def __getattr__(self, name):
        return getattr(self._get(), name)
    def execute(self, *args, **kwargs):
        return self._get().execute(*args, **kwargs)
    def executemany(self, *args, **kwargs):
        return self._get().executemany(*args, **kwargs)
    def fetchone(self):
        return self._get().fetchone()
    def fetchall(self):
        return self._get().fetchall()

conn = _ConnectionProxy()
cursor = _CursorProxy()

_init_conn = _new_connection()
_init_cursor = _init_conn.cursor()
_init_cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, is_active INTEGER DEFAULT 1, role TEXT DEFAULT 'planner', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, project_name TEXT NOT NULL, description TEXT, technology TEXT NOT NULL, budget REAL DEFAULT 0, status TEXT DEFAULT 'DRAFT', created_by INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS sites (id INTEGER PRIMARY KEY AUTOINCREMENT, project_id INTEGER, site_name TEXT NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, region TEXT, land_area REAL, elevation REAL, land_ownership TEXT, existing_infrastructure TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS environmental_data (id INTEGER PRIMARY KEY AUTOINCREMENT, site_id INTEGER UNIQUE, solar_irradiance REAL, temperature REAL, rainfall REAL, wind_speed REAL, wind_direction REAL, cloud_cover REAL, slope REAL, ndvi REAL, land_cover TEXT, data_source TEXT, fetch_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS solar_assessments (id INTEGER PRIMARY KEY AUTOINCREMENT, site_id INTEGER UNIQUE, peak_sun_hours REAL, solar_energy_potential REAL, capacity_factor REAL, performance_ratio REAL, monthly_generation TEXT, ml_prediction REAL, prediction_confidence REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, quality_score REAL);
CREATE TABLE IF NOT EXISTS wind_assessments (id INTEGER PRIMARY KEY AUTOINCREMENT, site_id INTEGER UNIQUE, avg_wind_speed REAL, wind_power_density REAL, capacity_factor REAL, annual_energy_production REAL, turbine_suitability TEXT, ml_prediction REAL, prediction_confidence REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, quality_score REAL);
CREATE TABLE IF NOT EXISTS suitability_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, site_id INTEGER UNIQUE, renewable_resource_score REAL, geographic_suitability_score REAL, infrastructure_accessibility_score REAL, environmental_impact_score REAL, economic_feasibility_score REAL, overall_score REAL, category TEXT, recommendations TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
""")
# Backward-compatible migrations for databases created by older versions.
try:
    _init_conn.execute("ALTER TABLE solar_assessments ADD COLUMN quality_score REAL")
except Exception:
    pass
try:
    _init_conn.execute("ALTER TABLE wind_assessments ADD COLUMN quality_score REAL")
except Exception:
    pass
_init_conn.commit()
_init_conn.close()

print("✅ Database initialized!")

SECRET_KEY = "your-secret-key-change-this-in-production"

# ============================================
# ML MODEL LOADING
# ============================================
ML_MODEL_LOADED = False
ml_model = None
ml_scaler = None
solar_ml_model = None
wind_ml_model = None
suitability_ml_model = None
solar_ml_features = []
wind_ml_features = []
suitability_ml_features = []

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

def _load_pickle(name):
    path = os.path.join(MODEL_DIR, name)
    return joblib.load(path) if os.path.exists(path) else None

def _unwrap_model(obj):
    if obj is None:
        return None
    if hasattr(obj, "predict"):
        return obj
    if isinstance(obj, dict):
        for key in ("model", "estimator", "regressor", "pipeline", "trained_model"):
            value = obj.get(key)
            if hasattr(value, "predict"):
                return value
    return None

def _unwrap_features(obj):
    if isinstance(obj, (list, tuple)):
        return list(obj)
    if isinstance(obj, dict):
        for key in ("features", "feature_names", "columns", "feature_columns"):
            value = obj.get(key)
            if isinstance(value, (list, tuple)):
                return list(value)
    return []

def load_ml_models():
    global ML_MODEL_LOADED, ml_model, ml_scaler
    global solar_ml_model, wind_ml_model, suitability_ml_model
    global solar_ml_features, wind_ml_features, suitability_ml_features
    try:
        solar_ml_model = _unwrap_model(_load_pickle("solar_model.pkl"))
        wind_ml_model = _unwrap_model(_load_pickle("wind_model.pkl"))
        suitability_ml_model = _unwrap_model(_load_pickle("suitability_model.pkl"))
        solar_ml_features = _unwrap_features(_load_pickle("solar_features.pkl"))
        wind_ml_features = _unwrap_features(_load_pickle("wind_features.pkl"))
        suitability_ml_features = _unwrap_features(_load_pickle("suitability_features.pkl"))
        ml_model = suitability_ml_model
        ml_scaler = None
        ML_MODEL_LOADED = solar_ml_model is not None and wind_ml_model is not None
        print("✅ Solar and Wind ML models loaded!" if ML_MODEL_LOADED else "⚠️ Solar/Wind ML models not found")
    except Exception as e:
        ML_MODEL_LOADED = False
        solar_ml_model = wind_ml_model = suitability_ml_model = None
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
# PYDANTIC MODELS (Altered to prevent 422 errors)
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
    description: Optional[str] = None
    technology: str = "SOLAR"
    budget: Optional[float] = 0.0

    @field_validator('budget', mode='before')
    @classmethod
    def validate_budget(cls, v):
        if v is None or v == "":
            return 0.0
        try:
            if isinstance(v, float) and math.isnan(v):
                return 0.0
            return float(v)
        except:
            return 0.0

class SiteCreate(BaseModel):
    project_id: Optional[int] = None
    site_name: str
    latitude: float
    longitude: float
    region: Optional[str] = None
    land_area: Optional[float] = None
    elevation: Optional[float] = None
    land_ownership: Optional[str] = None
    existing_infrastructure: Optional[str] = None

    # This catches 'NaN' or '' coming from your frontend and turns it into None
    @field_validator('latitude', 'longitude', 'land_area', 'elevation', 'project_id', mode='before')
    @classmethod
    def validate_numeric_fields(cls, v):
        if v is None or v == "":
            return None
        try:
            if isinstance(v, float) and math.isnan(v):
                return None
            if isinstance(v, str) and v.lower() == 'nan':
                return None
            return v
        except:
            return None

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

    if not location or not location.strip():
        return None, None

    location = location.strip()

    # ------------------------------------------------
    # If user didn't mention country, assume India.
    # This improves results for Indian towns/cities.
    # ------------------------------------------------

    search_location = location

    if "india" not in location.lower():
        search_location = f"{location}, India"

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": search_location,
        "format": "json",
        "addressdetails": 1,
        "limit": 10,
        "countrycodes": "in",
        "dedupe": 1
    }

    headers = {
        "User-Agent":
            "SolarWindDeploymentPlatform/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        results = response.json()

        if not results:

            print(
                f"❌ Location not found: {location}"
            )

            return None, None

        # ------------------------------------------------
        # Prefer actual town/city/village locations
        # instead of district/state boundaries.
        # ------------------------------------------------

        preferred_types = [
            "city",
            "town",
            "village",
            "municipality",
            "suburb",
            "neighbourhood",
            "hamlet",
            "locality"
        ]

        # First pass:
        # Find the best actual settlement.
        for result in results:

            result_type = result.get(
                "type",
                ""
            ).lower()

            address_type = result.get(
                "addresstype",
                ""
            ).lower()

            if (
                result_type in preferred_types
                or
                address_type in preferred_types
            ):

                try:

                    lat = float(
                        result["lat"]
                    )

                    lon = float(
                        result["lon"]
                    )

                    print(
                        f"📍 Geocoded town/place: "
                        f"{result.get('display_name')}"
                    )

                    return lat, lon

                except:

                    continue

        # ------------------------------------------------
        # Second pass:
        # Accept any valid result.
        # This allows district/state input too.
        # ------------------------------------------------

        for result in results:

            try:

                lat = float(
                    result["lat"]
                )

                lon = float(
                    result["lon"]
                )

                print(
                    f"📍 Geocoded location: "
                    f"{result.get('display_name')}"
                )

                return lat, lon

            except:

                continue

        return None, None

    except Exception as e:

        print(
            f"❌ Geocoding error: {e}"
        )

        return None, None


# ============================================
# ELEVATION
# ============================================

def get_elevation(
    lat: float,
    lon: float
):

    url = (
        "https://api.open-elevation.com/"
        "api/v1/lookup"
    )

    try:

        response = requests.get(
            url,
            params={
                "locations":
                    f"{lat},{lon}"
            },
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if data.get("results"):

            elevation = (
                data["results"][0]
                .get("elevation")
            )

            if elevation is not None:

                return float(
                    elevation
                )

    except Exception as e:

        print(
            f"⚠️ Elevation error: {e}"
        )

    # Don't use a fake elevation like 150.
    return 0.0
# ============================================
# NASA POWER SERVICE
# ============================================

NASA_POWER_API = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch_environmental_data(lat: float, lon: float) -> Dict[str, Any]:

    result = {
        "success": False,
        "data": {},
        "error": None
    }

    try:

        end_date = datetime.now().strftime("%Y%m%d")

        # Use 1 full year of historical daily data
        start_date = (
            datetime.now() - timedelta(days=365)
        ).strftime("%Y%m%d")

        response = requests.get(
            NASA_POWER_API,
            params={
                "parameters":
                    "ALLSKY_SFC_SW_DWN,"
                    "T2M,"
                    "PRECTOTCORR,"
                    "WS10M,"
                    "CLOUD_AMT",

                "community": "RE",

                "format": "JSON",

                "longitude": lon,

                "latitude": lat,

                "start": start_date,

                "end": end_date
            },

            timeout=30
        )

        response.raise_for_status()

        api_data = response.json()

        params = (
            api_data
            .get("properties", {})
            .get("parameter", {})
        )

        # ==================================================
        # SOLAR
        # ==================================================

        solar_values = params.get(
            "ALLSKY_SFC_SW_DWN",
            {}
        )

        valid_solar = []

        for value in solar_values.values():

            try:

                value = float(value)

                # Ignore NASA missing-value markers
                if value >= 0:

                    valid_solar.append(value)

            except:

                continue

        if valid_solar:

            solar_daily_kwh = (
                sum(valid_solar)
                / len(valid_solar)
            )

        else:

            solar_daily_kwh = 0.0

        # ==================================================
        # TEMPERATURE
        # ==================================================

        temperature_values = params.get(
            "T2M",
            {}
        )

        valid_temperature = []

        for value in temperature_values.values():

            try:

                value = float(value)

                if value > -100:

                    valid_temperature.append(value)

            except:

                continue

        if valid_temperature:

            temperature = (
                sum(valid_temperature)
                / len(valid_temperature)
            )

        else:

            temperature = 25.0

        # ==================================================
        # RAINFALL
        # ==================================================

        rainfall_values = params.get(
            "PRECTOTCORR",
            {}
        )

        valid_rainfall = []

        for value in rainfall_values.values():

            try:

                value = float(value)

                if value >= 0:

                    valid_rainfall.append(value)

            except:

                continue

        if valid_rainfall:

            # NASA value is approximately mm/day.
            # Convert average daily rainfall to annual mm.

            rainfall = (
                sum(valid_rainfall)
                / len(valid_rainfall)
                * 365
            )

        else:

            rainfall = 0.0

        # ==================================================
        # WIND
        # ==================================================

        wind_values = params.get(
            "WS10M",
            {}
        )

        valid_wind = []

        for value in wind_values.values():

            try:

                value = float(value)

                if value >= 0:

                    valid_wind.append(value)

            except:

                continue

        if valid_wind:

            wind_speed = (
                sum(valid_wind)
                / len(valid_wind)
            )

        else:

            wind_speed = 0.0

        # ==================================================
        # CLOUD COVER
        # ==================================================

        cloud_values = params.get(
            "CLOUD_AMT",
            {}
        )

        valid_cloud = []

        for value in cloud_values.values():

            try:

                value = float(value)

                if 0 <= value <= 100:

                    valid_cloud.append(value)

            except:

                continue

        if valid_cloud:

            cloud_cover = (
                sum(valid_cloud)
                / len(valid_cloud)
            )

        else:

            cloud_cover = 0.0

        # ==================================================
        # FINAL DATA
        # ==================================================

        result["success"] = True

        result["data"] = {

            # This is DAILY solar energy:
            # kWh/m²/day
            "solar_irradiance":
                round(
                    solar_daily_kwh,
                    3
                ),

            "temperature":
                round(
                    temperature,
                    2
                ),

            "rainfall":
                round(
                    rainfall,
                    2
                ),

            "wind_speed":
                round(
                    wind_speed,
                    2
                ),

            "cloud_cover":
                round(
                    cloud_cover,
                    2
                ),

            "lat": lat,

            "lon": lon,

            "fetch_date":
                datetime.now().isoformat(),

            "data_source":
                "NASA POWER",

            "solar_unit":
                "kWh/m2/day"
        }

        return result

    except Exception as e:

        result["error"] = str(e)

        print(
            f"NASA POWER error: {e}"
        )

        return result
# ============================================
# LIVE ML HELPERS
# ============================================
def _safe_float(v, default=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else default
    except Exception:
        return default

def build_ml_features(site, env):
    lat=_safe_float(site.get("latitude")); lon=_safe_float(site.get("longitude"))
    elev=_safe_float(site.get("elevation"),150.0)
    temp=_safe_float(env.get("temperature"),25.0)
    rain=_safe_float(env.get("rainfall"),800.0)
    wind=_safe_float(env.get("wind_speed"),5.0)
    solar=_safe_float(env.get("solar_irradiance"),5.0)
    cloud=_safe_float(env.get("cloud_cover"),30.0)
    return {
        "latitude":lat,"longitude":lon,"year":2024,
        "temp_mean_c":temp,"temp_max_c":temp+5,"temp_min_c":temp-5,
        "precip_total_mm":rain,"rh_mean_pct":60.0,"wind_mean_ms":wind,
        "wind_max_ms":wind*1.8,"wind_std_ms":wind*0.25,"high_wind_days":max(0,wind-5)*20,
        "pressure_mean_kpa":101.325*math.exp(-elev/8434.5),
        "wind_power_density":0.5*1.225*wind**3,
        "solar_total_mj":solar*3.6*365,"solar_mean_mj":solar*3.6,
        "solar_clear_mean_mj":solar*3.6,"solar_clearness_idx":max(0,min(1,1-cloud/100)),
        "solar_peak_days":max(0,min(365,365*(1-cloud/100))),
        "solar_annual_kwh_m2":solar*365,
        "heat_stress_index":max(0,min(100,(temp-25)*5)),
        "drought_stress_days":max(0,120-rain/10),"humidity_stress_days":20.0,
        "climate_volatility":10.0,"gdp_per_capita_usd":5000.0,"elevation":elev,
        "land_area":_safe_float(site.get("land_area"),100.0)
    }

def predict_site_ml(site, env):
    if not ML_MODEL_LOADED:
        return None
    f=build_ml_features(site,env)
    def run(model,names):
        if model is None or not names:
            return None
        try:
            return float(model.predict([[f.get(n,0.0) for n in names]])[0])
        except Exception as e:
            print(f"⚠️ ML prediction skipped: {e}")
            return None
    solar=run(solar_ml_model,solar_ml_features)
    predicted_wind_speed=run(wind_ml_model,wind_ml_features)
    score=run(suitability_ml_model,suitability_ml_features)
    return {
        "solar_resource_prediction_kwh_m2_year":round(max(0,solar),2) if solar is not None else None,
        "predicted_wind_speed_ms":round(max(0,predicted_wind_speed),2) if predicted_wind_speed is not None else None,
        "wind_power_density_prediction_w_m2":round(0.5*1.225*max(0,predicted_wind_speed)**3,2) if predicted_wind_speed is not None else None,
        "suitability_score":round(max(0,min(100,score)),2) if score is not None else None,
        "features_used":f
    }

def estimate_hub_height_wind(wind_speed_10m, hub_height=150.0, roughness_length=0.1):
    """Estimated hub-height wind from NASA 10m wind using log profile.
    This is an estimate, not a measured 150m resource value."""
    v=max(0.0,float(wind_speed_10m or 0.0))
    if v <= 0:
        return 0.0
    z0=max(0.01,float(roughness_length))
    return v * math.log(hub_height/z0) / math.log(10.0/z0)

# ============================================
# SOLAR ENGINE
# ============================================

class SolarEngine:

    def predict_solar_potential(
        self,
        lat,
        lon,
        irradiance,
        temperature,
        cloud_cover,
        elevation,
        slope,
        ndvi,
        capacity_mw=1.0
    ):

        # ==================================================
        # 1. SOLAR RESOURCE
        # ==================================================

        try:

            daily_solar = float(
                irradiance
            )

        except:

            daily_solar = 0.0

        # NASA POWER:
        #
        # ALLSKY_SFC_SW_DWN
        #
        # Daily solar radiation:
        # kWh/m²/day
        #
        # For PV analysis this is approximately
        # equivalent to Peak Sun Hours/day.

        daily_solar = max(
            0.0,
            daily_solar
        )

        # Avoid impossible values

        daily_solar = min(
            daily_solar,
            10.0
        )

        # ==================================================
        # 2. PEAK SUN HOURS
        # ==================================================

        peak_sun_hours = daily_solar

        # ==================================================
        # 3. TEMPERATURE EFFECT
        # ==================================================

        try:

            temp = float(
                temperature
            )

        except:

            temp = 25.0

        temperature_factor = 1.0

        if temp > 25:

            temperature_factor = (
                1.0
                -
                0.004
                *
                (temp - 25)
            )

        temperature_factor = max(
            0.80,
            min(
                temperature_factor,
                1.05
            )
        )

        # ==================================================
        # 4. CLOUD EFFECT
        # ==================================================

        try:

            cloud = float(
                cloud_cover
            )

        except:

            cloud = 0.0

        cloud = max(
            0.0,
            min(cloud, 100.0)
        )

        # Do NOT double penalize the solar resource.
        #
        # ALLSKY solar radiation already represents
        # actual sky conditions.
        #
        # Therefore cloud cover is used only lightly
        # for the quality score.

        cloud_factor = (
            1.0
            -
            0.05
            *
            (cloud / 100.0)
        )

        # ==================================================
        # 5. SYSTEM PERFORMANCE RATIO
        # ==================================================

        base_performance_ratio = 0.80

        performance_ratio = (
            base_performance_ratio
            *
            temperature_factor
            *
            cloud_factor
        )

        performance_ratio = max(
            0.60,
            min(
                performance_ratio,
                0.90
            )
        )

        # ==================================================
        # 6. ANNUAL ENERGY
        # ==================================================

        # Capacity:
        # MW
        #
        # Solar resource:
        # kWh/m²/day
        #
        # Result:
        # MWh/year

        annual_energy_mwh = (
            capacity_mw
            *
            peak_sun_hours
            *
            365
            *
            performance_ratio
        )

        # ==================================================
        # 7. CAPACITY FACTOR
        # ==================================================

        capacity_factor = (

            annual_energy_mwh
            /
            (
                capacity_mw
                *
                8760
            )

        ) * 100

        capacity_factor = max(
            0.0,
            min(
                capacity_factor,
                100.0
            )
        )

        # ==================================================
        # 8. SOLAR QUALITY SCORE
        # ==================================================

        # Solar resource = 60%
        # Temperature = 15%
        # Cloud = 10%
        # Terrain = 15%

        resource_score = (
            min(
                peak_sun_hours / 6.0,
                1.0
            )
            * 60
        )

        temperature_score = (
            temperature_factor
            * 15
        )

        cloud_score = (
            (
                1
                -
                cloud / 100
            )
            * 10
        )

        # ==================================================
        # TERRAIN
        # ==================================================

        terrain_score = 15

        try:

            slope_value = float(
                slope
            )

            if slope_value <= 5:

                terrain_score = 15

            elif slope_value <= 10:

                terrain_score = 12

            elif slope_value <= 15:

                terrain_score = 8

            elif slope_value <= 25:

                terrain_score = 4

            else:

                terrain_score = 1

        except:

            terrain_score = 10

        quality_score = (

            resource_score
            +
            temperature_score
            +
            cloud_score
            +
            terrain_score

        )

        quality_score = max(
            0.0,
            min(
                quality_score,
                100.0
            )
        )

        # ==================================================
        # 9. RECOMMENDATIONS
        # ==================================================

        recommendations = []

        if peak_sun_hours >= 5.5:

            recommendations.append(
                "Excellent solar resource for PV deployment."
            )

        elif peak_sun_hours >= 4.5:

            recommendations.append(
                "Good solar resource for PV deployment."
            )

        elif peak_sun_hours >= 3.5:

            recommendations.append(
                "Moderate solar resource."
            )

        elif peak_sun_hours >= 2.5:

            recommendations.append(
                "Low-to-moderate solar resource."
            )

        else:

            recommendations.append(
                "Low solar resource."
            )

        if temp > 35:

            recommendations.append(
                "High temperature may reduce PV efficiency."
            )

        if cloud > 70:

            recommendations.append(
                "High cloud cover may reduce solar availability."
            )

        if elevation is not None:

            try:

                if float(elevation) > 2000:

                    recommendations.append(
                        "High elevation site; check structural and weather conditions."
                    )

            except:

                pass

        # ==================================================
        # 10. MONTHLY GENERATION
        # ==================================================

        seasonal_factors = [

            0.82,
            0.86,
            0.95,
            1.02,
            1.10,
            1.12,
            0.95,
            0.90,
            0.94,
            1.00,
            1.05,
            1.09

        ]

        average_factor = (
            sum(seasonal_factors)
            /
            len(seasonal_factors)
        )

        monthly_generation = []

        for month, factor in enumerate(
            seasonal_factors,
            start=1
        ):

            monthly_energy = (

                annual_energy_mwh
                /
                12

                *
                (
                    factor
                    /
                    average_factor
                )

            )

            monthly_generation.append({

                "month":
                    month,

                "energy_mwh":
                    round(
                        monthly_energy,
                        2
                    )
            })

        # ==================================================
        # FINAL RESULT
        # ==================================================

        return {

            "peak_sun_hours":
                round(
                    peak_sun_hours,
                    2
                ),

            "annual_energy_mwh":
                round(
                    annual_energy_mwh,
                    2
                ),

            "capacity_factor":
                round(
                    capacity_factor,
                    2
                ),

            "performance_ratio":
                round(
                    performance_ratio,
                    3
                ),

            "quality_score":
                round(
                    quality_score,
                    2
                ),

            "monthly_generation":
                monthly_generation,

            "recommendations":
                recommendations
        }


solar_engine = SolarEngine()
# ============================================
# WIND ENGINE
# ============================================
class WindEngine:
    def predict_wind_potential(self, lat, lon, wind_speed, temperature, elevation, terrain="flat", capacity_mw=2.0, power_density_override=None, hub_height=150.0):
        wind_speed=max(0.0,float(wind_speed))
        capacity_mw=max(0.1,float(capacity_mw))
        power_density=max(0.0,float(power_density_override)) if power_density_override is not None else 0.5*1.225*wind_speed**3
        rotor_diameter=100.0
        swept_area=np.pi*(rotor_diameter/2)**2
        theoretical_power_mw=(power_density*swept_area)/1_000_000
        annual_energy=theoretical_power_mw*8760*0.45
        capacity_factor=max(0.0,min(100.0,(annual_energy/(capacity_mw*8760))*100))
        # Resource score based on WPD, not arbitrary temperature/elevation bonuses.
        quality_score=max(0.0,min(100.0,(power_density/500.0)*100.0))
        if power_density >= 500:
            recommendation="Strong wind resource; suitable for detailed turbine screening."
        elif power_density >= 300:
            recommendation="Good wind resource; detailed turbine and grid assessment recommended."
        elif power_density >= 200:
            recommendation="Moderate wind resource; detailed assessment required."
        elif power_density >= 100:
            recommendation="Marginal wind resource; utility-scale wind may be challenging."
        else:
            recommendation="Weak wind resource for utility-scale wind at this location."
        monthly=[{"month":m,"energy_mwh":round((annual_energy/12),2)} for m in range(1,13)]
        return {
            "avg_wind_speed":round(wind_speed,2),"hub_height_m":hub_height,
            "power_density":round(power_density,2),"annual_energy_mwh":round(annual_energy,2),
            "capacity_factor":round(capacity_factor,2),"quality_score":round(quality_score,2),
            "monthly_generation":monthly,"recommendations":[recommendation]
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
@app.post("/api/sites/{site_id}/analyze")
def analyze_complete_site(site_id: int, token: str = Depends(get_token)):
    """Run the complete site analysis and save all results."""
    email = verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")

    cursor.execute("""
        SELECT id, project_id, site_name, latitude, longitude,
               region, land_area, elevation, land_ownership,
               existing_infrastructure
        FROM sites WHERE id = ?
    """, (site_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Site not found")

    site = {
        "id": row[0], "project_id": row[1], "site_name": row[2],
        "latitude": row[3], "longitude": row[4], "region": row[5],
        "land_area": row[6] or 100.0, "elevation": row[7],
        "land_ownership": row[8], "existing_infrastructure": row[9]
    }

    try:
        # 1) Live environmental data
        env_response = fetch_environmental_data(site["latitude"], site["longitude"])
        if not env_response["success"]:
            raise HTTPException(status_code=502, detail=env_response.get("error", "Environmental API failed"))
        env = env_response["data"]

        # 2) Elevation
        if site["elevation"] is None:
            site["elevation"] = get_elevation(site["latitude"], site["longitude"])
            cursor.execute("UPDATE sites SET elevation = ? WHERE id = ?", (site["elevation"], site_id))

        cursor.execute("""
            INSERT OR REPLACE INTO environmental_data
            (site_id, solar_irradiance, temperature, rainfall, wind_speed, cloud_cover, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (site_id, env["solar_irradiance"], env["temperature"], env["rainfall"],
              env["wind_speed"], env["cloud_cover"], "NASA POWER"))

        # 3) ML prediction from the same feature schema used during training
        ml = predict_site_ml(site, env) if ML_MODEL_LOADED else None

        # 4) Solar: use live NASA POWER irradiance as the physical resource.
        # ML remains a supplementary prediction and never overwrites live measurements.
        predicted_solar_resource = env["solar_irradiance"] * 365.0
        predicted_solar_irradiance = max(0.1, float(env["solar_irradiance"]))

        solar_result = solar_engine.predict_solar_potential(
            lat=site["latitude"],
            lon=site["longitude"],
            irradiance=predicted_solar_irradiance,
            temperature=env["temperature"],
            cloud_cover=env["cloud_cover"],
            elevation=site["elevation"],
            slope=0,
            ndvi=0.2,
            capacity_mw=1.0
        )
        solar_result["ml_prediction_kwh_m2_year"] = round(predicted_solar_resource, 2) if ml else None

        cursor.execute("""
            INSERT OR REPLACE INTO solar_assessments
            (site_id, peak_sun_hours, solar_energy_potential, capacity_factor,
             performance_ratio, monthly_generation, ml_prediction, prediction_confidence,
             quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, solar_result["peak_sun_hours"], solar_result["annual_energy_mwh"],
              solar_result["capacity_factor"], solar_result["performance_ratio"],
              json.dumps(solar_result["monthly_generation"]),
              ml["solar_resource_prediction_kwh_m2_year"] if ml else None,
              0.85,
              float(max(0.0, min(100.0, solar_result["quality_score"])))))

        # 5) Wind: NASA POWER provides the measured/modelled near-surface value.
        # Estimate a 150m hub-height value for turbine screening; do not pretend it is measured.
        predicted_wind_speed = estimate_hub_height_wind(env["wind_speed"], 150.0, 0.1)
        predicted_wpd = 0.5 * 1.225 * predicted_wind_speed ** 3

        wind_result = wind_engine.predict_wind_potential(
            lat=site["latitude"], lon=site["longitude"],
            wind_speed=predicted_wind_speed, temperature=env["temperature"],
            elevation=site["elevation"], terrain="flat", capacity_mw=2.0,
            power_density_override=predicted_wpd, hub_height=150.0
        )
        wind_result["wind_speed_10m"] = round(float(env["wind_speed"]), 2)
        wind_result["hub_height_wind_source"] = "NASA POWER 10m extrapolated estimate"
        wind_result["ml_prediction_w_m2"] = ml.get("wind_power_density_prediction_w_m2") if ml else None

        cursor.execute("""
            INSERT OR REPLACE INTO wind_assessments
            (site_id, avg_wind_speed, wind_power_density, capacity_factor,
             annual_energy_production, turbine_suitability, ml_prediction,
             prediction_confidence, quality_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, wind_result["avg_wind_speed"], wind_result["power_density"],
              wind_result["capacity_factor"], wind_result["annual_energy_mwh"],
              json.dumps(wind_result["recommendations"]),
              ml["wind_power_density_prediction_w_m2"] if ml else None,
              0.85,
              float(max(0.0, min(100.0, wind_result["quality_score"])))))

        # 6) Suitability: actual solar/wind resource scores drive the renewable component.
        renewable_score = solar_result["quality_score"] * 0.60 + wind_result["quality_score"] * 0.40

        land_area = site["land_area"]
        if land_area >= 100:
            geographic_score = 90.0
        elif land_area >= 50:
            geographic_score = 78.0
        elif land_area >= 20:
            geographic_score = 65.0
        else:
            geographic_score = 50.0

        infra = (site["existing_infrastructure"] or "").lower()
        if any(x in infra for x in ["substation", "transmission", "power line"]):
            infrastructure_score = 90.0
        elif "road" in infra:
            infrastructure_score = 75.0
        elif infra.strip():
            infrastructure_score = 60.0
        else:
            infrastructure_score = 40.0

        temperature_penalty = min(50.0, abs(env["temperature"] - 25.0) * 2.0)
        cloud_penalty = min(35.0, max(0.0, env["cloud_cover"]) * 0.35)
        environmental_score = max(0.0, 100.0 - temperature_penalty - cloud_penalty)
        economic_score = min(95.0, 45.0 + min(50.0, land_area * 0.45))

        overall_score = (
            renewable_score * 0.35 +
            geographic_score * 0.25 +
            infrastructure_score * 0.15 +
            environmental_score * 0.15 +
            economic_score * 0.10
        )
        overall_score = round(max(0.0, min(100.0, overall_score)), 2)

        category = (
            "Excellent" if overall_score >= 90 else
            "Highly Suitable" if overall_score >= 80 else
            "Moderately Suitable" if overall_score >= 65 else
            "Low Suitability" if overall_score >= 40 else
            "Unsuitable"
        )

        recommendations = []
        if renewable_score >= 80:
            recommendations.append("⚡ Strong combined renewable resource.")
        elif renewable_score < 50:
            recommendations.append("⚠️ Renewable resource is relatively weak.")
        if solar_result["quality_score"] >= 70:
            recommendations.append("☀️ Solar resource is favorable.")
        if wind_result["quality_score"] >= 70:
            recommendations.append("💨 Wind resource is favorable.")
        if infrastructure_score < 60:
            recommendations.append("🏗️ Infrastructure access should be investigated further.")
        if environmental_score < 60:
            recommendations.append("🌍 Environmental conditions reduce suitability.")
        if not recommendations:
            recommendations.append("Balanced site conditions; detailed GIS screening is recommended before investment.")

        suitability_result = {
            "overall_score": overall_score,
            "category": category,
            "scores": {
                "renewable_resource": round(renewable_score, 2),
                "geographic_suitability": round(geographic_score, 2),
                "infrastructure": round(infrastructure_score, 2),
                "environmental": round(environmental_score, 2),
                "economic": round(economic_score, 2)
            },
            "recommendations": recommendations,
            "ml_prediction": ml
        }

        cursor.execute("""
            INSERT OR REPLACE INTO suitability_scores
            (site_id, renewable_resource_score, geographic_suitability_score,
             infrastructure_accessibility_score, environmental_impact_score,
             economic_feasibility_score, overall_score, category, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (site_id, renewable_score, geographic_score, infrastructure_score,
              environmental_score, economic_score, overall_score, category,
              " | ".join(recommendations)))

        conn.commit()

        return {
            "success": True,
            "message": "Complete site analysis completed",
            "site": site,
            "environmental": env,
            "solar": solar_result,
            "wind": wind_result,
            "ml": ml,
            "suitability": suitability_result
        }

    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        print(f"❌ Complete site analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Site analysis failed: {str(e)}")

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
    email=verify_token(token)
    if not email: raise HTTPException(status_code=401, detail="Unauthorized")
    cursor.execute("SELECT latitude,longitude,site_name,elevation,land_area FROM sites WHERE id=?",(site_id,))
    r=cursor.fetchone()
    if not r: raise HTTPException(status_code=404, detail="Site not found")
    cursor.execute("SELECT * FROM environmental_data WHERE site_id=?",(site_id,))
    er=cursor.fetchone()
    if not er: raise HTTPException(status_code=404, detail="Environmental data not found. Fetch first.")
    site={"latitude":r[0],"longitude":r[1],"site_name":r[2],"elevation":r[3] or get_elevation(r[0],r[1]),"land_area":r[4] or 100.0}
    env={"solar_irradiance":er[2] or 5.0,"temperature":er[3] or 25.0,"rainfall":er[4] or 800.0,"wind_speed":er[5] or 5.0,"cloud_cover":er[7] or 30.0}
    ml=predict_site_ml(site,env)
    irradiance=env["solar_irradiance"]
    result=solar_engine.predict_solar_potential(site["latitude"],site["longitude"],irradiance,env["temperature"],env["cloud_cover"],site["elevation"],0,0.2,capacity_mw)
    result["ml_prediction_kwh_m2_year"]=ml["solar_resource_prediction_kwh_m2_year"] if ml else None
    cursor.execute("INSERT OR REPLACE INTO solar_assessments (site_id,peak_sun_hours,solar_energy_potential,capacity_factor,performance_ratio,monthly_generation,ml_prediction,prediction_confidence,quality_score) VALUES (?,?,?,?,?,?,?,?,?)",(site_id,result["peak_sun_hours"],result["annual_energy_mwh"],result["capacity_factor"],result["performance_ratio"],json.dumps(result["monthly_generation"]),result["ml_prediction_kwh_m2_year"],0.85,result["quality_score"]))
    conn.commit()
    return {"message":"Solar analysis completed","result":result}

@app.get("/api/solar/assessment/{site_id}")
def get_solar_assessment(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401

    cursor.execute(
        """
        SELECT id, site_id, peak_sun_hours, solar_energy_potential,
               capacity_factor, performance_ratio, monthly_generation,
               ml_prediction, prediction_confidence, created_at
        FROM solar_assessments
        WHERE site_id = ?
        """,
        (site_id,)
    )
    row = cursor.fetchone()

    if not row:
        return {"error": "No assessment found"}, 404

    peak = _safe_float(row[2], 0.0)
    capacity_factor = _safe_float(row[4], 0.0)

    # Quality is ALWAYS a bounded physical score.
    # ml_prediction is never used as quality_score.
    quality_score = max(
        0.0,
        min(
            100.0,
            (peak / 6.0) * 60.0
            + min(15.0, max(0.0, capacity_factor) * 0.75)
            + 15.0
        )
    )

    return {
        "id": row[0],
        "site_id": row[1],
        "peak_sun_hours": row[2],
        "annual_energy_mwh": row[3],
        "capacity_factor": row[4],
        "performance_ratio": row[5],
        "monthly_generation": json.loads(row[6]) if row[6] else [],
        "quality_score": round(float(quality_score), 2),
        "ml_prediction_kwh_m2_year": row[7],
        "created_at": row[9]
    }

# ============================================
# WIND ROUTES
# ============================================
@app.post("/api/wind/analyze/{site_id}")
def analyze_wind(site_id: int, capacity_mw: float = 2.0, terrain: str = "flat", token: str = Depends(get_token)):
    email=verify_token(token)
    if not email: raise HTTPException(status_code=401, detail="Unauthorized")
    cursor.execute("SELECT latitude,longitude,site_name,elevation,land_area FROM sites WHERE id=?",(site_id,))
    r=cursor.fetchone()
    if not r: raise HTTPException(status_code=404, detail="Site not found")
    cursor.execute("SELECT * FROM environmental_data WHERE site_id=?",(site_id,))
    er=cursor.fetchone()
    if not er: raise HTTPException(status_code=404, detail="Environmental data not found. Fetch first.")
    site={"latitude":r[0],"longitude":r[1],"site_name":r[2],"elevation":r[3] or get_elevation(r[0],r[1]),"land_area":r[4] or 100.0}
    env={"solar_irradiance":er[2] or 5.0,"temperature":er[3] or 25.0,"rainfall":er[4] or 800.0,"wind_speed":er[5] or 5.0,"cloud_cover":er[7] or 30.0}
    ml=predict_site_ml(site,env)
    wind_speed=estimate_hub_height_wind(env["wind_speed"],150.0,0.1)
    wpd=0.5*1.225*wind_speed**3
    result=wind_engine.predict_wind_potential(site["latitude"],site["longitude"],wind_speed,env["temperature"],site["elevation"],terrain,capacity_mw,power_density_override=wpd,hub_height=150.0)
    result["wind_speed_10m"]=round(float(env["wind_speed"]),2)
    result["wind_power_density"] = result["power_density"]
    result["hub_height_wind_source"]="NASA POWER 10m extrapolated estimate"
    result["ml_prediction_w_m2"]=ml["wind_power_density_prediction_w_m2"] if ml else None
    cursor.execute("""
        INSERT OR REPLACE INTO wind_assessments
        (site_id, avg_wind_speed, wind_power_density, capacity_factor,
         annual_energy_production, turbine_suitability, ml_prediction,
         prediction_confidence, quality_score)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        site_id,
        result["avg_wind_speed"],
        result["power_density"],
        result["capacity_factor"],
        result["annual_energy_mwh"],
        json.dumps(result["recommendations"]),
        result["ml_prediction_w_m2"],
        0.85,
        float(max(0.0, min(100.0, result["quality_score"])))
    ))
    conn.commit()
    return {"message":"Wind analysis completed","result":result}

@app.get("/api/wind/assessment/{site_id}")
def get_wind_assessment(site_id: int, token: str = Depends(get_token)):
    email = verify_token(token)
    if not email:
        return {"error": "Unauthorized"}, 401

    cursor.execute(
        """
        SELECT id, site_id, avg_wind_speed, wind_power_density,
               capacity_factor, annual_energy_production,
               turbine_suitability, ml_prediction,
               prediction_confidence, created_at
        FROM wind_assessments
        WHERE site_id = ?
        """,
        (site_id,)
    )
    row = cursor.fetchone()

    if not row:
        return {"error": "No assessment found"}, 404

    wpd = _safe_float(row[3], 0.0)

    # Quality is ALWAYS a bounded physical wind-resource score.
    # ml_prediction is never used as quality_score.
    quality_score = max(
        0.0,
        min(100.0, (wpd / 500.0) * 100.0)
    )

    suitability = row[6]
    try:
        suitability = json.loads(suitability) if suitability else []
    except Exception:
        suitability = [suitability] if suitability else []

    return {
        "id": row[0],
        "site_id": row[1],
        "avg_wind_speed": row[2],
        "wind_power_density": round(wpd, 2),
        "power_density": round(wpd, 2),
        "capacity_factor": row[4],
        "annual_energy_mwh": row[5],
        "turbine_suitability": suitability,
        "quality_score": round(float(quality_score), 2),
        "ml_prediction_w_m2": row[7],
        "created_at": row[9]
    }

# ============================================
# SUITABILITY ROUTES
# ============================================
@app.post("/api/suitability/analyze/{site_id}")
def analyze_suitability(site_id: int, token: str = Depends(get_token)):
    email=verify_token(token)
    if not email: raise HTTPException(status_code=401, detail="Unauthorized")
    cursor.execute("SELECT latitude,longitude,site_name,elevation,land_area FROM sites WHERE id=?",(site_id,))
    r=cursor.fetchone()
    if not r: raise HTTPException(status_code=404, detail="Site not found")
    cursor.execute("SELECT * FROM environmental_data WHERE site_id=?",(site_id,)); er=cursor.fetchone()
    cursor.execute("SELECT * FROM solar_assessments WHERE site_id=?",(site_id,)); solar=cursor.fetchone()
    cursor.execute("SELECT * FROM wind_assessments WHERE site_id=?",(site_id,)); wind=cursor.fetchone()
    if not er or not solar or not wind: raise HTTPException(status_code=404,detail="Environmental, solar and wind analysis are required first.")
    site={"latitude":r[0],"longitude":r[1],"elevation":r[3] or get_elevation(r[0],r[1]),"land_area":r[4] or 100.0}
    env={"solar_irradiance":er[2] or 5.0,"temperature":er[3] or 25.0,"rainfall":er[4] or 800.0,"wind_speed":er[5] or 5.0,"cloud_cover":er[7] or 30.0}
    ml=predict_site_ml(site,env)
    renewable=ml["suitability_score"] if ml else ((solar[7] or 50)+(wind[7] or 50))/2
    geographic=70.0; infrastructure=60.0; environmental=max(0,min(100,100-env["cloud_cover"]*0.25)); economic=65.0
    result=suitability_engine.calculate_suitability_score(renewable,renewable,geographic,infrastructure,environmental,economic)
    result["scores"]["renewable_resource"]=round(renewable,2)
    if ml: result["ml_prediction"]=ml["suitability_score"]; result["ml_category"]=ml["category"]
    cursor.execute("INSERT OR REPLACE INTO suitability_scores (site_id,renewable_resource_score,geographic_suitability_score,infrastructure_accessibility_score,environmental_impact_score,economic_feasibility_score,overall_score,category,recommendations) VALUES (?,?,?,?,?,?,?,?,?)",(site_id,renewable,geographic,infrastructure,environmental,economic,result["overall_score"],result["category"]," | ".join(result["recommendations"])))
    conn.commit()
    return {"message":"Suitability analysis completed","result":result}

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
    email=verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    if not ML_MODEL_LOADED:
        raise HTTPException(status_code=503, detail="ML models not loaded. Train first.")
    site={"latitude":0.0,"longitude":0.0,"elevation":features.elevation,"land_area":features.land_area}
    env={"solar_irradiance":features.solar_irradiance,"temperature":features.temperature,"rainfall":features.rainfall,"wind_speed":features.wind_speed,"cloud_cover":features.cloud_cover}
    prediction=predict_site_ml(site,env)
    return {"suitability_score": prediction.get("suitability_score") if prediction else None, "category": ("Excellent" if prediction and prediction.get("suitability_score",0)>=90 else "Highly Suitable" if prediction and prediction.get("suitability_score",0)>=80 else "Moderately Suitable" if prediction and prediction.get("suitability_score",0)>=65 else "Low Suitability" if prediction and prediction.get("suitability_score",0)>=40 else "Unsuitable"), "prediction":prediction, "features":features.model_dump() if hasattr(features,"model_dump") else features.dict()}

@app.post("/api/ml/predict-location")
def predict_by_location(req: LocationPredictionRequest, token: str = Depends(get_token)):
    email=verify_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Unauthorized")
    lat,lon=geocode_location(req.location)
    if lat is None:
        raise HTTPException(status_code=404, detail="Location not found")
    env_data=fetch_environmental_data(lat,lon)
    if not env_data["success"]:
        raise HTTPException(status_code=502, detail="Failed to fetch environmental data")
    env=env_data["data"]; elevation=get_elevation(lat,lon)
    prediction=predict_site_ml({"latitude":lat,"longitude":lon,"elevation":elevation,"land_area":req.land_area},env)
    return {"location":req.location,"latitude":lat,"longitude":lon,"environmental_data":env,"ml_prediction":prediction,"hub_height_wind_estimate_ms":round(estimate_hub_height_wind(env["wind_speed"]),2)}

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
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from pwdlib import PasswordHash

from database import engine
from schemas import UserCreate, UserLogin, SolarAnalysisRequest


# ============================================================
# APP CONFIGURATION
# ============================================================

app = FastAPI(
    title="Solar & Wind Deployment Intelligence Platform",
    description="AI-powered renewable energy deployment platform",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# PASSWORD HASHING
# ============================================================

password_hash = PasswordHash.recommended()


# ============================================================
# WIND REQUEST SCHEMA
# ============================================================

class WindAnalysisRequest(BaseModel):
    location: str
    land_area: float
    wind_speed: float
    temperature: float
    air_density: float


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "Solar & Wind Deployment Intelligence Platform API is running!"
    }


# ============================================================
# DATABASE TEST
# ============================================================

@app.get("/db-test")
def database_test():

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            result.fetchone()

        return {
            "message": "Database connection successful!"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


# ============================================================
# REGISTER
# ============================================================

@app.post("/register")
def register(user: UserCreate):

    try:

        # Check existing email
        with engine.connect() as connection:

            existing_user = connection.execute(
                text("""
                    SELECT id
                    FROM users
                    WHERE email = :email
                """),
                {
                    "email": user.email
                }
            ).fetchone()

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        # Hash password
        hashed_password = password_hash.hash(user.password)

        # Insert user
        with engine.begin() as connection:

            result = connection.execute(
                text("""
                    INSERT INTO users
                    (
                        full_name,
                        email,
                        password_hash,
                        created_at
                    )
                    VALUES
                    (
                        :full_name,
                        :email,
                        :password_hash,
                        CURRENT_TIMESTAMP
                    )
                    RETURNING id
                """),
                {
                    "full_name": user.name,
                    "email": user.email,
                    "password_hash": hashed_password
                }
            )

            user_id = result.fetchone()[0]

        return {
            "message": "User registered successfully",
            "id": user_id,
            "name": user.name,
            "email": user.email
        }

    except HTTPException:
        raise

    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    except Exception as e:
        print("REGISTER ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )


# ============================================================
# LOGIN
# ============================================================

@app.post("/login")
def login(user: UserLogin):

    try:

        # Find user
        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT
                        id,
                        full_name,
                        email,
                        password_hash
                    FROM users
                    WHERE email = :email
                """),
                {
                    "email": user.email
                }
            ).fetchone()

        # User not found
        if not result:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # Verify password
        password_is_valid = password_hash.verify(
            user.password,
            result.password_hash
        )

        if not password_is_valid:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        return {
            "message": "Login successful",
            "user": {
                "id": result.id,
                "name": result.full_name,
                "email": result.email
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        print("LOGIN ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail="Login failed"
        )


# ============================================================
# SOLAR ANALYSIS
# ============================================================

@app.post("/solar-analysis")
def solar_analysis(data: SolarAnalysisRequest):

    land_area = data.land_area
    irradiance = data.irradiance
    temperature = data.temperature
    cloud_cover = data.cloud_cover

    # Solar efficiency
    efficiency = 20.0

    # Cloud impact
    efficiency -= cloud_cover * 0.08

    # Temperature impact
    if temperature > 25:
        efficiency -= (temperature - 25) * 0.25

    efficiency = max(
        10.0,
        min(22.0, efficiency)
    )

    # Estimated capacity
    capacity_mw = land_area * 0.04

    # Daily energy
    daily_energy = (
        capacity_mw
        * irradiance
        * (efficiency / 100)
    )

    # Solar score
    score = (
        irradiance * 12
        + (100 - cloud_cover) * 0.25
    )

    score = max(
        0,
        min(100, score)
    )

    # Rating
    if score >= 80:
        rating = "Excellent"
    elif score >= 60:
        rating = "Good"
    else:
        rating = "Moderate"

    return {
        "location": data.location,
        "score": round(score, 1),
        "rating": rating,
        "capacity": round(capacity_mw, 2),
        "energy": round(daily_energy, 2),
        "efficiency": round(efficiency, 1),
        "land_area": land_area
    }


# ============================================================
# WIND ANALYSIS
# ============================================================

@app.post("/wind-analysis")
def wind_analysis(data: WindAnalysisRequest):

    wind_speed = data.wind_speed
    land_area = data.land_area

    # Wind potential score
    score = wind_speed * 11

    score = max(
        0,
        min(100, score)
    )

    # Rating
    if score >= 80:
        rating = "Excellent"
    elif score >= 60:
        rating = "Good"
    else:
        rating = "Moderate"

    # Estimated capacity
    capacity_mw = land_area * 0.0317

    # Capacity factor
    capacity_factor = min(
        50,
        max(15, wind_speed * 5.5)
    )

    # Daily energy
    daily_energy = (
        capacity_mw
        * 24
        * (capacity_factor / 100)
    )

    return {
        "location": data.location,
        "score": round(score, 1),
        "rating": rating,
        "capacity": round(capacity_mw, 2),
        "energy": round(daily_energy, 2),
        "capacity_factor": round(capacity_factor, 1),
        "wind_speed": round(wind_speed, 1)
    }
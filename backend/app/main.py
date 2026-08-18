from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.database import engine, SessionLocal
from sqlalchemy import text
import hashlib

from ml.predict import predict_solar
from ml.predict_wind import predict_wind

# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Solar & Wind Deployment Intelligence Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1|192\.168\.0\.11)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# USER REGISTRATION MODEL
# =========================================================

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone_number: str
    organization: str


# =========================================================
# USER LOGIN MODEL
# =========================================================

class UserLogin(BaseModel):
    email: str
    password: str


# =========================================================
# PROJECT MODEL
# =========================================================

class ProjectCreate(BaseModel):
    project_name: str
    description: str | None = None
    region: str | None = None
    project_status: str = "Planning"

# =========================================================
# SOLAR PREDICTION MODEL
# =========================================================

class SolarPredictionRequest(BaseModel):
    temperature: float
    dni: float
    dhi: float
    wind_speed: float


# =========================================================
# WIND PREDICTION MODEL
# =========================================================

class WindPredictionRequest(BaseModel):
    temperature: float
    ghi: float
    dni: float
    dhi: float


# =========================================================
# SITE MODEL
# =========================================================

class SiteCreate(BaseModel):
    project_id: str
    site_name: str
    latitude: float | None = None
    longitude: float | None = None
    region: str | None = None
    land_area: float | None = None
    elevation: float | None = None
    land_type: str | None = None
    ownership: str | None = None


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Solar & Wind Platform API is running"
    }


# =========================================================
# DATABASE CONNECTION TEST
# =========================================================

@app.get("/database-test")
def database_test():

    try:

        with engine.connect():

            return {
                "status": "success",
                "message": "PostgreSQL connected successfully"
            }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# USER REGISTRATION
# =========================================================

@app.post("/register")
def register_user(user: UserCreate):

    db = SessionLocal()

    try:

        password_hash = hashlib.sha256(
            user.password.encode()
        ).hexdigest()

        query = text("""
            INSERT INTO users
            (
                full_name,
                email,
                password_hash,
                phone_number,
                organization
            )
            VALUES
            (
                :full_name,
                :email,
                :password_hash,
                :phone_number,
                :organization
            )
            RETURNING user_id
        """)

        result = db.execute(
            query,
            {
                "full_name": user.full_name,
                "email": user.email,
                "password_hash": password_hash,
                "phone_number": user.phone_number,
                "organization": user.organization
            }
        )

        user_id = result.fetchone()[0]

        db.commit()

        return {
            "status": "success",
            "message": "User registered successfully",
            "user_id": str(user_id),
            "name": user.full_name,
            "email": user.email
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# USER LOGIN
# =========================================================

@app.post("/login")
def login_user(user: UserLogin):

    db = SessionLocal()

    try:

        password_hash = hashlib.sha256(
            user.password.encode()
        ).hexdigest()

        query = text("""
            SELECT
                user_id,
                full_name,
                email
            FROM users
            WHERE email = :email
            AND password_hash = :password_hash
        """)

        result = db.execute(
            query,
            {
                "email": user.email,
                "password_hash": password_hash
            }
        )

        existing_user = result.fetchone()

        if existing_user is None:

            return {
                "status": "error",
                "message": "Invalid email or password"
            }

        return {
            "status": "success",
            "message": "Login successful",
            "user_id": str(existing_user[0]),
            "name": existing_user[1],
            "email": existing_user[2]
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# CREATE PROJECT
# =========================================================

@app.post("/projects")
def create_project(project: ProjectCreate):

    db = SessionLocal()

    try:

        query = text("""
            INSERT INTO projects
            (
                project_name,
                description,
                region,
                project_status
            )
            VALUES
            (
                :project_name,
                :description,
                :region,
                :project_status
            )
            RETURNING project_id
        """)

        result = db.execute(
            query,
            {
                "project_name": project.project_name,
                "description": project.description,
                "region": project.region,
                "project_status": project.project_status
            }
        )

        project_id = result.fetchone()[0]

        db.commit()

        return {
            "status": "success",
            "message": "Project created successfully",
            "project_id": str(project_id),
            "project_name": project.project_name,
            "description": project.description,
            "region": project.region,
            "project_status": project.project_status
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# GET ALL PROJECTS
# =========================================================

@app.get("/projects")
def get_projects():

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                project_id,
                project_name,
                description,
                region,
                project_status,
                created_by,
                created_at,
                updated_at
            FROM projects
            ORDER BY created_at DESC
        """)

        result = db.execute(query)

        projects = []

        for row in result:

            projects.append({
                "project_id": str(row[0]),
                "project_name": row[1],
                "description": row[2],
                "region": row[3],
                "project_status": row[4],
                "created_by": str(row[5]) if row[5] else None,
                "created_at": str(row[6]) if row[6] else None,
                "updated_at": str(row[7]) if row[7] else None
            })

        return {
            "status": "success",
            "count": len(projects),
            "projects": projects
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# UPDATE PROJECT
# =========================================================

@app.put("/projects/{project_id}")
def update_project(
    project_id: str,
    project: ProjectCreate
):

    db = SessionLocal()

    try:

        query = text("""
            UPDATE projects
            SET
                project_name = :project_name,
                description = :description,
                region = :region,
                project_status = :project_status,
                updated_at = CURRENT_TIMESTAMP
            WHERE project_id = CAST(:project_id AS UUID)
            RETURNING project_id
        """)

        result = db.execute(
            query,
            {
                "project_id": project_id,
                "project_name": project.project_name,
                "description": project.description,
                "region": project.region,
                "project_status": project.project_status
            }
        )

        updated_project = result.fetchone()

        if updated_project is None:

            db.rollback()

            return {
                "status": "error",
                "message": "Project not found"
            }

        db.commit()

        return {
            "status": "success",
            "message": "Project updated successfully",
            "project_id": str(updated_project[0])
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# DELETE PROJECT
# =========================================================

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):

    db = SessionLocal()

    try:

        query = text("""
            DELETE FROM projects
            WHERE project_id = CAST(:project_id AS UUID)
            RETURNING project_id
        """)

        result = db.execute(
            query,
            {
                "project_id": project_id
            }
        )

        deleted_project = result.fetchone()

        if deleted_project is None:

            db.rollback()

            return {
                "status": "error",
                "message": "Project not found"
            }

        db.commit()

        return {
            "status": "success",
            "message": "Project deleted successfully",
            "project_id": str(deleted_project[0])
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# CREATE SITE
# =========================================================

@app.post("/sites")
def create_site(site: SiteCreate):

    db = SessionLocal()

    try:

        query = text("""
            INSERT INTO sites
            (
                project_id,
                site_name,
                latitude,
                longitude,
                region,
                land_area,
                elevation,
                land_type,
                ownership
            )
            VALUES
            (
                CAST(:project_id AS UUID),
                :site_name,
                :latitude,
                :longitude,
                :region,
                :land_area,
                :elevation,
                :land_type,
                :ownership
            )
            RETURNING site_id
        """)

        result = db.execute(
            query,
            {
                "project_id": site.project_id,
                "site_name": site.site_name,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "region": site.region,
                "land_area": site.land_area,
                "elevation": site.elevation,
                "land_type": site.land_type,
                "ownership": site.ownership
            }
        )

        site_id = result.fetchone()[0]

        db.commit()

        return {
            "status": "success",
            "message": "Site created successfully",
            "site_id": str(site_id),
            "project_id": site.project_id,
            "site_name": site.site_name,
            "latitude": site.latitude,
            "longitude": site.longitude,
            "region": site.region,
            "land_area": site.land_area,
            "elevation": site.elevation,
            "land_type": site.land_type,
            "ownership": site.ownership
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# GET ALL SITES
# =========================================================

@app.get("/sites")
def get_sites():

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                site_id,
                project_id,
                site_name,
                latitude,
                longitude,
                region,
                land_area,
                elevation,
                land_type,
                ownership,
                created_at
            FROM sites
            ORDER BY created_at DESC
        """)

        result = db.execute(query)

        sites = []

        for row in result:

            sites.append({
                "site_id": str(row[0]),
                "project_id": str(row[1]),
                "site_name": row[2],
                "latitude": float(row[3]) if row[3] is not None else None,
                "longitude": float(row[4]) if row[4] is not None else None,
                "region": row[5],
                "land_area": row[6],
                "elevation": row[7],
                "land_type": row[8],
                "ownership": row[9],
                "created_at": str(row[10]) if row[10] else None
            })

        return {
            "status": "success",
            "count": len(sites),
            "sites": sites
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# GET SINGLE SITE
# =========================================================

@app.get("/sites/{site_id}")
def get_site(site_id: str):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                site_id,
                project_id,
                site_name,
                latitude,
                longitude,
                region,
                land_area,
                elevation,
                land_type,
                ownership,
                created_at
            FROM sites
            WHERE site_id = CAST(:site_id AS UUID)
        """)

        result = db.execute(
            query,
            {
                "site_id": site_id
            }
        )

        site = result.fetchone()

        if site is None:

            return {
                "status": "error",
                "message": "Site not found"
            }

        return {
            "status": "success",
            "site": {
                "site_id": str(site[0]),
                "project_id": str(site[1]),
                "site_name": site[2],
                "latitude": float(site[3]) if site[3] is not None else None,
                "longitude": float(site[4]) if site[4] is not None else None,
                "region": site[5],
                "land_area": site[6],
                "elevation": site[7],
                "land_type": site[8],
                "ownership": site[9],
                "created_at": str(site[10]) if site[10] else None
            }
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# UPDATE SITE
# =========================================================

@app.put("/sites/{site_id}")
def update_site(
    site_id: str,
    site: SiteCreate
):

    db = SessionLocal()

    try:

        query = text("""
            UPDATE sites
            SET
                project_id = CAST(:project_id AS UUID),
                site_name = :site_name,
                latitude = :latitude,
                longitude = :longitude,
                region = :region,
                land_area = :land_area,
                elevation = :elevation,
                land_type = :land_type,
                ownership = :ownership
            WHERE site_id = CAST(:site_id AS UUID)
            RETURNING site_id
        """)

        result = db.execute(
            query,
            {
                "site_id": site_id,
                "project_id": site.project_id,
                "site_name": site.site_name,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "region": site.region,
                "land_area": site.land_area,
                "elevation": site.elevation,
                "land_type": site.land_type,
                "ownership": site.ownership
            }
        )

        updated_site = result.fetchone()

        if updated_site is None:

            db.rollback()

            return {
                "status": "error",
                "message": "Site not found"
            }

        db.commit()

        return {
            "status": "success",
            "message": "Site updated successfully",
            "site_id": str(updated_site[0])
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()


# =========================================================
# DELETE SITE
# =========================================================

@app.delete("/sites/{site_id}")
def delete_site(site_id: str):

    db = SessionLocal()

    try:

        query = text("""
            DELETE FROM sites
            WHERE site_id = CAST(:site_id AS UUID)
            RETURNING site_id
        """)

        result = db.execute(
            query,
            {
                "site_id": site_id
            }
        )

        deleted_site = result.fetchone()

        if deleted_site is None:

            db.rollback()

            return {
                "status": "error",
                "message": "Site not found"
            }

        db.commit()

        return {
            "status": "success",
            "message": "Site deleted successfully",
            "site_id": str(deleted_site[0])
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# RESOURCE DATA MODEL
# =========================================================

class ResourceDataCreate(BaseModel):
    site_id: str
    recorded_date: str

    temperature: float | None = None
    humidity: float | None = None

    ghi: float | None = None
    dni: float | None = None
    dhi: float | None = None

    wind_speed: float | None = None
    wind_direction: float | None = None

    solar_potential: float | None = None
    wind_potential: float | None = None


# =========================================================
# CREATE RESOURCE DATA
# =========================================================

@app.post("/resource-data")
def create_resource_data(data: ResourceDataCreate):

    db = SessionLocal()

    try:

        query = text("""
            INSERT INTO resource_data
            (
                site_id,
                recorded_date,
                temperature,
                humidity,
                ghi,
                dni,
                dhi,
                wind_speed,
                wind_direction,
                solar_potential,
                wind_potential
            )
            VALUES
            (
                CAST(:site_id AS UUID),
                CAST(:recorded_date AS DATE),
                :temperature,
                :humidity,
                :ghi,
                :dni,
                :dhi,
                :wind_speed,
                :wind_direction,
                :solar_potential,
                :wind_potential
            )
            RETURNING resource_id
        """)

        result = db.execute(
            query,
            {
                "site_id": data.site_id,
                "recorded_date": data.recorded_date,
                "temperature": data.temperature,
                "humidity": data.humidity,
                "ghi": data.ghi,
                "dni": data.dni,
                "dhi": data.dhi,
                "wind_speed": data.wind_speed,
                "wind_direction": data.wind_direction,
                "solar_potential": data.solar_potential,
                "wind_potential": data.wind_potential
            }
        )

        resource_id = result.fetchone()[0]

        db.commit()

        return {
            "status": "success",
            "message": "Resource data created successfully",
            "resource_id": str(resource_id),
            "site_id": data.site_id,
            "recorded_date": data.recorded_date
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# GET ALL RESOURCE DATA
# =========================================================

@app.get("/resource-data")
def get_resource_data():

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                resource_id,
                site_id,
                recorded_date,
                temperature,
                humidity,
                ghi,
                dni,
                dhi,
                wind_speed,
                wind_direction,
                solar_potential,
                wind_potential,
                created_at
            FROM resource_data
            ORDER BY recorded_date DESC
        """)

        result = db.execute(query)

        resources = []

        for row in result:

            resources.append({
                "resource_id": str(row[0]),
                "site_id": str(row[1]),
                "recorded_date": str(row[2]),
                "temperature": row[3],
                "humidity": row[4],
                "ghi": row[5],
                "dni": row[6],
                "dhi": row[7],
                "wind_speed": row[8],
                "wind_direction": row[9],
                "solar_potential": row[10],
                "wind_potential": row[11],
                "created_at": str(row[12]) if row[12] else None
            })

        return {
            "status": "success",
            "count": len(resources),
            "resource_data": resources
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# GET SINGLE RESOURCE DATA
# =========================================================

@app.get("/resource-data/{resource_id}")
def get_single_resource_data(resource_id: str):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                resource_id,
                site_id,
                recorded_date,
                temperature,
                humidity,
                ghi,
                dni,
                dhi,
                wind_speed,
                wind_direction,
                solar_potential,
                wind_potential,
                created_at
            FROM resource_data
            WHERE resource_id = CAST(:resource_id AS UUID)
        """)

        result = db.execute(
            query,
            {
                "resource_id": resource_id
            }
        )

        resource = result.fetchone()

        if resource is None:

            return {
                "status": "error",
                "message": "Resource data not found"
            }

        return {
            "status": "success",
            "resource_data": {
                "resource_id": str(resource[0]),
                "site_id": str(resource[1]),
                "recorded_date": str(resource[2]),
                "temperature": resource[3],
                "humidity": resource[4],
                "ghi": resource[5],
                "dni": resource[6],
                "dhi": resource[7],
                "wind_speed": resource[8],
                "wind_direction": resource[9],
                "solar_potential": resource[10],
                "wind_potential": resource[11],
                "created_at": str(resource[12]) if resource[12] else None
            }
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# UPDATE RESOURCE DATA
# =========================================================

@app.put("/resource-data/{resource_id}")
def update_resource_data(
    resource_id: str,
    data: ResourceDataCreate
):

    db = SessionLocal()

    try:

        query = text("""
            UPDATE resource_data
            SET
                site_id = CAST(:site_id AS UUID),
                recorded_date = CAST(:recorded_date AS DATE),
                temperature = :temperature,
                humidity = :humidity,
                ghi = :ghi,
                dni = :dni,
                dhi = :dhi,
                wind_speed = :wind_speed,
                wind_direction = :wind_direction,
                solar_potential = :solar_potential,
                wind_potential = :wind_potential
            WHERE resource_id = CAST(:resource_id AS UUID)
            RETURNING resource_id
        """)

        result = db.execute(
            query,
            {
                "resource_id": resource_id,
                "site_id": data.site_id,
                "recorded_date": data.recorded_date,
                "temperature": data.temperature,
                "humidity": data.humidity,
                "ghi": data.ghi,
                "dni": data.dni,
                "dhi": data.dhi,
                "wind_speed": data.wind_speed,
                "wind_direction": data.wind_direction,
                "solar_potential": data.solar_potential,
                "wind_potential": data.wind_potential
            }
        )

        updated_resource = result.fetchone()

        if updated_resource is None:

            db.rollback()

            return {
                "status": "error",
                "message": "Resource data not found"
            }

        db.commit()

        return {
            "status": "success",
            "message": "Resource data updated successfully",
            "resource_id": str(updated_resource[0])
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# DELETE RESOURCE DATA
# =========================================================

@app.delete("/resource-data/{resource_id}")
def delete_resource_data(resource_id: str):

    db = SessionLocal()

    try:

        query = text("""
            DELETE FROM resource_data
            WHERE resource_id = CAST(:resource_id AS UUID)
            RETURNING resource_id
        """)

        result = db.execute(
            query,
            {
                "resource_id": resource_id
            }
        )

        deleted_resource = result.fetchone()

        if deleted_resource is None:

            db.rollback()

            return {
                "status": "error",
                "message": "Resource data not found"
            }

        db.commit()

        return {
            "status": "success",
            "message": "Resource data deleted successfully",
            "resource_id": str(deleted_resource[0])
        }

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# NASA POWER WEATHER DATA
# =========================================================

@app.get("/sites/{site_id}/weather")
def get_site_weather(site_id: str):

    db = SessionLocal()

    try:

        # Get site coordinates
        query = text("""
            SELECT
                site_id,
                latitude,
                longitude
            FROM sites
            WHERE site_id = CAST(:site_id AS UUID)
        """)

        result = db.execute(
            query,
            {
                "site_id": site_id
            }
        )

        site = result.fetchone()

        if site is None:

            return {
                "status": "error",
                "message": "Site not found"
            }

        latitude = site[1]
        longitude = site[2]

        if latitude is None or longitude is None:

            return {
                "status": "error",
                "message": "Site does not have latitude and longitude"
            }

        # NASA POWER API
        import requests

        url = "https://power.larc.nasa.gov/api/temporal/daily/point"

        params = {
            "parameters": (
                "T2M,WS10M,ALLSKY_SFC_SW_DWN,"
                "ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF"
            ),
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,
            "start": "20220101",
            "end": "20251231",
            "format": "JSON"
        }

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        nasa_data = response.json()

        return {
            "status": "success",
            "site_id": site_id,
            "latitude": latitude,
            "longitude": longitude,
            "source": "NASA POWER",
            "data": nasa_data
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# FETCH NASA POWER DATA AND SAVE TO DATABASE
# =========================================================

@app.post("/sites/{site_id}/fetch-weather")
def fetch_weather_and_save(site_id: str):

    db = SessionLocal()

    try:

        import requests

        # -------------------------------------------------
        # 1. GET SITE LATITUDE AND LONGITUDE
        # -------------------------------------------------

        query = text("""
            SELECT
                latitude,
                longitude
            FROM sites
            WHERE site_id = CAST(:site_id AS UUID)
        """)

        result = db.execute(
            query,
            {
                "site_id": site_id
            }
        )

        site = result.fetchone()

        if site is None:

            return {
                "status": "error",
                "message": "Site not found"
            }

        latitude = site[0]
        longitude = site[1]

        if latitude is None or longitude is None:

            return {
                "status": "error",
                "message": "Site does not have latitude and longitude"
            }

        # -------------------------------------------------
        # 2. NASA POWER API
        # -------------------------------------------------

        url = "https://power.larc.nasa.gov/api/temporal/daily/point"

        params = {
            "parameters": (
                "T2M,WS10M,ALLSKY_SFC_SW_DWN,"
                "ALLSKY_SFC_SW_DNI,ALLSKY_SFC_SW_DIFF"
            ),
            "community": "RE",
            "longitude": longitude,
            "latitude": latitude,

            # 4 YEARS OF HISTORICAL DATA
            "start": "20220101",
            "end": "20251231",

            "format": "JSON"
        }

        # -------------------------------------------------
        # 3. CALL NASA POWER
        # -------------------------------------------------

        response = requests.get(
            url,
            params=params,
            timeout=60
        )

        response.raise_for_status()

        nasa_data = response.json()

        # -------------------------------------------------
        # 4. GET NASA PARAMETERS
        # -------------------------------------------------

        properties = nasa_data["properties"]["parameter"]

        temperature_data = properties.get("T2M", {})
        wind_speed_data = properties.get("WS10M", {})
        ghi_data = properties.get(
            "ALLSKY_SFC_SW_DWN",
            {}
        )
        dni_data = properties.get(
            "ALLSKY_SFC_SW_DNI",
            {}
        )
        dhi_data = properties.get(
            "ALLSKY_SFC_SW_DIFF",
            {}
        )

        # -------------------------------------------------
        # 5. GET ALL DATES
        # -------------------------------------------------

        dates = list(temperature_data.keys())

        saved_count = 0
        skipped_count = 0

        # -------------------------------------------------
        # 6. SAVE EACH DAY
        # -------------------------------------------------

        for date in dates:

            temperature = temperature_data.get(date)

            wind_speed = wind_speed_data.get(date)

            ghi = ghi_data.get(date)

            dni = dni_data.get(date)

            dhi = dhi_data.get(date)

            # -------------------------------------------------
            # 7. AVOID DUPLICATES
            # -------------------------------------------------

            insert_query = text("""
                INSERT INTO resource_data
                (
                    site_id,
                    recorded_date,
                    temperature,
                    ghi,
                    dni,
                    dhi,
                    wind_speed
                )
                SELECT
                    CAST(:site_id AS UUID),
                    CAST(:recorded_date AS DATE),
                    :temperature,
                    :ghi,
                    :dni,
                    :dhi,
                    :wind_speed
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM resource_data
                    WHERE site_id = CAST(:site_id AS UUID)
                    AND recorded_date = CAST(:recorded_date AS DATE)
                )
            """)

            result = db.execute(
                insert_query,
                {
                    "site_id": site_id,
                    "recorded_date": date,
                    "temperature": temperature,
                    "ghi": ghi,
                    "dni": dni,
                    "dhi": dhi,
                    "wind_speed": wind_speed
                }
            )

            if result.rowcount > 0:
                saved_count += 1
            else:
                skipped_count += 1

        # -------------------------------------------------
        # 8. COMMIT
        # -------------------------------------------------

        db.commit()

        # -------------------------------------------------
        # 9. RESPONSE
        # -------------------------------------------------

        return {
            "status": "success",
            "message": "NASA POWER historical data processed successfully",
            "site_id": site_id,
            "latitude": latitude,
            "longitude": longitude,
            "period": "2022-01-01 to 2025-12-31",
            "records_saved": saved_count,
            "records_skipped": skipped_count,
            "total_dates_received": len(dates)
        }

    # -----------------------------------------------------
    # ERROR
    # -----------------------------------------------------

    except Exception as e:

        db.rollback()

        return {
            "status": "error",
            "message": str(e)
        }

    # -----------------------------------------------------
    # CLOSE DATABASE
    # -----------------------------------------------------

    finally:

        db.close()

# =========================================================
# GET ML TRAINING DATA
# =========================================================

@app.get("/ml-data")
def get_ml_data():

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                temperature,
                humidity,
                ghi,
                dni,
                dhi,
                wind_speed,
                wind_direction,
                solar_potential,
                wind_potential
            FROM resource_data
            WHERE
                temperature IS NOT NULL
                AND ghi IS NOT NULL
                AND wind_speed IS NOT NULL
        """)

        result = db.execute(query)

        data = []

        for row in result:

            data.append({
                "temperature": row[0],
                "humidity": row[1],
                "ghi": row[2],
                "dni": row[3],
                "dhi": row[4],
                "wind_speed": row[5],
                "wind_direction": row[6],
                "solar_potential": row[7],
                "wind_potential": row[8]
            })

        return {
            "status": "success",
            "count": len(data),
            "data": data
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# PREDICT SOLAR USING LATEST DATABASE DATA
# =========================================================

@app.get("/predict-latest-solar")
def predict_latest_solar():

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                temperature,
                dni,
                dhi,
                wind_speed,
                recorded_date
            FROM resource_data
            ORDER BY recorded_date DESC
            LIMIT 1
        """)

        result = db.execute(query)

        row = result.fetchone()

        if row is None:

            return {
                "status": "error",
                "message": "No resource data found"
            }

        temperature = float(row[0])
        dni = float(row[1])
        dhi = float(row[2])
        wind_speed = float(row[3])
        recorded_date = str(row[4])

        predicted_ghi = predict_solar(
            temperature=temperature,
            dni=dni,
            dhi=dhi,
            wind_speed=wind_speed
        )

        return {

            "status": "success",

            "message": "Solar prediction generated from latest database data",

            "recorded_date": recorded_date,

            "input": {

                "temperature": temperature,

                "dni": dni,

                "dhi": dhi,

                "wind_speed": wind_speed

            },

            "predicted_ghi": predicted_ghi

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }

    finally:

        db.close()

# =========================================================
# WIND PREDICTION
# =========================================================

@app.post("/predict-wind")
def predict_wind_api(data: WindPredictionRequest):

    try:

        predicted_wind = predict_wind(
            temperature=data.temperature,
            ghi=data.ghi,
            dni=data.dni,
            dhi=data.dhi
        )

        return {
            "status": "success",
            "message": "Wind prediction generated successfully",
            "input": {
                "temperature": data.temperature,
                "ghi": data.ghi,
                "dni": data.dni,
                "dhi": data.dhi
            },
            "predicted_wind_speed": predicted_wind
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

# =========================================================
# SITE RENEWABLE ENERGY PREDICTION
# =========================================================

@app.get("/sites/{site_id}/prediction")
def get_site_prediction(site_id: str):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                temperature,
                ghi,
                dni,
                dhi,
                wind_speed,
                recorded_date
            FROM resource_data
            WHERE site_id = CAST(:site_id AS UUID)
            ORDER BY recorded_date DESC
            LIMIT 1
        """)

        result = db.execute(
            query,
            {
                "site_id": site_id
            }
        )

        row = result.fetchone()

        if row is None:

            return {
                "status": "error",
                "message": "No resource data found for this site"
            }

        temperature = float(row[0])
        ghi = float(row[1])
        dni = float(row[2])
        dhi = float(row[3])
        wind_speed = float(row[4])
        recorded_date = str(row[5])

        # Solar prediction
        predicted_ghi = predict_solar(
            temperature=temperature,
            dni=dni,
            dhi=dhi,
            wind_speed=wind_speed
        )

        # Wind prediction
        predicted_wind = predict_wind(
            temperature=temperature,
            ghi=ghi,
            dni=dni,
            dhi=dhi
        )

        return {

            "status": "success",

            "site_id": site_id,

            "recorded_date": recorded_date,

            "input_data": {

                "temperature": temperature,

                "ghi": ghi,

                "dni": dni,

                "dhi": dhi,

                "wind_speed": wind_speed

            },

            "prediction": {

                "predicted_ghi": predicted_ghi,

                "predicted_wind_speed": predicted_wind

            }

        }

    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }

    finally:

        db.close()

# =========================================================
# SITE DASHBOARD
# =========================================================

@app.get("/sites/{site_id}/dashboard")
def get_site_dashboard(site_id: str):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                temperature,
                ghi,
                dni,
                dhi,
                wind_speed,
                recorded_date
            FROM resource_data
            WHERE site_id = CAST(:site_id AS UUID)
            ORDER BY recorded_date DESC
            LIMIT 1
        """)

        result = db.execute(
            query,
            {"site_id": site_id}
        )

        row = result.fetchone()

        if row is None:
            return {
                "status": "error",
                "message": "No resource data found for this site"
            }

        temperature = float(row[0])
        ghi = float(row[1])
        dni = float(row[2])
        dhi = float(row[3])
        wind_speed = float(row[4])
        recorded_date = str(row[5])

        # Solar ML prediction
        predicted_ghi = predict_solar(
            temperature=temperature,
            dni=dni,
            dhi=dhi,
            wind_speed=wind_speed
        )

        # Wind ML prediction
        predicted_wind = predict_wind(
            temperature=temperature,
            ghi=ghi,
            dni=dni,
            dhi=dhi
        )

        return {
            "status": "success",

            "site_id": site_id,

            "recorded_date": recorded_date,

            "weather": {
                "temperature": temperature,
                "wind_speed": wind_speed
            },

            "solar": {
                "ghi": ghi,
                "dni": dni,
                "dhi": dhi,
                "predicted_ghi": predicted_ghi
            },

            "wind": {
                "current_wind_speed": wind_speed,
                "predicted_wind_speed": predicted_wind
            }
        }

    except Exception as e:

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        db.close()

# =========================================================
# DEPLOYMENT RECOMMENDATION
# =========================================================

@app.get("/sites/{site_id}/deployment-recommendation")
def get_deployment_recommendation(site_id: str):

    db = SessionLocal()

    try:

        # ---------------------------------------------
        # GET LATEST RESOURCE DATA
        # ---------------------------------------------

        query = text("""
            SELECT
                temperature,
                ghi,
                dni,
                dhi,
                wind_speed,
                recorded_date
            FROM resource_data
            WHERE site_id = CAST(:site_id AS UUID)
            ORDER BY recorded_date DESC
            LIMIT 1
        """)

        result = db.execute(
            query,
            {"site_id": site_id}
        )

        row = result.fetchone()

        if row is None:

            return {
                "status": "error",
                "message": "No resource data found"
            }


        temperature = float(row[0])
        ghi = float(row[1])
        dni = float(row[2])
        dhi = float(row[3])
        wind_speed = float(row[4])
        recorded_date = str(row[5])


        # ---------------------------------------------
        # ML PREDICTIONS
        # ---------------------------------------------

        predicted_ghi = predict_solar(
            temperature=temperature,
            dni=dni,
            dhi=dhi,
            wind_speed=wind_speed
        )


        predicted_wind = predict_wind(
            temperature=temperature,
            ghi=ghi,
            dni=dni,
            dhi=dhi
        )


        # ---------------------------------------------
        # SOLAR SCORE
        # ---------------------------------------------

        if predicted_ghi >= 6:
            solar_score = 100

        elif predicted_ghi >= 5:
            solar_score = 90

        elif predicted_ghi >= 4:
            solar_score = 80

        elif predicted_ghi >= 3:
            solar_score = 70

        elif predicted_ghi >= 2:
            solar_score = 50

        else:
            solar_score = 30


        # ---------------------------------------------
        # WIND SCORE
        # ---------------------------------------------

        if predicted_wind >= 8:
            wind_score = 100

        elif predicted_wind >= 7:
            wind_score = 90

        elif predicted_wind >= 6:
            wind_score = 80

        elif predicted_wind >= 5:
            wind_score = 70

        elif predicted_wind >= 4:
            wind_score = 60

        elif predicted_wind >= 3:
            wind_score = 50

        else:
            wind_score = 30


        # ---------------------------------------------
        # OVERALL SCORE
        # ---------------------------------------------

        overall_score = round(
            (solar_score * 0.5) +
            (wind_score * 0.5)
        )


        # ---------------------------------------------
        # RECOMMENDATION
        # ---------------------------------------------

        if (
            solar_score >= 80 and
            wind_score >= 80
        ):

            recommendation = (
                "Excellent location for "
                "Hybrid Solar + Wind deployment."
            )

            deployment_type = "HYBRID"


        elif solar_score >= 80:

            recommendation = (
                "Strong solar potential. "
                "Solar deployment is recommended."
            )

            deployment_type = "SOLAR"


        elif wind_score >= 80:

            recommendation = (
                "Strong wind potential. "
                "Wind deployment is recommended."
            )

            deployment_type = "WIND"


        elif (
            solar_score >= 60 and
            wind_score >= 60
        ):

            recommendation = (
                "Moderate potential for both resources. "
                "Hybrid deployment can be considered."
            )

            deployment_type = "HYBRID"


        else:

            recommendation = (
                "Low renewable energy potential. "
                "Detailed site assessment is recommended."
            )

            deployment_type = "FURTHER_ANALYSIS"


        # ---------------------------------------------
        # RETURN RESULT
        # ---------------------------------------------

        return {

            "status": "success",

            "site_id": site_id,

            "recorded_date": recorded_date,

            "predictions": {

                "predicted_ghi": predicted_ghi,

                "predicted_wind_speed": predicted_wind

            },

            "scores": {

                "solar_score": solar_score,

                "wind_score": wind_score,

                "overall_score": overall_score

            },

            "recommendation": {

                "deployment_type": deployment_type,

                "message": recommendation

            }

        }


    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


    finally:

        db.close()

# =========================================================
# HISTORICAL RESOURCE DATA
# =========================================================

@app.get("/sites/{site_id}/historical-data")
def get_historical_data(site_id: str):

    db = SessionLocal()

    try:

        query = text("""
            SELECT
                recorded_date,
                temperature,
                ghi,
                dni,
                dhi,
                wind_speed
            FROM resource_data
            WHERE site_id = CAST(:site_id AS UUID)
            ORDER BY recorded_date ASC
        """)

        result = db.execute(
            query,
            {"site_id": site_id}
        )

        rows = result.fetchall()

        if not rows:

            return {
                "status": "error",
                "message": "No historical resource data found"
            }


        records = []

        for row in rows:

            records.append({

                "recorded_date": str(row[0]),

                "temperature": float(row[1]),

                "ghi": float(row[2]),

                "dni": float(row[3]),

                "dhi": float(row[4]),

                "wind_speed": float(row[5])

            })


        return {

            "status": "success",

            "site_id": site_id,

            "count": len(records),

            "data": records

        }


    except Exception as e:

        return {

            "status": "error",

            "message": str(e)

        }


    finally:

        db.close()
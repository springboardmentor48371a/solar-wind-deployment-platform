import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base
from app.models import Role, User, Project, Site, EnvironmentalData, SiteAssessment
from app.auth import get_password_hash
from app.gis_analysis import perform_gis_distance_analysis, calculate_suitability_score

# Static geographic features for distance calculations (Western/Southern India)
STATIC_SUBSTATIONS = [
    {"name": "Bhadla Solar Substation", "latitude": 27.53, "longitude": 72.18},
    {"name": "Charanka Solar Substation", "latitude": 23.90, "longitude": 71.20},
    {"name": "Kutch Wind Substation", "latitude": 23.45, "longitude": 69.50},
    {"name": "Jaisalmer Wind Substation", "latitude": 26.91, "longitude": 70.90},
    {"name": "Muppandal Wind Substation", "latitude": 8.26, "longitude": 77.54}
]

# Environmental protected areas represented as WKT polygons
STATIC_PROTECTED_ZONES = [
    # Desert National Park, Rajasthan (Approx polygon)
    {
        "name": "Desert National Park",
        "geometry_wkt": "POLYGON ((70.3 26.5, 70.8 26.5, 70.8 26.9, 70.3 26.9, 70.3 26.5))"
    },
    # Wild Ass Sanctuary, Kutch (Approx polygon)
    {
        "name": "Kutch Wild Ass Sanctuary",
        "geometry_wkt": "POLYGON ((70.8 23.1, 71.5 23.1, 71.5 23.6, 70.8 23.6, 70.8 23.1))"
    }
]

def create_database_if_not_exists():
    """Connects to 'postgres' default database and creates the target DB if missing."""
    print("Checking connection to PostgreSQL default database...")
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{settings.DB_NAME}';")
        exists = cursor.fetchone()
        if not exists:
            print(f"Database '{settings.DB_NAME}' does not exist. Creating...")
            cursor.execute(f"CREATE DATABASE {settings.DB_NAME};")
        else:
            print(f"Database '{settings.DB_NAME}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error connecting to/creating database: {e}")
        print("Please check your .env settings and ensure PostgreSQL is running.")
        raise e

def seed_data():
    create_database_if_not_exists()

    # Create session connection
    engine = create_engine(settings.DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Creating tables if they do not exist...")
    # Attempt to enable postgis (we handle exceptions if not installed)
    try:
        session.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        session.commit()
        print("PostGIS extension created/enabled successfully.")
    except Exception as e:
        session.rollback()
        print("Notice: PostGIS extension could not be loaded. Falling back to python GeoPandas/Shapely spatial processing.")

    print("Dropping existing tables for clean seed...")
    Base.metadata.drop_all(bind=engine)
    
    print("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("Seeding user roles...")
    role_names = ["Admin", "Planner", "GIS Analyst", "Project Manager"]
    role_map = {}
    for rname in role_names:
        role = session.query(Role).filter(Role.role_name == rname).first()
        if not role:
            role = Role(
                role_id=uuid.uuid4(),
                role_name=rname,
                description=f"{rname} role for platform analysis and operations."
            )
            session.add(role)
            session.flush()
        role_map[rname] = role.role_id

    # 2. Seed Users
    print("Seeding test users...")
    user_credentials = [
        {"full_name": "Admin User", "email": "admin@renewable.in", "password": "adminpassword", "role": "Admin"},
        {"full_name": "Planner User", "email": "planner@renewable.in", "password": "plannerpassword", "role": "Planner"},
        {"full_name": "GIS Analyst User", "email": "gis@renewable.in", "password": "gispassword", "role": "GIS Analyst"},
        {"full_name": "Project Manager User", "email": "manager@renewable.in", "password": "managerpassword", "role": "Project Manager"}
    ]
    
    planner_user_id = None
    for cred in user_credentials:
        user = session.query(User).filter(User.email == cred["email"]).first()
        if not user:
            user = User(
                user_id=uuid.uuid4(),
                full_name=cred["full_name"],
                email=cred["email"],
                password_hash=get_password_hash(cred["password"]),
                phone_number="+91 99999 88888",
                organization="National Renewable Energy Board",
                role_id=role_map[cred["role"]],
                account_status="Active"
            )
            session.add(user)
            session.flush()
        if cred["role"] == "Planner":
            planner_user_id = user.user_id

    # 3. Seed Projects
    print("Seeding demo projects...")
    proj_name = "India Western Corridor Plan"
    project = session.query(Project).filter(Project.project_name == proj_name).first()
    if not project:
        project = Project(
            project_id=uuid.uuid4(),
            project_name=proj_name,
            description="Feasibility study of high-capacity solar, wind, and hybrid sites in Gujarat & Rajasthan.",
            region="Gujarat/Rajasthan",
            project_status="Analysis",
            created_by=planner_user_id
        )
        session.add(project)
        session.flush()
    project_id = project.project_id

    # 4. Seed Sites and Environmental/Assessment data
    print("Seeding candidate locations in Gujarat/Rajasthan...")
    # List of candidate points:
    # Some close to Bhadla solar (Bhadla coordinates: 27.53, 72.18)
    # Some inside protected area Desert National Park (Rajasthan, roughly 26.7, 70.5)
    # Some close to Kutch wind (Kutch coordinates: 23.45, 69.50)
    candidate_sites_data = [
        {
            "name": "Bhadla Border Expansion Site",
            "lat": 27.5500, "lon": 72.1900,
            "area": 120.0, "elevation": 180.0, "slope": 1.2,
            "solar_irr": 6.8, "wind_spd": 4.1, "temp": 32.5,
            "rain": 210.0, "hum": 25.0, "cloud": 12.0, "veg": 0.12,
            "type": "Desert", "ownership": "Government"
        },
        {
            "name": "Jaisalmer Frontier Wind Ridge",
            "lat": 26.8900, "lon": 70.9200,
            "area": 85.0, "elevation": 240.0, "slope": 3.8,
            "solar_irr": 6.3, "wind_spd": 7.8, "temp": 30.0,
            "rain": 180.0, "hum": 30.0, "cloud": 15.0, "veg": 0.08,
            "type": "Desert", "ownership": "Government"
        },
        {
            "name": "Kutch Saline Plain (Near Substation)",
            "lat": 23.4800, "lon": 69.5500,
            "area": 150.0, "elevation": 12.0, "slope": 0.5,
            "solar_irr": 5.9, "wind_spd": 8.2, "temp": 28.5,
            "rain": 350.0, "hum": 55.0, "cloud": 20.0, "veg": 0.05,
            "type": "Wasteland", "ownership": "Government"
        },
        {
            "name": "Charanka Solar Buffer site",
            "lat": 23.9200, "lon": 71.2200,
            "area": 45.0, "elevation": 35.0, "slope": 1.0,
            "solar_irr": 6.1, "wind_spd": 3.5, "temp": 29.8,
            "rain": 400.0, "hum": 45.0, "cloud": 22.0, "veg": 0.15,
            "type": "Plain", "ownership": "Private"
        },
        {
            "name": "Desert National Park Core (Restricted Area)",
            "lat": 26.6500, "lon": 70.4500, # Inside Desert National Park
            "area": 200.0, "elevation": 220.0, "slope": 2.5,
            "solar_irr": 6.7, "wind_spd": 5.9, "temp": 31.0,
            "rain": 150.0, "hum": 20.0, "cloud": 10.0, "veg": 0.07,
            "type": "Desert", "ownership": "Government"
        },
        {
            "name": "Isolated Barmer Ridge (Far Grid)",
            "lat": 25.8000, "lon": 71.3000, # Far from substations
            "area": 90.0, "elevation": 310.0, "slope": 6.5,
            "solar_irr": 6.2, "wind_spd": 6.2, "temp": 31.5,
            "rain": 250.0, "hum": 28.0, "cloud": 14.0, "veg": 0.11,
            "type": "Barren", "ownership": "Government"
        }
    ]

    for sdata in candidate_sites_data:
        site = session.query(Site).filter(Site.site_name == sdata["name"]).first()
        if not site:
            # 1. Create Site
            site = Site(
                site_id=uuid.uuid4(),
                project_id=project_id,
                site_name=sdata["name"],
                latitude=sdata["lat"],
                longitude=sdata["lon"],
                region="Gujarat/Rajasthan",
                land_area=sdata["area"],
                elevation=sdata["elevation"],
                land_type=sdata["type"],
                ownership=sdata["ownership"]
            )
            session.add(site)
            session.flush()
            
            # 2. Compute GIS distances dynamically
            gis_res = perform_gis_distance_analysis(
                sdata["lat"], 
                sdata["lon"], 
                STATIC_SUBSTATIONS, 
                STATIC_PROTECTED_ZONES
            )
            
            # 3. Create Environmental Data
            env_rec = EnvironmentalData(
                environment_id=uuid.uuid4(),
                site_id=site.site_id,
                solar_irradiance=sdata["solar_irr"],
                wind_speed=sdata["wind_spd"],
                wind_direction=180.0, # South wind
                temperature=sdata["temp"],
                rainfall=sdata["rain"],
                humidity=sdata["hum"],
                cloud_cover=sdata["cloud"],
                terrain_slope=sdata["slope"],
                vegetation_index=sdata["veg"],
                nearest_substation_distance=gis_res["nearest_substation_distance"],
                road_distance=gis_res["road_distance"],
                protected_area=gis_res["protected_area"]
            )
            session.add(env_rec)
            
            # 4. Calculate suitability and AI predictions
            eval_res = calculate_suitability_score(
                solar_irradiance=sdata["solar_irr"],
                wind_speed=sdata["wind_spd"],
                nearest_substation_dist=gis_res["nearest_substation_distance"],
                road_dist=gis_res["road_distance"],
                protected_area=gis_res["protected_area"],
                terrain_slope=sdata["slope"],
                land_area=sdata["area"],
                land_type=sdata["type"]
            )
            
            # Formulate synthetic ML forecasts
            # Expected annual energy:
            # Solar: Irradiance * 365 * efficiency (0.75) * land area scaled capacity (e.g. 1 MW per 4 acres)
            capacity_solar_mw = sdata["area"] / 4.0
            solar_yield_mwh = sdata["solar_irr"] * 365 * 0.75 * capacity_solar_mw
            
            # Wind: CF * 8760 * capacity (e.g. 1 MW per 8 acres)
            capacity_wind_mw = sdata["area"] / 8.0
            cf_ratio = eval_res["scores"]["wind_factor"] / 100.0
            wind_yield_mwh = cf_ratio * 8760 * capacity_wind_mw
            
            # Revenue: MWh * rate (e.g. ₹3.0 per kWh = ₹3000 per MWh)
            tariff_per_mwh = 3000.0 # INR
            if eval_res["deployment_type"] == "Solar":
                energy_forecast = solar_yield_mwh
                cf_ratio_final = eval_res["scores"]["solar_factor"] / 100.0
            elif eval_res["deployment_type"] == "Wind":
                energy_forecast = wind_yield_mwh
                cf_ratio_final = cf_ratio
            else: # Hybrid
                energy_forecast = solar_yield_mwh + wind_yield_mwh
                cf_ratio_final = (eval_res["scores"]["solar_factor"] + eval_res["scores"]["wind_factor"]) / 200.0
            
            revenue_estimate = energy_forecast * tariff_per_mwh
            
            assessment = SiteAssessment(
                assessment_id=uuid.uuid4(),
                site_id=site.site_id,
                solar_energy_prediction=round(solar_yield_mwh, 2),
                wind_energy_prediction=round(wind_yield_mwh, 2),
                solar_capacity_factor=round(eval_res["scores"]["solar_factor"] / 100.0, 3),
                wind_capacity_factor=round(cf_ratio, 3),
                suitability_score=eval_res["suitability_score"],
                suitability_category=eval_res["suitability_category"],
                energy_forecast=round(energy_forecast, 2),
                revenue_estimate=round(revenue_estimate, 2),
                deployment_type=eval_res["deployment_type"],
                recommendation=(
                    f"Recommended for {eval_res['deployment_type']} development. "
                    f"Overall suitability is {eval_res['suitability_category']} with a score of {eval_res['suitability_score']}/100. "
                    f"Proximity to substation is {gis_res['nearest_substation_distance']} km. "
                    f"Environmental risk: {'HIGH (Protected Zone)' if gis_res['protected_area'] else 'None'}."
                ),
                analysis_status="Completed"
            )
            session.add(assessment)
            
    session.commit()
    print("Database seeding completed successfully!")
    session.close()

if __name__ == "__main__":
    seed_data()

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta
import uuid
from typing import List, Dict, Any, Optional

from app.config import settings
from app.database import get_db, engine
from app.models import Role, User, Project, Site, EnvironmentalData, SiteAssessment, Notification, Report
from app.schemas import (
    Token, UserRegister, UserResponse, ProjectCreate, ProjectResponse,
    SiteCreate, SiteResponse, RecalculateWeightsRequest, SiteAssessmentResponse,
    NotificationResponse, ReportResponse
)
from app.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, RoleChecker
)
from app.gis_analysis import perform_gis_distance_analysis, calculate_suitability_score
from app.ml_model import predictor
from app.seed import STATIC_SUBSTATIONS, STATIC_PROTECTED_ZONES

app = FastAPI(
    title="Solar & Wind Deployment Intelligence Platform API",
    description="API for evaluating renewable energy sites in India using AI and spatial analysis.",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development, we allow all origins. In production, configure this.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")

# ----------------- Auth Endpoints -----------------

@api_router.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )
    
    # Check if role exists
    role = db.query(Role).filter(Role.role_name == user_in.role_name).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role '{user_in.role_name}' does not exist."
        )
        
    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        user_id=uuid.uuid4(),
        full_name=user_in.full_name,
        email=user_in.email,
        password_hash=hashed_pwd,
        phone_number=user_in.phone_number,
        organization=user_in.organization,
        role_id=role.role_id,
        account_status="Active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@api_router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )
        
    if user.account_status != "Active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is inactive."
        )

    # Get user role
    role = db.query(Role).filter(Role.role_id == user.role_id).first()
    role_name = role.role_name if role else "Planner"

    # Issue JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.user_id), "role": role_name},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role_name,
        "user_id": user.user_id,
        "full_name": user.full_name
    }

@api_router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ----------------- Project Endpoints -----------------

@api_router.get("/projects", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # All roles can list projects
    return db.query(Project).all()

@api_router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Planner", "Project Manager", "Admin"]))
):
    new_project = Project(
        project_id=uuid.uuid4(),
        project_name=project_in.project_name,
        description=project_in.description,
        region=project_in.region,
        project_status="Planning",
        created_by=current_user.user_id
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    # Create system notification
    sys_admin = db.query(User).filter(User.email == "admin@renewable.in").first()
    notif = Notification(
        notification_id=uuid.uuid4(),
        user_id=current_user.user_id,
        title="Project Created",
        message=f"Project '{new_project.project_name}' has been created in region '{new_project.region}'.",
        notification_type="System",
        is_read=False
    )
    db.add(notif)
    db.commit()
    
    return new_project

# ----------------- Site Endpoints -----------------

@api_router.get("/sites", response_model=List[SiteResponse])
def get_sites(
    project_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    query = db.query(Site)
    if project_id:
        query = query.filter(Site.project_id == project_id)
    return query.all()

@api_router.post("/sites", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
def create_site(
    site_in: SiteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Planner", "GIS Analyst", "Admin"]))
):
    # Check if project exists
    project = db.query(Project).filter(Project.project_id == site_in.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found."
        )

    # 1. Spatial distance calculations (GIS Engine)
    from app.osm import fetch_osm_infrastructure
    
    osm_res = fetch_osm_infrastructure(site_in.latitude, site_in.longitude)
    
    gis_res = perform_gis_distance_analysis(
        site_in.latitude, 
        site_in.longitude, 
        STATIC_SUBSTATIONS, 
        STATIC_PROTECTED_ZONES
    )
    
    if osm_res:
        gis_res["nearest_substation_distance"] = osm_res["nearest_substation_distance"]
        gis_res["road_distance"] = osm_res["road_distance"]

    # 2. Climate variables mapping (Querying NASA POWER or falling back to local simulation)
    solar_irr = 6.2 # Default kWh/m2/day
    wind_spd = 5.5  # Default m/s
    wind_dir = 180.0 # Default Degrees
    temp = 30.5     # Default °C
    rain = 250.0    # Default mm
    hum = 35.0      # Default %
    cloud = 15.0    # Default %
    veg = 0.10      # Default NDVI
    
    # SRTM Elevation and Slope
    from app.srtm import fetch_srtm_data
    srtm_res = fetch_srtm_data(site_in.latitude, site_in.longitude)
    if srtm_res:
        elevation = srtm_res["elevation"]
        slope = srtm_res["terrain_slope"]
        srtm_source = srtm_res["source"]
    else:
        elevation = 150.0 # Default elevation
        slope = 1.5       # Default slope
        srtm_source = "Local Estimate"
        
    # Esri Land Cover
    from app.landcover import fetch_esri_landcover
    landcover_res = fetch_esri_landcover(site_in.latitude, site_in.longitude)
    if landcover_res:
        site_in.land_type = landcover_res["mapped_land_type"]
        
    # OSM Protected Area
    from app.osm import fetch_osm_protected_areas
    protected_res = fetch_osm_protected_areas(site_in.latitude, site_in.longitude)
    if protected_res:
        gis_res["protected_area"] = protected_res["is_protected"]
        
    climate_source = "Local Estimate"
    nasa_success = False
    gwa_success = False

    if site_in.environmental_data:
        solar_irr = site_in.environmental_data.solar_irradiance
        wind_spd = site_in.environmental_data.wind_speed
        wind_dir = site_in.environmental_data.wind_direction
        temp = site_in.environmental_data.temperature
        rain = site_in.environmental_data.rainfall
        hum = site_in.environmental_data.humidity
        cloud = site_in.environmental_data.cloud_cover
        slope = site_in.environmental_data.terrain_slope
        veg = site_in.environmental_data.vegetation_index
        climate_source = "Local Estimate"
    else:
        # Query Global Wind Atlas local cropped GeoTIFFs
        from app.global_wind_atlas import fetch_gwa_point_data
        gwa_data = fetch_gwa_point_data(site_in.latitude, site_in.longitude)
        if gwa_data:
            wind_spd = gwa_data["wind_speed"]
            gwa_success = True
            
        # Query NASA POWER Climatology Point API
        from app.nasa_power import fetch_nasa_power_climatology
        nasa_data = fetch_nasa_power_climatology(site_in.latitude, site_in.longitude)
        if nasa_data:
            solar_irr = nasa_data["ALLSKY_SFC_SW_DWN"]
            # Only use NASA wind speed if GWA is unavailable
            if not gwa_success:
                wind_spd = nasa_data["WS50M"]
            wind_dir = nasa_data["WD50M"]
            temp = nasa_data["T2M"]
            rain = nasa_data["PRECTOTCORR_annual"]
            hum = nasa_data["RH2M"]
            cloud = nasa_data["CLOUD_AMT"]
            climate_source = "NASA POWER Climatology"
            nasa_success = True
        else:
            climate_source = "Local Estimate"

    # 3. Model Predictions (Scikit-Learn ML Engine)
    ml_inputs = {
        "latitude": site_in.latitude,
        "longitude": site_in.longitude,
        "elevation": elevation, # fetched from SRTM or default
        "cloud_cover": cloud,
        "temperature": temp,
        "humidity": hum,
        "rainfall": rain,
        "terrain_slope": slope
    }
    ml_preds = predictor.predict_resource_potential(ml_inputs)

    # Use real resource data if successfully retrieved (manual, NASA, or GWA)
    if site_in.environmental_data:
        final_solar_irr = solar_irr
        final_wind_spd = wind_spd
    elif nasa_success or gwa_success:
        final_solar_irr = solar_irr
        final_wind_spd = wind_spd
        
        # Override ML prediction inputs with GWA/NASA values for yield forecasts
        solar_cf = (solar_irr * 0.75) / 24.0
        expected_solar_mwh = solar_irr * 365.0 * 0.75 * 1.0
        wind_cf_pct = min(48.0, max(5.0, (wind_spd ** 2.2) / (9.0 ** 2.2) * 35.0))
        wind_cf = wind_cf_pct / 100.0
        expected_wind_mwh = wind_cf * 8760.0 * 1.0
        
        ml_preds["solar_irradiance"] = round(solar_irr, 2)
        ml_preds["wind_speed"] = round(wind_spd, 2)
        ml_preds["solar_capacity_factor"] = round(solar_cf, 3)
        ml_preds["wind_capacity_factor"] = round(wind_cf, 3)
        ml_preds["expected_solar_energy"] = round(expected_solar_mwh, 2)
        ml_preds["expected_wind_energy"] = round(expected_wind_mwh, 2)
    else:
        final_solar_irr = ml_preds["solar_irradiance"]
        final_wind_spd = ml_preds["wind_speed"]

    # Calculate overall suitability score (Decision scoring Engine)
    suit_res = calculate_suitability_score(
        solar_irradiance=final_solar_irr,
        wind_speed=final_wind_spd,
        nearest_substation_dist=gis_res["nearest_substation_distance"],
        road_dist=gis_res["road_distance"],
        protected_area=gis_res["protected_area"],
        terrain_slope=slope,
        land_area=site_in.land_area,
        land_type=site_in.land_type
    )

    # Compute financial forecast scaling
    # Solar capacity: ~ 4 acres per MW
    # Wind capacity: ~ 8 acres per MW
    cap_solar_mw = site_in.land_area / 4.0
    cap_wind_mw = site_in.land_area / 8.0
    
    tariff_mwh = 3000.0 # INR per MWh (approx ₹3 per kWh)
    if suit_res["deployment_type"] == "Solar":
        expected_energy = ml_preds["expected_solar_energy"] * cap_solar_mw
    elif suit_res["deployment_type"] == "Wind":
        expected_energy = ml_preds["expected_wind_energy"] * cap_wind_mw
    else: # Hybrid
        expected_energy = (ml_preds["expected_solar_energy"] * cap_solar_mw) + (ml_preds["expected_wind_energy"] * cap_wind_mw)
    
    expected_revenue = expected_energy * tariff_mwh

    # Create DB records in Transaction
    try:
        new_site = Site(
            site_id=uuid.uuid4(),
            project_id=site_in.project_id,
            site_name=site_in.site_name,
            latitude=site_in.latitude,
            longitude=site_in.longitude,
            region=project.region,
            land_area=site_in.land_area,
            elevation=elevation, # fetched from SRTM or default
            land_type=site_in.land_type,
            ownership=site_in.ownership
        )
        db.add(new_site)
        db.flush()

        new_env_data = EnvironmentalData(
            environment_id=uuid.uuid4(),
            site_id=new_site.site_id,
            solar_irradiance=final_solar_irr,
            wind_speed=final_wind_spd,
            wind_direction=wind_dir,
            temperature=temp,
            rainfall=rain,
            humidity=hum,
            cloud_cover=cloud,
            terrain_slope=slope,
            vegetation_index=veg,
            nearest_substation_distance=gis_res["nearest_substation_distance"],
            road_distance=gis_res["road_distance"],
            protected_area=gis_res["protected_area"]
        )
        db.add(new_env_data)

        new_assessment = SiteAssessment(
            assessment_id=uuid.uuid4(),
            site_id=new_site.site_id,
            solar_energy_prediction=round(ml_preds["expected_solar_energy"] * cap_solar_mw, 2),
            wind_energy_prediction=round(ml_preds["expected_wind_energy"] * cap_wind_mw, 2),
            solar_capacity_factor=ml_preds["solar_capacity_factor"],
            wind_capacity_factor=ml_preds["wind_capacity_factor"],
            suitability_score=suit_res["suitability_score"],
            suitability_category=suit_res["suitability_category"],
            energy_forecast=round(expected_energy, 2),
            revenue_estimate=round(expected_revenue, 2),
            deployment_type=suit_res["deployment_type"],
            recommendation=(
                f"Recommended for {suit_res['deployment_type']} development. "
                f"Overall score is {suit_res['suitability_score']}/100 ({suit_res['suitability_category']}). "
                f"Proximity to grid: {gis_res['nearest_substation_distance']} km. "
                f"Environmental protection zone intersection: {'YES (UNSUITABLE)' if gis_res['protected_area'] else 'NO'}."
                f" | Climate Source: {climate_source}"
            ),
            analysis_status="Completed"
        )
        db.add(new_assessment)
        db.commit()

        # Send alert if it is inside protected area
        if gis_res["protected_area"]:
            warn_notif = Notification(
                notification_id=uuid.uuid4(),
                user_id=current_user.user_id,
                title="Environmental Protection Exclusion Triggered",
                message=f"Site '{new_site.site_name}' falls inside a protected wildlife/reserve sanctuary and has been flagged Unsuitable.",
                notification_type="Weather", # Matches Category
                is_read=False
            )
            db.add(warn_notif)
            db.commit()
            
        db.refresh(new_site)
        return new_site
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database transaction failed: {e}"
        )

@api_router.get("/sites/{site_id}", response_model=SiteResponse)
def get_site(site_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    site = db.query(Site).filter(Site.site_id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )
    return site

@api_router.post("/sites/{site_id}/recalculate", response_model=SiteAssessmentResponse)
def recalculate_suitability(
    site_id: uuid.UUID,
    weights_in: RecalculateWeightsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["Planner", "Project Manager", "Admin"]))
):
    site = db.query(Site).filter(Site.site_id == site_id).first()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found"
        )

    env_data = site.environmental_data
    if not env_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Environmental data is missing for this site."
        )

    # Compute suitability score using custom weights
    weights = {
        "resource": weights_in.weight_resource,
        "geographic": weights_in.weight_geographic,
        "infrastructure": weights_in.weight_infrastructure,
        "environment": weights_in.weight_environment,
        "economic": weights_in.weight_economic
    }

    suit_res = calculate_suitability_score(
        solar_irradiance=env_data.solar_irradiance,
        wind_speed=env_data.wind_speed,
        nearest_substation_dist=env_data.nearest_substation_distance,
        road_dist=env_data.road_distance,
        protected_area=env_data.protected_area,
        terrain_slope=env_data.terrain_slope,
        land_area=site.land_area,
        land_type=site.land_type,
        weights=weights
    )

    # Get latest assessment and update
    assessment = db.query(SiteAssessment).filter(SiteAssessment.site_id == site_id).order_by(SiteAssessment.analyzed_at.desc()).first()
    if not assessment:
        assessment = SiteAssessment(
            assessment_id=uuid.uuid4(),
            site_id=site_id
        )
        db.add(assessment)

    # Update fields
    assessment.suitability_score = suit_res["suitability_score"]
    assessment.suitability_category = suit_res["suitability_category"]
    assessment.deployment_type = suit_res["deployment_type"]
    assessment.recommendation = (
        f"Recalculated recommendation for {suit_res['deployment_type']}. "
        f"Custom score: {suit_res['suitability_score']}/100 ({suit_res['suitability_category']}). "
        f"Weights used: Resource={weights_in.weight_resource:.2f}, Geo={weights_in.weight_geographic:.2f}, "
        f"Infra={weights_in.weight_infrastructure:.2f}, Env={weights_in.weight_environment:.2f}, Econ={weights_in.weight_economic:.2f}."
    )
    assessment.analyzed_at = func.now()
    assessment.analysis_status = "Completed"

    db.commit()
    db.refresh(assessment)
    return assessment

# ----------------- Infrastructure Layer Endpoints -----------------

@api_router.get("/infrastructure")
def get_infrastructure(current_user: User = Depends(get_current_user)):
    """
    Returns spatial grid substations, major transmission lines, and environmental protected zones.
    This functions as the GIS Layer server for the React Leaflet map.
    """
    # Build GeoJSON for substations
    substation_features = []
    for sub in STATIC_SUBSTATIONS:
        substation_features.append({
            "type": "Feature",
            "properties": {
                "name": sub["name"],
                "type": "substation"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [sub["longitude"], sub["latitude"]]
            }
        })

    # Build GeoJSON for protected areas
    zone_features = []
    # Desert National Park (Rajasthan)
    zone_features.append({
        "type": "Feature",
        "properties": {
            "name": "Desert National Park (Protected)",
            "type": "protected_area"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[70.3, 26.5], [70.8, 26.5], [70.8, 26.9], [70.3, 26.9], [70.3, 26.5]]]
        }
    })
    # Wild Ass Sanctuary (Kutch, Gujarat)
    zone_features.append({
        "type": "Feature",
        "properties": {
            "name": "Kutch Wild Ass Sanctuary (Protected)",
            "type": "protected_area"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[70.8, 23.1], [71.5, 23.1], [71.5, 23.6], [70.8, 23.6], [70.8, 23.1]]]
        }
    })

    # Grid transmission lines
    transmission_features = [{
        "type": "Feature",
        "properties": {
            "name": "Bhuj-Bhadla Green Energy Corridor Grid Line",
            "type": "transmission_line"
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [69.50, 23.45], # Kutch Wind
                [71.20, 23.90], # Charanka Solar
                [70.90, 26.91], # Jaisalmer Wind
                [72.18, 27.53]  # Bhadla Solar
            ]
        }
    }]

    return {
        "substations": {
            "type": "FeatureCollection",
            "features": substation_features
        },
        "protected_zones": {
            "type": "FeatureCollection",
            "features": zone_features
        },
        "transmission_lines": {
            "type": "FeatureCollection",
            "features": transmission_features
        }
    }

# ----------------- Dashboard Stats Endpoints -----------------

@api_router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sites = db.query(Site).all()
    projects = db.query(Project).all()
    
    total_sites = len(sites)
    total_projects = len(projects)
    
    # Calculate averages
    avg_suitability = 0.0
    solar_sites_count = 0
    wind_sites_count = 0
    hybrid_sites_count = 0
    
    if total_sites > 0:
        scores = []
        for s in sites:
            latest_assessment = db.query(SiteAssessment).filter(SiteAssessment.site_id == s.site_id).order_by(SiteAssessment.analyzed_at.desc()).first()
            if latest_assessment:
                scores.append(latest_assessment.suitability_score)
                if latest_assessment.deployment_type == "Solar":
                    solar_sites_count += 1
                elif latest_assessment.deployment_type == "Wind":
                    wind_sites_count += 1
                elif latest_assessment.deployment_type == "Hybrid":
                    hybrid_sites_count += 1
        
        if scores:
            avg_suitability = sum(scores) / len(scores)

    return {
        "total_sites": total_sites,
        "total_projects": total_projects,
        "average_suitability_score": round(avg_suitability, 1),
        "solar_sites_count": solar_sites_count,
        "wind_sites_count": wind_sites_count,
        "hybrid_sites_count": hybrid_sites_count,
        "region_default": "Gujarat/Rajasthan (India)",
        "is_synthetic_mode": True # Clearly label synthetic predictions
    }

# ----------------- Notification Endpoints -----------------

@api_router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter(Notification.user_id == current_user.user_id).order_by(Notification.created_at.desc()).all()

@api_router.put("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(
        Notification.notification_id == notification_id,
        Notification.user_id == current_user.user_id
    ).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif

# ----------------- Reports Endpoints -----------------

@api_router.get("/reports", response_model=List[ReportResponse])
def get_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Report).all()

@api_router.post("/reports", response_model=ReportResponse)
def generate_report(report_in: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Simulates generation of static report file
    report_id = uuid.uuid4()
    new_report = Report(
        report_id=report_id,
        project_id=uuid.UUID("India Western Corridor Plan"), # Placeholder / demo project linkage
        report_type="Site Suitability Matrix",
        generated_by=current_user.user_id,
        report_url=f"/api/reports/download/{report_id}"
    )
    # We will look up a real project id if valid UUID passed
    try:
        proj = db.query(Project).first()
        if proj:
            new_report.project_id = proj.project_id
    except Exception:
        pass
        
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report

app.include_router(api_router)

@app.get("/")
def read_root():
    return {"message": "Solar & Wind Deployment Intelligence Platform API Running"}

import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, sync_engine, SyncSessionLocal
from app.core.security import get_password_hash
from app.models.sql_models import (
    Role, User, Region, Project, Site, EnvironmentalData,
    SolarPrediction, WindPrediction, SuitabilityScore,
    InvestmentAnalysis, Notification, DataSource
)
from app.gis.spatial_engine import spatial_engine, generate_site_boundary_polygon
from app.services.suitability_engine import suitability_engine
from app.ml.solar_engine import solar_ml_engine
from app.ml.wind_engine import wind_ml_engine
from app.services.investment_engine import investment_engine
from app.core.logging import logger


def seed_all():
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=sync_engine)

    session = SyncSessionLocal()
    try:
        # 1. Seed Roles
        logger.info("Seeding roles...")
        roles_data = [
            ("Renewable Energy Planner", "View recommended sites, compare sites, view forecasts, and view investment recommendations.",
             ["view_recommendations", "compare_sites", "view_forecasts", "view_investment"]),
            ("GIS Analyst", "GIS maps, environmental analytics, terrain analysis, and spatial site comparison.",
             ["view_gis_maps", "analyze_environment", "terrain_analysis", "compare_sites"]),
            ("Project Manager", "Manage projects, view feasibility, cost-benefit analysis, and deployment timelines.",
             ["manage_projects", "view_feasibility", "cost_benefit", "manage_sites"]),
            ("Administrator", "User management, dataset management, system monitoring, and platform analytics.",
             ["manage_users", "manage_datasets", "monitor_system", "manage_all"])
        ]
        roles = {}
        for name, desc, perms in roles_data:
            existing = session.query(Role).filter(Role.name == name).first()
            if not existing:
                role = Role(name=name, description=desc, permissions=perms)
                session.add(role)
                session.commit()
                session.refresh(role)
                roles[name] = role
            else:
                roles[name] = existing

        # 2. Seed Users
        logger.info("Seeding demo users...")
        users_data = [
            ("planner@example.com", "Planner123!", "Elena Rostova (Planner)", roles["Renewable Energy Planner"].id),
            ("analyst@example.com", "Analyst123!", "Marcus Chen (GIS Analyst)", roles["GIS Analyst"].id),
            ("manager@example.com", "Manager123!", "Sarah Jenkins (Project Manager)", roles["Project Manager"].id),
            ("admin@example.com", "Admin123!", "Administrator Root", roles["Administrator"].id)
        ]
        created_users = {}
        for email, pwd, name, r_id in users_data:
            existing = session.query(User).filter(User.email == email).first()
            if not existing:
                u = User(
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    full_name=name,
                    role_id=r_id,
                    is_active=True
                )
                session.add(u)
                session.commit()
                session.refresh(u)
                created_users[email] = u
            else:
                created_users[email] = existing

        # 3. Seed Data Sources
        logger.info("Seeding data sources...")
        sources_data = [
            ("NASA POWER Climatology", "nasa_power", "Solar Irradiance & Meteorology", "Global / North America", "Operational (99.9%)", "Satellite GHI/DNI and surface temperature API"),
            ("Global Wind Atlas v3", "global_wind_atlas", "High-Resolution Wind Regimes", "Global Onshore & Offshore", "Operational (99.7%)", "Microscale wind power density at 100m"),
            ("NASA SRTM Elevation", "nasa_srtm", "Topography & Digital Elevation Models", "Global (60N to 60S)", "Operational (100%)", "30-meter elevation and terrain slope grids"),
            ("OpenStreetMap Overpass", "osm_infrastructure", "Roads, Transmission & Substation Grid", "North America & International", "Operational (99.8%)", "Vector infrastructure connectivity lines"),
            ("Copernicus Sentinel-2", "copernicus_sentinel", "Multispectral Land Cover & NDVI", "Global", "Operational (99.5%)", "Vegetation index and protected habitat boundaries")
        ]
        for name, key, dtype, cov, qual, notes in sources_data:
            existing = session.query(DataSource).filter(DataSource.source_key == key).first()
            if not existing:
                ds = DataSource(
                    name=name, source_key=key, dataset_type=dtype, coverage=cov,
                    data_quality_status=qual, status="active", notes=notes
                )
                session.add(ds)
        session.commit()

        # 4. Seed Regions
        logger.info("Seeding geographic regions...")
        regions_data = [
            ("Mojave Desert Energy Zone", "United States", "California / Nevada", 35.15, -115.50, 6.2, 5.8, 320.0),
            ("Great Plains Wind Corridor", "United States", "Texas / Oklahoma", 35.20, -101.80, 4.9, 8.6, 420.0),
            ("Columbia Basin Clean Corridor", "United States", "Oregon / Washington", 45.70, -120.80, 4.2, 7.8, 180.0),
            ("Texas Gulf Coast Hybrid Basin", "United States", "Texas", 27.80, -97.40, 5.3, 7.5, 410.0),
            ("Appalachian Highlands Basin", "United States", "West Virginia / Virginia", 38.80, -79.60, 4.1, 7.2, 460.0)
        ]
        created_regions = {}
        for name, country, prov, lat, lon, ghi, wind, carbon in regions_data:
            existing = session.query(Region).filter(Region.name == name).first()
            if not existing:
                r = Region(
                    name=name, country=country, state_province=prov,
                    center_latitude=lat, center_longitude=lon,
                    avg_solar_ghi=ghi, avg_wind_speed=wind,
                    grid_carbon_intensity=carbon
                )
                session.add(r)
                session.commit()
                session.refresh(r)
                created_regions[name] = r
            else:
                created_regions[name] = existing

        # 5. Seed Projects
        logger.info("Seeding renewable projects...")
        projects_data = [
            ("Desert Sun Utility PV Project", "Utility-scale 100 MW bifacial solar array with single-axis tracking in Mojave Basin.", "solar", 100.0, 85000000.0, "active", created_regions["Mojave Desert Energy Zone"].id),
            ("Panhandle High Wind Phase 1", "150 MW high-capacity wind farm tapping the Panhandle ERCOT transmission highway.", "wind", 150.0, 195000000.0, "active", created_regions["Great Plains Wind Corridor"].id),
            ("Gulf Coast Hybrid Microgrid", "80 MW hybrid solar-wind deployment leveraging coastal sea breeze and summer solar irradiance.", "hybrid", 80.0, 92000000.0, "under_review", created_regions["Texas Gulf Coast Hybrid Basin"].id),
            ("Columbia Gorge Clean Energy Hub", "60 MW wind-solar pairing adjacent to BPA hydro interties.", "hybrid", 60.0, 72000000.0, "approved", created_regions["Columbia Basin Clean Corridor"].id)
        ]
        created_projects = {}
        for name, desc, tech, cap, budget, stat, reg_id in projects_data:
            existing = session.query(Project).filter(Project.name == name).first()
            if not existing:
                p = Project(
                    name=name, description=desc, technology=tech,
                    target_capacity_mw=cap, budget_usd=budget, status=stat,
                    region_id=reg_id, owner_id=created_users["manager@example.com"].id
                )
                session.add(p)
                session.commit()
                session.refresh(p)
                created_projects[name] = p
            else:
                created_projects[name] = existing

        # 6. Seed Detailed Candidate Sites
        logger.info("Seeding detailed candidate sites...")
        sites_seed = [
            # Site 1: Excellent Solar Site (Mojave)
            {
                "name": "Ivanpah Sun Vista Alpha",
                "project": created_projects["Desert Sun Utility PV Project"],
                "region": created_regions["Mojave Desert Energy Zone"],
                "lat": 35.52, "lon": -115.42, "area": 8.5, "elev": 780.0, "slope": 1.4,
                "land_ownership": "Federal BLM Leased", "status": "Selected",
                "env": {"ghi": 6.35, "dni": 7.45, "wind": 5.4, "temp": 25.2, "rain": 140.0, "cloud": 12.0, "ndvi": 0.11, "prot_dist": 14.5, "water_dist": 18.0}
            },
            # Site 2: High Suitability Solar Site (Mojave)
            {
                "name": "Eldorado Valley Solaria",
                "project": created_projects["Desert Sun Utility PV Project"],
                "region": created_regions["Mojave Desert Energy Zone"],
                "lat": 35.80, "lon": -115.05, "area": 6.2, "elev": 620.0, "slope": 2.2,
                "land_ownership": "Public Utility Corridor", "status": "Shortlisted",
                "env": {"ghi": 6.18, "dni": 7.10, "wind": 5.8, "temp": 26.0, "rain": 160.0, "cloud": 15.0, "ndvi": 0.12, "prot_dist": 16.0, "water_dist": 12.0}
            },
            # Site 3: Excellent Wind Site (Great Plains)
            {
                "name": "Caprock Escarpment Wind Mesa",
                "project": created_projects["Panhandle High Wind Phase 1"],
                "region": created_regions["Great Plains Wind Corridor"],
                "lat": 34.88, "lon": -101.45, "area": 14.0, "elev": 960.0, "slope": 2.8,
                "land_ownership": "Private Long-Term Lease", "status": "Selected",
                "env": {"ghi": 5.15, "dni": 5.80, "wind": 9.1, "temp": 17.5, "rain": 440.0, "cloud": 28.0, "ndvi": 0.32, "prot_dist": 22.0, "water_dist": 8.5}
            },
            # Site 4: Highly Suitable Wind Site (Great Plains)
            {
                "name": "Amarillo North Prairie Ridge",
                "project": created_projects["Panhandle High Wind Phase 1"],
                "region": created_regions["Great Plains Wind Corridor"],
                "lat": 35.40, "lon": -101.85, "area": 12.5, "elev": 1080.0, "slope": 1.9,
                "land_ownership": "Private Agricultural Lease", "status": "Shortlisted",
                "env": {"ghi": 5.02, "dni": 5.60, "wind": 8.5, "temp": 16.8, "rain": 480.0, "cloud": 32.0, "ndvi": 0.34, "prot_dist": 28.0, "water_dist": 11.0}
            },
            # Site 5: Excellent Hybrid Site (Gulf Coast)
            {
                "name": "Corpus Christi Coastal Hybrid Point",
                "project": created_projects["Gulf Coast Hybrid Microgrid"],
                "region": created_regions["Texas Gulf Coast Hybrid Basin"],
                "lat": 27.65, "lon": -97.55, "area": 7.8, "elev": 18.0, "slope": 0.8,
                "land_ownership": "Industrial Port Authority", "status": "Candidate",
                "env": {"ghi": 5.48, "dni": 5.95, "wind": 7.9, "temp": 24.2, "rain": 780.0, "cloud": 30.0, "ndvi": 0.48, "prot_dist": 18.5, "water_dist": 4.5}
            },
            # Site 6: Moderately Suitable Hybrid Site (Columbia Basin)
            {
                "name": "Wasco County Plateau Intertie",
                "project": created_projects["Columbia Gorge Clean Energy Hub"],
                "region": created_regions["Columbia Basin Clean Corridor"],
                "lat": 45.45, "lon": -120.75, "area": 6.5, "elev": 480.0, "slope": 4.5,
                "land_ownership": "Private Rangeland", "status": "Candidate",
                "env": {"ghi": 4.45, "dni": 4.90, "wind": 7.7, "temp": 14.5, "rain": 360.0, "cloud": 42.0, "ndvi": 0.28, "prot_dist": 12.0, "water_dist": 7.2}
            },
            # Site 7: Low Suitability Site (Steep Slope / High Protected Proximity)
            {
                "name": "San Gabriel Mountain Ridge Candidate",
                "project": created_projects["Desert Sun Utility PV Project"],
                "region": created_regions["Mojave Desert Energy Zone"],
                "lat": 34.32, "lon": -117.65, "area": 3.5, "elev": 1850.0, "slope": 16.8,
                "land_ownership": "Protected Forest Edge", "status": "Rejected",
                "env": {"ghi": 5.60, "dni": 6.20, "wind": 6.1, "temp": 12.0, "rain": 620.0, "cloud": 35.0, "ndvi": 0.55, "prot_dist": 2.2, "water_dist": 6.0}
            },
            # Site 8: Unsuitable Site (Wildlife Corridor & Floodplain)
            {
                "name": "Brazos River Floodplain Reserve",
                "project": created_projects["Gulf Coast Hybrid Microgrid"],
                "region": created_regions["Texas Gulf Coast Hybrid Basin"],
                "lat": 28.95, "lon": -95.60, "area": 4.2, "elev": 8.0, "slope": 0.5,
                "land_ownership": "Wetland Conservation Easement", "status": "Rejected",
                "env": {"ghi": 4.60, "dni": 4.90, "wind": 5.2, "temp": 23.5, "rain": 1250.0, "cloud": 48.0, "ndvi": 0.85, "prot_dist": 0.5, "water_dist": 0.4}
            }
        ]

        for s_data in sites_seed:
            existing = session.query(Site).filter(Site.name == s_data["name"]).first()
            if existing:
                continue

            dist = spatial_engine.compute_distances(s_data["lat"], s_data["lon"])
            boundary = generate_site_boundary_polygon(s_data["lat"], s_data["lon"], s_data["area"])

            site = Site(
                name=s_data["name"],
                latitude=s_data["lat"],
                longitude=s_data["lon"],
                project_id=s_data["project"].id,
                region_id=s_data["region"].id,
                land_area_sqkm=s_data["area"],
                elevation_m=s_data["elev"],
                slope_deg=s_data["slope"],
                distance_to_grid_km=dist["distance_to_grid_km"],
                distance_to_road_km=dist["distance_to_road_km"],
                distance_to_substation_km=dist["distance_to_substation_km"],
                land_ownership=s_data["land_ownership"],
                status=s_data["status"],
                boundary_geojson=boundary
            )
            session.add(site)
            session.commit()
            session.refresh(site)

            # Environmental Data
            e = s_data["env"]
            env = EnvironmentalData(
                site_id=site.id,
                ghi_kwh_m2_day=e["ghi"],
                dni_kwh_m2_day=e["dni"],
                wind_speed_100m=e["wind"],
                wind_direction_deg=225.0,
                temperature_c=e["temp"],
                rainfall_mm=e["rain"],
                cloud_cover_pct=e["cloud"],
                elevation_m=s_data["elev"],
                slope_deg=s_data["slope"],
                ndvi=e["ndvi"],
                protected_zone_distance_km=e["prot_dist"],
                water_body_distance_km=e["water_dist"],
                is_demo_data=True,
                data_source="NASA POWER / Global Wind Atlas DEMO"
            )
            session.add(env)

            # Solar ML prediction
            solar_pred = solar_ml_engine.predict({
                "latitude": site.latitude, "longitude": site.longitude,
                "elevation_m": site.elevation_m, "slope_deg": site.slope_deg,
                "cloud_cover_pct": env.cloud_cover_pct, "temperature_c": env.temperature_c,
                "rainfall_mm": env.rainfall_mm, "ndvi": env.ndvi,
                "ghi_kwh_m2_day": env.ghi_kwh_m2_day
            }, plant_capacity_mw=s_data["project"].target_capacity_mw)

            solar_rec = SolarPrediction(
                site_id=site.id,
                annual_irradiance_kwh=solar_pred["annual_irradiance_kwh"],
                peak_sun_hours=solar_pred["peak_sun_hours"],
                expected_mwh_year=solar_pred["expected_mwh_year"],
                capacity_factor=solar_pred["capacity_factor"],
                performance_ratio=solar_pred["performance_ratio"],
                solar_suitability_score=solar_pred["solar_suitability_score"],
                model_name=solar_pred["model_name"],
                model_metrics=solar_pred["model_metrics"]
            )
            session.add(solar_rec)

            # Wind ML prediction
            wind_pred = wind_ml_engine.predict({
                "latitude": site.latitude, "longitude": site.longitude,
                "elevation_m": site.elevation_m, "slope_deg": site.slope_deg,
                "temperature_c": env.temperature_c,
                "wind_speed_100m": env.wind_speed_100m
            }, plant_capacity_mw=s_data["project"].target_capacity_mw)

            wind_rec = WindPrediction(
                site_id=site.id,
                avg_wind_speed=wind_pred["avg_wind_speed"],
                wind_power_density=wind_pred["wind_power_density"],
                turbulence_intensity=wind_pred["turbulence_intensity"],
                capacity_factor=wind_pred["capacity_factor"],
                expected_mwh_year=wind_pred["expected_mwh_year"],
                model_name=wind_pred["model_name"],
                model_metrics=wind_pred["model_metrics"]
            )
            session.add(wind_rec)

            # Multi-factor Suitability Score
            suit_res = suitability_engine.calculate_scores(
                environmental_data={
                    "ghi_kwh_m2_day": env.ghi_kwh_m2_day,
                    "wind_speed_100m": env.wind_speed_100m,
                    "protected_zone_distance_km": env.protected_zone_distance_km,
                    "water_body_distance_km": env.water_body_distance_km
                },
                site_data={
                    "slope_deg": site.slope_deg,
                    "elevation_m": site.elevation_m,
                    "distance_to_grid_km": site.distance_to_grid_km,
                    "distance_to_road_km": site.distance_to_road_km,
                    "distance_to_substation_km": site.distance_to_substation_km,
                    "land_ownership": site.land_ownership
                }
            )
            suit_rec = SuitabilityScore(
                site_id=site.id,
                resource_score=suit_res["resource_score"],
                geographic_score=suit_res["geographic_score"],
                infrastructure_score=suit_res["infrastructure_score"],
                environmental_score=suit_res["environmental_score"],
                economic_score=suit_res["economic_score"],
                overall_score=suit_res["overall_score"],
                category=suit_res["category"],
                breakdown_details=suit_res["breakdown_details"]
            )
            session.add(suit_rec)

            # Investment Analytics
            inv_res = investment_engine.calculate_investment(
                site_name=site.name,
                technology=s_data["project"].technology,
                capacity_mw=s_data["project"].target_capacity_mw,
                annual_expected_mwh=wind_pred["expected_mwh_year"] if "wind" in s_data["project"].technology.lower() else solar_pred["expected_mwh_year"],
                distance_to_grid_km=site.distance_to_grid_km
            )
            inv_rec = InvestmentAnalysis(
                site_id=site.id,
                capex_usd=inv_res["capex_usd"],
                opex_per_year_usd=inv_res["opex_per_year_usd"],
                annual_revenue_usd=inv_res["annual_revenue_usd"],
                lcoe_per_mwh=inv_res["lcoe_per_mwh"],
                npv_usd=inv_res["npv_usd"],
                irr_pct=inv_res["irr_pct"],
                payback_years=inv_res["payback_years"],
                feasibility_score=inv_res["feasibility_score"],
                investment_score=inv_res["investment_score"],
                recommendation=inv_res["recommendation"],
                assumptions=inv_res["assumptions"]
            )
            session.add(inv_rec)

        session.commit()

        # 7. Seed Notifications
        logger.info("Seeding initial notifications...")
        sample_notifications = [
            ("Weather Alert: High Wind Shear Event", "An unexpected wind shear anomaly was recorded in the Great Plains Corridor. Sensor calibration updated.", "high", "weather", 3, None),
            ("Site Suitability Assessment Complete", "Ivanpah Sun Vista Alpha scored 92.4 (Excellent). Interconnection queue study recommended.", "medium", "suitability", 1, 1),
            ("New Environmental Protection Boundary", "Updated buffer around Coastal Avian Sanctuary in Texas Gulf Coast Basin. Site Brazos River re-classified.", "critical", "environmental", 8, 3),
            ("Q3 Financial Forecast Ready", "Updated forward generation estimates using revised electricity tariffs ($0.075/kWh).", "low", "forecast", 1, 1),
            ("Project Milestone: Approvals Submitted", "Desert Sun Utility PV Project permits submitted to California ISO.", "medium", "project", None, 1)
        ]
        for title, msg, prio, cat, s_id, p_id in sample_notifications:
            n = Notification(
                user_id=created_users["planner@example.com"].id,
                title=title, message=msg, priority=prio, category=cat,
                site_id=s_id, project_id=p_id, is_read=False
            )
            session.add(n)
        session.commit()

        logger.info("Database seeding completed successfully!")
    finally:
        session.close()


if __name__ == "__main__":
    seed_all()

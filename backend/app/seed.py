"""
Database seeder — run once after first docker compose up --build

Usage:
    docker exec solar-wind-deployment-platform-backend-1 python app/seed.py
"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.project import Project, Region
from app.models.site import Site, EnergyType, LandOwnership, SiteStatus
from app.models.environmental import EnvironmentalData
from app.core.security import hash_password
from app.services.environmental import collect_environmental_data

Base.metadata.create_all(bind=engine)

def add(obj):
    db = SessionLocal()
    try:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    finally:
        db.close()

def seed():
    # Skip if already seeded
    db = SessionLocal()
    exists = db.query(User).filter(User.email == "admin@solarwind.com").first()
    db.close()
    if exists:
        print("Database already seeded. Skipping.")
        return

    print("Seeding database...")

    # --- Users ---
    admin   = add(User(full_name="Administrator",   email="admin@solarwind.com",   hashed_password=hash_password("admin123"),   role=UserRole.administrator,   is_active=True))
    planner = add(User(full_name="Energy Planner",  email="planner@solarwind.com", hashed_password=hash_password("planner123"), role=UserRole.energy_planner,  is_active=True))
    add(User(full_name="GIS Analyst",     email="gis@solarwind.com",     hashed_password=hash_password("gis12345"),   role=UserRole.gis_analyst,     is_active=True))
    add(User(full_name="Project Manager", email="manager@solarwind.com", hashed_password=hash_password("manager123"), role=UserRole.project_manager, is_active=True))
    print("  ✓ 4 users created")

    # --- Region ---
    region = add(Region(name="Tamil Nadu", country="India", state="Tamil Nadu", description="Southern India renewable energy zone"))
    print("  ✓ 1 region created")

    # --- Projects ---
    project1 = add(Project(name="Tamil Nadu Solar Farm",         description="Large scale solar deployment across Tamil Nadu plains",                        region_id=region.id, created_by=planner.id))
    project2 = add(Project(name="Coastal Wind Energy Project",   description="Offshore and coastal wind turbine deployment along Tamil Nadu coastline",      region_id=region.id, created_by=planner.id))
    print("  ✓ 2 projects created")

    # --- Sites ---
    site_data = [
        dict(name="Ramanathapuram Solar Site", project_id=project1.id, latitude=9.3639,  longitude=78.8395, elevation=12.0,  land_area=250.0, energy_type=EnergyType.solar,  land_ownership=LandOwnership.government),
        dict(name="Tirunelveli Solar Site",    project_id=project1.id, latitude=8.7139,  longitude=77.7567, elevation=45.0,  land_area=180.0, energy_type=EnergyType.solar,  land_ownership=LandOwnership.private),
        dict(name="Madurai Hybrid Site",       project_id=project1.id, latitude=9.9252,  longitude=78.1198, elevation=101.0, land_area=320.0, energy_type=EnergyType.hybrid, land_ownership=LandOwnership.government),
        dict(name="Kanyakumari Wind Site",     project_id=project2.id, latitude=8.0883,  longitude=77.5385, elevation=8.0,   land_area=400.0, energy_type=EnergyType.wind,   land_ownership=LandOwnership.government),
        dict(name="Tuticorin Offshore Wind",   project_id=project2.id, latitude=8.7642,  longitude=78.1348, elevation=3.0,   land_area=600.0, energy_type=EnergyType.wind,   land_ownership=LandOwnership.government),
        dict(name="Nagapattinam Coastal Wind", project_id=project2.id, latitude=10.7672, longitude=79.8449, elevation=5.0,   land_area=350.0, energy_type=EnergyType.wind,   land_ownership=LandOwnership.private),
    ]
    sites = [add(Site(**s, status=SiteStatus.under_review, created_by=planner.id)) for s in site_data]
    print(f"  ✓ {len(sites)} sites created")

    # --- Environmental Data ---
    print("  Fetching environmental data for all sites (this takes ~30 seconds)...")
    fetched = 0
    for site in sites:
        try:
            records = asyncio.run(collect_environmental_data(site.latitude, site.longitude, 30))
            db = SessionLocal()
            for r in records:
                db.add(EnvironmentalData(site_id=site.id, **r))
            db.commit()
            db.close()
            fetched += 1
            print(f"    ✓ {site.name} — {len(records)} days")
        except Exception as e:
            print(f"    ✗ {site.name} — failed: {e}")
    print(f"  ✓ Environmental data fetched for {fetched}/{len(sites)} sites")

    print("\nSeeding complete.")
    print("\nDefault accounts:")
    print("  admin@solarwind.com    / admin123   (administrator)")
    print("  planner@solarwind.com  / planner123 (energy_planner)")
    print("  gis@solarwind.com      / gis12345   (gis_analyst)")
    print("  manager@solarwind.com  / manager123 (project_manager)")

if __name__ == "__main__":
    seed()

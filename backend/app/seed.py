"""
Database seeder — run once after first docker compose up --build

Usage:
    docker exec -i solar-wind-deployment-platform-backend-1 python app/seed.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.project import Project, Region
from app.models.site import Site, EnergyType, LandOwnership
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

def seed():
    # Skip if already seeded
    if db.query(User).filter(User.email == "admin@solarwind.com").first():
        print("Database already seeded. Skipping.")
        return

    print("Seeding database...")

    # --- Users ---
    users = [
        User(full_name="Administrator",   email="admin@solarwind.com",   hashed_password=hash_password("admin123"),   role=UserRole.administrator,   is_active=True),
        User(full_name="Energy Planner",  email="planner@solarwind.com", hashed_password=hash_password("planner123"), role=UserRole.energy_planner,  is_active=True),
        User(full_name="GIS Analyst",     email="gis@solarwind.com",     hashed_password=hash_password("gis12345"),   role=UserRole.gis_analyst,     is_active=True),
        User(full_name="Project Manager", email="manager@solarwind.com", hashed_password=hash_password("manager123"), role=UserRole.project_manager, is_active=True),
    ]
    for u in users:
        db.add(u)
    db.commit()
    print(f"  ✓ {len(users)} users created")

    admin = db.query(User).filter(User.email == "admin@solarwind.com").first()
    planner = db.query(User).filter(User.email == "planner@solarwind.com").first()

    # --- Region ---
    region = Region(name="Tamil Nadu", country="India", state="Tamil Nadu", description="Southern India renewable energy zone")
    db.add(region)
    db.commit()
    print("  ✓ 1 region created")

    # --- Projects ---
    project1 = Project(name="Tamil Nadu Solar Farm", description="Large scale solar deployment across Tamil Nadu plains", region_id=region.id, created_by=planner.id)
    project2 = Project(name="Coastal Wind Energy Project", description="Offshore and coastal wind turbine deployment along Tamil Nadu coastline", region_id=region.id, created_by=planner.id)
    db.add(project1)
    db.add(project2)
    db.commit()
    print("  ✓ 2 projects created")

    # --- Sites ---
    sites = [
        Site(name="Ramanathapuram Solar Site", project_id=project1.id, latitude=9.3639,  longitude=78.8395, elevation=12.0,  land_area=250.0, energy_type=EnergyType.solar,  land_ownership=LandOwnership.government, created_by=planner.id),
        Site(name="Tirunelveli Solar Site",    project_id=project1.id, latitude=8.7139,  longitude=77.7567, elevation=45.0,  land_area=180.0, energy_type=EnergyType.solar,  land_ownership=LandOwnership.private,    created_by=planner.id),
        Site(name="Madurai Hybrid Site",       project_id=project1.id, latitude=9.9252,  longitude=78.1198, elevation=101.0, land_area=320.0, energy_type=EnergyType.hybrid, land_ownership=LandOwnership.government, created_by=planner.id),
        Site(name="Kanyakumari Wind Site",     project_id=project2.id, latitude=8.0883,  longitude=77.5385, elevation=8.0,   land_area=400.0, energy_type=EnergyType.wind,   land_ownership=LandOwnership.government, created_by=planner.id),
        Site(name="Tuticorin Offshore Wind",   project_id=project2.id, latitude=8.7642,  longitude=78.1348, elevation=3.0,   land_area=600.0, energy_type=EnergyType.wind,   land_ownership=LandOwnership.government, created_by=planner.id),
        Site(name="Nagapattinam Coastal Wind", project_id=project2.id, latitude=10.7672, longitude=79.8449, elevation=5.0,   land_area=350.0, energy_type=EnergyType.wind,   land_ownership=LandOwnership.private,    created_by=planner.id),
    ]
    for s in sites:
        db.add(s)
    db.commit()
    print(f"  ✓ {len(sites)} sites created")

    print("\nSeeding complete.")
    print("\nDefault accounts:")
    print("  admin@solarwind.com    / admin123   (administrator)")
    print("  planner@solarwind.com  / planner123 (energy_planner)")
    print("  gis@solarwind.com      / gis12345   (gis_analyst)")
    print("  manager@solarwind.com  / manager123 (project_manager)")

if __name__ == "__main__":
    try:
        seed()
    finally:
        db.close()

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.database.session import engine

def main():
    print("=" * 60)
    print("DATABASE INSPECTION UTILITY")
    print("=" * 60)

    try:
        # 1. Connect and inspect database tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n[INFO] Connected database: {engine.url}")
        print(f"[INFO] Constructed tables found: {tables}")
        
        if "users" not in tables:
            print("\n[ERROR] The 'users' table has not been created yet.")
            return

        # 2. Inspect 'users' table columns
        print("\nColumns in 'users' table:")
        print("-" * 60)
        columns = inspector.get_columns("users")
        for col in columns:
            print(f" - {col['name']:<20} {str(col['type']):<15} Nullable: {col['nullable']}")
        
        # 3. Retrieve and display data rows
        Session = sessionmaker(bind=engine)
        session = Session()
        
        users = session.query(User).all()
        
        print(f"\n[INFO] Total registered users: {len(users)}")
        print("\nRegistered Users Records:")
        print("-" * 80)
        print(f"{'UUID (ID)':<38} | {'Full Name':<20} | {'Email':<25}")
        print("-" * 80)
        
        for user in users:
            print(f"{str(user.id):<38} | {user.full_name:<20} | {user.email:<25}")
        print("-" * 80)

        # 4. Retrieve and display assessed sites
        if "sites" in tables:
            from app.models.site import Site
            sites = session.query(Site).all()
            print(f"\n[INFO] Total assessed sites: {len(sites)}")
            print("\nAssessed Sites Records:")
            print("-" * 120)
            print(f"{'Site Name':<25} | {'Coordinates (Lat, Lon)':<25} | {'Region':<15} | {'Score':<8} | {'Suitability':<12}")
            print("-" * 120)
            for s in sites:
                coords = f"{s.latitude:.4f}, {s.longitude:.4f}"
                score_str = f"{s.overall_score}%"
                print(f"{s.name:<25} | {coords:<25} | {s.region:<15} | {score_str:<8} | {s.suitability_class:<12}")
            print("-" * 120)

        session.close()
        
    except Exception as e:
        print(f"\n[ERROR] Failed to query database: {e}")

if __name__ == "__main__":
    main()

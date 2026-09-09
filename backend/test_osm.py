import sys
import os
import time

sys.path.append(r"c:\Users\sanje\Downloads\PROJECTS\AI_Solar_And_Wind\backend")
from app.osm import fetch_osm_infrastructure, load_osm_cache

def test_osm():
    lat = 26.9
    lon = 70.9

    # Clear cache for this key for fresh test
    cache_key = f"{round(lat, 2)}_{round(lon, 2)}"
    cache_path = r"c:\Users\sanje\Downloads\PROJECTS\AI_Solar_And_Wind\backend\app\data\osm_cache.json"
    if os.path.exists(cache_path):
        import json
        with open(cache_path, "r") as f:
            data = json.load(f)
        if cache_key in data:
            del data[cache_key]
            with open(cache_path, "w") as f:
                json.dump(data, f)
    
    print("--- 1. Testing First Call (Cache Miss) ---")
    start = time.time()
    res1 = fetch_osm_infrastructure(lat, lon)
    print(f"Time taken: {time.time() - start:.2f}s")
    print(f"Result: {res1}")

    print("\n--- 2. Testing Second Call (Cache Hit) ---")
    start = time.time()
    res2 = fetch_osm_infrastructure(lat, lon)
    print(f"Time taken: {time.time() - start:.2f}s")
    print(f"Result: {res2}")

if __name__ == '__main__':
    test_osm()

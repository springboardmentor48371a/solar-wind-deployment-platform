"""
Dataset Generator & CSV Schema Exporter (Section 24).

Generates a structured dataset CSV file (`dataset.csv`) containing normalized
site and environmental parameters for demonstration, offline testing, and ML training.
"""
import os
import pandas as pd
from app.services.environmental_provider import DatasetEnvironmentalProvider


def generate_dataset_csv(output_path: str = None, num_samples: int = 50) -> str:
    if output_path is None:
        base_dir = os.path.dirname(__file__)
        output_path = os.path.join(base_dir, "dataset.csv")

    provider = DatasetEnvironmentalProvider()
    rows = []

    # Regions around major India renewable hubs (Delhi, Rajasthan, Gujarat, Tamil Nadu, etc.)
    base_coords = [
        (28.6139, 77.2090),  # Delhi
        (26.9124, 75.7873),  # Jaipur / Rajasthan
        (23.2156, 72.6369),  # Gandhinagar / Gujarat
        (13.0827, 80.2707),  # Chennai / Tamil Nadu
        (15.3173, 75.7139),  # Karnataka
    ]

    count = 1
    for lat_base, lon_base in base_coords:
        for i in range(num_samples // len(base_coords)):
            lat = lat_base + (i * 0.05) - 0.2
            lon = lon_base + (i * 0.05) - 0.2
            env = provider.get_environmental_data(lat, lon, site_id=count)
            row = {
                "site_id": count,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "land_area_hectares": round(5.0 + (i % 10) * 2.5, 1),
                "elevation_m": round(200.0 + (i * 15.0), 1),
                "land_slope_deg": env["land_slope_pct"],
                "irradiance": env["solar_irradiance_kwh_m2_day"],
                "wind_speed": env["wind_speed_avg_ms"],
                "wind_direction": env["wind_direction_deg"],
                "temperature": env["temperature_avg_c"],
                "rainfall": env["rainfall_mm_year"],
                "cloud_cover": env["cloud_cover_pct"],
                "vegetation_index": env["vegetation_index_ndvi"],
                "distance_to_road_km": env["distance_to_road_km"],
                "distance_to_substation_km": env["distance_to_substation_km"],
                "distance_to_transmission_km": env["distance_to_transmission_km"],
                "distance_to_water_km": env["distance_to_water_km"],
                "protected_zone": env["in_protected_zone"],
                "land_ownership": "Government / Leasehold" if i % 2 == 0 else "Private / Agricultural",
                "existing_infrastructure": "Substation nearby" if env["distance_to_substation_km"] < 5 else "Unimproved",
            }
            rows.append(row)
            count += 1

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    path = generate_dataset_csv()
    print(f"Generated dataset CSV at {path}")

import math
from schemas import Coordinates

def clamp(v, low, high):
    return max(low, min(high, v))

def environmental_analysis(c: Coordinates):
    lat_factor = math.cos(math.radians(c.latitude))
    solar_irradiance = round(4.2 + 2.1 * abs(lat_factor), 2)
    avg_temp = round(18 + 12 * math.cos(math.radians(c.latitude)), 1)
    cloud_cover = round(clamp(45 - abs(c.latitude) * 0.35 + (abs(c.longitude) % 17), 8, 85), 1)
    rainfall = round(clamp(900 + 350 * math.sin(math.radians(c.longitude)), 150, 1800), 1)
    wind_speed = round(clamp(4.0 + abs(math.sin(math.radians(c.longitude))) * 5 + c.elevation / 5000, 2, 14), 2)
    wind_direction = round((c.longitude * 3 + c.latitude * 2) % 360, 1)
    slope = round(clamp(abs(math.sin(math.radians(c.latitude * 4))) * 18, 1, 25), 1)
    vegetation_index = round(clamp(0.25 + abs(math.sin(math.radians(c.longitude))) * 0.55, 0.1, 0.9), 2)
    return {
        "solar_irradiance_kwh_m2_day": solar_irradiance,
        "temperature_c": avg_temp,
        "cloud_cover_percent": cloud_cover,
        "rainfall_mm_year": rainfall,
        "wind_speed_m_s": wind_speed,
        "wind_direction_deg": wind_direction,
        "elevation_m": c.elevation,
        "land_slope_deg": slope,
        "vegetation_index": vegetation_index
    }

def solar_prediction(c: Coordinates):
    env = environmental_analysis(c)
    irradiance = env["solar_irradiance_kwh_m2_day"]
    cloud_factor = 1 - env["cloud_cover_percent"] / 250
    peak_sun_hours = round(irradiance * cloud_factor, 2)
    capacity_mw = max(c.land_area * 0.5, 0.1)
    capacity_factor = round(clamp(peak_sun_hours / 24, 0.08, 0.32), 3)
    annual_energy_mwh = round(capacity_mw * 8760 * capacity_factor, 2)
    performance_ratio = round(clamp(0.82 - env["cloud_cover_percent"] / 1000, 0.65, 0.9), 2)
    return {
        "annual_irradiance_kwh_m2": round(irradiance * 365, 1),
        "peak_sun_hours": peak_sun_hours,
        "suggested_capacity_mw": round(capacity_mw, 2),
        "capacity_factor": capacity_factor,
        "performance_ratio": performance_ratio,
        "expected_annual_energy_mwh": annual_energy_mwh
    }

def wind_prediction(c: Coordinates):
    env = environmental_analysis(c)
    v = env["wind_speed_m_s"]
    air_density = 1.225
    power_density = round(0.5 * air_density * (v ** 3), 2)
    capacity_mw = max(c.land_area * 0.25, 0.1)
    capacity_factor = round(clamp((v / 12) ** 2 * 0.42, 0.08, 0.55), 3)
    annual_energy_mwh = round(capacity_mw * 8760 * capacity_factor, 2)
    turbulence = round(clamp(0.08 + abs(math.sin(math.radians(c.latitude))) * 0.18, 0.05, 0.35), 3)
    return {
        "average_wind_speed_m_s": v,
        "wind_direction_deg": env["wind_direction_deg"],
        "wind_power_density_w_m2": power_density,
        "turbulence_intensity": turbulence,
        "suggested_capacity_mw": round(capacity_mw, 2),
        "capacity_factor": capacity_factor,
        "expected_annual_energy_mwh": annual_energy_mwh
    }

def assessment(c: Coordinates):
    env = environmental_analysis(c)
    solar = solar_prediction(c)
    wind = wind_prediction(c)
    solar_score = clamp((solar["capacity_factor"] / 0.32) * 100, 0, 100)
    wind_score = clamp((wind["capacity_factor"] / 0.55) * 100, 0, 100)
    terrain_score = clamp(100 - env["land_slope_deg"] * 3, 0, 100)
    overall = round(solar_score * 0.4 + wind_score * 0.3 + terrain_score * 0.3, 1)
    category = "Excellent" if overall >= 80 else "Highly Suitable" if overall >= 65 else "Moderately Suitable" if overall >= 45 else "Low Suitability"
    return {
        "environment": env,
        "solar": solar,
        "wind": wind,
        "scores": {
            "solar_score": round(solar_score, 1),
            "wind_score": round(wind_score, 1),
            "terrain_score": round(terrain_score, 1),
            "overall_score": overall,
            "category": category
        }
    }

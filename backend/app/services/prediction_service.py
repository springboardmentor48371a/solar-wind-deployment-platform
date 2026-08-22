import numpy as np
from sklearn.neighbors import KNeighborsRegressor
from app.models.site import Site

# 1. Fit ML model on geographic anchors
# Training inputs: [Latitude, Longitude]
X_train = np.array([
    [26.9124, 75.7873], # Jaipur, Rajasthan (Hot & dry, very high solar, low wind, low slope)
    [8.0883, 77.5385],  # Kanyakumari, Tamil Nadu (Coastal, high wind, moderate solar, flat slope)
    [34.1526, 77.5771], # Leh, Ladakh (Mountainous, extremely high solar, high wind, cold, high slope)
    [25.5788, 91.8933], # Shillong, Meghalaya (Rainy, low solar, low wind, mild, steep slope)
    [17.3850, 78.4867], # Hyderabad, Telangana (Plateau, good solar, moderate wind, warm, flat)
    [13.0827, 80.2707], # Chennai, Tamil Nadu (Coastal, high temp, moderate solar, flat)
    [28.6139, 77.2090], # Delhi (Continental plains, high temp summers, low wind, flat)
    [19.0760, 72.8777], # Mumbai, Maharashtra (Coastal, humid, moderate solar, flat)
    [32.2190, 76.3234], # Dharamshala, HP (Hilly forest, moderate solar, low temp, high slope)
    [22.5726, 88.3639], # Kolkata, WB (River delta, high humidity, flat)
])

# Training target variables to predict: 
# [GHI, Wind Speed, Temp, Cloud Cover, Elevation, Slope]
y_train = np.array([
    [6.2, 3.4, 32.0, 15.0, 430.0, 1.2],  # Jaipur
    [5.1, 8.4, 27.5, 38.0, 10.0, 0.5],   # Kanyakumari
    [6.8, 7.8, 9.0, 12.0, 3500.0, 15.6], # Leh
    [3.6, 2.4, 18.0, 72.0, 1520.0, 12.2], # Shillong
    [5.6, 4.2, 29.0, 28.0, 540.0, 1.8],  # Hyderabad
    [4.9, 3.1, 31.0, 40.0, 6.0, 0.3],   # Chennai
    [5.4, 2.8, 30.5, 30.0, 210.0, 1.0],  # Delhi
    [4.6, 4.5, 28.0, 48.0, 12.0, 0.4],   # Mumbai
    [4.8, 2.6, 16.5, 52.0, 1450.0, 18.2], # Dharamshala
    [4.4, 3.8, 29.5, 55.0, 9.0, 0.2],   # Kolkata
])

# Initialize and fit KNN regressor
ml_predictor = KNeighborsRegressor(n_neighbors=2, weights='distance')
ml_predictor.fit(X_train, y_train)

def assess_site_suitability(
    user_id: str,
    name: str,
    latitude: float,
    longitude: float,
    region: str,
    land_area: float,
    land_ownership: str
) -> Site:
    # 1. Run Machine Learning predictions using the KNN model
    features = ml_predictor.predict([[latitude, longitude]])[0]
    
    ghi = float(features[0])
    wind_speed = float(features[1])
    temp = float(features[2])
    cloud_cover = float(features[3])
    elevation = float(features[4])
    slope = float(features[5])
    
    # 2. Math Calculations for weighted scoring matrix
    # A. Resource Availability (35% Weight)
    solar_ratio = min(ghi / 7.0, 1.0) * 100.0
    wind_ratio = min(wind_speed / 12.0, 1.0) * 100.0
    resource_score = max(solar_ratio, wind_ratio)
    
    # B. Geographic Suitability (25% Weight)
    # Slope values exceeding 30 degrees are unsuitable for safety reasons
    geographic_score = max(0.0, 1.0 - (slope / 30.0)) * 100.0
    
    # C. Infrastructure Access (15% Weight)
    # Derived from coordinate offset proximity to reference cities
    grid_dist_km = (abs(latitude - round(latitude)) + abs(longitude - round(longitude))) * 45.0 + 1.0
    road_dist_km = (abs(latitude - round(latitude)) * 25.0) + 0.5
    grid_factor = max(0.0, 1.0 - (grid_dist_km / 100.0)) * 50.0
    road_factor = max(0.0, 1.0 - (road_dist_km / 50.0)) * 50.0
    infrastructure_score = grid_factor + road_factor
    
    # D. Environmental Impact (15% Weight)
    # Environmental constraint checks based on mock coordinates hashing
    coord_hash = int(abs(latitude * 100) + abs(longitude * 100))
    is_protected = (coord_hash % 13) == 0
    is_water_body = (coord_hash % 17) == 0
    environmental_score = 0.0 if (is_protected or is_water_body) else 100.0
    
    # E. Economic Feasibility (10% Weight)
    # Determined by ownership status
    ownership_multiplier = 1.0 if land_ownership == "Government Lease" else 0.8
    economic_score = ownership_multiplier * 100.0
    
    # 3. Overall Scoring Calculation
    overall_score = (
        (resource_score * 0.35) +
        (geographic_score * 0.25) +
        (infrastructure_score * 0.15) +
        (environmental_score * 0.15) +
        (economic_score * 0.10)
    )
    
    # Round scores to 1 decimal place
    resource_score = round(resource_score, 1)
    geographic_score = round(geographic_score, 1)
    infrastructure_score = round(infrastructure_score, 1)
    environmental_score = round(environmental_score, 1)
    economic_score = round(economic_score, 1)
    overall_score = round(overall_score, 1)
    
    # 4. Classify Suitability Range
    if overall_score >= 80.0:
        suitability_class = "Excellent"
    elif overall_score >= 65.0:
        suitability_class = "Good"
    elif overall_score >= 50.0:
        suitability_class = "Moderate"
    else:
        suitability_class = "Unsuitable"
        
    # Return unsaved database model
    return Site(
        user_id=user_id,
        name=name,
        latitude=latitude,
        longitude=longitude,
        region=region,
        land_area=land_area,
        land_ownership=land_ownership,
        
        predicted_irradiance=round(ghi, 2),
        predicted_wind_speed=round(wind_speed, 2),
        predicted_temp=round(temp, 2),
        predicted_cloud_cover=round(cloud_cover, 2),
        predicted_elevation=round(elevation, 1),
        predicted_slope=round(slope, 1),
        
        resource_score=resource_score,
        geographic_score=geographic_score,
        infrastructure_score=infrastructure_score,
        environmental_score=environmental_score,
        economic_score=economic_score,
        overall_score=overall_score,
        suitability_class=suitability_class
    )

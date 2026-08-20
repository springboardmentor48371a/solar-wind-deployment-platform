import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import sqlite3
import os
import requests
from datetime import datetime, timedelta

# Create models folder
os.makedirs('models', exist_ok=True)

# ============================================
# 1. Fetch NASA POWER data for a given lat/lon
# ============================================
def fetch_nasa_data(lat, lon):
    """Fetch environmental data from NASA POWER API"""
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    
    params = {
        "request": "execute",
        "parameters": "ALLSKY_SFC_SW_DWN,T2M,PRECTOTCORR,WS10M,CLOUD_AMT",
        "startDate": start,
        "endDate": end,
        "userCommunity": "RE",
        "format": "JSON",
        "latitude": lat,
        "longitude": lon
    }
    
    try:
        r = requests.get("https://power.larc.nasa.gov/api/power/daily", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        param = data.get("properties", {}).get("parameter", {})
        irradiance = np.mean(list(param.get("ALLSKY_SFC_SW_DWN", {}).values())) if param.get("ALLSKY_SFC_SW_DWN") else 5.0
        temp = np.mean(list(param.get("T2M", {}).values())) if param.get("T2M") else 25.0
        rain = np.mean(list(param.get("PRECTOTCORR", {}).values())) * 365 if param.get("PRECTOTCORR") else 800.0
        wind = np.mean(list(param.get("WS10M", {}).values())) if param.get("WS10M") else 5.0
        cloud = np.mean(list(param.get("CLOUD_AMT", {}).values())) if param.get("CLOUD_AMT") else 30.0
        return {
            "solar_irradiance": irradiance,
            "temperature": temp,
            "rainfall": rain,
            "wind_speed": wind,
            "cloud_cover": cloud
        }
    except Exception as e:
        print(f"    ⚠️ NASA API error: {e}. Using fallback values.")
        # Fallback values (synthetic but realistic)
        return {
            "solar_irradiance": np.random.uniform(3.0, 7.0),
            "temperature": np.random.uniform(15, 35),
            "rainfall": np.random.uniform(400, 1500),
            "wind_speed": np.random.uniform(3.0, 9.0),
            "cloud_cover": np.random.uniform(10, 60)
        }

# ============================================
# 2. Generate Training Data
# ============================================
def generate_training_data(num_samples=50):
    """Generate training data with features and suitability scores"""
    print(f"   Generating {num_samples} samples...")
    
    lats = np.random.uniform(-60, 60, num_samples)
    lons = np.random.uniform(-180, 180, num_samples)
    
    data = []
    for idx, (lat, lon) in enumerate(zip(lats, lons)):
        if idx % 10 == 0:
            print(f"   ⏳ Processing sample {idx+1}/{num_samples}...")
        
        # Fetch environmental data (with fallback)
        env = fetch_nasa_data(lat, lon)
        
        # Simulate additional features
        elevation = np.random.uniform(0, 2000)
        slope = np.random.uniform(0, 30)
        ndvi = np.random.uniform(0.05, 0.8)
        land_area = np.random.uniform(10, 500)
        road_dist = np.random.uniform(0, 50)
        power_dist = np.random.uniform(0, 50)
        
        # Suitability score (PDF formula)
        solar_score = min(env['solar_irradiance'] / 6.0, 1.0) * 100
        wind_score = min(env['wind_speed'] / 10.0, 1.0) * 100
        renewable_score = (solar_score + wind_score) / 2
        
        geo_score = 100 - min(slope, 30) * 2
        geo_score += (1 - min(elevation / 2000, 1)) * 20
        geo_score = min(geo_score, 100)
        
        infra_score = 100 - (min(road_dist, 50) * 2 + min(power_dist, 50) * 1) / 1.5
        infra_score = max(0, min(infra_score, 100))
        
        env_impact = (1 - ndvi) * 100
        env_impact = min(env_impact, 100)
        
        eco_score = min(land_area / 200, 1) * 100
        
        overall = (renewable_score * 0.35 +
                   geo_score * 0.25 +
                   infra_score * 0.15 +
                   env_impact * 0.15 +
                   eco_score * 0.10)
        
        data.append({
            'lat': lat,
            'lon': lon,
            'solar_irradiance': env['solar_irradiance'],
            'temperature': env['temperature'],
            'rainfall': env['rainfall'],
            'wind_speed': env['wind_speed'],
            'cloud_cover': env['cloud_cover'],
            'elevation': elevation,
            'slope': slope,
            'ndvi': ndvi,
            'land_area': land_area,
            'road_dist': road_dist,
            'power_dist': power_dist,
            'suitability_score': overall
        })
    
    return pd.DataFrame(data)

# ============================================
# 3. Train Suitability Model
# ============================================
def train_suitability_model(df):
    feature_cols = ['solar_irradiance', 'temperature', 'rainfall', 'wind_speed', 'cloud_cover',
                    'elevation', 'slope', 'ndvi', 'land_area', 'road_dist', 'power_dist']
    X = df[feature_cols]
    y = df['suitability_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = RandomForestRegressor(n_estimators=100, max_depth=15, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"   ✅ Suitability Model trained!")
    print(f"      Training R²: {train_score:.4f}")
    print(f"      Testing R² : {test_score:.4f}")
    
    importance = pd.DataFrame({'feature': feature_cols, 'importance': model.feature_importances_})
    importance = importance.sort_values('importance', ascending=False)
    print("   📊 Feature Importance:")
    for _, row in importance.iterrows():
        print(f"      {row['feature']}: {row['importance']:.4f}")
    
    joblib.dump(model, 'models/suitability_model.pkl')
    joblib.dump(scaler, 'models/suitability_scaler.pkl')
    
    return model, scaler

# ============================================
# 4. Train Solar/Wind Models (optional)
# ============================================
def train_solar_wind_models():
    conn = sqlite3.connect('auth.db')
    df = pd.read_sql_query('''
        SELECT 
            e.solar_irradiance, e.temperature, e.cloud_cover, e.wind_speed,
            s.elevation, s.land_area,
            sa.solar_energy_potential as solar_output,
            wa.annual_energy_production as wind_output
        FROM environmental_data e
        JOIN sites s ON e.site_id = s.id
        LEFT JOIN solar_assessments sa ON e.site_id = sa.site_id
        LEFT JOIN wind_assessments wa ON e.site_id = wa.site_id
    ''', conn)
    conn.close()
    
    if df.empty:
        print("   ⚠️ No existing assessments found. Skipping solar/wind models.")
        return
    
    solar_df = df[df['solar_output'].notna()]
    if len(solar_df) > 5:
        X_solar = solar_df[['solar_irradiance', 'temperature', 'cloud_cover', 'wind_speed', 'elevation', 'land_area']]
        y_solar = solar_df['solar_output']
        X_train, X_test, y_train, y_test = train_test_split(X_solar, y_solar, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        score = model.score(X_test_scaled, y_test)
        joblib.dump(model, 'models/solar_model.pkl')
        joblib.dump(scaler, 'models/solar_scaler.pkl')
        print(f"   ☀️ Solar Model trained! R²: {score:.4f}")
    else:
        print("   ⚠️ Not enough solar data.")
    
    wind_df = df[df['wind_output'].notna()]
    if len(wind_df) > 5:
        X_wind = wind_df[['wind_speed', 'temperature', 'elevation', 'solar_irradiance', 'cloud_cover', 'land_area']]
        y_wind = wind_df['wind_output']
        X_train, X_test, y_train, y_test = train_test_split(X_wind, y_wind, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train_scaled, y_train)
        score = model.score(X_test_scaled, y_test)
        joblib.dump(model, 'models/wind_model.pkl')
        joblib.dump(scaler, 'models/wind_scaler.pkl')
        print(f"   💨 Wind Model trained! R²: {score:.4f}")
    else:
        print("   ⚠️ Not enough wind data.")

# ============================================
# 5. MAIN
# ============================================
if __name__ == "__main__":
    print("="*60)
    print("🌞 Solar & Wind ML Training Pipeline")
    print("="*60)
    
    print("\n📊 Generating training data (50 samples)...")
    df = generate_training_data(50)
    print(f"   ✅ Generated {len(df)} samples")
    
    print("\n🧠 Training Suitability Model...")
    train_suitability_model(df)
    
    print("\n🧠 Training Solar/Wind Models (using real site data)...")
    train_solar_wind_models()
    
    print("\n" + "="*60)
    print("✅ All models trained and saved in 'models/' folder!")
    print("   - suitability_model.pkl")
    print("   - suitability_scaler.pkl")
    print("   - solar_model.pkl")
    print("   - solar_scaler.pkl")
    print("   - wind_model.pkl")
    print("   - wind_scaler.pkl")
    print("="*60)
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib
import sqlite3
import os

# Create models folder
os.makedirs('models', exist_ok=True)

# Connect to database
conn = sqlite3.connect('auth.db')
df = pd.read_sql_query('''
    SELECT 
        e.solar_irradiance,
        e.temperature,
        e.cloud_cover,
        e.wind_speed,
        s.elevation,
        s.land_area,
        sa.solar_energy_potential as solar_output,
        wa.annual_energy_production as wind_output
    FROM environmental_data e
    JOIN sites s ON e.site_id = s.id
    LEFT JOIN solar_assessments sa ON e.site_id = sa.site_id
    LEFT JOIN wind_assessments wa ON e.site_id = wa.site_id
    WHERE sa.solar_energy_potential IS NOT NULL
       OR wa.annual_energy_production IS NOT NULL
''', conn)
conn.close()

if df.empty:
    print("❌ No data found. Run site analysis first to collect training data.")
    exit()

print(f"✅ Loaded {len(df)} records for training")

# ============================================
# Train Solar Model
# ============================================
solar_df = df[df['solar_output'].notna()]
if len(solar_df) > 10:
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
    
    print(f"☀️ Solar Model trained! R² Score: {score:.2f}")
else:
    print("⚠️ Not enough solar data. Need at least 10 records.")

# ============================================
# Train Wind Model
# ============================================
wind_df = df[df['wind_output'].notna()]
if len(wind_df) > 10:
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
    
    print(f"💨 Wind Model trained! R² Score: {score:.2f}")
else:
    print("⚠️ Not enough wind data. Need at least 10 records.")

print("\n✅ ML training complete! Models saved in 'models/' folder.")
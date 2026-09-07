import os
import glob
import zipfile
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_squared_error

# 1. Locate wind dataset zip in Downloads or synthesize wind power curve
downloads_dir = os.path.expanduser("~/Downloads")
zip_candidates = (
    glob.glob(os.path.join(downloads_dir, "*wind*.zip")) +
    glob.glob(os.path.join(downloads_dir, "*scada*.zip")) +
    glob.glob(os.path.join(downloads_dir, "*.zip"))
)

found_csv = False
df = None

if zip_candidates:
    for zpath in zip_candidates:
        try:
            with zipfile.ZipFile(zpath, "r") as z:
                csv_files = [f for f in z.namelist() if f.endswith(".csv") and not f.startswith("__MACOSX")]
                wind_files = [f for f in csv_files if any(k in f.lower() for k in ["wind", "turbine", "scada"])]
                target_file = wind_files[0] if wind_files else (csv_files[0] if csv_files else None)
                
                if target_file:
                    print(f"Reading '{target_file}' from '{zpath}' in memory...")
                    with z.open(target_file) as f:
                        df = pd.read_csv(f)
                    found_csv = True
                    break
        except Exception:
            continue

# 2. Extract or synthesize physics-based wind power curves (IEC 61400 standard)
if found_csv and df is not None:
    df.columns = df.columns.str.strip().str.upper()
    numeric_df = df.select_dtypes(include=[np.number])
    
    speed_col = next((c for c in numeric_df.columns if "SPEED" in c or "WIND" in c), numeric_df.columns[0])
    power_col = next((c for c in numeric_df.columns if "POWER" in c or "ACTIVE" in c), numeric_df.columns[-1])
    
    data = numeric_df[[speed_col, power_col]].dropna()
    X = data[[speed_col]]
    y = data[power_col]
    print(f"Loaded real dataset: Speed='{speed_col}', Power='{power_col}' ({len(data)} samples)")
else:
    print("No external wind archive found. Generating 30-day IEC turbine power curve in RAM...")
    np.random.seed(42)
    # Wind speeds between cut-in (3.0 m/s) and cut-out (25.0 m/s)
    wind_speeds = np.random.uniform(2.5, 24.0, 5000)
    # Standard 2.5 MW turbine power output curve
    rated_speed = 12.0
    rated_power = 2500.0  # kW
    
    powers = []
    for ws in wind_speeds:
        if ws < 3.0 or ws > 25.0:
            powers.append(0.0)
        elif ws >= rated_speed:
            powers.append(rated_power)
        else:
            powers.append(rated_power * ((ws - 3.0) / (rated_speed - 3.0)) ** 3)
            
    X = pd.DataFrame({"WIND_SPEED_100M": wind_speeds})
    y = pd.Series(powers)

# 3. Train Random Forest Regressor
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training Random Forest on {len(X_train)} samples in memory...")
wind_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=8,
    random_state=42,
    n_jobs=-1
)
wind_model.fit(X_train, y_train)

# 4. Evaluate
preds = wind_model.predict(X_test)
r2 = r2_score(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))

print(f"Wind Model R² Score: {r2:.4f}")
print(f"Wind Model RMSE: {rmse:.2f} kW")

# 5. Save Artifact
artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(artifacts_dir, exist_ok=True)
artifact_path = os.path.join(artifacts_dir, "wind_aep_rf.pkl")

joblib.dump(wind_model, artifact_path)
print(f"Wind model artifact saved successfully to: {artifact_path}")

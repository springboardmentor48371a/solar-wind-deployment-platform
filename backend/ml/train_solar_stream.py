import os
import glob
import zipfile
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb

downloads_dir = os.path.expanduser("~/Downloads")
zip_candidates = (
    glob.glob(os.path.join(downloads_dir, "*solar*.zip")) +
    glob.glob(os.path.join(downloads_dir, "*pv*.zip")) +
    glob.glob(os.path.join(downloads_dir, "archive*.zip")) +
    glob.glob(os.path.join(downloads_dir, "*.zip"))
)

if not zip_candidates:
    raise FileNotFoundError("No .zip file found in your Downloads folder.")

zip_path = zip_candidates[0]
print(f"Streaming from archive: {zip_path}")

with zipfile.ZipFile(zip_path, "r") as z:
    all_files = [f for f in z.namelist() if f.endswith(".csv") and not f.startswith("__MACOSX")]
    print(f"Files found in archive: {all_files}")

    gen_file = next((f for f in all_files if "generation" in f.lower()), None)
    weather_file = next((f for f in all_files if "weather" in f.lower() or "sensor" in f.lower()), None)

    if gen_file and weather_file:
        print(f"Loading '{gen_file}' and '{weather_file}' directly into RAM...")
        with z.open(gen_file) as f_gen:
            df_gen = pd.read_csv(f_gen)
        with z.open(weather_file) as f_w:
            df_weather = pd.read_csv(f_w)

        df_gen.columns = df_gen.columns.str.strip().str.upper()
        df_weather.columns = df_weather.columns.str.strip().str.upper()

        # Parse timestamps properly using format='mixed' to handle mismatched date formats
        df_gen["DATE_TIME_PARSED"] = pd.to_datetime(df_gen["DATE_TIME"], format="mixed")
        df_weather["DATE_TIME_PARSED"] = pd.to_datetime(df_weather["DATE_TIME"], format="mixed")

        # Aggregate total plant power across all inverters at each timestamp
        df_gen_grouped = (
            df_gen.groupby("DATE_TIME_PARSED")[["DC_POWER", "AC_POWER"]]
            .sum()
            .reset_index()
        )

        # Merge on parsed timestamps
        df = pd.merge(df_gen_grouped, df_weather, on="DATE_TIME_PARSED", how="inner")
        
        feature_cols = ["IRRADIATION", "AMBIENT_TEMPERATURE"]
        target_col = "AC_POWER"
    else:
        with z.open(all_files[0]) as f:
            df = pd.read_csv(f)
        df.columns = df.columns.str.strip().str.upper()
        numeric_df = df.select_dtypes(include=[np.number])
        feature_cols = [c for c in numeric_df.columns if c not in ["DC_POWER", "AC_POWER", "TOTAL_YIELD", "DAILY_YIELD"]][:2]
        target_col = "AC_POWER" if "AC_POWER" in numeric_df.columns else numeric_df.columns[-1]

print(f"Selected features: {feature_cols} -> Target: '{target_col}'")

# Clean numeric records
clean_df = df[feature_cols + [target_col]].dropna()
X = clean_df[feature_cols]
y = clean_df[target_col]

print(f"Valid merged records for training: {len(clean_df)}")

# Train / Test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"Training XGBoost on {len(X_train)} samples...")
solar_model = xgb.XGBRegressor(
    n_estimators=120,
    learning_rate=0.08,
    max_depth=5,
    random_state=42,
    n_jobs=-1
)
solar_model.fit(X_train, y_train)

preds = solar_model.predict(X_test)
r2 = r2_score(y_test, preds)
rmse = np.sqrt(mean_squared_error(y_test, preds))

print(f"Solar Model R² Score: {r2:.4f}")
print(f"Solar Model RMSE: {rmse:.2f}")

# Save artifact
artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
os.makedirs(artifacts_dir, exist_ok=True)
artifact_path = os.path.join(artifacts_dir, "solar_aep_xgb.pkl")

joblib.dump(solar_model, artifact_path)
print(f"Model saved successfully to: {artifact_path}")
import os
import json
import logging
import datetime
from pathlib import Path
import pandas as pd
import requests
import kagglehub
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "raw"
MODELS_DIR = BASE_DIR / "models"

SOLAR_DIR = DATA_DIR / "solar"
WIND_DIR = DATA_DIR / "wind"

SOLAR_DIR.mkdir(parents=True, exist_ok=True)
WIND_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def download_solar_data():
    logging.info("Downloading Solar Data from Kaggle...")
    try:
        path = kagglehub.dataset_download("anikannal/solar-power-generation-data")
        logging.info(f"Solar data downloaded to: {path}")
        
        gen_file = os.path.join(path, "Plant_1_Generation_Data.csv")
        sensor_file = os.path.join(path, "Plant_1_Weather_Sensor_Data.csv")
        
        return gen_file, sensor_file
    except Exception as e:
        logging.error(f"Failed to download solar data: {e}")
        return None, None

def download_wind_data():
    logging.info("Downloading Wind Data from Zenodo...")
    zenodo_api_url = "https://zenodo.org/api/records/5841834"
    try:
        resp = requests.get(zenodo_api_url)
        resp.raise_for_status()
        data = resp.json()
        
        target_file = None
        for f in data.get("files", []):
            if "2021" in f["key"] and "SCADA" in f["key"] and f["key"].endswith(".zip"):
                target_file = f
                break
                    
        if target_file:
            download_url = target_file["links"]["self"]
            filename = target_file["key"]
            filepath = WIND_DIR / filename
            
            logging.info(f"Selected Wind file: {filename} ({(target_file['size']/1024/1024):.2f} MB)")
            
            if not filepath.exists():
                logging.info(f"Downloading {filename}...")
                file_resp = requests.get(download_url, stream=True)
                file_resp.raise_for_status()
                with open(filepath, "wb") as out:
                    for chunk in file_resp.iter_content(chunk_size=8192):
                        out.write(chunk)
                logging.info("Wind data download complete.")
                
                # Unzip it
                import zipfile
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(WIND_DIR)
                    
            # Find all actual csvs inside the extracted folder
            csv_files = []
            for root, dirs, files in os.walk(WIND_DIR):
                for file in files:
                    if file.endswith('.csv') and 'TURBINE_DATA' in file.upper():
                        csv_files.append(Path(root) / file)
            
            if csv_files:
                return csv_files
                        
            return filepath
        else:
            logging.error("Could not find suitable SCADA file on Zenodo.")
            return None
    except Exception as e:
        logging.error(f"Failed to download wind data: {e}")
        return None

def train_solar_model(gen_file, sensor_file):
    logging.info("--- Processing Solar Data ---")
    gen_df = pd.read_csv(gen_file)
    sensor_df = pd.read_csv(sensor_file)
    
    raw_count = len(gen_df)
    logging.info(f"Raw solar generation records: {raw_count}")
    
    # Parse dates before merge since formats differ
    gen_df["DATE_TIME"] = pd.to_datetime(gen_df["DATE_TIME"], format="mixed", dayfirst=True)
    sensor_df["DATE_TIME"] = pd.to_datetime(sensor_df["DATE_TIME"], format="mixed", dayfirst=True)
    
    # Merge on DATE_TIME and PLANT_ID
    df = pd.merge(gen_df, sensor_df, on=["DATE_TIME", "PLANT_ID"], how="inner")
    df = df.sort_values("DATE_TIME")
    
    # Drop missing
    df = df.dropna(subset=["AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION", "AC_POWER"])
    cleaned_count = len(df)
    logging.info(f"Cleaned solar records: {cleaned_count}")
    
    features = ["AMBIENT_TEMPERATURE", "MODULE_TEMPERATURE", "IRRADIATION"]
    target = "AC_POWER"
    
    X = df[features]
    y = df[target]
    
    # Time-aware split (first 80% train, last 20% test)
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    logging.info(f"Solar Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    # Linear Regression
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_mae = mean_absolute_error(y_test, lr_preds)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))
    lr_r2 = r2_score(y_test, lr_preds)
    
    # Random Forest
    rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    
    logging.info(f"Solar LR Metrics: MAE={lr_mae:.2f}, RMSE={lr_rmse:.2f}, R2={lr_r2:.4f}")
    logging.info(f"Solar RF Metrics: MAE={rf_mae:.2f}, RMSE={rf_rmse:.2f}, R2={rf_r2:.4f}")
    
    best_model = "Random Forest" if rf_r2 > lr_r2 else "Linear Regression"
    model_to_save = rf if rf_r2 > lr_r2 else lr
    
    model_path = MODELS_DIR / "solar_model_real.joblib"
    joblib.dump(model_to_save, model_path)
    
    meta = {
        "model_name": f"Solar {best_model}",
        "dataset_source": "Kaggle - Solar Power Generation Data by Ani Kannal",
        "license": "Data files (c) Original Authors",
        "features": features,
        "target": target,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "raw_records": raw_count,
        "cleaned_records": cleaned_count,
        "lr_metrics": {"mae": lr_mae, "rmse": lr_rmse, "r2": lr_r2},
        "rf_metrics": {"mae": rf_mae, "rmse": rf_rmse, "r2": rf_r2},
        "training_timestamp": datetime.datetime.now().isoformat()
    }
    
    meta_path = MODELS_DIR / "solar_model_real_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
        
    logging.info(f"Solar model saved to {model_path}")
    return meta

def train_wind_model(wind_files):
    logging.info("--- Processing Wind Data ---")
    
    dfs = []
    if isinstance(wind_files, list):
        for f in wind_files:
            logging.info(f"Loading {f}")
            dfs.append(pd.read_csv(f, skiprows=9))
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = pd.read_csv(wind_files, skiprows=9)
    
    raw_count = len(df)
    logging.info(f"Raw wind records: {raw_count}")
    
    cols = list(df.columns)
    
    time_col = next((c for c in cols if 'time' in c.lower() or 'date' in c.lower()), cols[0])
    ws_col = next((c for c in cols if 'wind speed' in c.lower() or ('wind' in c.lower() and 'speed' in c.lower())), None)
    wd_col = next((c for c in cols if 'wind direction' in c.lower() or ('wind' in c.lower() and 'dir' in c.lower())), None)
    power_col = next((c for c in cols if 'power' in c.lower() and ('kw' in c.lower() or 'active' in c.lower())), None)
    temp_col = next((c for c in cols if 'temperature' in c.lower() and 'ambient' in c.lower()), None)
    
    if not temp_col:
        temp_col = next((c for c in cols if 'temperature' in c.lower()), None)
        
    if not all([ws_col, wd_col, power_col]):
        logging.error(f"Missing required columns! Found: {cols}")
        return None
        
    features = [ws_col, wd_col]
    if temp_col:
        features.append(temp_col)
        
    target = power_col
    
    df[time_col] = pd.to_datetime(df[time_col])
    df = df.sort_values(time_col)
    
    for col in features + [target]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df = df.dropna(subset=features + [target])
    
    # Filter explicitly only invalid/faulted data (e.g. unrealistic outliers)
    # Keeping low wind speeds (< 3m/s) as requested by user.
    df = df[(df[ws_col] >= 0) & (df[ws_col] <= 60)] # Physical wind speeds
    df = df[df[target] >= -1000] # Allow negative power (idle consumption)
    
    cleaned_count = len(df)
    logging.info(f"Cleaned wind records: {cleaned_count}")
    
    X = df[features]
    y = df[target]
    
    split_idx = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    logging.info(f"Wind Train size: {len(X_train)}, Test size: {len(X_test)}")
    
    lr = LinearRegression()
    lr.fit(X_train, y_train)
    lr_preds = lr.predict(X_test)
    lr_mae = mean_absolute_error(y_test, lr_preds)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))
    lr_r2 = r2_score(y_test, lr_preds)
    
    rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    
    logging.info(f"Wind LR Metrics: MAE={lr_mae:.2f}, RMSE={lr_rmse:.2f}, R2={lr_r2:.4f}")
    logging.info(f"Wind RF Metrics: MAE={rf_mae:.2f}, RMSE={rf_rmse:.2f}, R2={rf_r2:.4f}")
    
    best_model = "Random Forest" if rf_r2 > lr_r2 else "Linear Regression"
    model_to_save = rf if rf_r2 > lr_r2 else lr
    
    model_path = MODELS_DIR / "wind_model_real.joblib"
    joblib.dump(model_to_save, model_path)
    
    meta = {
        "model_name": f"Wind {best_model}",
        "dataset_source": "Zenodo - Kelmarsh Wind Farm SCADA dataset by Cubico",
        "license": "CC-BY-4.0",
        "features": features,
        "target": target,
        "train_size": len(X_train),
        "test_size": len(X_test),
        "raw_records": raw_count,
        "cleaned_records": cleaned_count,
        "lr_metrics": {"mae": lr_mae, "rmse": lr_rmse, "r2": lr_r2},
        "rf_metrics": {"mae": rf_mae, "rmse": rf_rmse, "r2": rf_r2},
        "training_timestamp": datetime.datetime.now().isoformat()
    }
    
    meta_path = MODELS_DIR / "wind_model_real_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
        
    logging.info(f"Wind model saved to {model_path}")
    return meta

if __name__ == "__main__":
    gen, sensor = download_solar_data()
    if gen and sensor:
        train_solar_model(gen, sensor)
        
    wind_file = download_wind_data()
    if wind_file:
        train_wind_model(wind_file)

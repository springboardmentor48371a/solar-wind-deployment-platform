import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import xgboost as xgb

def train_solar_engine():
    artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    print("[Module 5] Initializing Solar Potential Machine Learning Training...")

    np.random.seed(42)
    n_samples = 4000

    solar_ghi = np.random.uniform(2.5, 7.5, n_samples)          # kWh/m²/day
    temp_avg = np.random.uniform(15.0, 44.0, n_samples)         # °C
    peak_sun_hours = solar_ghi * np.random.uniform(0.98, 1.02, n_samples)
    cloud_cover = np.random.uniform(10.0, 85.0, n_samples)      # %
    elevation = np.random.uniform(10.0, 800.0, n_samples)       # m

    # Standard PV Derate model: P = GHI * PR * (1 - gamma*(T - 25))
    temp_derate = np.maximum(0.0, (temp_avg - 25.0) * 0.004)
    cloud_derate = (cloud_cover / 100.0) * 0.12
    
    target_yield = solar_ghi * 0.79 * (1.0 - temp_derate - cloud_derate)
    target_yield += np.random.normal(0, 0.05, n_samples)

    X = pd.DataFrame({
        "solar_irradiance": solar_ghi,
        "peak_sun_hours": peak_sun_hours,
        "temperature_avg": temp_avg,
        "cloud_cover": cloud_cover,
        "elevation": elevation
    })
    y = target_yield

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train Regressor
    model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.04,
        max_depth=5,
        subsample=0.85,
        random_state=42
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    print(f"[Solar ML Complete] Validation R² Score: {r2:.4f}")
    print(f"[Solar ML Complete] RMSE: {rmse:.4f} kWh/kWp")

    # Save artifact
    output_path = os.path.join(artifacts_dir, "solar_aep_xgb.pkl")
    joblib.dump(model, output_path)
    print(f"Artifact successfully saved at: {output_path}")

if __name__ == "__main__":
    train_solar_engine()
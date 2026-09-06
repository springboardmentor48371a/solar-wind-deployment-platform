import io
import os
import zipfile
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error

# Path to the single downloaded zip file (reads without extracting to disk)
zip_path = os.path.expanduser("~/Downloads/wind-turbine-scada-dataset.zip")

print("Streaming dataset into memory...")
with zipfile.ZipFile(zip_path, 'r') as z:
    # Opens T1.csv directly from the compressed stream
    csv_filename = [f for f in z.namelist() if f.endswith('.csv')][0]
    with z.open(csv_filename) as f:
        df = pd.read_csv(f)

# Clean columns
df.columns = df.columns.str.strip()

feature_cols = ['Wind Speed (m/s)', 'Wind Direction (°)', 'Theoretical_Power_Curve (KWh)']
target_col = 'LV ActivePower (kW)'

df = df.dropna(subset=feature_cols + [target_col])
X = df[feature_cols]
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training model in RAM...")
model = RandomForestRegressor(n_estimators=60, max_depth=10, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

preds = model.predict(X_test)
print(f"Model R²: {r2_score(y_test, preds):.4f}")
print(f"Model RMSE: {np.sqrt(mean_squared_error(y_test, preds)):.2f} kW")

# Save only the lightweight model artifact (~1 MB)
os.makedirs("ml/artifacts", exist_ok=True)
joblib.dump(model, "ml/artifacts/wind_scada_rf.pkl")
print("Model saved to ml/artifacts/wind_scada_rf.pkl")
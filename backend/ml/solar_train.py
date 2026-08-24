import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor


# ============================================================
# CONFIG
# ============================================================

DATASET_PATH = "../../datasets/nasa_power_climate_risk_indices_190_capitals_1990_2024.csv"

MODEL_DIR = "artifacts"

os.makedirs(MODEL_DIR, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading NASA POWER dataset...")

df = pd.read_csv(DATASET_PATH)

print(f"Dataset shape: {df.shape}")


# ============================================================
# FEATURES
# ============================================================

FEATURES = [
    "latitude",
    "longitude",
    "temp_mean_c",
    "temp_max_c",
    "temp_min_c",
    "precip_total_mm",
    "rh_mean_pct",
    "wind_mean_ms",
    "solar_mean_mj",
    "solar_clear_mean_mj",
    "solar_clearness_idx",
    "pressure_mean_kpa",
    "climate_volatility"
]

TARGET = "solar_annual_kwh_m2"


# ============================================================
# CHECK COLUMNS
# ============================================================

required = FEATURES + [TARGET]

missing = [
    column for column in required
    if column not in df.columns
]

if missing:
    raise ValueError(
        f"Missing columns: {missing}"
    )


# ============================================================
# SELECT DATA
# ============================================================

data = df[required].copy()

print(f"Selected rows: {len(data)}")


# ============================================================
# REMOVE MISSING TARGETS
# ============================================================

data = data.dropna(subset=[TARGET])

print(
    f"Rows after target cleaning: {len(data)}"
)


# ============================================================
# FEATURES / TARGET
# ============================================================

X = data[FEATURES]

y = data[TARGET]


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42
)


# ============================================================
# MISSING VALUE IMPUTATION
# ============================================================

imputer = SimpleImputer(
    strategy="median"
)

X_train = imputer.fit_transform(X_train)

X_test = imputer.transform(X_test)


# ============================================================
# XGBOOST
# ============================================================

model = XGBRegressor(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)


# ============================================================
# TRAIN
# ============================================================

print("\nTraining XGBoost Solar Model...")

model.fit(
    X_train,
    y_train
)

print("Training completed.")


# ============================================================
# PREDICTION
# ============================================================

predictions = model.predict(
    X_test
)


# ============================================================
# EVALUATION
# ============================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = mean_squared_error(
    y_test,
    predictions
) ** 0.5

r2 = r2_score(
    y_test,
    predictions
)


print("\n================================")
print("SOLAR MODEL RESULTS")
print("================================")

print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nFeature Importance:")

print(
    importance.to_string(
        index=False
    )
)


# ============================================================
# SAVE
# ============================================================

joblib.dump(
    model,
    f"{MODEL_DIR}/solar_xgb_model.pkl"
)

joblib.dump(
    imputer,
    f"{MODEL_DIR}/solar_imputer.pkl"
)

joblib.dump(
    FEATURES,
    f"{MODEL_DIR}/solar_features.pkl"
)


print("\n================================")
print("MODEL SAVED")
print("================================")

print(
    f"{MODEL_DIR}/solar_xgb_model.pkl"
)

print(
    f"{MODEL_DIR}/solar_imputer.pkl"
)

print(
    f"{MODEL_DIR}/solar_features.pkl"
)
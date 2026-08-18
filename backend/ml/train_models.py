import pandas as pd
import joblib

from sqlalchemy import text

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from xgboost import XGBRegressor
from lightgbm import LGBMRegressor

from app.database import SessionLocal


# =========================================================
# 1. CONNECT TO DATABASE
# =========================================================

db = SessionLocal()

try:

    query = text("""
        SELECT
            temperature,
            ghi,
            dni,
            dhi,
            wind_speed,
            recorded_date
        FROM resource_data
        WHERE ghi IS NOT NULL
        ORDER BY recorded_date
    """)

    result = db.execute(query)

    rows = result.fetchall()

finally:

    db.close()


# =========================================================
# 2. CREATE DATAFRAME
# =========================================================

columns = [
    "temperature",
    "ghi",
    "dni",
    "dhi",
    "wind_speed",
    "recorded_date"
]

df = pd.DataFrame(rows, columns=columns)


print("\n===================================")
print("DATASET")
print("===================================")

print(df.head())

print("\nColumns:")
print(df.columns.tolist())

print("\nNumber of records:", len(df))


# =========================================================
# 3. CONVERT NUMERIC DATA
# =========================================================

numeric_columns = [
    "temperature",
    "ghi",
    "dni",
    "dhi",
    "wind_speed"
]

for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# =========================================================
# 4. REMOVE MISSING VALUES
# =========================================================

df = df.dropna(
    subset=numeric_columns
)


print("\n===================================")
print("AFTER REMOVING MISSING VALUES")
print("===================================")

print(df.head())

print("\nNumber of usable records:", len(df))


# =========================================================
# 5. CHECK DATA
# =========================================================

if len(df) < 20:

    print("\nNot enough data for ML training.")

    print("Need at least 20 usable records.")

    exit()


# =========================================================
# 6. FEATURES
# =========================================================
#
# We are predicting GHI.
#
# GHI is NOT included in X.
#
# Otherwise the model would already know
# the answer it is trying to predict.
# =========================================================

X = df[
    [
        "temperature",
        "dni",
        "dhi",
        "wind_speed"
    ]
]


# =========================================================
# 7. TARGET
# =========================================================

y = df["ghi"]


# =========================================================
# 8. TRAIN / TEST SPLIT
# =========================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.2,

    random_state=42
)


print("\nTraining records:", len(X_train))

print("Testing records:", len(X_test))


# =========================================================
# 9. RANDOM FOREST
# =========================================================

print("\n===================================")
print("TRAINING RANDOM FOREST")
print("===================================")


rf_model = RandomForestRegressor(

    n_estimators=100,

    random_state=42
)


rf_model.fit(

    X_train,

    y_train
)


rf_prediction = rf_model.predict(

    X_test
)


rf_r2 = r2_score(

    y_test,

    rf_prediction
)


rf_mae = mean_absolute_error(

    y_test,

    rf_prediction
)


rf_rmse = mean_squared_error(

    y_test,

    rf_prediction

) ** 0.5


print("Random Forest R2:", rf_r2)

print("Random Forest MAE:", rf_mae)

print("Random Forest RMSE:", rf_rmse)


# =========================================================
# 10. XGBOOST
# =========================================================

print("\n===================================")
print("TRAINING XGBOOST")
print("===================================")


xgb_model = XGBRegressor(

    n_estimators=100,

    max_depth=5,

    learning_rate=0.05,

    random_state=42

)


xgb_model.fit(

    X_train,

    y_train

)


xgb_prediction = xgb_model.predict(

    X_test

)


xgb_r2 = r2_score(

    y_test,

    xgb_prediction
)


xgb_mae = mean_absolute_error(

    y_test,

    xgb_prediction

)


xgb_rmse = mean_squared_error(

    y_test,

    xgb_prediction

) ** 0.5


print("XGBoost R2:", xgb_r2)

print("XGBoost MAE:", xgb_mae)

print("XGBoost RMSE:", xgb_rmse)


# =========================================================
# 11. LIGHTGBM
# =========================================================

print("\n===================================")
print("TRAINING LIGHTGBM")
print("===================================")


lgb_model = LGBMRegressor(

    n_estimators=100,

    learning_rate=0.05,

    random_state=42,

    verbosity=-1

)


lgb_model.fit(

    X_train,

    y_train

)


lgb_prediction = lgb_model.predict(

    X_test

)


lgb_r2 = r2_score(

    y_test,

    lgb_prediction
)


lgb_mae = mean_absolute_error(

    y_test,

    lgb_prediction

)


lgb_rmse = mean_squared_error(

    y_test,

    lgb_prediction

) ** 0.5


print("LightGBM R2:", lgb_r2)

print("LightGBM MAE:", lgb_mae)

print("LightGBM RMSE:", lgb_rmse)


# =========================================================
# 12. MODEL COMPARISON
# =========================================================

results = pd.DataFrame({

    "Model": [
        "Random Forest",
        "XGBoost",
        "LightGBM"
    ],

    "R2": [
        rf_r2,
        xgb_r2,
        lgb_r2
    ],

    "MAE": [
        rf_mae,
        xgb_mae,
        lgb_mae
    ],

    "RMSE": [
        rf_rmse,
        xgb_rmse,
        lgb_rmse
    ]

})


print("\n===================================")
print("MODEL COMPARISON")
print("===================================")

print(results)


# =========================================================
# 13. SAVE MODELS
# =========================================================

joblib.dump(

    rf_model,

    "random_forest_solar.pkl"

)


joblib.dump(

    xgb_model,

    "xgboost_solar.pkl"

)


joblib.dump(

    lgb_model,

    "lightgbm_solar.pkl"

)


print("\n===================================")
print("SUCCESS")
print("===================================")

print("Models saved successfully.")

print("random_forest_solar.pkl")

print("xgboost_solar.pkl")

print("lightgbm_solar.pkl")
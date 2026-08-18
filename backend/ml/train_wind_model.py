import pandas as pd
import joblib

from sqlalchemy import text
from app.database import SessionLocal

from xgboost import XGBRegressor


# =========================================================
# GET DATA FROM DATABASE
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
        ORDER BY recorded_date
    """)

    result = db.execute(query)

    rows = result.fetchall()

finally:

    db.close()


# =========================================================
# CREATE DATAFRAME
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


print("===================================")
print("WIND DATA")
print("===================================")

print(df.head())

print("Number of records:", len(df))


# =========================================================
# CLEAN DATA
# =========================================================

df = df.dropna()

print("Usable records:", len(df))


# =========================================================
# CHECK DATA
# =========================================================

if len(df) < 50:

    print("Not enough data for wind ML training.")

    exit()


# =========================================================
# INPUT FEATURES
# =========================================================

X = df[
    [
        "temperature",
        "ghi",
        "dni",
        "dhi"
    ]
]


# =========================================================
# TARGET
# =========================================================

y = df["wind_speed"]


# =========================================================
# TRAIN XGBOOST
# =========================================================

print()
print("===================================")
print("TRAINING WIND XGBOOST")
print("===================================")


model = XGBRegressor(

    n_estimators=200,

    max_depth=6,

    learning_rate=0.05,

    random_state=42

)


model.fit(X, y)


# =========================================================
# SAVE MODEL
# =========================================================

joblib.dump(

    model,

    "xgboost_wind.pkl"

)


print()
print("===================================")
print("SUCCESS")
print("===================================")

print("Wind XGBoost model saved successfully.")

print("xgboost_wind.pkl")
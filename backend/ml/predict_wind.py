import joblib
import pandas as pd
from pathlib import Path


# =========================================================
# FIND MODEL
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "xgboost_wind.pkl"


# =========================================================
# LOAD MODEL
# =========================================================

model = joblib.load(MODEL_PATH)

print("Wind XGBoost model loaded successfully!")


# =========================================================
# WIND PREDICTION FUNCTION
# =========================================================

def predict_wind(
    temperature,
    ghi,
    dni,
    dhi
):

    data = pd.DataFrame({

        "temperature": [temperature],

        "ghi": [ghi],

        "dni": [dni],

        "dhi": [dhi]

    })


    prediction = model.predict(data)


    return float(prediction[0])


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    predicted_wind = predict_wind(

        temperature=30.0,

        ghi=5.5,

        dni=5.0,

        dhi=1.5

    )


    print(
        "Predicted Wind Speed:",
        predicted_wind
    )
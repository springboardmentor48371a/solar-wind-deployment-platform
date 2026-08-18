import joblib
import pandas as pd
from pathlib import Path


# =========================================================
# FIND RANDOM FOREST SOLAR MODEL
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "random_forest_solar.pkl"


# =========================================================
# LOAD MODEL
# =========================================================

model = joblib.load(MODEL_PATH)

print("Random Forest solar model loaded successfully!")


# =========================================================
# PREDICTION FUNCTION
# =========================================================

def predict_solar(
    temperature,
    dni,
    dhi,
    wind_speed
):

    data = pd.DataFrame({

        "temperature": [temperature],

        "dni": [dni],

        "dhi": [dhi],

        "wind_speed": [wind_speed]

    })

    prediction = model.predict(data)

    return float(prediction[0])


# =========================================================
# TEST PREDICTION
# =========================================================

if __name__ == "__main__":

    predicted_ghi = predict_solar(

        temperature=30.0,

        dni=5.5,

        dhi=2.0,

        wind_speed=4.5

    )

    print(
        "Predicted GHI:",
        predicted_ghi
    )
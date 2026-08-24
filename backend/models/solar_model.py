import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


class SolarModel:

    def __init__(self):
        self.model = None

        self.features = [
            "latitude",
            "longitude",
            "year",
            "temp_mean_c",
            "precip_total_mm",
            "rh_mean_pct",
            "wind_mean_ms",
            "solar_mean_mj",
            "solar_clear_mean_mj",
            "solar_clearness_idx",
            "solar_peak_days",
            "climate_volatility"
        ]

    def train(self, dataframe):

        df = dataframe.copy()

        df = df.dropna(
            subset=["solar_annual_kwh_m2"]
        )

        train = df[df["year"] < 2020]

        X = train[self.features]

        y = train["solar_annual_kwh_m2"]

        self.model = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="median")
            ),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=300,
                    max_depth=18,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            )
        ])

        self.model.fit(X, y)

        print("☀️ Solar model trained successfully")

    def predict(self, data):

        if self.model is None:
            raise Exception(
                "Solar model is not trained/loaded"
            )

        df = pd.DataFrame([data])

        prediction = self.model.predict(
            df[self.features]
        )[0]

        return float(prediction)

    def save(self, path):

        joblib.dump(
            self.model,
            path
        )

        print(
            f"☀️ Solar model saved: {path}"
        )

    def load(self, path):

        self.model = joblib.load(path)

        print(
            f"☀️ Solar model loaded: {path}"
        )
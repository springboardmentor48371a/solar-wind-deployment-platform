import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


class SuitabilityModel:

    def __init__(self):

        self.model = None

        self.features = [
            "latitude",
            "longitude",
            "temp_mean_c",
            "precip_total_mm",
            "rh_mean_pct",
            "wind_mean_ms",
            "wind_power_density",
            "solar_annual_kwh_m2",
            "solar_clearness_idx",
            "solar_peak_days",
            "heat_stress_index",
            "drought_stress_days",
            "humidity_stress_days",
            "climate_volatility",
            "gdp_per_capita_usd"
        ]

    def train(self, dataframe):

        df = dataframe.copy()

        df = df.dropna(
            subset=[
                "solar_annual_kwh_m2",
                "wind_power_density"
            ]
        )

        # -----------------------------------------
        # Create suitability target
        # -----------------------------------------

        solar_score = (
            df["solar_annual_kwh_m2"]
            .rank(pct=True)
        )

        wind_score = (
            df["wind_power_density"]
            .rank(pct=True)
        )

        heat_score = 1 - (
            df["heat_stress_index"]
            .rank(pct=True)
        )

        drought_score = 1 - (
            df["drought_stress_days"]
            .rank(pct=True)
        )

        humidity_score = 1 - (
            df["humidity_stress_days"]
            .rank(pct=True)
        )

        climate_score = 1 - (
            df["climate_volatility"]
            .rank(pct=True)
        )

        df["suitability_score"] = (

            0.40 * solar_score
            + 0.30 * wind_score
            + 0.08 * heat_score
            + 0.08 * drought_score
            + 0.07 * humidity_score
            + 0.07 * climate_score

        ) * 100

        train = df[df["year"] < 2020]

        X = train[self.features]

        y = train[
            "suitability_score"
        ]

        self.model = Pipeline([
            (
                "imputer",
                SimpleImputer(strategy="median")
            ),
            (
                "model",
                RandomForestRegressor(
                    n_estimators=400,
                    max_depth=20,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            )
        ])

        self.model.fit(X, y)

        print(
            "🏆 Suitability model trained successfully"
        )

    def predict(self, data):

        if self.model is None:
            raise Exception(
                "Suitability model is not trained/loaded"
            )

        df = pd.DataFrame([data])

        prediction = self.model.predict(
            df[self.features]
        )[0]

        prediction = max(
            0,
            min(100, prediction)
        )

        return float(prediction)

    def get_category(self, score):

        if score >= 90:
            return "Excellent"

        if score >= 80:
            return "Highly Suitable"

        if score >= 65:
            return "Moderately Suitable"

        if score >= 40:
            return "Low Suitability"

        return "Unsuitable"

    def save(self, path):

        joblib.dump(
            self.model,
            path
        )

        print(
            f"🏆 Suitability model saved: {path}"
        )

    def load(self, path):

        self.model = joblib.load(path)

        print(
            f"🏆 Suitability model loaded: {path}"
        )
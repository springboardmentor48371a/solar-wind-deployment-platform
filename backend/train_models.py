import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.solar_engine import solar_ml_engine
from app.ml.wind_engine import wind_ml_engine
from app.core.logging import logger


def train_all_models():
    logger.info("Training Solar Potential ML Pipeline (Gradient Boosting)...")
    solar_metrics = solar_ml_engine.train(model_type="gradient_boosting", n_estimators=150)
    logger.info(f"Solar ML Metrics: {solar_metrics}")

    logger.info("Training Wind Potential ML Pipeline (Gradient Boosting)...")
    wind_metrics = wind_ml_engine.train(model_type="gradient_boosting", n_estimators=150)
    logger.info(f"Wind ML Metrics: {wind_metrics}")

    logger.info("Both ML pipelines trained and serialized to backend/app/ml/artifacts/ successfully!")


if __name__ == "__main__":
    train_all_models()

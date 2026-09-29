import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.ml.data_generator import generate_solar_dataset, generate_wind_dataset
from app.core.logging import logger

DEMO_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "demo"))
os.makedirs(DEMO_DATA_DIR, exist_ok=True)


def generate_all():
    logger.info("Generating realistic solar demonstration dataset (2500 samples)...")
    solar_df = generate_solar_dataset(n_samples=2500)
    solar_path = os.path.join(DEMO_DATA_DIR, "solar_demo_dataset.csv")
    solar_df.to_csv(solar_path, index=False)
    logger.info(f"Saved solar dataset to: {solar_path}")

    logger.info("Generating realistic wind demonstration dataset (2500 samples)...")
    wind_df = generate_wind_dataset(n_samples=2500)
    wind_path = os.path.join(DEMO_DATA_DIR, "wind_demo_dataset.csv")
    wind_df.to_csv(wind_path, index=False)
    logger.info(f"Saved wind dataset to: {wind_path}")

    logger.info("Demo datasets successfully generated!")


if __name__ == "__main__":
    generate_all()

import torch
import numpy as np
from pathlib import Path
from datetime import date, timedelta

MODEL_PATH = Path(__file__).parent.parent / "models" / "forecast_model.pt"

model = None

def load_model():
    global model
    if MODEL_PATH.exists():
        model = torch.load(MODEL_PATH, map_location="cpu")
        model.eval()

def predict_forecast(
    historical_solar: list[float],
    historical_wind: list[float],
    days_ahead: int = 30,
) -> list[dict]:
    if model is None:
        return []

    with torch.no_grad():
        solar_tensor = torch.tensor(historical_solar, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
        wind_tensor = torch.tensor(historical_wind, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
        input_tensor = torch.cat([solar_tensor, wind_tensor], dim=-1)
        output = model(input_tensor).squeeze().numpy()

    forecasts = []
    today = date.today()
    for i in range(days_ahead):
        solar_kwh = float(output[i][0]) if output.ndim > 1 else float(output[i])
        wind_kwh = float(output[i][1]) if output.ndim > 1 else 0.0
        forecasts.append({
            "forecast_date": today + timedelta(days=i + 1),
            "predicted_solar_kwh": round(max(solar_kwh, 0), 2),
            "predicted_wind_kwh": round(max(wind_kwh, 0), 2),
            "predicted_total_kwh": round(max(solar_kwh + wind_kwh, 0), 2),
            "confidence": 0.85,
        })

    return forecasts

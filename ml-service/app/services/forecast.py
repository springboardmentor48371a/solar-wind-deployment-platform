# Forecast engine is paused — model file does not exist.
# PyTorch dependency removed to keep the ml-service image lightweight.
# This module is kept as a stub so the rest of the service doesn't need to change.

model = None

def load_model():
    pass  # no-op until forecast model is retrained

def predict_forecast(
    historical_solar: list,
    historical_wind: list,
    days_ahead: int = 30,
) -> list:
    return []

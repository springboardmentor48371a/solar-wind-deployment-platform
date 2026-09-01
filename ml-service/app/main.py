from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .models import SitePrediction, EnergyForecast, LandCover
from .routers import predict
from .services import solar, wind, land_cover, forecast

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Solar & Wind ML Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def load_models():
    solar.load_model()
    wind.load_model()
    land_cover.load_model()
    forecast.load_model()

app.include_router(predict.router)

@app.get("/health")
def health():
    return {
        "status": "ok",
        "models": {
            "solar":      solar.model is not None,
            "wind":       wind.model is not None,
            "land_cover": land_cover.model is not None,
            "forecast":   forecast.model is not None,
        }
    }

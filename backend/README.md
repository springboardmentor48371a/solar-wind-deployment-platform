# Backend

FastAPI backend for the Solar and Wind Prediction platform. It handles authentication, projects, sites, suitability calculations, reports and the Random Forest ML prediction layer.

Run:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

API: `http://127.0.0.1:8000`
Swagger: `http://127.0.0.1:8000/docs`

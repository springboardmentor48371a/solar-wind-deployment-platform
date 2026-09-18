
from contextlib import asynccontextmanager
from typing import Optional
import csv, io

import jwt
from fastapi import Depends, FastAPI, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import re

from database import get_conn, init_db
from auth import create_access_token, decode_token, hash_password, verify_password
from ml_models import predict_site, MODEL_METRICS

ROLES = [
    "Renewable Energy Planner",
    "GIS Analyst",
    "Project Manager",
    "Administrator",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Solar & Wind Deployment Intelligence API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=6, max_length=128)
    role: str = "Renewable Energy Planner"

class LoginRequest(BaseModel):
    email: str
    password: str

class ProjectRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    region: str = Field(min_length=2, max_length=120)
    technology: str = "Hybrid Solar + Wind"

class SiteRequest(BaseModel):
    project_id: int
    name: str = Field(min_length=2, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    region: str
    land_area: float = Field(ge=0)
    elevation: float = Field(ge=-500, le=9000)
    infrastructure: str = "Moderate"
    land_ownership: str = "Private"
    solar_irradiance: float = Field(ge=0, le=10)
    wind_speed: float = Field(ge=0, le=50)
    wind_direction: float = Field(ge=0, le=360)
    temperature: float = Field(ge=-80, le=70)
    rainfall: float = Field(ge=0, le=10000)
    cloud_cover: float = Field(ge=0, le=100)
    slope: float = Field(ge=0, le=90)
    vegetation_index: float = Field(ge=-1, le=1)
    roads_distance: float = Field(ge=0)
    transmission_distance: float = Field(ge=0)
    protected_zone: bool = False
    water_body: bool = False
    agricultural_land: bool = False

def valid_email(email: str):
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email))

def current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid or expired token")
    conn = get_conn()
    user = conn.execute("SELECT id, full_name, email, role, created_at FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(401, "User no longer exists")
    return dict(user)

def score_site(s):
    resource = min(100, (s["solar_irradiance"] / 6.5) * 50 + (s["wind_speed"] / 9.0) * 50)
    geographic = max(0, min(100, 100 - s["slope"] * 4 - s["elevation"] / 80))
    infra_base = {"Excellent": 95, "Good": 80, "Moderate": 60, "Poor": 35}.get(s["infrastructure"], 60)
    infra = max(0, min(100, infra_base - s["roads_distance"] * 1.5 - s["transmission_distance"] * 1.0))
    environmental = 100
    if s["protected_zone"]: environmental -= 55
    if s["water_body"]: environmental -= 20
    if s["agricultural_land"]: environmental -= 15
    environmental = max(0, environmental - max(0, s["vegetation_index"]) * 10)
    economic = max(0, min(100, 100 - s["roads_distance"] * 2 - s["transmission_distance"] * 1.5))
    overall = resource*.35 + geographic*.25 + infra*.15 + environmental*.15 + economic*.10
    category = "Excellent" if overall >= 85 else "Highly Suitable" if overall >= 70 else "Moderately Suitable" if overall >= 55 else "Low Suitability" if overall >= 40 else "Unsuitable"
    solar_output = max(0, s["solar_irradiance"] * s["land_area"] * 0.18 * 365)
    wind_output = max(0, (s["wind_speed"] ** 3) * s["land_area"] * 0.003 * 365)
    return {
        "resource_score": round(resource, 1), "geographic_score": round(geographic, 1),
        "infrastructure_score": round(infra, 1), "environmental_score": round(environmental, 1),
        "economic_score": round(economic, 1), "overall_score": round(overall, 1),
        "category": category,
        "estimated_solar_mwh_year": round(solar_output, 1),
        "estimated_wind_mwh_year": round(wind_output, 1),
        "estimated_total_mwh_year": round(solar_output + wind_output, 1),
        **predict_site(s),
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/register")
def register(body: RegisterRequest):
    if not valid_email(body.email):
        raise HTTPException(400, "Please enter a valid email address")
    if body.role not in ROLES:
        raise HTTPException(400, "Invalid role")
    conn = get_conn()
    existing = conn.execute("SELECT id FROM users WHERE lower(email)=lower(?)", (body.email,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(409, "An account with this email already exists")
    cur = conn.execute(
        "INSERT INTO users(full_name,email,password_hash,role) VALUES(?,?,?,?)",
        (body.full_name.strip(), body.email.lower().strip(), hash_password(body.password), body.role)
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()
    token = create_access_token(user_id, body.role)
    return {"access_token": token, "token_type": "bearer", "user": {"id": user_id, "full_name": body.full_name.strip(), "email": body.email.lower().strip(), "role": body.role}}

@app.post("/auth/login")
def login(body: LoginRequest):
    if not valid_email(body.email):
        raise HTTPException(400, "Please enter a valid email address")
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE lower(email)=lower(?)", (body.email,)).fetchone()
    conn.close()
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(401, "Incorrect email or password")
    token = create_access_token(user["id"], user["role"])
    return {"access_token": token, "token_type": "bearer", "user": {"id": user["id"], "full_name": user["full_name"], "email": user["email"], "role": user["role"]}}

@app.get("/auth/me")
def me(user=Depends(current_user)):
    return user

@app.get("/projects")
def list_projects(user=Depends(current_user)):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM projects WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/projects")
def create_project(body: ProjectRequest, user=Depends(current_user)):
    conn = get_conn()
    cur = conn.execute("INSERT INTO projects(user_id,name,region,technology) VALUES(?,?,?,?)", (user["id"], body.name.strip(), body.region.strip(), body.technology))
    conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)

@app.get("/sites")
def list_sites(project_id: Optional[int]=Query(None), user=Depends(current_user)):
    conn = get_conn()
    if project_id:
        rows = conn.execute("SELECT * FROM sites WHERE user_id=? AND project_id=? ORDER BY id DESC", (user["id"], project_id)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM sites WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
    conn.close()
    return [{**dict(r), **score_site(dict(r))} for r in rows]

@app.post("/sites")
def create_site(body: SiteRequest, user=Depends(current_user)):
    conn = get_conn()
    project = conn.execute("SELECT id FROM projects WHERE id=? AND user_id=?", (body.project_id, user["id"])).fetchone()
    if not project:
        conn.close()
        raise HTTPException(404, "Project not found")
    values = body.model_dump()
    cur = conn.execute("""INSERT INTO sites(
        project_id,user_id,name,latitude,longitude,region,land_area,elevation,infrastructure,land_ownership,
        solar_irradiance,wind_speed,wind_direction,temperature,rainfall,cloud_cover,slope,vegetation_index,
        roads_distance,transmission_distance,protected_zone,water_body,agricultural_land
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        user["id"] and body.project_id, user["id"], values["name"].strip(), values["latitude"], values["longitude"], values["region"],
        values["land_area"], values["elevation"], values["infrastructure"], values["land_ownership"],
        values["solar_irradiance"], values["wind_speed"], values["wind_direction"], values["temperature"],
        values["rainfall"], values["cloud_cover"], values["slope"], values["vegetation_index"],
        values["roads_distance"], values["transmission_distance"], int(values["protected_zone"]),
        int(values["water_body"]), int(values["agricultural_land"])
    ))
    conn.commit()
    row = conn.execute("SELECT * FROM sites WHERE id=?", (cur.lastrowid,)).fetchone()
    conn.close()
    d = dict(row)
    return {**d, **score_site(d)}

@app.get("/sites/{site_id}")
def get_site(site_id: int, user=Depends(current_user)):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sites WHERE id=? AND user_id=?", (site_id, user["id"])).fetchone()
    conn.close()
    if not row: raise HTTPException(404, "Site not found")
    d=dict(row)
    return {**d, **score_site(d)}

@app.get("/dashboard")
def dashboard(user=Depends(current_user)):
    conn = get_conn()
    projects = conn.execute("SELECT COUNT(*) c FROM projects WHERE user_id=?", (user["id"],)).fetchone()["c"]
    sites = [dict(r) for r in conn.execute("SELECT * FROM sites WHERE user_id=?", (user["id"],)).fetchall()]
    conn.close()
    scored = [{**s, **score_site(s)} for s in sites]
    scored.sort(key=lambda x: x["overall_score"], reverse=True)
    avg = round(sum(x["overall_score"] for x in scored)/len(scored), 1) if scored else 0
    total_mwh = round(sum(x["estimated_total_mwh_year"] for x in scored), 1)
    ml_total = round(sum(float(x.get("ml_total_mwh_year", 0)) for x in scored), 1)
    return {"projects": projects, "sites": len(scored), "average_score": avg, "annual_energy_mwh": total_mwh, "ml_annual_energy_mwh": ml_total, "recommended_sites": scored[:5]}

@app.get("/ml/info")
def ml_info(user=Depends(current_user)):
    return {
        "model": MODEL_METRICS["model"],
        "training_rows": MODEL_METRICS["training_rows"],
        "solar_r2": round(MODEL_METRICS["solar_r2"], 3),
        "wind_r2": round(MODEL_METRICS["wind_r2"], 3),
        "solar_mae": round(MODEL_METRICS["solar_mae"], 1),
        "wind_mae": round(MODEL_METRICS["wind_mae"], 1),
        "features": MODEL_METRICS["features"],
        "data_note": MODEL_METRICS["data_note"],
    }

@app.post("/ml/predict")
def ml_predict(body: SiteRequest, user=Depends(current_user)):
    result = predict_site(body.model_dump())
    return {
        "site_name": body.name,
        **result,
        "training_rows": MODEL_METRICS["training_rows"],
        "data_note": MODEL_METRICS["data_note"],
    }

@app.get("/projects/{project_id}/comparison")
def compare_project_sites(project_id: int, user=Depends(current_user)):
    conn = get_conn()
    project = conn.execute("SELECT * FROM projects WHERE id=? AND user_id=?", (project_id, user["id"])).fetchone()
    rows = conn.execute("SELECT * FROM sites WHERE project_id=? AND user_id=? ORDER BY id DESC", (project_id, user["id"])).fetchall()
    conn.close()
    if not project:
        raise HTTPException(404, "Project not found")
    scored = [{**dict(r), **score_site(dict(r))} for r in rows]
    scored.sort(key=lambda x: x["overall_score"], reverse=True)
    for i, site in enumerate(scored, 1):
        site["rank"] = i
    return {"project": dict(project), "sites": scored, "best_site": scored[0] if scored else None}

@app.get("/reports/sites.csv")
def export_sites(user=Depends(current_user)):
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM sites WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()]
    conn.close()
    output=io.StringIO()
    if not rows:
        output.write("No sites yet\n")
    else:
        fields=list(rows[0].keys()) + ["overall_score","category","estimated_total_mwh_year"]
        w=csv.DictWriter(output, fieldnames=fields)
        w.writeheader()
        for r in rows:
            r.update(score_site(r))
            w.writerow({k:r.get(k,"") for k in fields})
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition":"attachment; filename=site-assessment-report.csv"})

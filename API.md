# REST API Documentation

The platform exposes interactive OpenAPI and ReDoc documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

---

## Authentication Endpoints (`/api/v1/auth`)

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Register new user account with role selection |
| `POST` | `/api/v1/auth/login` | Public | OAuth2 form-encoded login returning Bearer token |
| `POST` | `/api/v1/auth/login-json` | Public | JSON-encoded login returning Bearer token |
| `GET` | `/api/v1/auth/me` | Authenticated | Retrieve authenticated user profile and permissions |

---

## Projects Endpoints (`/api/v1/projects`)

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/projects` | Authenticated | List projects with optional technology and status filters |
| `POST` | `/api/v1/projects` | Planner/Manager/Admin | Create a new renewable project |
| `GET` | `/api/v1/projects/{id}` | Authenticated | Get project details and candidate sites count |
| `PUT` | `/api/v1/projects/{id}` | Manager/Admin | Update project details, budget, or capacity |
| `DELETE` | `/api/v1/projects/{id}` | Manager/Admin | Delete project and related site bindings |

---

## Sites Endpoints (`/api/v1/sites`)

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/sites` | Authenticated | List candidate sites with scoring category filters |
| `POST` | `/api/v1/sites` | Analyst/Manager/Admin | Register site, compute boundary, and trigger ML predictions |
| `GET` | `/api/v1/sites/{id}` | Authenticated | Get complete 11-section site evaluation |
| `PUT` | `/api/v1/sites/{id}` | Analyst/Manager/Admin | Update site coordinates, area, or slope |
| `DELETE` | `/api/v1/sites/{id}` | Analyst/Manager/Admin | Remove site |
| `POST` | `/api/v1/sites/compare` | Authenticated | Multi-site side-by-side comparison matrix |

---

## Environmental & GIS (`/api/v1/environment`)

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/environment/layers` | Authenticated | Fetch categorized GeoJSON vector layers |
| `GET` | `/api/v1/environment/heatmap` | Authenticated | Fetch spatial grid tiles of solar and wind potential |
| `GET` | `/api/v1/environment/sites/{id}`| Authenticated | Get environmental factor readings for site |
| `POST` | `/api/v1/environment/collect` | Authenticated | Collect NASA POWER / OpenWeather data |

---

## Machine Learning Endpoints

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/solar/sites/{id}` | Authenticated | Get solar potential prediction and metrics |
| `POST` | `/api/v1/solar/predict` | Authenticated | Predict solar capacity factor from features |
| `POST` | `/api/v1/solar/train` | Analyst/Admin | Retrain Solar GBDT ML pipeline |
| `GET` | `/api/v1/wind/sites/{id}` | Authenticated | Get wind potential prediction and power density |
| `POST` | `/api/v1/wind/predict` | Authenticated | Predict wind capacity factor from features |
| `POST` | `/api/v1/wind/train` | Analyst/Admin | Retrain Wind Random Forest ML pipeline |

---

## Suitability & Optimization Endpoints

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/suitability/sites/{id}` | Authenticated | Get 35/25/15/15/10 suitability score breakdown |
| `POST` | `/api/v1/suitability/calculate` | Authenticated | Calculate suitability with custom weights |
| `GET` | `/api/v1/suitability/ranking` | Authenticated | Get ranked candidate sites with sorting options |
| `POST` | `/api/v1/optimization/recommend`| Authenticated | Run multi-objective optimization with Explainable AI |

---

## Forecasting & Investment Endpoints

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/forecast/sites/{id}` | Authenticated | Daily, monthly, seasonal, or annual forecast |
| `POST` | `/api/v1/forecast/generate` | Authenticated | Custom forecast with dynamic tariff pricing |
| `GET` | `/api/v1/investment/sites/{id}` | Authenticated | 25-year cash flow, LCOE, NPV, and IRR analysis |
| `POST` | `/api/v1/investment/calculate` | Authenticated | Investment analysis with parameter sensitivity |

---

## Reporting Endpoints (`/api/v1/reports`)

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/reports/site` | Authenticated | Export Site Assessment Report (PDF / Excel) |
| `POST` | `/api/v1/reports/solar` | Authenticated | Export Solar Potential Report (PDF / Excel) |
| `POST` | `/api/v1/reports/wind` | Authenticated | Export Wind Potential Report (PDF / Excel) |
| `POST` | `/api/v1/reports/feasibility` | Authenticated | Export Feasibility Report (PDF / Excel) |
| `POST` | `/api/v1/reports/investment` | Authenticated | Export Investment Report (PDF / Excel) |

---

## Admin Endpoints (`/api/v1/admin`)

| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/users` | Administrator | List registered users and roles |
| `GET` | `/api/v1/admin/data-sources` | Administrator | List external dataset ingestion pipelines |
| `PUT` | `/api/v1/admin/data-sources/{id}`| Administrator | Enable or disable data source |
| `POST` | `/api/v1/admin/data-sources/{id}/sync` | Administrator | Trigger data source synchronization |
| `GET` | `/api/v1/admin/system-health` | Administrator | System telemetry, uptime, and ML model status |

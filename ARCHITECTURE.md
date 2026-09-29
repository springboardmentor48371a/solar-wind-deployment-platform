# System Architecture

The **Solar & Wind Deployment Intelligence Platform** is architected using a decoupled, asynchronous microservices-ready structure.

```
React + Vite Frontend (Port 3000)
       | (REST / JWT)
       v
FastAPI REST API Layer (Port 8000)
       |
       +------------------------------------+
       |                                    |
       v                                    v
PostgreSQL + PostGIS 16             MongoDB 7.0 Document Store
(Structured Tables, Geometries)     (Raw Observation Feeds, Audit Logs)
       |
       v
GIS & Spatial Layer (Shapely, Proj)
       |
       +--------------------+--------------------+
       |                    |                    |
       v                    v                    v
Solar ML Engine       Wind ML Engine      Forecasting Engine
(GBDT / RF)           (GBDT / RF)         (Multi-Horizon)
       |                    |                    |
       +--------------------+--------------------+
                            |
                            v
                   Suitability Engine (35/25/15/15/10)
                            |
                            v
               Optimization & Decision Engine
                            |
                            v
               Investment Intelligence (DCF/LCOE)
                            |
                            v
             ReportLab & OpenPyXL Export Layer
```

## Layer Responsibilities

1. **Presentation Layer (React 18 SPA)**:
   - Client-side routing with role-based route guards (`ProtectedRoute`, `AdminRoute`).
   - Interactive Leaflet mapping with layer control switches and color-coded vector pins.
   - Recharts visual analytics for generation profiles and discounted cash flows.

2. **API & Business Logic Layer (FastAPI)**:
   - Dependency injection for database sessions, JWT verification, and RBAC permission checks.
   - Pydantic v2 schemas validating request/response serialization.
   - Asynchronous request lifecycle with synchronous worker execution for CPU-bound ML tasks.

3. **Spatial & Environmental GIS Layer**:
   - Geodesic Haversine calculations computing proximity to high-voltage transmission lines, substations, and major access roads.
   - Polygon boundary generation and spatial overlay with environmental exclusion buffers (wildlife sanctuaries, wetlands).

4. **Machine Learning Pipeline**:
   - Training pipeline with Scikit-learn pipelines and train/test splits.
   - Metric tracking: Root Mean Squared Error (RMSE), Mean Absolute Error (MAE), and Coefficient of Determination ($R^2$).
   - Persistent `.joblib` model artifacts stored in `backend/app/ml/artifacts/`.

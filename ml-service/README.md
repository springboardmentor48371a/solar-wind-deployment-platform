# ML Service — Scoring Reference

This document explains every score the ML service computes, what inputs it uses, and the exact formula behind each one.

---

## 1. Solar Score

**File:** `app/services/solar.py`  
**Model:** Random Forest regressor (`solar_model.pkl`, R² = 0.79)  
**Output range:** 0 – 100

The model predicts a **capacity factor** (0–1), which represents how much of the theoretical maximum power the site produces on average.

### Features fed to the model

| Feature | Description |
|---|---|
| `solar_irradiance` | Daily insolation ÷ 24 (converts kWh/m²/day → mean hourly kW/m²) |
| `temperature_avg` | Ambient temperature (°C) |
| `cloud_cover` | Cloud cover (%) |
| `temp_delta` | Module temp rise above ambient — estimated as `(1 - cloud_cover/100) × 15` |
| `sin_time`, `cos_time` | Cyclic encoding of current UTC hour |
| `inv_perf` | Inverter performance proxy: `(1 - cloud_cover/100) × min(irradiance/0.6, 1)` |
| `irr_lag_1`, `irr_lag_2`, `irr_roll_mean` | Lag/rolling irradiance — current value used as proxy (no history at prediction time) |

### Score formula

```
capacity_factor  = model.predict(features)          # clipped to [0, 1]
solar_yield_kwh  = capacity_factor × 24             # daily energy output proxy
solar_score      = min(capacity_factor / 0.25 × 100, 100)
```

A capacity factor of 0.25 (25%) is treated as the benchmark for a fully suitable solar site (score = 100). Sites above 25% are capped at 100.

---

## 2. Wind Score

**File:** `app/services/wind.py`  
**Model:** Gradient Boosting regressor (`wind_model.pkl`, R² = 0.96)  
**Output range:** 0 – 100

The model predicts **power output in kW** for a reference 2 MW turbine (rotor radius = 41 m).

### Features fed to the model

| Feature | Description |
|---|---|
| `wind_speed` | 10 m wind speed (m/s) |
| `wind_speed_cubed` | `wind_speed³` — direct proportional to kinetic energy |
| `theoretical_power` | Betz-limit estimate: `0.5 × 1.225 × π × 41² × v³ / 1000` (kW) |
| `sin_wind_dir`, `cos_wind_dir` | Cyclic encoding of wind direction |
| `sin_hour`, `cos_hour` | Cyclic encoding of current UTC hour |
| `month` | Calendar month (1–12) |
| `wind_speed_lag_1`, `wind_speed_roll_mean` | Lag/rolling wind speed — current value used as proxy |

### Score formula

```
power_kw = model.predict(features)

# If model returns negative (below cut-in speed ~9 m/s), fall back to Betz curve:
power_kw = max(0, 0.35 × 0.5 × 1.225 × π × 41² × v³ / 1000)

capacity_factor = min(power_kw / 2000, 1.0)        # rated at 2 MW
wind_score      = min(capacity_factor / 0.45 × 100, 100)
```

A capacity factor of 0.35 (35%) is the benchmark for a fully suitable wind site (score = 100).

---

## 3. Land Cover Score

**File:** `app/services/land_cover.py`  
**Model:** Random Forest classifier (`land_cover_model.pkl`, accuracy = 81%)  
**Output range:** 0 – 100

The model classifies land into one of 5 classes and returns class probabilities.

### Classes

`vegetation`, `urban`, `barren`, `water`, `cropland`

### Features fed to the model

| Feature | Source |
|---|---|
| `ndvi` | NDVI proxy computed from rainfall, temperature, irradiance, cloud cover |
| `slope_deg` | Computed from 4-point OpenTopoData elevation grid |
| `elevation` | metres above sea level |

### Score formula

```
score = (P(vegetation) × 100 + P(barren) × 60) − (P(urban) × 80 + P(water) × 100)
score = clamp(score, 0, 100)
```

- Vegetation and barren land are good for deployment (open, buildable)
- Urban land is penalised (permitting difficulty, existing structures)
- Water is heavily penalised (not buildable)
- Cropland has no explicit term — it contributes 0 (neutral)

---

## 4. Infrastructure Score

**File:** `backend/app/services/infrastructure.py`  
**Method:** Nominatim reverse geocode (OpenStreetMap)  
**Output range:** 0 – 100

Queries the nearest OSM feature at the site coordinates and scores based on road type. Power infrastructure score is inferred from road quality (they are strongly correlated).

### Road type → road score

| Road type | Score |
|---|---|
| motorway | 100 |
| trunk | 95 |
| primary | 90 |
| secondary | 75 |
| tertiary | 60 |
| unclassified | 40 |
| residential | 35 |
| track | 15 |
| path | 10 |
| footway | 5 |
| no road found | 10 |

### Score formula

```
power_score         = min(road_score + 10, 100)
infrastructure_score = (road_score + power_score) / 2
```

Fallback: if the API request fails for any reason, `infrastructure_score = 50.0`.

---

## 5. Geographic Score

**File:** `ml-service/app/services/suitability.py` → `_geographic_score()`  
**Method:** Rule-based  
**Output range:** 0 – 100

### Component breakdown

| Component | Weight | Formula |
|---|---|---|
| Slope score | 50% | `max(0, 100 − (slope_deg / 15) × 100)` |
| Elevation score | 30% | `max(0, 100 − (elevation / 2000) × 100)` |
| Aspect score | 20% | See table below |

### Aspect score (solar sites only)

| Facing direction | Aspect range | Score |
|---|---|---|
| South-facing | 135° – 225° | 100 |
| East / West | 45° – 135° or 225° – 315° | 60 |
| North-facing | 0° – 45° or 315° – 360° | 20 |
| Wind / Hybrid sites | — | 70 (neutral) |

### Final formula

```
geographic_score = slope_score × 0.5 + elevation_score × 0.3 + aspect_score × 0.2
```

---

## 6. Economic Score

**File:** `ml-service/app/services/suitability.py` → `_economic_score()`  
**Method:** Rule-based  
**Output range:** 0 – 100

### Component breakdown

| Component | Max pts | Formula |
|---|---|---|
| Land ownership | 40 | See table below |
| Terrain cost | 40 | `40 − slope_penalty − elevation_penalty` |
| Resource ROI | 20 | `(resource_score / 100) × 20` |

### Land ownership points

| Ownership type | Points |
|---|---|
| government | 40 |
| community | 30 |
| private | 20 |
| unknown | 10 |

### Terrain cost formula

```
slope_penalty     = min(slope_deg / 15, 1.0) × 20      # max 20pt penalty
elevation_penalty = min(elevation / 2000, 1.0) × 20    # max 20pt penalty
terrain_pts       = max(0, 40 − slope_penalty − elevation_penalty)
```

### Final formula

```
economic_score = ownership_pts + terrain_pts + resource_pts   (capped at 100)
```

---

## 7. Overall Suitability Score

**File:** `ml-service/app/services/suitability.py` → `predict_suitability()`  
**Output range:** 0 – 100

### Resource score (input to suitability)

| Energy type | Resource score |
|---|---|
| solar | `solar_score` |
| wind | `wind_score` |
| hybrid | `(solar_score + wind_score) / 2` |

### Weighted final formula

```
suitability_score = resource_score      × 0.35
                  + geographic_score    × 0.25
                  + infrastructure_score × 0.15
                  + environmental_score × 0.15   ← land_cover_score
                  + economic_score      × 0.10
```

### Suitability categories

| Score range | Category |
|---|---|
| ≥ 80 | Excellent |
| 65 – 79 | Highly Suitable |
| 50 – 64 | Moderately Suitable |
| 35 – 49 | Low Suitability |
| < 35 | Unsuitable |

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

# If model returns negative, fall back to Betz curve
# (the SCADA-trained model predicts negative at low wind speeds where
# the turbine is below cut-in — no explicit cut-in constant is used;
# the fallback simply floors at 0):
# A = π × r²  where r = 41 m (rotor radius)
power_kw = max(0, 0.35 × 0.5 × 1.225 × (π × 41²) × v³ / 1000)

capacity_factor = min(power_kw / 2000, 1.0)        # rated at 2 MW
wind_score      = min(capacity_factor / 0.35 × 100, 100)
```

Note: rotor area is `π × r²` (not `π × d²`). The `theoretical_power` training feature uses the same formula with an additional `/ 4` term in the code (`41² × π / 4`) because that implementation uses diameter rather than radius — both resolve to the same physical area.

A capacity factor of 0.35 (35%) is the benchmark for a fully suitable wind site (score = 100). Sites above 35% CF are capped at 100. This aligns with the commonly cited 30–40% range for good onshore wind sites in siting literature.

---

## 3. Land Cover Score

**File:** `app/services/land_cover.py` + `app/services/earth_engine.py`  
**Model:** XGBoost classifier (`land_cover_model.pkl`)  
**Output range:** 0 – 100

### Model details

| Property | Value |
|---|---|
| Algorithm | XGBoost classifier (joblib format) |
| Input features | 8 — see table below, order is fixed |
| Output classes | cropland, forest, grassland, urban, water, barren |
| Training data | ESA WorldCover v200 labels — stratified global sample, 3,000 points (500/class). Real per-point features from Sentinel-2 annual median composite (NDVI, NDBI, texture), Copernicus GLO-30 DEM (elevation, slope), and VIIRS night lights. Not region-specific. |
| Label encoding | cropland=0, forest=1, grassland=2, urban=3, water=4, barren=5 — fixed at training time, not alphabetical |
| Overall test accuracy | 78% |

### Feature order (must match exactly)

| # | Feature | Source | Notes |
|---|---|---|---|
| 1 | `ndvi` | Sentinel-2 B8/B4 annual median | |
| 2 | `ndbi` | Sentinel-2 B11/B8 annual median | Normalised Difference Built-up Index |
| 3 | `elevation` | Copernicus GLO-30 DEM | metres |
| 4 | `slope_deg` | Derived from GLO-30 | degrees |
| 5 | `ndvi_seasonal_std` | Std dev of 4 quarterly NDVI composites | |
| 6 | `ndvi_seasonal_amplitude` | max(quarterly NDVI) − min(quarterly NDVI) | |
| 7 | `ndvi_texture` | GLCM contrast on annual NDVI × 10000, window=3 | |
| 8 | `night_lights_log` | `log1p(VIIRS avg_rad)` | **log transform must be applied before inference** |

### Per-class accuracy

| Class | Recall | Notes |
|---|---|---|
| water | 98% | Most reliable class |
| barren | 93% | Strong separation |
| urban | 87% | Improved from ~53% in the 3-feature model — NDBI + night lights resolved most urban misclassification |
| forest | 76% | Some leakage into cropland at forest’s lower-NDVI tail |
| cropland | 67% | Overlaps with grassland and barren |
| grassland | 47% | Weakest class — confused with cropland and forest. Single annual NDVI composite + terrain cannot fully separate these. |

**Known remaining limitation:** grassland/cropland/forest boundary confusion is a ceiling of this feature set. Improving it requires multi-season temporal NDVI stacks or additional spectral indices.

**Previously tried and ruled out** (do not re-attempt without reading this first):
- EuroSAT — Europe-only domain mismatch, no real terrain features
- Globe230k — multimodal dataset hosted on Baidu Wangpan, not downloadable
- Brazil crop-rotation NDVI time series — crop-type labels, not land-cover labels (wrong taxonomy)
- NDBI alone (3-feature model) — did not cleanly separate urban at 30 m resolution; WorldCover’s “Built-up” class includes low-density/mixed-pixel settlements that dilute the NDBI signal

### Live feature extraction (Earth Engine)

Production predictions use live Sentinel-2/VIIRS/DEM data fetched from Google Earth Engine via a service account, not the old climate-derived NDVI proxy.

**Date-range policy:** rolling 12-month window ending on the prediction date (today − 365 days → today). Differs from the fixed 2023 training window but is correct for production — the model is globally sampled and not year-sensitive.

**Caching:** EE features are cached per site for **90 days** (`ee_features_fetched_at` column in the `land_cover` table). Land cover changes on a timescale of years; re-querying EE on every prediction would be wasteful and slow.

**Fallback:** if `GEE_SERVICE_ACCOUNT`/`GEE_KEY_FILE` are not configured, or if EE initialisation fails, or if the model file is missing, the service falls back to the previous rule-based NDVI+slope classifier and logs a warning. Email/password login and all other platform features work normally without EE configured.

**Service account setup:**
1. Go to [console.cloud.google.com](https://console.cloud.google.com) → IAM & Admin → Service Accounts
2. Create a service account and grant it Earth Engine access
3. Generate a JSON key file — save it outside the repo, never commit it
4. Register the service account at [code.earthengine.google.com](https://code.earthengine.google.com)
5. Set `GEE_SERVICE_ACCOUNT`, `GEE_KEY_FILE`, and optionally `GEE_PROJECT` in `.env`

### Score formula

Probability-weighted across all 6 classes (Ayodele et al. 2018; Wolaita AHP-GIS Sci Reports 2023; Prieto-Amparán et al. 2021; Burundi F-AHP Frontiers 2024; GIS-agrovoltaics 2026):

```
score = P(grassland) × 100
      + P(cropland)  ×  90
      + P(barren)    ×  60
      − P(forest)    ×  40
      − P(urban)     ×  80
      − P(water)     × 100
score = clamp(score, 0, 100)
```

| Class | Weight | Rationale |
|---|---|---|
| grassland | +100 | Dominant land type in “most suitable” tier across all siting studies reviewed |
| cropland | +90 | Highly suitable per GIS-MCDA literature across both solar and wind |
| barren | +60 | Open buildable land; usable, not preferred |
| forest | −40 | Soft penalty — 76% recall means some cropland leaks here; not a hard exclusion |
| urban | −80 | Strong exclusion; 87% recall makes this reliable |
| water | −100 | Hard exclusion; 98% recall — most trustworthy penalty |

### Fallback (rule-based)

If EE is unavailable or the model fails to load, a rule-based NDVI+slope classifier is used with fixed per-class scores. A warning is logged. The fallback is never used in normal operation.

---

## 4. Infrastructure Score

**File:** `backend/app/services/infrastructure.py`  
**Method:** Nominatim reverse geocode (road) + Overpass API (grid proximity)  
**Output range:** 0 – 100

Scores two independent components and averages them. Each component falls back to 50.0 independently if its API call fails.

### Road accessibility score

Queries the nearest OSM feature at the site coordinates via Nominatim at zoom=17 and scores based on road type.

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
| API failure | 50 (fallback) |

### Grid proximity score

Queries OSM power infrastructure tags (`power=line`, `power=minor_line`, `power=substation`, `power=tower`) via the Overpass API within a **25 km search radius**. Scores based on Haversine distance to the nearest matched feature using a linear decay curve.

| Distance to nearest grid feature | Score |
|---|---|
| 0 – 5 km | 100 |
| 5 – 20 km | Linear decay: `100 − ((d − 5) / 15) × 80` |
| > 20 km or no feature found | 20 (floor) |
| API failure | 50 (fallback) |

The 5–20 km range reflects the wind-siting literature treatment of grid connection distance as a key feasibility factor.

### Final formula

```
infrastructure_score = (road_score + power_score) / 2
```

Fallback: if an individual API request fails, that half defaults to 50.0. If both fail, `infrastructure_score = 50.0`.

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

### Aspect score

**Solar sites**

| Facing direction | Aspect range | Score |
|---|---|---|
| South-facing | 135° – 225° | 100 |
| East / West | 45° – 135° or 225° – 315° | 60 |
| North-facing | 0° – 45° or 315° – 360° | 20 |

**Wind sites** (uses prevailing `wind_direction` from averaged NASA POWER `WD10M` records)

Scored by angular difference between slope aspect and prevailing wind direction. An upwind-facing slope accelerates airflow over the ridge (favorable); a lee-facing slope creates turbulence and wind shadow (unfavorable).

| Angular difference (aspect vs wind direction) | Score |
|---|---|
| ≤ 45° (slope faces into prevailing wind) | 100 |
| 45° – 90° | 70 |
| 90° – 135° | 40 |
| > 135° (slope faces away from wind) | 10 |

Fallback to 70 (neutral) if `wind_direction` or `aspect_deg` is unavailable.

**Hybrid sites** — 70 (neutral)

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
| hybrid | `sqrt(solar_score × wind_score)` — geometric mean |

The geometric mean is used for hybrid (not arithmetic) to prevent a strong score in one resource from fully compensating a weak score in the other. A site with solar=90, wind=10 scores 30 geometrically vs 50 arithmetically — the same reasoning the UN HDI adopted when it switched from arithmetic to geometric mean in 2010 to eliminate perfect substitutability between dimensions.

### Weighted final formula — deployment-type-specific

Each deployment type uses a different weight set derived from a dedicated AHP siting study. Applying one universal formula to all site types was the original bug this corrects.

#### Wind sites

Source: Frontiers in Energy Research (2024) — "Wind farm site selection using GIS-based mathematical modeling and fuzzy logic tools: a case study of Burundi"  
https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2024.1353388/full

```
suitability_score (wind) = resource_score       × 0.36
                         + geographic_score     × 0.31
                         + infrastructure_score × 0.19
                         + environmental_score  × 0.04
                         + economic_score       × 0.10
```

| Factor | Weight | Basis |
|---|---|---|
| Resource | 36% | Resource availability is the dominant criterion |
| Geographic | 31% | Slope + aspect + elevation cluster (24% + 7.3% + 4%) |
| Infrastructure | 19% | Grid proximity + road distance (13% + 8%) |
| Environmental | 4% | Smallest weight — land use is secondary once resource, terrain, and infrastructure are accounted for |
| Economic | 10% | No economic criterion in source study; retained from platform baseline |

#### Solar sites

Source: ISPRS International Journal of Geo-Information (2025, open access) — "Integrating Remote Sensing and Geospatial-Based Comprehensive Multi-Criteria Decision Analysis Approach for Sustainable Coastal Solar Site Selection in Southern India" (Thoothukudi, Tamil Nadu)  
https://www.mdpi.com/2220-9964/14/10/377

```
suitability_score (solar) = resource_score       × 0.43
                          + geographic_score     × 0.19
                          + infrastructure_score × 0.16
                          + environmental_score  × 0.12
                          + economic_score       × 0.10
```

| Factor | Weight | Basis |
|---|---|---|
| Resource | 43% | Source: Photovoltaic 28% + Climatic 20% = 48%, scaled to 43% after adding 10% economic |
| Geographic | 19% | Source: Topographic 21%, scaled proportionally |
| Infrastructure | 16% | Source: Accessibility 18%, scaled proportionally |
| Environmental | 12% | Source: Environmental 13%, scaled proportionally |
| Economic | 10% | No economic criterion in source study; retained from platform baseline |

Note: the source study's five categories were scaled proportionally to accommodate this platform's existing 10% economic weight, preserving the relative ranking of the other four factors.

#### Hybrid sites ⚠️ interim weights

> **These weights are NOT backed by a dedicated hybrid solar-wind AHP siting study.** No such study was found during the research process for this platform. The values below are the arithmetic average of the wind and solar weight sets above, used as a reasonable interim approximation. If a hybrid-specific AHP siting study is found, replace these weights rather than leaving the average in place long-term.

```
suitability_score (hybrid) = resource_score       × 0.40
                           + geographic_score     × 0.25
                           + infrastructure_score × 0.18
                           + environmental_score  × 0.08
                           + economic_score       × 0.10
```

### Suitability categories

| Score range | Category |
|---|---|
| ≥ 80 | Excellent |
| 65 – 79 | Highly Suitable |
| 50 – 64 | Moderately Suitable |
| 35 – 49 | Low Suitability |
| < 35 | Unsuitable |

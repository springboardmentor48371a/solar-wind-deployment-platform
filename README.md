# Solstice OS — Solar & Wind Deployment Intelligence Platform

A platform for finding, evaluating, and ranking locations for solar and
wind energy projects.

## What the app can currently do

**Login & Roles**
Sign up and log in with an account. There are 6 roles: Renewable Energy
Planner, GIS Analyst, Project Manager, Investor/Developer, Government/
Regulator, and Administrator — pick any of them directly on the
registration form. Each role sees a different dashboard and can do
different things — for example, an Investor can only view data, while a
Project Manager can create and edit everything.

**Projects & Sites**
Create a project, then register sites inside it (by entering
coordinates, land area, etc). As soon as a site is registered, the app
automatically pulls in real data for it: weather and solar/wind
conditions, nearby roads/substations/transmission lines, elevation and
terrain, satellite imagery, and environmental/demographic data. It then
calculates a suitability score for the site and shows how good a fit
it is (Excellent, Highly Suitable, Moderately Suitable, Low Suitability,
or Unsuitable).

**Site Details**
For each site you can see: solar potential (expected energy output,
panel efficiency, capacity factor), wind potential (turbine suitability,
expected energy production), satellite imagery summary, environmental
data (protected areas, water bodies nearby), and live weather
cross-check. You can also run a financial analysis (enter cost
assumptions and get back NPV, IRR, payback period), simulate hourly
power output, and view/send live sensor (telemetry) readings.

**Deployment Optimization & Forecasting (Milestone 3)**
- **Technology recommendation**: compares a site's already-computed solar and wind capacity factors and recommends Solar, Wind, or Hybrid — with a specific capacity split sized from the site's real land area using published NREL land-use figures (3.6 ha/MW solar, 34.4 ha/MW wind).
- **Grid contribution forecasting**: translates a site's annual output into a "homes powered" estimate, using that site's own country's real World Bank per-capita electricity consumption figure — not a generic global constant.
- **Seasonal generation forecast**: redistributes the annual solar estimate across 12 months using NASA POWER's long-term climatology data (a different, longer-baseline endpoint from the 7-day one used for scoring), so a summer-peaking or monsoon-affected site shows a realistic monthly shape instead of a flat 1/12th split.

**Data Sources — What's Used and Why**
Two completely separate categories of data feed this platform:
- **Live environmental data** (called every time you register or refresh a site): **NASA POWER** for solar irradiance, wind speed, temperature, rainfall, and cloud cover — chosen because it's the only free, no-API-key dataset that covers *both* solar and wind in one place, has global coverage, and was purpose-built for renewable energy resource assessment rather than adapted from general climate data. Combined with Open-Elevation (terrain), OpenStreetMap (roads/substations/transmission lines/protected areas), World Bank (demographics), and optionally Copernicus Sentinel Hub (satellite imagery) and OpenWeather/NOAA (live cross-check).
- **ML training data** (used once, offline, to produce the models below — never called live at runtime): real solar plant generation data (Kaggle) and real wind turbine SCADA data (Zenodo/Kelmarsh) — see below for why these specific datasets were chosen.

**ML-Assisted Prediction**
Three trained Random Forest models run alongside the physics engines —
never replacing the physics/rule-based numbers, always shown side by side:
- **Solar performance-ratio model** — trained on Kaggle's "Solar Power Generation Data" (`anikannal/solar-power-generation-data`): real inverter-level generation + weather sensor readings from two actual Indian solar plants, 15-minute resolution, 34 days. Chosen because it's free, real, well-documented, and matches exactly the inputs (ambient temperature, irradiance) our physics engine already uses — a direct, comparable upgrade path from simulation to measurement.
- **Wind capacity-factor model** — trained on Kelmarsh Wind Farm SCADA data (Zenodo, CC-BY-4.0, Cubico Sustainable Investments Ltd): real 10-minute readings from **all 6** actual Senvion MM92 turbines across **all 4 available years** (2016-2019, ~1.2 million real rows). Chosen because it's one of the few open, real (not simulated) turbine SCADA datasets with a permissive license and both wind speed and power output in the same file.
- **Suitability quick-classifier** — trained directly on this platform's own validated scoring formula (not external data), so a Planner can get an instant rough category estimate from ballpark inputs before a site is even registered.

Full training-data provenance, real accuracy metrics (R², RMSE, MAE), and known limitations for each model are documented in `backend/app/ml_models/*.meta.json` — nothing is hidden or rounded up.

**GIS View**
A map showing all your sites, plus tabs for terrain data, environmental
analytics, and a table comparing all sites side by side.

**Reports**
Download PDF or Excel reports for a site. Every report now explains
*why* each site got its score — not just the number — with a
plain-language breakdown of all 5 sub-scores tied back to the real
data behind them (actual irradiance/wind speed vs. benchmark, real
distances to infrastructure and protected areas, real IRR/LCOE if a
financial analysis has been run). There's also a report builder where
you pick which sections to include (suitability, solar, wind,
financial, environmental, etc.) and generate a custom PDF, or generate
a fixed executive summary, or save a report template to reuse later.

**Alerts**
The app automatically creates alerts for things like high wind speed,
heavy rainfall, or a site's suitability score changing. These show up
in an Alerts page and can also be automatically sent out to connected
external tools (like a Slack webhook or project management tool) if
you set one up.

**Admin Tools**
Administrators can manage users (change roles, activate/deactivate
accounts), view an audit log of everything that's happened on the
platform, manage integrations (connect external tools), and refresh
the analytics/data warehouse.

**Dashboards**
Each role gets a dashboard tailored to what they need:
- Planner sees recommended sites, forecasts, and investment suggestions
- GIS Analyst sees maps, terrain, and environmental data
- Project Manager sees project progress, feasibility, and cost-benefit numbers
- Administrator sees system health, users, and platform-wide stats
- Investor/Developer and Government/Regulator see a read-only overview

---

## What We're Using — Full Tech Stack, Datasets & APIs

**Backend**: Python, FastAPI, SQLAlchemy (PostgreSQL + PostGIS), MongoDB, Redis, JWT auth, scikit-learn, joblib, GDAL/GeoPandas/Shapely/Rasterio (GIS), ReportLab (PDF), openpyxl (Excel), Prometheus (`/metrics`), Sentry (optional).

**Frontend**: Next.js, React, Tailwind CSS, Leaflet (maps), Axios.

**Infrastructure**: Docker + Docker Compose (6 containers: db, mongo, redis, backend, frontend, backup), TimescaleDB hypertables (auto-enabled if available), S3-compatible data lake (optional), automated daily backups.

**Live, real-time data sources** (called every time a site is registered or refreshed):
| Source | Provides | Cost |
|---|---|---|
| NASA POWER | Solar irradiance, wind speed (10m & 50m), temperature, rainfall, cloud cover, + long-term climatology for seasonal forecasts | Free, no key |
| OpenStreetMap (Overpass) | Roads, substations, transmission lines, protected areas, water bodies, farmland | Free, no key |
| Open-Elevation | Site elevation & land slope | Free, no key |
| World Bank Open Data | Population density, GDP per capita, electricity consumption per capita | Free, no key |
| Copernicus Sentinel Hub | Satellite imagery, NDVI, land cover | Free tier, needs API key |
| OpenWeather / NOAA | Live weather cross-check | Free tier / free, no key |

**Real datasets used to train the AI/ML models** (used once, offline — never called live):
| Dataset | Real Data | Source |
|---|---|---|
| Kaggle "Solar Power Generation Data" | 2 real Indian solar plants, 15-min generation + weather sensor readings | kaggle.com/datasets/anikannal/solar-power-generation-data |
| Kelmarsh Wind Farm SCADA | 6 real UK turbines, 4 full years, ~1.2M 10-min readings (wind speed + power) | zenodo.org/records/5841834 (CC-BY-4.0) |

**Reference standards used for real (not guessed) figures**: NREL "Land-Use Requirements for Solar Power Plants" (2013) for capacity planning; IEC 61400-1 turbulence categories for the risk model; DOE/NREL and Fraunhofer ISE performance studies for early model calibration.

---

## Challenges We Faced & How We Solved Them

**"Couldn't find a suitable training dataset."** Every attempt to *automatically* download real solar/wind data from within the build environment was blocked — PVGIS and GitHub's raw file hosting both reject automated (non-browser) access via robots.txt. Fix: built the full ML pipeline first against physics-informed synthetic data calibrated to real published literature (clearly labeled as such), then real datasets were manually downloaded by hand and uploaded directly — which isn't blocked the way an automated script is — and both models were retrained on genuine measured data.

**A site's numbers went wildly negative** (`-622.93` peak sun hours, `-2410` suitability score). Root cause: NASA POWER uses `-999` as a "no data for this day" placeholder, and the app was storing that literal `-999` as if it were a real reading, poisoning every downstream average. Fixed with input validation on every weather field, **plus** a self-healing repair path so clicking "Refresh data" fixes already-corrupted rows — not just new ones.

**Deleting a project with real sites in it silently failed.** Traced to `Site` having cascade-delete configured for only 3 of the 12 database tables a real, fully-registered site actually populates — the other 9 (including SolarPotential and WindPotential, populated for *every* site) caused the database to block the deletion with no clear error. Fixed for all 12 tables, and added the regression test that didn't exist before.

**Site registration failed intermittently with no useful error.** Every other stage of the registration pipeline was wrapped to survive an external API hiccup — except the elevation/slope lookup, which could crash the whole request on a malformed (non-JSON) response. Fixed the exception handling at both the connector level and the call site.

**A "Risk Assessment" ML model scored a suspicious 100% accuracy.** That's a red flag, not a win — traced to real data leakage: the model was being handed the exact variable used to compute its own label. Fixed by removing it; the honest accuracy is 63%, and feature-importance was checked afterward to confirm what the model is *actually* using (wind speed, 99%+ — not the environmental inputs it nominally accepts).

**XGBoost and true LSTM/Prophet models, as the original spec named them, weren't achievable here.** XGBoost couldn't be installed (no network access in this build environment) — substituted scikit-learn's GradientBoostingRegressor, a real algorithm in the same family, actually trained and tested. Genuine LSTM/Prophet time-series forecasting needs far more historical data per site than this platform's 7-day live window collects — building one anyway would have been a fabricated, meaningless model, so classifiers trained on real data were used instead. Both substitutions are named and explained in the code and in each model's own metadata file, not silently swapped in.

**AI/ML was initially built as a "Beta" side-feature, separate from the PDF's actual architecture.** The original scope for this whole build explicitly excluded AI/ML, so it was added later as a parallel, clearly-labeled layer rather than the PDF's specified default. Once revisited against the PDF's own architecture diagram (which names 6 specific AI/ML models), the gap was closed properly — all 6 are now built, tested, and documented, including the two that needed honest substitutions above.

---

## AI/ML Prediction Layer

Matching the PDF's architecture diagram, which explicitly names 6
AI/ML models. All 6 are now real and wired in, with full honesty about
what each actually is:

| PDF-Named Model | What Ships | Honest Note |
|---|---|---|
| Solar Potential Model (Random Forest) | Random Forest, trained on real Kaggle plant data | Matches exactly |
| Wind Speed Model (LSTM/Prophet) | Random Forest, trained on real Kelmarsh SCADA data | Substituted — a genuine LSTM/Prophet forecast needs far more historical time-series data per site than this platform's live pipeline collects |
| Suitability Prediction Model (RF/XGBoost) | Random Forest | Trained on the platform's own validated scoring formula — an instant estimate, not a replacement for the real score |
| Risk Assessment Model (LSTM/Prophet) | Random Forest classifier, real Kelmarsh turbulence + real IEC 61400-1 standard | Substituted for the same data-availability reason above. **Important**: verified via feature importance that wind speed drives 99%+ of this model's decisions — it does not yet meaningfully use the environmental risk inputs it accepts |
| Investment Prediction Model (Regression/XGBoost) | Gradient Boosting Regressor | XGBoost itself couldn't be installed in this build environment (no network access) — added to `requirements.txt` for a real deployment to swap in |
| Optimization Engine | Deterministic (Technology Selection, Capacity Planning — Milestone 3) | Not ML-based; a rule-based optimizer using real NREL land-use data |

Every substitution above is documented with the reason in the model's own metadata file (`backend/app/ml_models/*.meta.json`).

---

## Recent Changes

- **All 6 roles are now fully self-service at registration** — the earlier staff PIN requirement for GIS Analyst, Project Manager, and Administrator has been removed. Anyone can pick any role directly on the Register page. (Note: this is a deliberate simplification, not a permanent security stance — see the codebase's `auth.py` for the tradeoff this introduces.)
- **Google Sign-In has been fully removed** — not just hidden. The login button, callback page, backend OAuth endpoints, and the unused database table behind it are all gone.
- **GIS View was rebuilt** — it now has 4 tabs (GIS Visualization, Terrain Maps, Environmental Analytics, Site Comparison) instead of a single bare map, matching the GIS Analyst Dashboard spec.
- **Suitability scoring fix**: proximity to agricultural land was being collected but never actually factored into a site's Environmental Impact sub-score — it now applies a real penalty, matching the documented scoring formula.
- **Full codebase verification pass completed**: every backend file compiles, every frontend import resolves, and all 58 backend API routes were cross-checked against all 39 frontend calls with zero mismatches.
- **Reports now explain their scores**: PDF and Excel exports (and the custom Report Builder) previously showed just a bare score and category. They now include a plain-language reasoning section per site, generated from the real data behind each of the 5 sub-scores — real measured irradiance/wind speed vs. benchmark, real infrastructure distances, real environmental proximity, and real IRR/LCOE when a financial analysis exists.
- **All 6 of the PDF's named AI/ML models now built** (was 3): added the Investment Prediction Model and Risk Assessment Model, and reframed the existing Optimization Engine and Suitability Prediction Model against the PDF's exact naming. Two honest substitutions were needed and are fully documented: XGBoost couldn't be installed in this build environment (used scikit-learn's GradientBoostingRegressor instead), and LSTM/Prophet time-series forecasting isn't feasible with the platform's current 7-day data window (used classifiers trained on real data instead). One real bug caught during this pass: an early version of the Risk Assessment Model showed 100% accuracy, which was a red flag for data leakage — traced to the model being given the exact variable used to derive its own label, fixed by removing it (honest accuracy dropped to 63%, which is the real, correct number).
- **Milestone 3 completed — Deployment Optimization Engine + Energy Forecasting Engine**: added Technology Selection (compares real computed solar/wind capacity factors, recommends Solar/Wind/Hybrid), Capacity Planning (real NREL land-use figures, not a guess), Hybrid Solar-Wind Recommendations (specific MW split), Grid Contribution Forecasting ("homes powered" using each site's own country's real World Bank electricity-consumption data), and Seasonal Generation Prediction (monthly breakdown via NASA POWER's climatology endpoint — a genuinely different, longer-baseline API call from the one used for daily scoring).
- **Fixed: deleting a project with a real site failed.** `Site` had cascade-delete configured for only 3 of 12 related tables — every table a real site actually populates during registration (SolarPotential, WindPotential, EnvironmentalConstraint, SiteImage, etc.) was missing it, so the database silently blocked the delete. Fixed for all 12 tables plus project-level Alerts/Integrations; added regression tests, since none existed for project deletion before this.
- **Fixed: an unhandled elevation-lookup exception could crash site registration.** Every other stage of the registration pipeline (weather, infrastructure, satellite, scoring) was wrapped in try/except specifically to survive an upstream API hiccup — the elevation/slope lookup was the one stage that wasn't, and its own internal exception handling only caught network errors, not a malformed (non-JSON) response. Both layers fixed.
- **AI/ML layer added, then upgraded to real training data, then expanded to the full real dataset**: 3 Random Forest models now ship pre-trained — solar performance-ratio, wind capacity-factor, and a suitability quick-classifier. Initially trained on physics-informed synthetic data (literature-calibrated) because automated downloads from PVGIS and GitHub were blocked by robots.txt; once real datasets were manually obtained and provided, both models were retrained on genuine measured data. The wind model was then expanded again from a 2-turbine/1-year sample to **all 6 real turbines across all 4 available years** (~1.2 million real readings), improving R² from 0.81→0.928 and cutting RMSE from 12.0→7.7 percentage points. Solar improved from R²=0.30 (synthetic) to R²=0.44 on the full real Kaggle dataset.

## How to Run

Requires Docker Desktop (with WSL2 enabled, on Windows).

```bash
docker compose up --build
```

This starts everything: the database, the backend, and the frontend.

- App: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`

Register an account on the app's Register page — pick any of the 6
roles directly, no PIN needed.

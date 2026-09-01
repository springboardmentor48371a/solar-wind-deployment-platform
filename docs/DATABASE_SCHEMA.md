# Database Schema

Complete database schema for the Solar & Wind Deployment Intelligence Platform.

---

## Overview

- **Database:** PostgreSQL 16
- **ORM:** SQLAlchemy 2.0
- **Connection:** Managed via `DATABASE_URL` in `.env`
- **Table creation:** Automatic on backend startup via `Base.metadata.create_all()`

**Tables implemented so far:**

| Table | Module | Purpose |
|---|---|---|
| `users` | Module 1 | User accounts and authentication |
| `regions` | Module 2 | Geographic grouping for projects — auto-created from coordinates |
| `projects` | Module 2 | Renewable energy projects |
| `sites` | Module 2 | Individual deployment sites within projects |
| `deployment_history` | Module 2 | Audit log of site status changes |
| `environmental_data` | Module 3 | Daily climate and weather data per site |
| `site_predictions` | Modules 4-7, 10 | Stores ML predictions (solar, wind, land cover) and suitability scores |
| `energy_forecasts` | Module 8 | Stores 30-day forecast projections for energy output |
| `land_cover` | Module 4 | Detailed land cover probability percentages for site regions |

---

## Tables

### `users`

Stores all platform user accounts including OAuth users.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `full_name` | String(100) | No | User's display name |
| `email` | String(255) | No | Unique email address |
| `hashed_password` | String(255) | Yes | bcrypt hash — null for OAuth-only users |
| `role` | Enum(UserRole) | No | User's platform role, default `energy_planner` |
| `is_active` | Boolean | No | Whether account is active, default `true` |
| `is_verified` | Boolean | No | Email verification status, default `false` |
| `oauth_provider` | String(50) | Yes | OAuth provider name e.g. `google` |
| `oauth_sub` | String(255) | Yes | Provider's unique user ID |
| `profile_picture` | Text | Yes | URL to profile image |
| `created_at` | DateTime | No | Account creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

---

### `regions`

Geographic regions auto-created from Nominatim reverse geocoding when a site is added. Not user-facing.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `name` | String(100) | No | Region name e.g. `Tamil Nadu` |
| `country` | String(100) | No | Country name |
| `state` | String(100) | Yes | State or province |
| `description` | Text | Yes | Optional description |
| `created_at` | DateTime | No | Creation timestamp |

---

### `projects`

Renewable energy deployment projects. Region is auto-assigned from the first site added to the project.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `name` | String(150) | No | Project name |
| `description` | Text | Yes | Project description |
| `status` | Enum(ProjectStatus) | No | Current status, default `planning` |
| `region_id` | Integer (FK → regions) | Yes | Auto-assigned from first site's coordinates |
| `created_by` | Integer (FK → users) | No | User who created the project |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

---

### `sites`

Individual deployment sites within a project. Region and elevation are auto-detected from coordinates on creation.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `name` | String(150) | No | Site name |
| `project_id` | Integer (FK → projects) | No | Project this site belongs to |
| `latitude` | Float | No | Geographic latitude |
| `longitude` | Float | No | Geographic longitude |
| `elevation` | Float | Yes | Elevation in meters — auto-fetched from OpenTopoData |
| `land_area` | Float | Yes | Land area in hectares |
| `energy_type` | Enum(EnergyType) | No | `solar`, `wind`, or `hybrid` |
| `status` | Enum(SiteStatus) | No | Review status, default `under_review` |
| `land_ownership` | Enum(LandOwnership) | No | Ownership type, default `unknown` |
| `existing_infrastructure` | Text | Yes | Notes on existing infrastructure |
| `notes` | Text | Yes | General notes |
| `created_by` | Integer (FK → users) | No | User who registered the site |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

---

### `deployment_history`

Audit log that records every status change made to a site. Automatically written when site status is updated.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `site_id` | Integer (FK → sites) | No | Site that was changed |
| `changed_by` | Integer (FK → users) | No | User who made the change |
| `previous_status` | Enum(SiteStatus) | Yes | Status before the change |
| `new_status` | Enum(SiteStatus) | No | Status after the change |
| `notes` | Text | Yes | Optional reason for change |
| `changed_at` | DateTime | No | Timestamp of the change |

---

### `environmental_data`

Daily environmental readings per site fetched from external APIs. One row per site per day. Auto-fetched for last 30 days when a site is created.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `site_id` | Integer (FK → sites) | No | Site this data belongs to |
| `date` | Date | No | Date of the reading |
| `solar_irradiance` | Float | Yes | Solar irradiance W/m² |
| `peak_sun_hours` | Float | Yes | Peak sun hours per day |
| `wind_speed` | Float | Yes | Wind speed m/s at 10m height |
| `wind_speed_50m` | Float | Yes | Wind speed m/s at 50m height |
| `wind_direction` | Float | Yes | Wind direction in degrees |
| `temperature_max` | Float | Yes | Max temperature °C |
| `temperature_min` | Float | Yes | Min temperature °C |
| `temperature_avg` | Float | Yes | Average temperature °C |
| `rainfall` | Float | Yes | Rainfall in mm |
| `cloud_cover` | Float | Yes | Cloud cover percentage |
| `humidity` | Float | Yes | Relative humidity percentage |
| `elevation` | Float | Yes | Elevation in meters (static, fetched once) |
| `land_slope` | Float | Yes | Land slope in degrees |
| `vegetation_index` | Float | Yes | NDVI value -1 to 1 |
| `source` | String(50) | Yes | Data source identifier |
| `fetched_at` | DateTime | No | When data was fetched |

---

### `site_predictions`

Stores machine learning-predicted metrics and overall suitability ratings calculated for each site. Updates automatically when predictions are executed or manually rerun.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `site_id` | Integer (Index) | No | Target site identifier (logical one-to-one mapping) |
| `solar_yield_kwh` | Float | Yes | Predicted daily solar yield per kWp (kWh/day) |
| `solar_capacity_factor` | Float | Yes | Solar capacity factor rating (0.0 to 1.0) |
| `solar_score` | Float | Yes | Solar suitability score (0 to 100) |
| `wind_power_kw` | Float | Yes | Estimated wind turbine power output in kW |
| `wind_capacity_factor` | Float | Yes | Wind capacity factor rating (0.0 to 1.0) |
| `wind_score` | Float | Yes | Wind suitability score (0 to 100) |
| `land_cover_class` | String(50) | Yes | Dominant predicted cover class (e.g., vegetation, cropland) |
| `vegetation_index` | Float | Yes | Site average NDVI value (-1.0 to 1.0) |
| `land_slope` | Float | Yes | Derived terrain slope in degrees |
| `land_cover_score` | Float | Yes | Final environment suitability score (0 to 100) |
| `suitability_score` | Float | Yes | Final weighted deployment suitability score (0 to 100) |
| `suitability_category` | String(50) | Yes | Rating category (Excellent, Highly Suitable, etc.) |
| `resource_score` | Float | Yes | Weighted Resource score (35% weight) |
| `geographic_score` | Float | Yes | Weighted Geographic score (25% weight) |
| `infrastructure_score` | Float | Yes | Weighted Infrastructure score (15% weight - default 50.0) |
| `environmental_score` | Float | Yes | Weighted Environmental score (15% weight) |
| `economic_score` | Float | Yes | Weighted Economic score (10% weight - default 50.0) |
| `predicted_at` | DateTime | No | Timestamp of initial prediction |
| `updated_at` | DateTime | No | Timestamp of last prediction update |

---

### `energy_forecasts`

Stores PyTorch LSTM model forecast projections for future daily energy outputs. Contains 30 daily forecast entries per site.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `site_id` | Integer (Index) | No | Target site identifier |
| `forecast_date` | Date | No | Future calendar date for the prediction |
| `predicted_solar_kwh` | Float | Yes | Forecasted solar generation on this date in kWh |
| `predicted_wind_kwh` | Float | Yes | Forecasted wind generation on this date in kWh |
| `predicted_total_kwh` | Float | Yes | Combined forecasted generation on this date in kWh |
| `confidence` | Float | Yes | Forecast accuracy confidence score (e.g., 0.85) |
| `created_at` | DateTime | No | Timestamp of forecast creation |

---

### `land_cover`

Stores raw classification probability percentages mapped from satellite image processing.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `site_id` | Integer (Index) | No | Target site identifier |
| `cover_class` | String(50) | Yes | Predicted dominant class name |
| `vegetation_pct` | Float | Yes | Probability percentage of vegetation coverage |
| `urban_pct` | Float | Yes | Probability percentage of urban coverage |
| `water_pct` | Float | Yes | Probability percentage of water body coverage |
| `barren_pct` | Float | Yes | Probability percentage of barren land coverage |
| `ndvi` | Float | Yes | Processed NDVI value |
| `slope_deg` | Float | Yes | Derived terrain slope in degrees |
| `aspect_deg` | Float | Yes | Terrain orientation / aspect in degrees |
| `notes` | Text | Yes | Optional analyst notes |
| `analyzed_at` | DateTime | No | Timestamp of geographic analysis |

---

## Relationships

```
users
 ├── projects (created_by)
 ├── sites (created_by)
 └── deployment_history (changed_by)

regions
 └── projects (one region → many projects)

projects
 └── sites (one project → many sites)

sites
 ├── deployment_history (one site → many history records)
 ├── environmental_data (one site → many daily records)
 ├── site_predictions (one site → one prediction record)
 ├── energy_forecasts (one site → many daily forecasts)
 └── land_cover (one site → one detailed land cover assessment)
```

**Entity Relationship Summary:**

```
users ──< projects >── regions
users ──< sites >── projects
users ──< deployment_history >── sites
sites ──< environmental_data
sites ─── site_predictions
sites ──< energy_forecasts
sites ─── land_cover
```

---

## Enums

### UserRole
| Value | Description |
|---|---|
| `energy_planner` | Plans and recommends deployment sites |
| `gis_analyst` | Analyzes geospatial and environmental data |
| `project_manager` | Manages project execution and timelines |
| `administrator` | Full platform access and user management |

### ProjectStatus
| Value | Description |
|---|---|
| `planning` | Project is in planning phase (default) |
| `active` | Project is actively being worked on |
| `completed` | Project has been completed |
| `on_hold` | Project is temporarily paused |

### SiteStatus
| Value | Description |
|---|---|
| `under_review` | Site is being evaluated (default) |
| `approved` | Site has been approved for deployment |
| `rejected` | Site was rejected after review |

### EnergyType
| Value | Description |
|---|---|
| `solar` | Solar energy deployment |
| `wind` | Wind energy deployment |
| `hybrid` | Combined solar and wind |

### LandOwnership
| Value | Description |
|---|---|
| `government` | Government owned land |
| `private` | Privately owned land |
| `community` | Community owned land |
| `unknown` | Ownership not determined (default) |

---

## External Data Sources

| Source | API | Data Provided | Cost |
|---|---|---|---|
| NASA POWER | `power.larc.nasa.gov/api` | Solar irradiance, wind speed (10m & 50m), wind direction, temperature, rainfall, cloud cover | Free, no key |
| Open-Meteo | `archive-api.open-meteo.com` | Relative humidity | Free, no key |
| OpenTopoData | `api.opentopodata.org/v1/srtm30m` | Elevation from SRTM30m dataset | Free, no key |
| Nominatim | `nominatim.openstreetmap.org` | Reverse geocoding — country, state, city from coordinates | Free, no key |

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
| `regions` | Module 2 | Geographic grouping for projects |
| `projects` | Module 2 | Renewable energy projects |
| `sites` | Module 2 | Individual deployment sites within projects |
| `deployment_history` | Module 2 | Audit log of site status changes |
| `environmental_data` | Module 3 | Daily climate and weather data per site |

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

Geographic regions used to group projects. Only administrators can create or delete regions.

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

Renewable energy deployment projects. Each project belongs to a region and is created by a user.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `name` | String(150) | No | Project name |
| `description` | Text | Yes | Project description |
| `status` | Enum(ProjectStatus) | No | Current status, default `planning` |
| `region_id` | Integer (FK → regions) | No | Region this project belongs to |
| `created_by` | Integer (FK → users) | No | User who created the project |
| `created_at` | DateTime | No | Creation timestamp |
| `updated_at` | DateTime | No | Last update timestamp |

---

### `sites`

Individual deployment sites within a project. Stores geographic coordinates and land information.

| Column | Type | Nullable | Description |
|---|---|---|---|
| `id` | Integer | No | Primary key |
| `name` | String(150) | No | Site name |
| `project_id` | Integer (FK → projects) | No | Project this site belongs to |
| `latitude` | Float | No | Geographic latitude |
| `longitude` | Float | No | Geographic longitude |
| `elevation` | Float | Yes | Elevation in meters |
| `land_area` | Float | Yes | Land area in hectares |
| `energy_type` | Enum(EnergyType) | No | `solar`, `wind`, or `hybrid` |
| `status` | Enum(SiteStatus) | No | Deployment status, default `planned` |
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

Daily environmental readings per site fetched from external APIs. One row per site per day.

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
 └── environmental_data (one site → many daily records)
```

**Entity Relationship Summary:**

```
users ──< projects >── regions
users ──< sites >── projects
users ──< deployment_history >── sites
sites ──< environmental_data
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
| `planned` | Site registered, not yet reviewed (default) |
| `under_review` | Site is being evaluated |
| `approved` | Site has been approved for deployment |
| `deployed` | Site has been deployed |
| `rejected` | Site was rejected |

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

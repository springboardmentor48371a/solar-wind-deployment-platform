# Workflows

Key workflows and processes implemented in the Solar & Wind Deployment Intelligence Platform.

---

## Table of Contents

1. [User Registration & Login](#1-user-registration--login)
2. [Google OAuth Login](#2-google-oauth-login)
3. [Token Refresh](#3-token-refresh)
4. [Project & Site Creation](#4-project--site-creation)
5. [Site Status Update & Audit Trail](#5-site-status-update--audit-trail)
6. [Environmental Data Collection](#6-environmental-data-collection)
7. [ML Prediction Pipeline](#7-ml-prediction-pipeline)
8. [API Endpoints Reference](#api-endpoints-reference)
9. [Role-Based Access Control](#role-based-access-control)

---

## 1. User Registration & Login

```
User submits email + password + role
        ↓
Backend checks email is not already registered
        ↓
Password is hashed with bcrypt
        ↓
User record saved to `users` table
        ↓
access_token (30 min) + refresh_token (7 days) returned
        ↓
Frontend stores tokens in localStorage
        ↓
Frontend fetches GET /users/me to get profile
        ↓
User redirected to their role-specific dashboard
```

---

## 2. Google OAuth Login

```
User clicks "Continue with Google"
        ↓
Frontend calls GET /auth/google/login
        ↓
Backend returns Google OAuth URL
        ↓
Browser redirects to Google login page
        ↓
User approves → Google redirects to GET /auth/google/callback?code=...
        ↓
Backend exchanges code for Google access token
        ↓
Backend fetches user info from Google (name, email, picture)
        ↓
If user exists → link Google account
If user doesn't exist → create new account
        ↓
Backend redirects to http://localhost:5173?access_token=...&refresh_token=...
        ↓
Frontend reads tokens from URL, stores in localStorage, clears URL
        ↓
User is logged in
```

---

## 3. Token Refresh

```
access_token expires after 30 minutes
        ↓
Frontend sends POST /auth/refresh with refresh_token
        ↓
Backend validates refresh_token signature and type
        ↓
New access_token issued (refresh_token unchanged)
        ↓
Frontend updates localStorage with new access_token
```

**Token lifetimes:**
- `access_token` → 30 minutes
- `refresh_token` → 7 days

After 7 days the refresh token expires and the user must log in again.

---

## 4. Project & Site Creation

### Project Creation
```
Energy Planner / Project Manager / Admin creates a Project
  → only name + description required
  → region is NOT set at this point
  → project saved with status = "planning", region_id = null
```

### Site Creation (2-step)

**Step 1 — Location Preview**
```
User enters site name, coordinates, energy type, land ownership
        ↓
Frontend calls GET /sites/preview?lat=&lon=
        ↓
Backend calls Nominatim reverse geocoding API
        ↓
Backend calls OpenTopoData for elevation
        ↓
Returns detected country, state, city, display_name, elevation
        ↓
Frontend shows preview card — "Is this the correct location?"
User can go back to edit coordinates or confirm
```

**Step 2 — Site Creation**
```
User confirms location
        ↓
POST /sites/ called
        ↓
Backend reverse geocodes coordinates → gets region info
        ↓
Region looked up in DB by country + state
  → if not found: new region auto-created
        ↓
If project has no region_id → auto-assigned from this site's region
        ↓
Elevation fetched from OpenTopoData
        ↓
Site saved with status = "under_review" (default)
        ↓
30 days of environmental data auto-fetched in background
  (NASA POWER + Open-Meteo + OpenTopoData)
        ↓
Site appears on map and in project's site list
```

---

## 5. Site Status Update & Audit Trail

```
Authorized user changes site status via dropdown
        ↓
PATCH /sites/{id}/status called with new status
        ↓
Backend reads current status as previous_status
        ↓
New DeploymentHistory record written:
  - site_id
  - changed_by (current user)
  - previous_status
  - new_status
  - changed_at (timestamp)
        ↓
Site status updated in `sites` table
        ↓
Full history retrievable via GET /sites/{id}/history
```

**Site status progression:**
```
under_review → approved
             ↘ rejected
```

Sites enter as `under_review` by default. Our platform's role is to evaluate and approve or reject sites — deployment tracking is out of scope.

---

## 6. Environmental Data Collection

```
Site is created → auto-triggers data collection for last 30 days
        ↓
POST /environmental/{site_id}/collect?days=30 called internally
        ↓
Backend checks if data was already fetched within 24 hours
  → if yes: returns "Data already up to date" (no API calls made)
  → if no: proceeds with collection
        ↓
3 API calls made:
  1. NASA POWER API  → solar irradiance, wind speed (10m & 50m),
                       wind direction, temperature, rainfall, cloud cover
  2. Open-Meteo API  → relative humidity
  3. OpenTopoData    → elevation (fetched once, static per location)
        ↓
Data parsed into daily records (one record per day)
        ↓
Old records for this site deleted from `environmental_data`
New records inserted (30 rows per site)
        ↓
GET /environmental/{site_id}/summary returns:
  - avg solar irradiance
  - avg peak sun hours
  - avg wind speed (10m and 50m)
  - avg temperature
  - total rainfall
  - avg cloud cover
  - avg humidity
  - elevation
  - total days of data
```

**Refresh behaviour:**
- Clicking Refresh in the UI calls `POST /environmental/{site_id}/collect`
- If data was fetched within the last 24 hours, the cache check skips re-fetching and re-reads from DB
- After 24 hours, old rows are deleted and fresh 30-day data is inserted

---

## 7. ML Prediction Pipeline

```
User triggers ML predictions (manually or on site creation)
        ↓
POST /predictions/{site_id}/run proxy endpoint called
        ↓
Backend queries database for site details (coordinates, elevation, type)
        ↓
Backend forwards request to the ml-service: POST /predict/all
        ↓
ml-service averages 30 days of site's environmental_data
        ↓
ml-service executes 3 prediction modules:
  - Solar Model: predicts capacity factor & daily solar yield (10 features)
  - Wind Model: predicts power output with Betz-limit low speed fallback (10 features)
  - Land Cover Model: predicts dominant cover class & vegetation index (3 features)
        ↓
ml-service calculates final deployment suitability score & rating category
        ↓
ml-service writes/updates record in `site_predictions` table
        ↓
Frontend displays scores, sub-scores, and recommendations in real-time
```

---

## API Endpoints Reference

### Authentication — `/auth`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | Public | Register new user, returns tokens |
| POST | `/auth/login` | Public | Login with email/password, returns tokens |
| POST | `/auth/refresh` | Public | Exchange refresh token for new access token |
| GET | `/auth/google/login` | Public | Get Google OAuth redirect URL |
| GET | `/auth/google/callback` | Public | Google OAuth callback, redirects to frontend with tokens |

### Users — `/users`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/users/me` | Any | Get own profile |
| PATCH | `/users/me` | Any | Update own profile |
| GET | `/users/` | Admin | List all users |
| PATCH | `/users/{id}/role` | Admin | Change a user's role |
| PATCH | `/users/{id}/deactivate` | Admin | Deactivate a user account |

### Regions — `/regions`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/regions/` | Admin | Create a new region manually |
| GET | `/regions/` | Any | List all regions |
| DELETE | `/regions/{id}` | Admin | Delete a region |

> Regions are normally auto-created from site coordinates. Manual creation is admin-only.

### Projects — `/projects`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/projects/` | Planner, Manager, Admin | Create a new project (name + description only) |
| GET | `/projects/` | Any | List all projects |
| GET | `/projects/{id}` | Any | Get a specific project |
| PATCH | `/projects/{id}` | Creator or Admin | Update project details or status |
| DELETE | `/projects/{id}` | Admin | Delete a project |

### Sites — `/sites`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/sites/preview?lat=&lon=` | Any | Preview detected location + elevation before creating site |
| POST | `/sites/` | Any | Register a new site — auto-detects region, elevation, fetches env data |
| GET | `/sites/` | Any | List sites, filter by `?project_id=` |
| GET | `/sites/compare?ids=1,2,3` | Any | Compare multiple sites side by side |
| GET | `/sites/{id}` | Any | Get a specific site |
| PATCH | `/sites/{id}` | Creator or Admin | Update site details |
| PATCH | `/sites/{id}/status` | Planner, Manager, Admin | Update site status (writes history) |
| GET | `/sites/{id}/history` | Any | Get full deployment history for a site |
| DELETE | `/sites/{id}` | Creator or Admin | Delete a site |

### Predictions — `/predictions`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/predictions/{site_id}` | Any | Retrieve calculated ML predictions & suitability scores |
| POST | `/predictions/{site_id}/run` | Any | Manually trigger/re-run all ML models for a site |

### Environmental Data — `/environmental`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/environmental/{site_id}/collect?days=30` | Any | Fetch and store environmental data from external APIs |
| GET | `/environmental/{site_id}` | Any | Get all daily records for a site |
| GET | `/environmental/{site_id}?start_date=&end_date=` | Any | Get records filtered by date range |
| GET | `/environmental/{site_id}/summary` | Any | Get aggregated averages and totals |

---

## Role-Based Access Control

### Backend permissions

| Action | Energy Planner | GIS Analyst | Project Manager | Administrator |
|---|---|---|---|---|
| Register / Login | ✅ | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ | ✅ |
| Update own profile | ✅ | ✅ | ✅ | ✅ |
| List all users | ❌ | ❌ | ❌ | ✅ |
| Change user role | ❌ | ❌ | ❌ | ✅ |
| Deactivate user | ❌ | ❌ | ❌ | ✅ |
| Create region (manual) | ❌ | ❌ | ❌ | ✅ |
| Delete region | ❌ | ❌ | ❌ | ✅ |
| View regions | ✅ | ✅ | ✅ | ✅ |
| Create project | ✅ | ❌ | ✅ | ✅ |
| Edit own project | ✅ | ❌ | ✅ | ✅ |
| Edit any project | ❌ | ❌ | ❌ | ✅ |
| Delete project | ❌ | ❌ | ❌ | ✅ |
| View projects | ✅ | ✅ | ✅ | ✅ |
| Create site | ✅ | ✅ | ✅ | ✅ |
| Edit own site | ✅ | ✅ | ✅ | ✅ |
| Edit any site | ❌ | ❌ | ❌ | ✅ |
| Update site status | ✅ | ❌ | ✅ | ✅ |
| Delete own site | ✅ | ✅ | ✅ | ✅ |
| Delete any site | ❌ | ❌ | ❌ | ✅ |
| View sites | ✅ | ✅ | ✅ | ✅ |
| Collect environmental data | ✅ | ✅ | ✅ | ✅ |
| View environmental data | ✅ | ✅ | ✅ | ✅ |
| Run ML predictions | ✅ | ❌ | ✅ | ✅ |
| View ML predictions | ✅ | ✅ | ✅ | ✅ |

### Frontend UI visibility by role

| UI Element | Energy Planner | GIS Analyst | Project Manager | Administrator |
|---|---|---|---|---|
| Create Project button | ✅ | ❌ | ✅ | ✅ |
| Delete Project button | ❌ | ❌ | ❌ | ✅ |
| Site status dropdown | ✅ | ❌ | ✅ | ✅ |
| User Management tab | ❌ | ❌ | ❌ | ✅ |
| Default landing page | Projects | Map | Projects | Projects |

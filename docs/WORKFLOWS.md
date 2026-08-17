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
7. [API Endpoints Reference](#api-endpoints-reference)
8. [Role-Based Access Control](#role-based-access-control)

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

```
Admin creates a Region (required first)
        ↓
Energy Planner / Project Manager / Admin creates a Project
  → must select an existing Region
  → project saved with created_by = current user id
  → default status = "planning"
        ↓
Any user creates a Site under the Project
  → must provide name, latitude, longitude, energy_type
  → site saved with status = "planned"
        ↓
Site appears as a pin on the map
Site appears in the project's site list
```

---

## 5. Site Status Update & Audit Trail

```
Authorized user changes site status via dropdown or API
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
planned → under_review → approved → deployed
                       ↘ rejected
```

---

## 6. Environmental Data Collection

```
User clicks "Collect Data" on a site
        ↓
POST /environmental/{site_id}/collect?days=30 called
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
New records inserted
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
| POST | `/regions/` | Admin | Create a new region |
| GET | `/regions/` | Any | List all regions |
| DELETE | `/regions/{id}` | Admin | Delete a region |

### Projects — `/projects`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/projects/` | Planner, Manager, Admin | Create a new project |
| GET | `/projects/` | Any | List all projects |
| GET | `/projects/{id}` | Any | Get a specific project |
| PATCH | `/projects/{id}` | Creator or Admin | Update project details or status |
| DELETE | `/projects/{id}` | Admin | Delete a project |

### Sites — `/sites`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/sites/` | Any | Register a new site |
| GET | `/sites/` | Any | List sites, filter by `?project_id=` |
| GET | `/sites/compare?ids=1,2,3` | Any | Compare multiple sites side by side |
| GET | `/sites/{id}` | Any | Get a specific site |
| PATCH | `/sites/{id}` | Creator or Admin | Update site details |
| PATCH | `/sites/{id}/status` | Planner, Manager, Admin | Update site status (writes history) |
| GET | `/sites/{id}/history` | Any | Get full deployment history for a site |
| DELETE | `/sites/{id}` | Creator or Admin | Delete a site |

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
| Create region | ❌ | ❌ | ❌ | ✅ |
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

### Frontend UI visibility by role

| UI Element | Energy Planner | GIS Analyst | Project Manager | Administrator |
|---|---|---|---|---|
| Create Project button | ✅ | ❌ | ✅ | ✅ |
| Delete Project button | ❌ | ❌ | ❌ | ✅ |
| Create Region button | ❌ | ❌ | ❌ | ✅ |
| Site status dropdown | ✅ | ❌ | ✅ | ✅ |
| User Management tab | ❌ | ❌ | ❌ | ✅ |
| Default landing page | Projects | Map | Projects | Projects |

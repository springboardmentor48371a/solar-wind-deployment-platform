# Solar & Wind Deployment Intelligence Platform

An AI-powered platform that recommends optimal locations for renewable energy projects by analyzing environmental, geographic, climatic, and infrastructure-related factors.

For the full project specification see [docs/PROJECT_SPEC.md](docs/PROJECT_SPEC.md).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Frontend | React.js, Vite |
| Database | PostgreSQL 16 |
| Auth | JWT, bcrypt, Google OAuth2 |
| Maps | Leaflet.js, OpenStreetMap |
| DevOps | Docker, Docker Compose |

---

## Prerequisites

Only two things needed:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — runs everything
- [Git](https://git-scm.com/) — to clone the repo

No Node.js, no Python, no pip — Docker handles all of that.

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd solar-wind-deployment-platform
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and replace `SECRET_KEY` with a freshly generated one:

```bash
docker run --rm python:3.11-slim python -c "import secrets; print(secrets.token_hex(32))"
```

Paste the output as your `SECRET_KEY` in `.env`. Leave everything else as is.

### 3. Start everything

```bash
docker compose up --build
```

This starts PostgreSQL, the FastAPI backend, and the React frontend all at once. Wait until you see:

```
backend-1   | INFO:     Application startup complete.
frontend-1  | VITE ready in ... ms
```

### 4. Seed the database (first time only)

Open a new terminal and run:

```bash
docker exec solar-wind-deployment-platform-backend-1 python app/seed.py
```

This creates 4 default accounts, 2 sample projects, and 6 sites with environmental data.

### 5. Open the app

Open **http://localhost:5173** in your browser.

---

## Default Accounts

Created by `seed.py`. Use these to log in and test each role.

| Role | Email | Password |
|---|---|---|
| Administrator | `admin@solarwind.com` | `admin123` |
| Energy Planner | `planner@solarwind.com` | `planner123` |
| GIS Analyst | `gis@solarwind.com` | `gis12345` |
| Project Manager | `manager@solarwind.com` | `manager123` |

---


## Google OAuth

Google OAuth **will not work out of the box** when you clone this repo.

Google OAuth credentials (`GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`) are registered under a specific Google account and tied to specific localhost for now. The `.env.example` contains placeholders that won't work for anyone other than the original developer who set them up.

Email and password login works perfectly without any additional setup.

---

## API Docs

Once the backend is running, the full interactive API documentation is available at:

**http://localhost:8000/docs**

---

## Project Structure

```
solar-wind-deployment-platform/
├── backend/
│   ├── app/
│   │   ├── core/          → config, security, dependencies
│   │   ├── models/        → SQLAlchemy database models
│   │   ├── routers/       → API endpoint handlers
│   │   ├── schemas/       → Pydantic request/response schemas
│   │   ├── services/      → external API integrations
│   │   ├── database.py    → DB engine and session
│   │   ├── main.py        → FastAPI app entry point
│   │   └── seed.py        → database seeder
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/    → shared UI components
│       ├── pages/         → role-based dashboard pages
│       ├── App.jsx        → root component with routing
│       └── api.js         → axios API helper
├── docs/
│   ├── PROJECT_SPEC.md    → full project specification
│   ├── DATABASE_SCHEMA.md → database tables, relationships, enums
│   └── WORKFLOWS.md       → API endpoints, workflows, RBAC
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Module Progress

| Module | Status |
|---|---|
| 1. User Authentication & RBAC | ✅ Complete |
| 2. Project & Site Management | ✅ Complete |
| 3. Environmental Data Collection | ✅ Complete |
| 4. Geographic Intelligence Engine | 🔜 Planned |
| 5. Solar Potential Prediction | 🔜 Planned |
| 6. Wind Potential Prediction | 🔜 Planned |
| 7. Site Suitability Engine | 🔜 Planned |
| 8. Energy Forecasting Engine | 🔜 Planned |
| 9. Deployment Optimization Engine | 🔜 Planned |
| 10. Site Scoring Engine | 🔜 Planned |
| 11. Dashboard & Analytics | 🔄 In Progress |
| 12. Notification & Alert System | 🔜 Planned |
| 13. Reports & Export System | 🔜 Planned |
| 14. Final Integration & Deployment | 🔜 Planned |

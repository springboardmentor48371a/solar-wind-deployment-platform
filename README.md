# Solar & Wind Deployment Intelligence Platform

An AI-powered geospatial platform for evaluating and managing potential **solar and wind energy project sites** using environmental, geographic, and infrastructure data.

> **Status:** 🟢 Milestone 1 Complete · 🟡 Milestone 2 In Progress

## Overview

The platform follows an end-to-end renewable energy site evaluation workflow:

```text
Authentication
     ↓
Project & Site Management
     ↓
Environmental & GIS Data
     ↓
Resource Prediction
     ↓
Site Suitability
     ↓
Deployment Recommendations
```

The current release focuses on the core platform, authentication, project/site management, and geospatial data infrastructure.

## Tech Stack

| Layer            | Technology                   |
| ---------------- | ---------------------------- |
| Backend          | FastAPI, Python, JWT, OAuth2 |
| Frontend         | Next.js, React, Tailwind CSS |
| Database         | PostgreSQL, PostGIS, MongoDB |
| ORM / Migrations | GeoAlchemy2, Alembic         |
| Infrastructure   | Docker, Docker Compose       |

## Current Features

* JWT + OAuth2-style authentication
* Role-based access control
* User registration and login
* Renewable Energy Planner, GIS Analyst, Project Manager & Administrator roles
* Project creation and management
* Renewable energy site management
* PostGIS-backed geospatial data
* FastAPI REST API with Swagger documentation
* Dockerized development environment
* Next.js frontend integrated with the backend

## Project Structure

```text
solar-wind-deployment-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   ├── components/
│   └── Dockerfile
│
├── docker-compose.yml
├── SETUP.md
└── README.md
```

## Roadmap

* [x] Project initialization & core architecture
* [x] Authentication & role-based access
* [x] Project & site management
* [x] PostgreSQL + PostGIS integration
* [x] Dockerized environment
* [ ] Environmental intelligence & resource prediction
* [ ] GIS-based site suitability analysis
* [ ] Site ranking & optimization
* [ ] Analytics & deployment

## Getting Started

### Requirements

* Docker Desktop
* Git

### Run

```bash
git clone https://github.com/Aadi-2k7/aditya-yadav.git
cd aditya-yadav

docker compose up --build postgres mongo backend
docker compose exec backend alembic upgrade head
docker compose up --build frontend
```

### Access

* **Frontend:** http://localhost:3000
* **API:** http://localhost:8000
* **Swagger:** http://localhost:8000/docs

See [`SETUP.md`](SETUP.md) for detailed setup instructions.

## Author

**Aditya Yadav**
B.Tech CSE — Data Science

[GitHub](https://github.com/Aadi-2k7)

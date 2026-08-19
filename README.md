# Solar & Wind Deployment Intelligence Platform

An AI-powered web platform designed to recommend optimal locations for renewable energy projects (solar arrays and wind turbines) by performing multi-criteria suitability analysis on environmental, geographic, climate, and infrastructure datasets.

This repository contains the full-stack implementation of **Milestone 1**: A secure User Authentication system (Register/Login) styled with an interactive clean-tech animated interface.

---

## Technical Architecture

The platform is divided into a decoupled frontend client and a backend API server:

```
       [ FRONTEND ]
    React + TypeScript
     (Vite + Tailwind)
            │
            ▼
    [ HTTP CLIENT ]
      Axios API calls
            │
            ▼
       [ BACKEND ]
    FastAPI (Python)
      - CORS Middleware
      - JWT Bearer authentication
      - bcrypt password hashing
            │
            ▼
      [ DATABASE ]
       PostgreSQL
   (or SQLite fallback)
```

---

## Features (Milestone 1)

1. **Clean-Tech SVG/CSS Background**:
   * Vector wind turbines with rotors spinning slowly at distinct, realistic speeds.
   * Floating breeze wind flow lines moving horizontally across the sky.
   * Drifting clouds and an atmospheric sun core with a glowing pulse effect.
   * Isometric solar panels with a reflective light glint animation.
   * Pulsing AI grid network nodes linking the power generation sources.
   * Fully responsive: scales down on tablets and simplifies to basic gradients on mobile to preserve layout focus.
   * Reduced-motion support: automatically freezes all animations if `prefers-reduced-motion` is enabled in the user's OS settings.
2. **Glassmorphic Credentials Form**: Centered transparent navy auth card with precise borders, soft shadow elevation, and high text contrast compliance.
3. **Secure Encryption Flow**:
   * Direct password encryption using the salted `bcrypt` algorithm.
   * Clear text passwords and password hashes are strictly excluded from outgoing JSON schemas to prevent data exposure.
4. **Stateless JWT Sessions**:
   * Encodes signed tokens containing encrypted subject identifiers.
   * Intercepts Axios requests frontend-side to inject tokens into headers automatically.
   * Secure dashboard view displaying the authenticated session profile (no raw JWTs printed on screen).

---

## Directory Structure

```
├── frontend/                     # React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── background/      # RenewableBackground.tsx (Animated SVGs)
│   │   │   ├── auth/            # AuthCard, LoginForm, RegisterForm
│   │   │   └── dashboard/       # PlatformDashboard.tsx
│   │   ├── routes/              # AppRoutes.tsx (Protected routes)
│   │   ├── context/             # AuthContext.tsx (Token state & user session)
│   │   ├── services/            # api.ts (Axios configurations)
│   │   └── index.css            # Custom CSS & Glassmorphism definitions
│   └── package.json
│
└── backend/                      # Python FastAPI Backend
    ├── app/
    │   ├── core/                # config.py, security.py (hashing & JWT)
    │   ├── database/            # session.py (DB sessions)
    │   ├── models/              # user.py (SQLAlchemy ORM Model)
    │   ├── schemas/             # user.py (Pydantic schemas)
    │   └── routes/              # auth.py (Endpoints)
    ├── .env.example
    ├── requirements.txt
    └── view_db.py               # CLI tool to inspect the database
```

---

## Installation & Setup

Ensure you have **Python 3.10+** and **Node.js 18+** installed.

### 1. Backend Server Setup

Navigate to the `backend/` directory:
```bash
cd backend
```

Create a virtual environment and activate it (optional but recommended):
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt email-validator
```

Create a `.env` file (you can copy `.env.example` as a starting point):
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/solar_wind_db
JWT_SECRET_KEY=solar_wind_intelligence_secret_key_change_in_production_32bytes
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Start the FastAPI backend:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API is now running at `http://127.0.0.1:8000/`. You can view the interactive documentation at `http://127.0.0.1:8000/docs`.

### 2. Frontend Client Setup

Open a new terminal window and navigate to the `frontend/` directory:
```bash
cd frontend
```

Install packages:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```
Open **`http://localhost:5173/`** in your browser to view the application.

---

## Relational Database Schema

The platform initializes a single table named `users` to manage accounts:

### Table: `users`
* **`id`** (`UUID` / `CHAR(36)`): Primary key. Globally unique identifier.
* **`full_name`** (`VARCHAR(100)`): Display name of the user.
* **`email`** (`VARCHAR(150)`): Unique, indexed login email.
* **`password_hash`** (`VARCHAR(255)`): Password string encrypted with bcrypt.
* **`created_at`** (`TIMESTAMP`): Time of registration (UTC).
* **`updated_at`** (`TIMESTAMP`): Time of the last account edit (UTC).

### Database Fallback Architecture
* **PostgreSQL (Production)**: Connects to `postgresql://postgres:postgres@localhost:5432/solar_wind_db` automatically if active.
* **SQLite (Development Fallback)**: If no PostgreSQL instance is found, it automatically initializes a local file database at `backend/solar_wind_fallback.db` to keep the application running immediately.

To visually inspect the tables and columns without downloading external database utilities, execute this script in your `backend/` folder:
```bash
python view_db.py
```

---

## Entity-Relationship (ER) Models

### Current ER Model (Milestone 1)
```mermaid
erDiagram
    users {
        uuid id PK "Primary Key (Auto-UUID)"
        varchar(100) full_name "Not Null"
        varchar(150) email "Unique Login Email (NOT NULL, UNIQUE, INDEX)"
        varchar(255) password_hash "Bcrypt Encrypted Hash (NOT NULL)"
        timestamp created_at "Registration date"
        timestamp updated_at "Last updated date"
    }
```

### Future Expanded Platform Model (Milestones 2 & 3)
```mermaid
erDiagram
    users ||--o{ projects : "manages"
    projects ||--|{ sites : "contains"
    sites ||--|| solar_metrics : "has"
    sites ||--|| wind_metrics : "has"

    users {
        uuid id PK
        varchar(100) full_name
        varchar(150) email
        varchar(255) password_hash
    }

    projects {
        uuid id PK
        uuid user_id FK "References users.id"
        varchar(100) project_name
        varchar(255) description
        timestamp created_at
    }

    sites {
        uuid id PK
        uuid project_id FK "References projects.id"
        varchar(100) site_name
        float latitude
        float longitude
        float land_area_sqm
        float elevation
        varchar(100) land_ownership
    }

    solar_metrics {
        uuid site_id PK, FK "References sites.id"
        float annual_irradiance
        float peak_sun_hours
        float expected_solar_output_kwh
        float capacity_factor
    }

    wind_metrics {
        uuid site_id PK, FK "References sites.id"
        float average_wind_speed
        float wind_power_density
        float turbulence_intensity
        float expected_wind_output_kwh
    }
```
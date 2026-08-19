# solar-wind-deployment-platform# ☀️ Solar & Wind Deployment Intelligence Platform


An AI-powered renewable energy deployment and feasibility intelligence platform designed to identify, assess, and recommend optimal geographical sites for Solar PV, Wind Farms, and Hybrid clean energy infrastructure.

---

## 📌 Key Highlights & Implemented Features

- **🔐 Module 1: Role-Based Authentication (RBAC):**
  - Secure user registration and login with Bcrypt password hashing and JWT bearer tokens.
  - Multi-role permission architecture (`Renewable Energy Planner`, `GIS Analyst`, `Project Manager`, `Administrator`).
  - Active session handling, profile dropdown with one-click email copying, and confirmation sign-out modals.

- **🗺️ Module 2: Interactive GIS Site Management & Mapping:**
  - Dynamic GIS Map Picker powered by **Leaflet & OpenStreetMap**.
  - Interactive pin dropping and real-time draggable coordinates extraction.
  - Live reverse-geocoding via **OpenStreetMap Nominatim API** (strictly English place names).
  - Topological Digital Elevation Modeling (DEM) integration via **Open-Meteo Elevation API**.
  - Automated infrastructure proximity buffering and suitability indexing.

- **💾 Persistent Relational Storage:**
  - SQLite database management via **SQLAlchemy ORM** to persist registered user accounts and evaluated site boundaries across page refreshes and server restarts.

- **📊 Multi-View Executive Dashboard:**
  - **Active Deployment Zone:** Instant resource breakdown (Solar GHI, Wind Speed @ 100m, Terrain DEM, Substation proximity).
  - **Stored Candidate Sites:** Relational repository of all registered geographical corridors.
  - **Multi-Site Comparison Matrix:** Side-by-side benchmarking of site metrics and suitability scores.
  - **Executive Feasibility Dossier:** Generation yield and capacity utilization factor (CUF) summaries.

---

## 🛠️ System Architecture & Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS | High-performance SPA with responsive executive dark UI |
| **GIS Visualization** | Leaflet.js, React-Leaflet, CartoDB Positron | Interactive geospatial search and pin-drop mapping |
| **Icons & UI** | Lucide React | Modern icon library |
| **Backend API** | FastAPI, Python, Uvicorn | Asynchronous RESTful API Gateway |
| **Data Validation** | Pydantic v2, Email Validator | Request/response schema validation |
| **Security & Auth** | JWT (HS256), Passlib, Bcrypt | Role-Based Access Control and password encryption |
| **Database & ORM** | SQLite, SQLAlchemy 2.0 | Persistent relational storage for users and sites |

---

## 🌐 External Meteorological & Geospatial Connectors

- **Reverse Geocoding:** OpenStreetMap Nominatim API (`accept-language=en`)
- **Digital Elevation Modeling (DEM):** Open-Meteo Elevation API
- **Solar Potential Feeds:** NASA POWER API specifications (Global Horizontal Irradiance - GHI)
- **Wind Resource Feeds:** Global Wind Atlas / Open-Meteo (100m hub height velocities)

---

## 🚀 Quickstart: Run the Project Locally

Follow these step-by-step commands to clone and start both the backend API and frontend client.

### Prerequisites
- **Python 3.10+** installed
- **Node.js 18+ & npm** installed
- **Git** installed

---

### 1. Clone the Repository & Checkout Branch
```bash
git clone [https://github.com/springboardmentor48371a/solar-wind-deployment-platform.git](https://github.com/springboardmentor48371a/solar-wind-deployment-platform.git)
cd solar-wind-deployment-platform
git checkout shruti-mishra

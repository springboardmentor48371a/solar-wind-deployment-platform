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

**GIS View**
A map showing all your sites, plus tabs for terrain data, environmental
analytics, and a table comparing all sites side by side.

**Reports**
Download PDF or Excel reports for a site. There's also a report builder
where you pick which sections to include (suitability, solar, wind,
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

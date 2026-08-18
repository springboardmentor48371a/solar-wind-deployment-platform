# Getting the backend running locally

1. Make sure Docker & Docker Compose are installed.
2. From the project root:
   ```
   docker compose up --build postgres mongo backend
   ```
3. In a second terminal, generate and apply the first migration (creates users/projects/sites tables + enables PostGIS):
   ```
   docker compose exec backend alembic revision --autogenerate -m "initial schema"
   docker compose exec backend alembic upgrade head
   ```
4. Open http://localhost:8000/docs — interactive Swagger UI for every endpoint.
5. Try the flow:
   - POST /api/v1/auth/register (create a user, pick a role)
   - POST /api/v1/auth/login (get a JWT — use the email as "username")
   - Authorize in Swagger with the token
   - POST /api/v1/projects, then POST .../sites to register a site with lat/lon

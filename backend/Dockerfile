FROM python:3.12-slim

# GDAL and friends (rasterio, geopandas, fiona, shapely, pyproj) need the
# underlying system libraries, not just the Python wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    build-essential \
    curl \
    ca-certificates \
    gnupg \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# pg_dump must be >= the Postgres *server* major version (16, per
# docker-compose's postgis/postgis:16-3.4) — pg_dump can safely dump from
# an older server, never a newer one. Debian bookworm's own repo ships an
# older client, so pull postgresql-client-16 specifically from the
# official PostgreSQL apt repository instead of whatever version bookworm
# happens to default to.
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /usr/share/keyrings/postgresql.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql.gpg] http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client-16 \
    && rm -rf /var/lib/apt/lists/*

# GDAL's Python bindings compile against the system headers — these need
# to be on the include path for `pip install GDAL` (below) to succeed,
# since GDAL doesn't reliably ship prebuilt wheels for every version.
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

WORKDIR /app

COPY requirements.txt .
# GDAL's Python bindings must match the system libgdal version exactly —
# install it separately, pinned to whatever apt just installed, before the
# rest of requirements.txt (which excludes GDAL for that reason in Docker).
RUN GDAL_VER=$(gdal-config --version) && pip install --no-cache-dir "GDAL==${GDAL_VER}"
RUN pip install --no-cache-dir -r requirements.txt

# Non-root, same rationale as always — created before COPY so ownership
# can be set via COPY's own --chown flag (one pass) instead of a separate
# `RUN chown -R` afterward (a second full-tree walk over files already
# written once). See frontend/Dockerfile for the fuller rationale; the
# same fix applies here even though this tree is much smaller than
# node_modules.
RUN useradd --create-home --shell /bin/bash appuser

COPY --chown=appuser:appuser . .

# Backup destination for the `backup` compose service (bind-mounted from a
# named volume there). Freshly created and empty, so chown here is a
# single cheap operation, not a recursive walk over pre-existing files.
RUN mkdir -p /backups && chown appuser:appuser /backups && chmod +x scripts/*.sh 2>/dev/null || true

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

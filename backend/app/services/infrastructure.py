"""
Infrastructure proximity connector — OpenStreetMap (OSM), via the public
Overpass API. Matches "OpenStreetMap -> Road networks / Infrastructure
mapping" in the Recommended Datasets section, and feeds the Geographic
Intelligence Engine's "Infrastructure proximity analysis".

Distance calculation uses GeoPandas/Shapely/PyProj (see geo_utils.py)
rather than a hand-rolled haversine formula, and the full Overpass
response is archived to MongoDB (the platform's secondary database) so
it can be reprocessed later without re-querying the external API.
"""

import requests
from sqlalchemy.orm import Session

from app.cache import cache_get, cache_set
from app.config import settings
from app import models
from app.services.geo_utils import nearest_features_km
from app import mongo
from app import data_lake

# Overpass query radius in meters for "nearby infrastructure"
SEARCH_RADIUS_M = 15000

FEATURE_TYPE_MAP = {"substation": "substation", "primary": "road", "line": "transmission_line"}


def fetch_and_store_infrastructure(db: Session, site: models.Site) -> None:
    """
    Queries Overpass for the nearest substation, primary road, and
    transmission line around a site's coordinates, and stores the
    distances in InfrastructureFeature rows.
    """
    from app.services.data_source_overrides import is_disabled
    if is_disabled(db, "OpenStreetMap (Overpass)"):
        print(f"Info: OpenStreetMap (Overpass) is manually paused by an administrator — skipping infrastructure fetch for site {site.id}")
        return

    query = f"""
    [out:json][timeout:20];
    (
      node["power"="substation"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
      way["highway"="primary"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
      way["power"="line"](around:{SEARCH_RADIUS_M},{site.latitude},{site.longitude});
    );
    out center 10;
    """

    # Overpass is public infrastructure — it changes rarely and the public
    # instance is aggressively rate-limited, so cache by rounded site
    # coordinates + search radius for a full day.
    cache_key = (
        f"infra:overpass:{round(site.latitude, 3)}:{round(site.longitude, 3)}:{SEARCH_RADIUS_M}"
    )
    payload = cache_get(cache_key)
    if payload is None:
        from app.services.overpass_client import query_overpass
        payload = query_overpass(query, timeout=8)
        cache_set(cache_key, payload, ttl_seconds=60 * 60 * 24)

    elements = payload.get("elements", [])

    # Archive the full raw response to MongoDB before any parsing/loss.
    mongo.store_raw_payload("infrastructure_raw", site.id, "OVERPASS", payload)
    data_lake.archive_payload("infrastructure_raw", site.id, "OVERPASS", payload)

    candidates = []
    for el in elements:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue

        tags = el.get("tags", {})
        raw_type = tags.get("power") or tags.get("highway")
        feature_type = FEATURE_TYPE_MAP.get(raw_type)
        if not feature_type:
            continue

        candidates.append(
            {"feature_type": feature_type, "name": tags.get("name"), "lat": lat, "lon": lon}
        )

    nearest_by_type = {}
    if candidates:
        scored = nearest_features_km(site.latitude, site.longitude, candidates)
        for _, row in scored.iterrows():
            ftype = row["feature_type"]
            distance_km = round(float(row["distance_km"]), 2)
            if ftype not in nearest_by_type or distance_km < nearest_by_type[ftype][0]:
                nearest_by_type[ftype] = (distance_km, row["name"])

    # Clear old readings for this site before inserting fresh ones
    db.query(models.InfrastructureFeature).filter(
        models.InfrastructureFeature.site_id == site.id
    ).delete()

    for feature_type, (distance_km, name) in nearest_by_type.items():
        db.add(
            models.InfrastructureFeature(
                site_id=site.id,
                feature_type=feature_type,
                name=name,
                distance_km=distance_km,
            )
        )

    db.commit()

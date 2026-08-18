"""
Power System Simulation — the "Power system simulation" integration
point in the architecture diagram. Generates an hourly output profile
(kW) for a hypothetical installation at a site, driven by the same
deterministic capacity-factor figures the Solar/Wind Potential Engines
already computed — a simple, explainable physics/statistics simulation,
explicitly not the AI/ML forecasting layer.

Solar: a clipped sine diurnal curve scaled so its mean matches the
site's solar capacity factor (peaks at local solar noon, zero overnight).

Wind: capacity factor plus a small pseudo-random (deterministic, seeded
by site id) fluctuation representative of real turbine output variance,
since wind — unlike solar — doesn't follow a clean diurnal shape.
"""

import math
import random

from sqlalchemy.orm import Session

from app import models


def simulate_power_output(
    db: Session, site: models.Site, technology: str, capacity_mw: float, hours: int
) -> list[dict]:
    if technology == "solar":
        latest = (
            db.query(models.SolarPotential)
            .filter(models.SolarPotential.site_id == site.id)
            .order_by(models.SolarPotential.computed_at.desc())
            .first()
        )
        capacity_factor_pct = latest.capacity_factor_pct if latest and latest.capacity_factor_pct else 18.0
    else:
        latest = (
            db.query(models.WindPotential)
            .filter(models.WindPotential.site_id == site.id)
            .order_by(models.WindPotential.computed_at.desc())
            .first()
        )
        capacity_factor_pct = latest.capacity_factor_pct if latest and latest.capacity_factor_pct else 30.0

    capacity_kw = capacity_mw * 1000
    avg_output_kw = capacity_kw * (capacity_factor_pct / 100)
    rng = random.Random(site.id)  # deterministic per-site seed, not true randomness

    series = []
    for h in range(hours):
        hour_of_day = h % 24
        if technology == "solar":
            # Zero output outside 6am-6pm; sine-shaped peak at solar noon,
            # scaled so the 24h mean equals avg_output_kw (a plain sine
            # half-wave averages 2/pi of its peak).
            if 6 <= hour_of_day <= 18:
                peak_kw = avg_output_kw * math.pi
                fraction = math.sin(math.pi * (hour_of_day - 6) / 12)
                output_kw = round(max(peak_kw * fraction, 0), 1)
            else:
                output_kw = 0.0
        else:
            fluctuation = 1 + (rng.uniform(-0.35, 0.35))
            output_kw = round(max(avg_output_kw * fluctuation, 0), 1)
        series.append({"hour": h, "output_kw": min(output_kw, capacity_kw)})

    return series

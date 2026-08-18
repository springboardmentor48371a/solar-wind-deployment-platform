"""
Data Warehouse rollup — recomputes app.models.SiteRollup from the
operational tables (Sites, SuitabilityScore, SolarPotential,
WindPotential, FinancialAnalysis, EnvironmentalConstraint,
InfrastructureFeature) and optionally exports the same rows to Parquet.

Called on-demand via POST /analytics/warehouse/refresh (admin/PM), and
safe to call as often as needed — it's a full recompute, not an
incremental append, so it never drifts from the source tables.
"""

import datetime
import os

from sqlalchemy.orm import Session

from app import models
from app.config import settings


def _latest(db: Session, model, site_id: int, order_col):
    return (
        db.query(model)
        .filter(model.site_id == site_id)
        .order_by(order_col.desc())
        .first()
    )


def refresh_warehouse(db: Session) -> int:
    """Recomputes the SiteRollup table for every site. Returns row count."""
    sites = db.query(models.Site).all()
    now = datetime.datetime.utcnow()

    for site in sites:
        score = _latest(db, models.SuitabilityScore, site.id, models.SuitabilityScore.computed_at)
        solar = _latest(db, models.SolarPotential, site.id, models.SolarPotential.computed_at)
        wind = _latest(db, models.WindPotential, site.id, models.WindPotential.computed_at)
        fin = _latest(db, models.FinancialAnalysis, site.id, models.FinancialAnalysis.computed_at)
        env = _latest(db, models.EnvironmentalConstraint, site.id, models.EnvironmentalConstraint.fetched_at)

        substation = next(
            (f.distance_km for f in site.infrastructure_features if f.feature_type == "substation"),
            None,
        )
        region_name = (
            site.project.region_ref.name if (site.project and site.project.region_ref)
            else (site.project.region if site.project else None)
        )

        row = db.query(models.SiteRollup).filter(models.SiteRollup.site_id == site.id).first()
        if row is None:
            row = models.SiteRollup(site_id=site.id)
            db.add(row)

        row.project_id = site.project_id
        row.site_name = site.name
        row.region_name = region_name
        row.overall_suitability_score = score.overall_score if score else None
        row.suitability_category = score.category if score else None
        row.solar_expected_output_mwh_yr = solar.expected_energy_output_mwh_yr if solar else None
        row.solar_capacity_factor_pct = solar.capacity_factor_pct if solar else None
        row.wind_expected_aep_mwh_yr = wind.expected_aep_mwh_yr if wind else None
        row.wind_capacity_factor_pct = wind.capacity_factor_pct if wind else None
        row.financial_npv_usd = fin.npv_usd if fin else None
        row.financial_irr_pct = fin.irr_pct if fin else None
        row.financial_lcoe_usd_per_mwh = fin.lcoe_usd_per_mwh if fin else None
        row.protected_area_distance_km = env.protected_area_distance_km if env else None
        row.substation_distance_km = substation
        row.refreshed_at = now

    db.commit()
    _export_parquet(db)
    return len(sites)


def _export_parquet(db: Session) -> None:
    """Best-effort Parquet snapshot for an external warehouse to bulk-load."""
    if not settings.warehouse_export_dir:
        return
    try:
        import pandas as pd  # noqa: local import — only needed when export is configured

        rows = db.query(models.SiteRollup).all()
        df = pd.DataFrame(
            [
                {c.name: getattr(r, c.name) for c in models.SiteRollup.__table__.columns}
                for r in rows
            ]
        )
        os.makedirs(settings.warehouse_export_dir, exist_ok=True)
        path = os.path.join(
            settings.warehouse_export_dir,
            f"site_rollup_{datetime.datetime.utcnow():%Y%m%dT%H%M%S}.parquet",
        )
        df.to_parquet(path, index=False)
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: warehouse Parquet export failed: {exc}")

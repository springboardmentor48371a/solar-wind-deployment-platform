"""
Investment Analytics / financial modeling — NPV, IRR, LCOE, payback
period. Standard deterministic corporate-finance formulas (numpy-based
IRR root-finding), not AI/ML. Feeds the "Investment Intelligence" and
"Financial modeling tools" integration point in the architecture diagram.
"""

import numpy as np
from sqlalchemy.orm import Session

from app import models


def _npv(rate_pct: float, cashflows: list[float]) -> float:
    rate = rate_pct / 100
    return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(cashflows))


def _irr(cashflows: list[float]) -> float | None:
    """Solves for the discount rate that zeroes NPV, via numpy's polynomial roots."""
    try:
        roots = np.roots(list(reversed(cashflows)))
        real_roots = [r.real for r in roots if abs(r.imag) < 1e-6 and r.real > 0]
        if not real_roots:
            return None
        rate = (1 / min(real_roots)) - 1
        return round(rate * 100, 2)
    except Exception:  # noqa: BLE001
        return None


def compute_financial_analysis(
    db: Session,
    site: models.Site,
    *,
    technology: str,
    capacity_mw: float,
    capex_usd: float,
    opex_usd_per_yr: float,
    discount_rate_pct: float,
    project_lifetime_yrs: int,
    electricity_price_usd_per_mwh: float,
    annual_energy_mwh: float,
) -> models.FinancialAnalysis:
    cashflows = [-capex_usd]
    annual_revenue = annual_energy_mwh * electricity_price_usd_per_mwh
    annual_net_cashflow = annual_revenue - opex_usd_per_yr
    cashflows.extend([annual_net_cashflow] * project_lifetime_yrs)

    npv = round(_npv(discount_rate_pct, cashflows), 2)
    irr = _irr(cashflows)

    total_lifetime_energy = annual_energy_mwh * project_lifetime_yrs
    total_lifetime_cost = capex_usd + (opex_usd_per_yr * project_lifetime_yrs)
    lcoe = round(total_lifetime_cost / total_lifetime_energy, 2) if total_lifetime_energy else None

    payback_years = None
    if annual_net_cashflow > 0:
        cumulative = -capex_usd
        for year in range(1, project_lifetime_yrs + 1):
            cumulative += annual_net_cashflow
            if cumulative >= 0:
                payback_years = round(year - (cumulative / annual_net_cashflow), 2)
                break

    record = models.FinancialAnalysis(
        site_id=site.id,
        technology=technology,
        capacity_mw=capacity_mw,
        capex_usd=capex_usd,
        opex_usd_per_yr=opex_usd_per_yr,
        discount_rate_pct=discount_rate_pct,
        project_lifetime_yrs=project_lifetime_yrs,
        electricity_price_usd_per_mwh=electricity_price_usd_per_mwh,
        annual_energy_mwh=annual_energy_mwh,
        npv_usd=npv,
        irr_pct=irr,
        lcoe_usd_per_mwh=lcoe,
        payback_years=payback_years,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

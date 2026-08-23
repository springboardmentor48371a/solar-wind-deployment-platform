"""
Investment Prediction Model (PDF: "Regression/XGBoost") — instant NPV/IRR
estimate without running the full financial.py calculation, trained on
that exact real formula as ground truth. See
app/ml_models/investment_*_gbr.meta.json for full provenance, including
why GradientBoostingRegressor substitutes for XGBoost (network access
to install xgboost was unavailable in this build environment).

Always shown alongside, never in place of, the real financial.py
calculation — this is a fast estimate for screening many scenarios
quickly, not the authoritative number once real assumptions are entered.
"""

import os

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml_models")
_models = {}
_metadata = {}
_load_attempted = {"npv_usd": False, "irr_pct": False}


def _load(target: str):
    if _load_attempted[target]:
        return _models.get(target)
    _load_attempted[target] = True
    path = os.path.join(MODEL_DIR, f"investment_{target}_gbr.joblib")
    meta_path = os.path.join(MODEL_DIR, f"investment_{target}_gbr.meta.json")
    if not os.path.exists(path):
        return None
    try:
        import joblib
        import json

        _models[target] = joblib.load(path)
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                _metadata[target] = json.load(f)
        return _models[target]
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: failed to load investment prediction model ({target}): {exc}")
        return None


def is_model_available() -> bool:
    return _load("npv_usd") is not None and _load("irr_pct") is not None


def model_version() -> str | None:
    _load("npv_usd")
    return _metadata.get("npv_usd", {}).get("version")


def predict_npv_and_irr(
    capacity_mw: float,
    capex_usd: float,
    opex_usd_per_yr: float,
    discount_rate_pct: float,
    project_lifetime_yrs: int,
    electricity_price_usd_per_mwh: float,
    annual_energy_mwh: float,
) -> dict | None:
    npv_model = _load("npv_usd")
    irr_model = _load("irr_pct")
    if npv_model is None or irr_model is None:
        return None
    try:
        import pandas as pd

        features = pd.DataFrame(
            [[capacity_mw, capex_usd, opex_usd_per_yr, discount_rate_pct, project_lifetime_yrs, electricity_price_usd_per_mwh, annual_energy_mwh]],
            columns=["capacity_mw", "capex_usd", "opex_usd_per_yr", "discount_rate_pct", "project_lifetime_yrs", "electricity_price_usd_per_mwh", "annual_energy_mwh"],
        )
        npv_pred = round(float(npv_model.predict(features)[0]), 2)
        irr_pred = round(float(irr_model.predict(features)[0]), 2)
        return {"npv_usd": npv_pred, "irr_pct": irr_pred}
    except Exception as exc:  # noqa: BLE001
        print(f"Warning: ML investment prediction failed: {exc}")
        return None

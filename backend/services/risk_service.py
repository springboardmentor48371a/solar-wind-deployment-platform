def assess_site_risks(
    solar_ghi: float,
    wind_speed_100m: float,
    avg_temp_c: float = 28.0,
    slope_degrees: float = 2.1,
    suitability_score: int = 85
) -> dict:
    """
    Module 12: Automated Threshold & Risk Analysis System.
    Evaluates extreme environmental hazards and terrain constraints.
    """
    alerts = []
    risk_level = "LOW"

    # 1. Extreme Wind Speed Hazard (Turbine Cut-out is typically 25 m/s)
    if wind_speed_100m >= 25.0:
        alerts.append({
            "severity": "CRITICAL",
            "category": "Wind Hazard",
            "message": f"Extreme wind velocity ({wind_speed_100m} m/s) exceeds turbine structural cut-out limit (25 m/s). Risk of mechanical shutdown."
        })
        risk_level = "CRITICAL"
    elif wind_speed_100m < 3.5:
        alerts.append({
            "severity": "WARNING",
            "category": "Low Resource",
            "message": f"Mean wind speed ({wind_speed_100m} m/s) is near turbine cut-in threshold (3.0 m/s). Low aerodynamic yield expected."
        })

    # 2. Thermal Loss Hazard for Solar PV
    if avg_temp_c >= 42.0:
        alerts.append({
            "severity": "WARNING",
            "category": "Thermal Derating",
            "message": f"Elevated ambient temperature ({avg_temp_c}°C) causes severe PV efficiency derating (~0.4%/°C above 25°C)."
        })
        if risk_level != "CRITICAL":
            risk_level = "MEDIUM"

    # 3. Terrain Slope & Civil Engineering Hazard
    if slope_degrees > 10.0:
        alerts.append({
            "severity": "CRITICAL",
            "category": "Topography Constraint",
            "message": f"Terrain slope ({slope_degrees}°) exceeds safe civil grading limit (10°). High risk of erosion and excavation costs."
        })
        risk_level = "CRITICAL"
    elif slope_degrees > 5.0:
        alerts.append({
            "severity": "WARNING",
            "category": "Moderate Slope",
            "message": f"Terrain slope ({slope_degrees}°) requires terracing for ground-mounted Solar PV tracking systems."
        })
        if risk_level == "LOW":
            risk_level = "MEDIUM"

    # 4. Low Overall Feasibility Flag
    if suitability_score < 60:
        alerts.append({
            "severity": "WARNING",
            "category": "Feasibility Concern",
            "message": f"Overall deployment suitability index ({suitability_score}/100) is suboptimal for commercial capital investment."
        })

    return {
        "overall_risk_level": risk_level,
        "active_alerts_count": len(alerts),
        "alerts": alerts
    }
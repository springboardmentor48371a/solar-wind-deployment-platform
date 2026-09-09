import httpx
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def fetch_nasa_power_climatology(latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
    """
    Fetches solar and meteorological parameters from the public NASA POWER Climatology API.
    Does not require an API key.
    
    Returns a dictionary of annual averages or None if the request fails.
    """
    url = "https://power.larc.nasa.gov/api/temporal/climatology/point"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "parameters": "ALLSKY_SFC_SW_DWN,T2M,WS50M,PRECTOTCORR,RH2M,CLOUD_AMT,WD50M",
        "community": "RE",
        "format": "JSON"
    }
    try:
        # Use a 5-second timeout to prevent API slowness from hanging the FastAPI app
        response = httpx.get(url, params=params, timeout=5.0)
        if response.status_code != 200:
            logger.error(f"NASA POWER API returned status code {response.status_code}")
            return None
            
        data = response.json()
        parameter_data = data.get("properties", {}).get("parameter", {})
        
        # Verify that all requested parameters are returned
        required_params = ["ALLSKY_SFC_SW_DWN", "T2M", "WS50M", "PRECTOTCORR", "RH2M", "CLOUD_AMT", "WD50M"]
        if not all(p in parameter_data for p in required_params):
            logger.error("NASA POWER API response missing required parameters.")
            return None
            
        parsed_data = {}
        for param in required_params:
            vals = parameter_data[param]
            if "ANN" not in vals:
                logger.error(f"NASA POWER parameter {param} missing annual average 'ANN'.")
                return None
            parsed_data[param] = float(vals["ANN"])
            
        # Conversion verification:
        # PRECTOTCORR is precipitation corrected in mm/day.
        # We multiply by 365 to convert it to total annual rainfall in mm for our environmental_data table.
        parsed_data["PRECTOTCORR_annual"] = parsed_data["PRECTOTCORR"] * 365.0
        
        return parsed_data

    except Exception as e:
        logger.error(f"Exception raised during NASA POWER query: {e}")
        return None

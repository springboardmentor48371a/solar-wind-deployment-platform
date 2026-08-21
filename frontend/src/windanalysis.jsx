import React, { useState } from "react";
import "./windanalysis.css";

const API_URL = "http://127.0.0.1:8000";

function WindAnalysis() {
  const [location, setLocation] = useState("");
  const [landArea, setLandArea] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ============================================================
  // ANALYZE WIND
  // ============================================================

  const analyzeWind = async () => {
    // Clear old data
    setError("");
    setResult(null);

    // Validate location
    if (!location.trim()) {
      setError("Please enter a location.");
      return;
    }

    // Validate land area
    if (!landArea || Number(landArea) <= 0) {
      setError("Please enter a valid land area.");
      return;
    }

    setLoading(true);

    try {
      // --------------------------------------------------------
      // GET USER ID
      // --------------------------------------------------------
      // If your login stores user_id, it will use that.
      // Otherwise, user ID 1 is used for testing.
      // --------------------------------------------------------

      const storedUserId =
        localStorage.getItem("user_id") ||
        localStorage.getItem("userId");

      const userId = Number(storedUserId || 1);

      if (!userId || userId <= 0) {
        throw new Error("Invalid user ID. Please login again.");
      }

      // --------------------------------------------------------
      // REQUEST BODY
      // --------------------------------------------------------

      const requestBody = {
        user_id: userId,
        location: location.trim(),
        land_area: Number(landArea)
      };

      console.log("WIND REQUEST:", requestBody);

      // --------------------------------------------------------
      // CALL FASTAPI
      // --------------------------------------------------------

      const response = await fetch(
        `${API_URL}/wind-analysis`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Accept: "application/json"
          },

          body: JSON.stringify(requestBody)
        }
      );

      // --------------------------------------------------------
      // READ RESPONSE
      // --------------------------------------------------------

      const data = await response.json();

      console.log("WIND RESPONSE:", data);

      // --------------------------------------------------------
      // HANDLE ERROR
      // --------------------------------------------------------

      if (!response.ok) {
        let message = "Wind analysis failed.";

        if (typeof data.detail === "string") {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail
            .map((item) => item.msg || JSON.stringify(item))
            .join(", ");
        } else if (data.detail) {
          message = JSON.stringify(data.detail);
        }

        throw new Error(message);
      }

      // --------------------------------------------------------
      // SUCCESS
      // --------------------------------------------------------

      setResult(data);

    } catch (err) {
      console.error("WIND ANALYSIS ERROR:", err);

      setError(
        err.message ||
        "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // BACK TO DASHBOARD
  // ============================================================

  const goBack = () => {
    window.history.back();
  };

  // ============================================================
  // SAFELY READ RESULT
  // ============================================================

  const wind = result?.wind || {};

  const score = Number(
    result?.score ??
    wind?.score ??
    0
  );

  const rating =
    result?.rating ||
    wind?.rating ||
    (
      score >= 80
        ? "Excellent"
        : score >= 60
        ? "Good"
        : score >= 40
        ? "Moderate"
        : "Low"
    );

  const capacity =
    result?.capacity ??
    result?.capacity_mw ??
    wind?.capacity ??
    wind?.capacity_mw ??
    "N/A";

  const dailyEnergy =
    result?.energy ??
    result?.daily_energy_mwh ??
    wind?.daily_energy ??
    wind?.daily_energy_mwh ??
    "N/A";

  const annualEnergy =
    result?.annual_energy ??
    result?.annual_energy_mwh ??
    wind?.annual_energy ??
    wind?.annual_energy_mwh ??
    "N/A";

  const capacityFactor =
    result?.capacity_factor ??
    wind?.capacity_factor ??
    "N/A";

  const windSpeed =
    result?.wind_speed ??
    result?.environment?.wind_speed ??
    wind?.wind_speed ??
    "N/A";

  const powerDensity =
    result?.wind_power_density_w_m2 ??
    result?.environment?.wind_power_density_w_m2 ??
    wind?.wind_power_density_w_m2 ??
    "N/A";

  const dataSource =
    result?.data_source ||
    result?.environment?.wind_data_source ||
    "Global Wind Atlas / NASA POWER";

  const resolvedLocation =
    result?.location ||
    result?.site?.resolved_location ||
    location;

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="wind-analysis-page">

      {/* BACK BUTTON */}

      <button
        className="back-button"
        onClick={goBack}
      >
        ← Dashboard
      </button>

      {/* HEADER */}

      <div className="wind-header">

        <div className="wind-icon">
          💨
        </div>

        <div>
          <h1>Wind Analysis</h1>

          <p>
            Analyze wind potential using real environmental data
          </p>
        </div>

      </div>

      {/* MAIN CONTENT */}

      <div className="wind-content">

        {/* ======================================================
            LEFT CARD
        ====================================================== */}

        <div className="wind-input-card">

          <h2>Site Information</h2>

          <p className="wind-description">
            Enter only the location and available land.
            Wind data will be fetched automatically.
          </p>

          {/* LOCATION */}

          <label>
            Location
          </label>

          <input
            type="text"
            value={location}
            onChange={(e) =>
              setLocation(e.target.value)
            }
            placeholder="e.g. Agra, Uttar Pradesh"
            disabled={loading}
          />

          {/* LAND AREA */}

          <label>
            Land Area (acres)
          </label>

          <input
            type="number"
            value={landArea}
            onChange={(e) =>
              setLandArea(e.target.value)
            }
            placeholder="e.g. 100"
            min="0"
            disabled={loading}
          />

          {/* INFORMATION BOX */}

          <div className="wind-info-box">

            <strong>
              💨 Automatic Wind Data
            </strong>

            <p>
              Wind information is retrieved automatically
              by the backend for the selected location.
            </p>

          </div>

          {/* ERROR */}

          {error && (
            <div className="wind-error">
              {error}
            </div>
          )}

          {/* ====================================================
              ANALYZE WIND BUTTON
          ==================================================== */}

          <button
            className="wind-analyze-button"
            onClick={analyzeWind}
            disabled={loading}
          >
            {loading
              ? "⏳ Analyzing..."
              : "💨 Analyze Wind Potential"}
          </button>

        </div>

        {/* ======================================================
            RIGHT RESULT CARD
        ====================================================== */}

        <div className="wind-result-card">

          {/* EMPTY */}

          {!result && !loading && (

            <div className="wind-empty">

              <div className="wind-empty-icon">
                💨
              </div>

              <h2>
                Wind Potential
              </h2>

              <p>
                Enter the location and land area
                to calculate wind potential.
              </p>

            </div>

          )}

          {/* LOADING */}

          {loading && (

            <div className="wind-empty">

              <div className="wind-empty-icon">
                💨
              </div>

              <h2>
                Analyzing Site...
              </h2>

              <p>
                Fetching location and wind data
                from the backend.
              </p>

            </div>

          )}

          {/* RESULT */}

          {result && !loading && (

            <div className="wind-result">

              <div className="wind-result-header">

                <div className="wind-result-icon">
                  💨
                </div>

                <h2>
                  Wind Analysis Result
                </h2>

                <p>
                  {resolvedLocation}
                </p>

              </div>

              {/* SCORE */}

              <div className="wind-score-section">

                <span>
                  Wind Potential Score
                </span>

                <strong>
                  {score}%
                </strong>

                <div className="wind-rating">
                  {rating}
                </div>

              </div>

              {/* DATA GRID */}

              <div className="wind-data-grid">

                {/* LOCATION */}

                <div className="wind-data-box">

                  <span>
                    Location
                  </span>

                  <strong>
                    {resolvedLocation}
                  </strong>

                </div>

                {/* LAND */}

                <div className="wind-data-box">

                  <span>
                    Land Area
                  </span>

                  <strong>
                    {landArea} acres
                  </strong>

                </div>

                {/* WIND SPEED */}

                <div className="wind-data-box">

                  <span>
                    Average Wind Speed
                  </span>

                  <strong>
                    {typeof windSpeed === "number"
                      ? `${windSpeed.toFixed(2)} m/s`
                      : windSpeed}
                  </strong>

                </div>

                {/* POWER DENSITY */}

                <div className="wind-data-box">

                  <span>
                    Wind Power Density
                  </span>

                  <strong>
                    {typeof powerDensity === "number"
                      ? `${powerDensity.toFixed(2)} W/m²`
                      : powerDensity}
                  </strong>

                </div>

                {/* CAPACITY */}

                <div className="wind-data-box">

                  <span>
                    Estimated Capacity
                  </span>

                  <strong>
                    {typeof capacity === "number"
                      ? `${capacity.toFixed(2)} MW`
                      : capacity}
                  </strong>

                </div>

                {/* CAPACITY FACTOR */}

                <div className="wind-data-box">

                  <span>
                    Capacity Factor
                  </span>

                  <strong>
                    {typeof capacityFactor === "number"
                      ? `${capacityFactor.toFixed(1)}%`
                      : capacityFactor}
                  </strong>

                </div>

                {/* DAILY ENERGY */}

                <div className="wind-data-box">

                  <span>
                    Daily Energy
                  </span>

                  <strong>
                    {typeof dailyEnergy === "number"
                      ? `${dailyEnergy.toFixed(2)} MWh`
                      : dailyEnergy}
                  </strong>

                </div>

                {/* ANNUAL ENERGY */}

                <div className="wind-data-box">

                  <span>
                    Annual Energy
                  </span>

                  <strong>
                    {typeof annualEnergy === "number"
                      ? `${annualEnergy.toFixed(2)} MWh`
                      : annualEnergy}
                  </strong>

                </div>

              </div>

              {/* DATA SOURCE */}

              <div className="wind-source">

                <strong>
                  🔬 Data Source
                </strong>

                <p>
                  {typeof dataSource === "string"
                    ? dataSource
                    : JSON.stringify(dataSource)}
                </p>

                <small>
                  Wind data is retrieved automatically
                  by the backend for the selected location.
                </small>

              </div>

            </div>

          )}

        </div>

      </div>

    </div>
  );
}

export default WindAnalysis;
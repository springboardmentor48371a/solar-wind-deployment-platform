import React, { useState } from "react";
import "./index.css";

const API_URL = "http://127.0.0.1:8000";

function SolarAnalysis() {
  const [location, setLocation] = useState("");
  const [landArea, setLandArea] = useState("");

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // ============================================================
  // ANALYZE SOLAR
  // ============================================================

  const analyzeSolar = async () => {
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
        land_area: Number(landArea),
      };

      console.log("SOLAR REQUEST:", requestBody);

      // --------------------------------------------------------
      // CALL BACKEND
      // --------------------------------------------------------

      const response = await fetch(
        `${API_URL}/solar-analysis`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },

          body: JSON.stringify(requestBody),
        }
      );

      // --------------------------------------------------------
      // READ RESPONSE
      // --------------------------------------------------------

      const raw = await response.text();

      console.log("STATUS:", response.status);
      console.log("RAW SOLAR RESPONSE:", raw);

      let data;

      try {
        data = JSON.parse(raw);
      } catch {
        throw new Error(
          `Backend returned non-JSON response: ${raw.substring(
            0,
            300
          )}`
        );
      }

      // --------------------------------------------------------
      // HANDLE BACKEND ERROR
      // --------------------------------------------------------

      if (!response.ok) {
        if (Array.isArray(data.detail)) {
          throw new Error(
            data.detail
              .map((item) => item.msg || JSON.stringify(item))
              .join(", ")
          );
        }

        throw new Error(
          data.detail || `HTTP ${response.status}`
        );
      }

      // --------------------------------------------------------
      // SUCCESS
      // --------------------------------------------------------

      console.log("SOLAR RESPONSE:", data);

      setResult(data);

    } catch (err) {
      console.error("SOLAR ANALYSIS ERROR:", err);

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
    window.location.href = "/dashboard";
  };

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="analysis-page">

      {/* ======================================================
          BACK BUTTON
      ====================================================== */}

      <button
        className="back-button"
        onClick={goBack}
      >
        ← Dashboard
      </button>


      {/* ======================================================
          HEADER
      ====================================================== */}

      <div className="analysis-header">

        <div className="analysis-icon">
          ☀️
        </div>

        <div>

          <h1>
            Solar Analysis
          </h1>

          <p>
            Analyze solar potential using real environmental data
          </p>

        </div>

      </div>


      {/* ======================================================
          MAIN GRID
      ====================================================== */}

      <div className="analysis-grid">


        {/* ====================================================
            INPUT CARD
        ==================================================== */}

        <div className="input-card">

          <h2>
            Site Information
          </h2>

          <p>
            Enter only the location and available land.
            Solar data will be fetched automatically.
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
            placeholder="Example: Shimla"
            disabled={loading}
          />


          {/* LAND AREA */}

          <label>
            Land Area (acres)
          </label>

          <input
            type="number"
            min="0"
            value={landArea}
            onChange={(e) =>
              setLandArea(e.target.value)
            }
            placeholder="Example: 76"
            disabled={loading}
          />


          {/* AUTOMATIC DATA */}

          <div className="automatic-data">

            <strong>
              ☀️ Automatic Solar Data
            </strong>

            <p>
              NASA POWER automatically provides solar
              irradiance, temperature and other environmental
              information for the selected location.
            </p>

          </div>


          {/* ERROR */}

          {error && (

            <div className="error-message">
              {error}
            </div>

          )}


          {/* ANALYZE BUTTON */}

          <button
            className="analyze-button"
            onClick={analyzeSolar}
            disabled={loading}
          >

            {loading
              ? "⏳ Analyzing..."
              : "☀️ Analyze Solar Potential"}

          </button>

        </div>


        {/* ====================================================
            RESULT CARD
        ==================================================== */}

        <div className="result-card">


          {/* ==================================================
              EMPTY STATE
          ================================================== */}

          {!result && !loading && (

            <div className="empty-result">

              <div className="large-sun">
                ☀️
              </div>

              <h2>
                Solar Potential
              </h2>

              <p>
                Enter the location and land area.
                The backend will automatically retrieve
                real environmental information and
                calculate the solar potential.
              </p>

            </div>

          )}


          {/* ==================================================
              LOADING STATE
          ================================================== */}

          {loading && (

            <div className="empty-result">

              <div className="large-sun">
                ☀️
              </div>

              <h2>
                Analyzing...
              </h2>

              <p>
                Converting location into coordinates
                and fetching environmental data...
              </p>

            </div>

          )}


          {/* ==================================================
              RESULT
          ================================================== */}

          {result && (

            <div className="result-content">


              {/* RESULT HEADER */}

              <div className="result-title">

                <div className="large-sun">
                  ☀️
                </div>

                <div>

                  <h2>
                    Solar Analysis Result
                  </h2>

                  <p>
                    {result.location}
                  </p>

                </div>

              </div>


              {/* SCORE */}

              <div className="score-section">

                <span>
                  Solar Potential Score
                </span>

                <div className="score">
                  {result.score}%
                </div>

                <div className="rating">
                  {result.rating}
                </div>

              </div>


              {/* =================================================
                  RESULT GRID
              ================================================= */}

              <div className="result-grid">


                {/* LOCATION */}

                <div className="result-item">

                  <span>
                    Location
                  </span>

                  <strong>
                    {result.location}
                  </strong>

                </div>


                {/* LATITUDE */}

                <div className="result-item">

                  <span>
                    Latitude
                  </span>

                  <strong>
                    {result.latitude !== undefined &&
                    result.latitude !== null
                      ? Number(result.latitude).toFixed(6)
                      : "N/A"}
                  </strong>

                </div>


                {/* LONGITUDE */}

                <div className="result-item">

                  <span>
                    Longitude
                  </span>

                  <strong>
                    {result.longitude !== undefined &&
                    result.longitude !== null
                      ? Number(result.longitude).toFixed(6)
                      : "N/A"}
                  </strong>

                </div>


                {/* LAND AREA */}

                <div className="result-item">

                  <span>
                    Land Area
                  </span>

                  <strong>
                    {result.land_area} acres
                  </strong>

                </div>


                {/* SOLAR IRRADIANCE */}

                <div className="result-item">

                  <span>
                    Solar Irradiance
                  </span>

                  <strong>
                    {result.irradiance}
                  </strong>

                </div>


                {/* TEMPERATURE */}

                <div className="result-item">

                  <span>
                    Temperature
                  </span>

                  <strong>
                    {result.temperature} °C
                  </strong>

                </div>


                {/* SOLAR CAPACITY */}

                <div className="result-item">

                  <span>
                    Solar Capacity
                  </span>

                  <strong>
                    {result.capacity} MW
                  </strong>

                </div>


                {/* DAILY ENERGY */}

                <div className="result-item">

                  <span>
                    Daily Energy
                  </span>

                  <strong>
                    {result.energy} MWh
                  </strong>

                </div>


                {/* ANNUAL ENERGY */}

                <div className="result-item">

                  <span>
                    Annual Energy
                  </span>

                  <strong>
                    {result.annual_energy} MWh
                  </strong>

                </div>


                {/* EFFICIENCY */}

                <div className="result-item">

                  <span>
                    Efficiency
                  </span>

                  <strong>
                    {result.efficiency}%
                  </strong>

                </div>


                {/* DATA SOURCE */}

                <div className="result-item">

                  <span>
                    Data Source
                  </span>

                  <strong>
                    {result.data_source}
                  </strong>

                </div>

              </div>


              {/* =================================================
                  COORDINATE INFORMATION
              ================================================= */}

              <div
                className="automatic-data"
                style={{
                  marginTop: "20px"
                }}
              >

                <strong>
                  📍 Geographic Coordinates
                </strong>

                <p>
                  The location was automatically converted
                  into latitude and longitude using
                  OpenStreetMap geocoding.
                </p>

                <p>
                  <strong>
                    Latitude:
                  </strong>{" "}
                  {result.latitude !== undefined
                    ? Number(result.latitude).toFixed(6)
                    : "N/A"}
                </p>

                <p>
                  <strong>
                    Longitude:
                  </strong>{" "}
                  {result.longitude !== undefined
                    ? Number(result.longitude).toFixed(6)
                    : "N/A"}
                </p>

              </div>


            </div>

          )}

        </div>

      </div>

    </div>
  );
}

export default SolarAnalysis;
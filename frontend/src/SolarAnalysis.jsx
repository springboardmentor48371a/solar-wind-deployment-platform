import React, { useState } from "react";
import "./SolarAnalysis.css";

function SolarAnalysis({ user, onBack }) {
  const [form, setForm] = useState({
    location: "",
    landArea: "",
    irradiance: "",
    temperature: "",
    cloudCover: "",
  });

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((prev) => ({
      ...prev,
      [name]: value,
    }));

    setError("");
  };

  const analyzeSolar = (e) => {
    e.preventDefault();

    setError("");
    setResult(null);

    // Convert input values to numbers
    const landArea = Number(form.landArea);
    const irradiance = Number(form.irradiance);
    const temperature = Number(form.temperature);
    const cloudCover = Number(form.cloudCover);

    // Validation
    if (!form.location.trim()) {
      setError("Please enter a location.");
      return;
    }

    if (landArea <= 0) {
      setError("Land area must be greater than 0.");
      return;
    }

    if (irradiance <= 0) {
      setError("Solar irradiance must be greater than 0.");
      return;
    }

    if (temperature === "" || Number.isNaN(temperature)) {
      setError("Please enter the average temperature.");
      return;
    }

    if (
      cloudCover === "" ||
      Number.isNaN(cloudCover) ||
      cloudCover < 0 ||
      cloudCover > 100
    ) {
      setError("Cloud cover must be between 0 and 100.");
      return;
    }

    /*
    =====================================================
    SOLAR POTENTIAL CALCULATION
    =====================================================

    This is currently a preliminary calculation.
    Later this can be replaced by the FastAPI/ML model.
    */

    // Base panel efficiency
    let efficiency = 20;

    // Cloud cover reduces efficiency
    efficiency -= cloudCover * 0.08;

    // High temperature reduces efficiency
    if (temperature > 25) {
      efficiency -= (temperature - 25) * 0.25;
    }

    // Keep efficiency within realistic demo limits
    efficiency = Math.max(10, Math.min(22, efficiency));

    // Estimated installed capacity
    const capacityMW = landArea * 0.04;

    // Estimated daily energy production
    const dailyEnergy =
      capacityMW *
      irradiance *
      (efficiency / 100);

    // Solar potential score
    let score =
      irradiance * 12 +
      (100 - cloudCover) * 0.25;

    // Keep score between 0 and 100
    score = Math.max(0, Math.min(100, score));

    // Rating
    let rating = "Moderate";

    if (score >= 80) {
      rating = "Excellent";
    } else if (score >= 60) {
      rating = "Good";
    }

    // Save result
    setResult({
      score: score.toFixed(1),
      rating,
      capacity: capacityMW.toFixed(2),
      energy: dailyEnergy.toFixed(2),
      efficiency: efficiency.toFixed(1),
    });
  };

  return (
    <div className="solar-page">

      {/* =================================================
          HEADER
      ================================================= */}

      <header className="solar-header">

        <button
          className="back-btn"
          onClick={onBack}
          type="button"
        >
          ← Dashboard
        </button>

        <div className="solar-user">

          <div className="solar-user-icon">
            {(user?.name || "User")
              .charAt(0)
              .toUpperCase()}
          </div>

          <div>
            <strong>
              {user?.name || "User"}
            </strong>

            <span>
              {user?.email || ""}
            </span>
          </div>

        </div>

      </header>


      {/* =================================================
          TITLE
      ================================================= */}

      <section className="solar-title">

        <div className="solar-title-icon">
          ☀️
        </div>

        <div>
          <h1>Solar Analysis</h1>

          <p>
            Analyze the solar energy potential of a location
          </p>
        </div>

      </section>


      {/* =================================================
          MAIN CONTENT
      ================================================= */}

      <div className="solar-content">


        {/* =================================================
            INPUT CARD
        ================================================= */}

        <div className="solar-card">

          <div className="solar-card-header">

            <h2>
              Site Information
            </h2>

            <p>
              Enter the environmental and site parameters
            </p>

          </div>


          <form onSubmit={analyzeSolar}>

            {/* LOCATION */}

            <div className="input-group">

              <label>
                Location
              </label>

              <input
                type="text"
                name="location"
                placeholder="e.g. Visakhapatnam, Andhra Pradesh"
                value={form.location}
                onChange={handleChange}
              />

            </div>


            {/* LAND + IRRADIANCE */}

            <div className="input-row">

              <div className="input-group">

                <label>
                  Land Area (acres)
                </label>

                <input
                  type="number"
                  name="landArea"
                  placeholder="e.g. 100"
                  min="1"
                  step="0.1"
                  value={form.landArea}
                  onChange={handleChange}
                />

              </div>


              <div className="input-group">

                <label>
                  Solar Irradiance (kWh/m²/day)
                </label>

                <input
                  type="number"
                  name="irradiance"
                  placeholder="e.g. 5.5"
                  min="0"
                  step="0.1"
                  value={form.irradiance}
                  onChange={handleChange}
                />

              </div>

            </div>


            {/* TEMPERATURE + CLOUD */}

            <div className="input-row">

              <div className="input-group">

                <label>
                  Average Temperature (°C)
                </label>

                <input
                  type="number"
                  name="temperature"
                  placeholder="e.g. 28"
                  step="0.1"
                  value={form.temperature}
                  onChange={handleChange}
                />

              </div>


              <div className="input-group">

                <label>
                  Cloud Cover (%)
                </label>

                <input
                  type="number"
                  name="cloudCover"
                  placeholder="e.g. 20"
                  min="0"
                  max="100"
                  step="1"
                  value={form.cloudCover}
                  onChange={handleChange}
                />

              </div>

            </div>


            {/* ERROR */}

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}


            {/* ANALYZE BUTTON */}

            <button
              type="submit"
              className="analyze-btn"
            >
              ☀️ Analyze Solar Potential
            </button>

          </form>

        </div>


        {/* =================================================
            RESULT CARD
        ================================================= */}

        <div className="solar-card result-card">

          {!result ? (

            /* EMPTY RESULT */

            <div className="empty-result">

              <div className="empty-icon">
                ☀️
              </div>

              <h2>
                Solar Potential
              </h2>

              <p>
                Enter the site information and click
                <strong>
                  {" "}Analyze Solar Potential{" "}
                </strong>
                to see the results.
              </p>

            </div>

          ) : (

            /* RESULT */

            <>

              {/* RESULT HEADER */}

              <div className="result-header">

                <div>

                  <h2>
                    Analysis Result
                  </h2>

                  <p>
                    {form.location}
                  </p>

                </div>

                <div className="rating">
                  {result.rating}
                </div>

              </div>


              {/* SCORE */}

              <div className="potential-score">

                <span>
                  Solar Potential Score
                </span>

                <strong>
                  {result.score}%
                </strong>

                <div className="score-bar">

                  <div
                    style={{
                      width: `${result.score}%`,
                    }}
                  />

                </div>

              </div>


              {/* RESULT GRID */}

              <div className="result-grid">


                {/* CAPACITY */}

                <div className="result-box">

                  <span>
                    Estimated Capacity
                  </span>

                  <strong>
                    {result.capacity} MW
                  </strong>

                </div>


                {/* ENERGY */}

                <div className="result-box">

                  <span>
                    Daily Energy
                  </span>

                  <strong>
                    {result.energy} MWh
                  </strong>

                </div>


                {/* EFFICIENCY */}

                <div className="result-box">

                  <span>
                    Panel Efficiency
                  </span>

                  <strong>
                    {result.efficiency}%
                  </strong>

                </div>


                {/* LAND */}

                <div className="result-box">

                  <span>
                    Land Area
                  </span>

                  <strong>
                    {form.landArea} acres
                  </strong>

                </div>

              </div>


              {/* RECOMMENDATION */}

              <div className="recommendation">

                <h3>
                  💡 Recommendation
                </h3>

                <p>
                  This location has a{" "}
                  <strong>
                    {result.rating.toLowerCase()}
                  </strong>{" "}
                  solar energy potential. Further
                  geographical and environmental analysis
                  can be performed before final deployment.
                </p>

              </div>

            </>

          )}

        </div>

      </div>

    </div>
  );
}

export default SolarAnalysis;
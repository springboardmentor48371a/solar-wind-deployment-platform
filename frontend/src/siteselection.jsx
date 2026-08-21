import React, { useState } from "react";
import "./siteselection.css";

function SiteSelection() {
  const [location, setLocation] = useState("");
  const [area, setArea] = useState("");
  const [result, setResult] = useState(null);

  const goTo = (path) => {
    window.location.href = path;
  };

  const analyzeSite = () => {
    if (!location.trim() || !area) {
      alert("Please enter location and land area.");
      return;
    }

    const land = Number(area);

    // Simple rule-based site suitability calculation
    const solarScore = Math.min(95, Math.max(45, 65 + land * 0.25));
    const windScore = Math.min(92, Math.max(40, 55 + land * 0.18));

    const overallScore = (solarScore * 0.6 + windScore * 0.4).toFixed(1);

    let category = "Moderate";
    if (overallScore >= 80) category = "Excellent";
    else if (overallScore >= 65) category = "Good";

    const technology =
      solarScore >= windScore
        ? "Solar Energy"
        : "Wind Energy";

    setResult({
      solar: solarScore.toFixed(1),
      wind: windScore.toFixed(1),
      overall: overallScore,
      category,
      technology,
    });
  };

  return (
    <div className="site-selection-page">

      {/* HEADER */}
      <header className="site-header">

        <button
          className="back-button"
          onClick={() => goTo("/dashboard")}
        >
          ← Dashboard
        </button>

        <div className="site-user">
          <div className="site-avatar">U</div>
          <strong>User</strong>
        </div>

      </header>

      {/* TITLE */}
      <section className="site-title">

        <div className="site-title-icon">
          🗺️
        </div>

        <div>
          <h1>Site Selection</h1>
          <p>
            Find the most suitable renewable energy technology
            for your location.
          </p>
        </div>

      </section>

      {/* MAIN */}
      <main className="site-container">

        {/* INPUT CARD */}
        <section className="site-input-card">

          <h2>Site Information</h2>

          <p>
            Enter your location and available land area to
            evaluate renewable energy potential.
          </p>

          <label>Location</label>

          <input
            type="text"
            placeholder="e.g. Agra"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
          />

          <label>Land Area (acres)</label>

          <input
            type="number"
            placeholder="e.g. 50"
            value={area}
            onChange={(e) => setArea(e.target.value)}
          />

          <div className="info-box">
            🌍 Environmental data will be considered automatically
            for the selected site.
          </div>

          <button
            className="analyze-site-button"
            onClick={analyzeSite}
          >
            🗺️ Analyze Site
          </button>

        </section>

        {/* RESULT CARD */}
        <section className="site-result-card">

          {!result ? (
            <div className="empty-result">

              <div className="large-icon">
                🗺️
              </div>

              <h2>Site Suitability</h2>

              <p>
                Enter location and land area to evaluate
                the site.
              </p>

            </div>
          ) : (

            <div className="result-content">

              <h2>Site Selection Result</h2>

              <p className="result-location">
                📍 {location}
              </p>

              <div className="overall-score">

                <span>Overall Suitability</span>

                <strong>
                  {result.overall}%
                </strong>

                <div className="score-category">
                  {result.category}
                </div>

              </div>

              <div className="result-grid">

                <div className="result-box">
                  <span>☀️ Solar Potential</span>
                  <strong>{result.solar}%</strong>
                </div>

                <div className="result-box">
                  <span>💨 Wind Potential</span>
                  <strong>{result.wind}%</strong>
                </div>

                <div className="result-box">
                  <span>🌱 Land Area</span>
                  <strong>{area} acres</strong>
                </div>

                <div className="result-box recommended">
                  <span>⚡ Recommended Technology</span>
                  <strong>{result.technology}</strong>
                </div>

              </div>

              <div className="recommendation">
                <h3>Recommendation</h3>

                <p>
                  Based on the available land and calculated
                  renewable potential,{" "}
                  <strong>{result.technology}</strong>{" "}
                  is currently the recommended technology
                  for this site.
                </p>
              </div>

            </div>

          )}

        </section>

      </main>

    </div>
  );
}

export default SiteSelection;
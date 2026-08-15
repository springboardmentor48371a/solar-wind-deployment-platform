import { useState } from "react";
import "./windanalysis.css";

function WindAnalysis({ user, onBack }) {
  const [form, setForm] = useState({
    location: "",
    landArea: "",
    windSpeed: "",
    temperature: "",
    airDensity: "1.225",
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const analyzeWind = async (e) => {
    e.preventDefault();

    if (
      !form.location ||
      !form.landArea ||
      !form.windSpeed ||
      !form.temperature ||
      !form.airDensity
    ) {
      alert("Please fill all fields.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/wind-analysis",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            location: form.location,
            land_area: Number(form.landArea),
            wind_speed: Number(form.windSpeed),
            temperature: Number(form.temperature),
            air_density: Number(form.airDensity),
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Wind analysis failed");
      }

      setResult(data);
    } catch (error) {
      console.error(error);
      alert(
        "Wind endpoint is not available yet. Add the backend code below."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="wind-page">

      <header className="wind-header">
        <button className="back-btn" onClick={onBack}>
          ← Dashboard
        </button>

        <div className="wind-user">
          <div className="wind-user-icon">
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>

          <div>
            <strong>{user?.name || "User"}</strong>
            <span>{user?.email || ""}</span>
          </div>
        </div>
      </header>

      <section className="wind-title">
        <div className="wind-title-icon">🌬️</div>

        <div>
          <h1>Wind Analysis</h1>
          <p>Analyze the wind energy potential of a location</p>
        </div>
      </section>

      <div className="wind-content">

        <div className="wind-card">

          <div className="wind-card-header">
            <h2>Site Information</h2>
            <p>Enter the environmental and site parameters</p>
          </div>

          <form onSubmit={analyzeWind}>

            <div className="input-group">
              <label>Location</label>

              <input
                type="text"
                name="location"
                placeholder="e.g. Visakhapatnam"
                value={form.location}
                onChange={handleChange}
              />
            </div>

            <div className="input-row">

              <div className="input-group">
                <label>Land Area (acres)</label>

                <input
                  type="number"
                  name="landArea"
                  placeholder="e.g. 100"
                  min="1"
                  value={form.landArea}
                  onChange={handleChange}
                />
              </div>

              <div className="input-group">
                <label>Average Wind Speed (m/s)</label>

                <input
                  type="number"
                  name="windSpeed"
                  placeholder="e.g. 7.5"
                  step="0.1"
                  min="0"
                  value={form.windSpeed}
                  onChange={handleChange}
                />
              </div>

            </div>

            <div className="input-row">

              <div className="input-group">
                <label>Average Temperature (°C)</label>

                <input
                  type="number"
                  name="temperature"
                  placeholder="e.g. 30"
                  value={form.temperature}
                  onChange={handleChange}
                />
              </div>

              <div className="input-group">
                <label>Air Density (kg/m³)</label>

                <input
                  type="number"
                  name="airDensity"
                  placeholder="e.g. 1.225"
                  step="0.001"
                  value={form.airDensity}
                  onChange={handleChange}
                />
              </div>

            </div>

            <button
              type="submit"
              className="analyze-btn"
              disabled={loading}
            >
              {loading
                ? "⏳ Analyzing..."
                : "🌬️ Analyze Wind Potential"}
            </button>

          </form>
        </div>

        <div className="wind-card result-card">

          {!result ? (
            <div className="empty-result">
              <div className="empty-icon">🌬️</div>

              <h2>Wind Potential</h2>

              <p>
                Enter site information and click
                <strong> Analyze Wind Potential </strong>
                to see the results.
              </p>
            </div>
          ) : (

            <>
              <div className="result-header">

                <div>
                  <h2>Analysis Result</h2>
                  <p>{result.location}</p>
                </div>

                <div className="rating">
                  {result.rating}
                </div>

              </div>

              <div className="potential-score">

                <span>Wind Potential Score</span>

                <strong>{result.score}%</strong>

                <div className="score-bar">
                  <div
                    style={{
                      width: `${result.score}%`,
                    }}
                  />
                </div>

              </div>

              <div className="result-grid">

                <div className="result-box">
                  <span>Estimated Capacity</span>
                  <strong>{result.capacity} MW</strong>
                </div>

                <div className="result-box">
                  <span>Daily Energy</span>
                  <strong>{result.energy} MWh</strong>
                </div>

                <div className="result-box">
                  <span>Capacity Factor</span>
                  <strong>{result.capacity_factor}%</strong>
                </div>

                <div className="result-box">
                  <span>Wind Speed</span>
                  <strong>{result.wind_speed} m/s</strong>
                </div>

              </div>

              <div className="recommendation">
                <h3>💡 Recommendation</h3>

                <p>
                  This location has a{" "}
                  <strong>
                    {result.rating.toLowerCase()}
                  </strong>{" "}
                  wind energy potential. Further wind-resource
                  and geographical analysis should be performed
                  before final deployment.
                </p>
              </div>
            </>
          )}

        </div>
      </div>
    </div>
  );
}

export default WindAnalysis;
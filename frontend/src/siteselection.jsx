import React, { useState } from "react";
import "./siteselection.css";

function SiteSelection({ user, onBack }) {
  const [form, setForm] = useState({
    location: "",
    landArea: "",
    irradiance: "",
    windSpeed: "",
  });

  const [results, setResults] = useState(null);

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const findSites = (e) => {
    e.preventDefault();

    if (
      !form.location ||
      !form.landArea ||
      !form.irradiance ||
      !form.windSpeed
    ) {
      return;
    }

    setResults([
      {
        name: `${form.location} North`,
        type: "Solar + Wind",
        capacity: "12.4 MW",
        score: 98,
      },
      {
        name: `${form.location} East`,
        type: "Solar",
        capacity: "9.8 MW",
        score: 95,
      },
      {
        name: `${form.location} South`,
        type: "Wind",
        capacity: "8.6 MW",
        score: 92,
      },
    ]);
  };

  return (
    <div className="site-page">

      {/* HEADER */}
      <header className="module-header">

        <button
          className="module-back-btn"
          onClick={onBack}
        >
          ← Dashboard
        </button>

        <div className="module-user">

          <div className="module-avatar">
            {user?.name?.charAt(0)?.toUpperCase() || "U"}
          </div>

          <div className="module-user-info">
            <strong>{user?.name || "User"}</strong>
            <span>{user?.email || ""}</span>
          </div>

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
            Find the best locations for renewable energy deployment
          </p>
        </div>

      </section>


      <main className="site-container">

        {/* REQUIREMENTS */}
        <section className="site-card">

          <div className="site-card-header">
            <h2>Site Requirements</h2>
            <p>
              Enter your requirements to find suitable locations
            </p>
          </div>

          <form onSubmit={findSites}>

            <div className="site-input-grid">

              <div className="site-input-group">
                <label>Region / Location</label>

                <input
                  type="text"
                  name="location"
                  placeholder="e.g. Vizag"
                  value={form.location}
                  onChange={handleChange}
                  required
                />
              </div>


              <div className="site-input-group">
                <label>Available Land (acres)</label>

                <input
                  type="number"
                  name="landArea"
                  placeholder="e.g. 100"
                  min="1"
                  value={form.landArea}
                  onChange={handleChange}
                  required
                />
              </div>


              <div className="site-input-group">
                <label>Solar Irradiance</label>

                <input
                  type="number"
                  name="irradiance"
                  placeholder="e.g. 5.2"
                  step="0.1"
                  min="0"
                  value={form.irradiance}
                  onChange={handleChange}
                  required
                />
              </div>


              <div className="site-input-group">
                <label>Wind Speed (m/s)</label>

                <input
                  type="number"
                  name="windSpeed"
                  placeholder="e.g. 6.0"
                  step="0.1"
                  min="0"
                  value={form.windSpeed}
                  onChange={handleChange}
                  required
                />
              </div>

            </div>


            <button
              type="submit"
              className="find-sites-btn"
            >
              🗺️ Find Best Sites
            </button>

          </form>

        </section>


        {/* RESULTS */}
        {results && (
          <section className="site-results-card">

            <div className="site-results-header">
              <div>
                <h2>AI Recommended Sites</h2>
                <p>
                  Best locations based on your requirements
                </p>
              </div>

              <span>3 Sites</span>
            </div>


            {results.map((site, index) => (
              <div
                className="site-result"
                key={site.name}
              >

                <div className="site-rank">
                  {index + 1}
                </div>

                <div className="site-result-info">

                  <h3>{site.name}</h3>

                  <p>{site.type}</p>

                  <span>
                    Estimated Capacity: {site.capacity}
                  </span>

                </div>

                <div className="site-score">

                  <strong>
                    {site.score}%
                  </strong>

                  <span>
                    Match Score
                  </span>

                </div>

              </div>
            ))}

          </section>
        )}

      </main>

    </div>
  );
}

export default SiteSelection;
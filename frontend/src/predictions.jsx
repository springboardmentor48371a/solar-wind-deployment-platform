import React, { useState } from "react";
import "./predictions.css";

function Predictions({ user, onBack }) {
  const [type, setType] = useState("Solar");

  const solarData = [
    { month: "Jan", value: 62 },
    { month: "Feb", value: 68 },
    { month: "Mar", value: 74 },
    { month: "Apr", value: 81 },
    { month: "May", value: 88 },
    { month: "Jun", value: 94 },
  ];

  const windData = [
    { month: "Jan", value: 55 },
    { month: "Feb", value: 61 },
    { month: "Mar", value: 67 },
    { month: "Apr", value: 73 },
    { month: "May", value: 80 },
    { month: "Jun", value: 87 },
  ];

  const data = type === "Solar" ? solarData : windData;

  return (
    <div className="prediction-page">

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
      <section className="prediction-title">

        <div className="prediction-icon">
          📈
        </div>

        <div>
          <h1>Energy Predictions</h1>

          <p>
            Forecast renewable energy deployment potential
          </p>
        </div>

      </section>


      {/* FORECAST */}
      <main className="prediction-container">

        <section className="prediction-card">

          <div className="prediction-header">

            <div>
              <h2>6 Month Forecast</h2>

              <p>
                Predicted energy potential
              </p>
            </div>

            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
            >
              <option>Solar</option>
              <option>Wind</option>
            </select>

          </div>


          {/* CHART */}

          <div className="prediction-chart">

            {data.map((item) => (

              <div
                className="prediction-column"
                key={item.month}
              >

                <strong>
                  {item.value}%
                </strong>

                <div className="prediction-bar-area">

                  <div
                    className="prediction-bar"
                    style={{
                      height: `${item.value}%`,
                    }}
                  ></div>

                </div>

                <span>
                  {item.month}
                </span>

              </div>

            ))}

          </div>


          {/* SUMMARY */}

          <div className="prediction-summary">

            <div>
              <span>Current Potential</span>
              <strong>{data[0].value}%</strong>
            </div>

            <div>
              <span>6 Month Potential</span>
              <strong>{data[5].value}%</strong>
            </div>

            <div>
              <span>Growth</span>
              <strong>
                +{data[5].value - data[0].value}%
              </strong>
            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Predictions;
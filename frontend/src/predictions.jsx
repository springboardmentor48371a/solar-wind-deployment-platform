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
    { month: "Jun", value: 94 }
  ];

  const windData = [
    { month: "Jan", value: 55 },
    { month: "Feb", value: 61 },
    { month: "Mar", value: 67 },
    { month: "Apr", value: 73 },
    { month: "May", value: 80 },
    { month: "Jun", value: 87 }
  ];

  const data =
    type === "Solar"
      ? solarData
      : windData;

  const userName =
    user?.name ||
    user?.full_name ||
    "User";

  const userEmail =
    user?.email ||
    "";

  return (

    <div className="prediction-page">

      <header className="module-header">

        <button
          className="module-back-btn"
          onClick={
            onBack ||
            (() => {
              window.location.href =
                "/dashboard";
            })
          }
        >
          ← Dashboard
        </button>


        <div className="module-user">

          <div className="module-avatar">

            {userName
              .charAt(0)
              .toUpperCase()}

          </div>

          <div className="module-user-info">

            <strong>
              {userName}
            </strong>

            <span>
              {userEmail}
            </span>

          </div>

        </div>

      </header>


      <section className="prediction-title">

        <div className="prediction-icon">
          📈
        </div>

        <div>

          <h1>
            Energy Predictions
          </h1>

          <p>
            Forecast renewable energy deployment potential
          </p>

        </div>

      </section>


      <main className="prediction-container">

        <section className="prediction-card">

          <div className="prediction-header">

            <div>

              <h2>
                6 Month Forecast
              </h2>

              <p>
                Predicted energy potential
              </p>

            </div>


            <select
              value={type}
              onChange={(e) =>
                setType(e.target.value)
              }
            >

              <option value="Solar">
                Solar
              </option>

              <option value="Wind">
                Wind
              </option>

            </select>

          </div>


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
                      height:
                        `${item.value}%`
                    }}
                  />

                </div>

                <span>
                  {item.month}
                </span>

              </div>

            ))}

          </div>


          <div className="prediction-summary">

            <div>

              <span>
                Current Potential
              </span>

              <strong>
                {data[0].value}%
              </strong>

            </div>


            <div>

              <span>
                6 Month Potential
              </span>

              <strong>
                {data[5].value}%
              </strong>

            </div>


            <div>

              <span>
                Growth
              </span>

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
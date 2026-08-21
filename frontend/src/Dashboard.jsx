import React from "react";
import "./dashboard.css";

function Dashboard() {

  // =========================
  // GET LOGGED-IN USER
  // =========================

  let storedUser = {};

  try {
    storedUser = JSON.parse(
      localStorage.getItem("user") || "{}"
    );
  } catch {
    storedUser = {};
  }

  const userName =
    storedUser.name ||
    localStorage.getItem("user_name") ||
    "User";

  const userEmail =
    storedUser.email ||
    localStorage.getItem("user_email") ||
    "";

  const userInitial =
    userName.charAt(0).toUpperCase();

  // =========================
  // NAVIGATION
  // =========================

  const goTo = (path) => {
    window.location.href = path;
  };

  // =========================
  // LOGOUT
  // =========================

  const logout = () => {

    localStorage.removeItem("user");
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_name");
    localStorage.removeItem("user_email");
    localStorage.removeItem("loggedInUser");
    localStorage.removeItem("token");

    window.location.href = "/";
  };

  return (
    <div className="dashboard-container">

      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">

        <div className="logo-section">

          <div className="logo-icons">
            ☀️ 💨
          </div>

          <h1>
            Solar & Wind
          </h1>

          <p>
            Deployment Intelligence
          </p>

        </div>

        <nav className="sidebar-menu">

          {/* DASHBOARD */}

          <button
            className="sidebar-item active"
            onClick={() =>
              goTo("/dashboard")
            }
          >
            <span>📊</span>
            <span>Dashboard</span>
          </button>


          {/* SOLAR */}

          <button
            className="sidebar-item"
            onClick={() =>
              goTo("/solar-analysis")
            }
          >
            <span>☀️</span>
            <span>Solar Analysis</span>
          </button>


          {/* WIND */}

          <button
            className="sidebar-item"
            onClick={() =>
              goTo("/wind-analysis")
            }
          >
            <span>💨</span>
            <span>Wind Analysis</span>
          </button>


          {/* SITE SELECTION */}

          <button
            className="sidebar-item"
            onClick={() =>
              goTo("/site-selection")
            }
          >
            <span>🗺️</span>
            <span>Site Selection</span>
          </button>


          {/* PREDICTIONS */}

          <button
            className="sidebar-item"
            onClick={() =>
              goTo("/predictions")
            }
          >
            <span>📈</span>
            <span>Predictions</span>
          </button>


          {/* REPORTS */}

          <button
            className="sidebar-item"
            onClick={() =>
              goTo("/reports")
            }
          >
            <span>📄</span>
            <span>Reports</span>
          </button>


          {/* LOGOUT */}

          <button
            type="button"
            className="sidebar-item logout-btn"
            onClick={logout}
          >
            <span>🚪</span>
            <span>Logout</span>
          </button>

        </nav>

      </aside>


      {/* ================= MAIN ================= */}

      <main className="dashboard-main">

        {/* HEADER */}

        <header className="dashboard-header">

          <div>

            <h1>
              Dashboard
            </h1>

            <p>
              Renewable energy deployment overview
            </p>

          </div>


          {/* USER */}

          <div className="user-section">

            <div className="user-circle">
              {userInitial}
            </div>

            <div>
              <strong>
                {userName}
              </strong>

              {userEmail && (
                <small
                  style={{
                    display: "block",
                    opacity: 0.7,
                  }}
                >
                  {userEmail}
                </small>
              )}

            </div>

          </div>

        </header>


        {/* ================= WELCOME ================= */}

        <section className="welcome-section">

          <h2>
            Welcome back, {userName} 👋
          </h2>

          <p>
            Monitor and analyze renewable
            energy deployment opportunities.
          </p>

        </section>


        {/* ================= STATISTICS ================= */}

        <section className="stats-grid">

          {/* SOLAR */}

          <div className="stat-card">

            <div className="stat-icon solar">
              ☀️
            </div>

            <div>

              <span>
                Solar Potential
              </span>

              <h2>
                77.6%
              </h2>

              <small>
                Good
              </small>

            </div>

          </div>


          {/* WIND */}

          <div className="stat-card">

            <div className="stat-icon wind">
              💨
            </div>

            <div>

              <span>
                Wind Potential
              </span>

              <h2>
                82.2%
              </h2>

              <small>
                Excellent
              </small>

            </div>

          </div>


          {/* SITES */}

          <div className="stat-card">

            <div className="stat-icon sites">
              🗺️
            </div>

            <div>

              <span>
                Sites Analyzed
              </span>

              <h2>
                12
              </h2>

              <small>
                +3 this month
              </small>

            </div>

          </div>


          {/* REPORTS */}

          <div className="stat-card">

            <div className="stat-icon reports">
              📄
            </div>

            <div>

              <span>
                Reports
              </span>

              <h2>
                3
              </h2>

              <small>
                Generated
              </small>

            </div>

          </div>

        </section>


        {/* ================= CONTENT ================= */}

        <section className="dashboard-content">

          {/* OVERVIEW */}

          <div className="overview-card">

            <h2>
              Renewable Energy Overview
            </h2>

            <p>
              Current deployment potential
            </p>


            <div className="chart-placeholder">

              <div className="bar">

                <span>
                  74%
                </span>

                <div
                  style={{
                    height: "74%",
                  }}
                />

                <label>
                  Jan
                </label>

              </div>


              <div className="bar">

                <span>
                  82%
                </span>

                <div
                  style={{
                    height: "82%",
                  }}
                />

                <label>
                  Feb
                </label>

              </div>


              <div className="bar">

                <span>
                  92%
                </span>

                <div
                  style={{
                    height: "92%",
                  }}
                />

                <label>
                  Mar
                </label>

              </div>


              <div className="bar">

                <span>
                  98%
                </span>

                <div
                  style={{
                    height: "98%",
                  }}
                />

                <label>
                  Apr
                </label>

              </div>

            </div>

          </div>


          {/* QUICK ACTIONS */}

          <div className="quick-actions">

            <h2>
              Quick Actions
            </h2>

            <p>
              Start a new analysis
            </p>


            {/* SOLAR */}

            <button
              type="button"
              onClick={() =>
                goTo("/solar-analysis")
              }
            >

              <span className="quick-icon">
                ☀️
              </span>

              <span className="quick-text">

                <strong>
                  Solar Analysis
                </strong>

                <small>
                  Analyze solar potential
                </small>

              </span>

              <span className="arrow">
                →
              </span>

            </button>


            {/* WIND */}

            <button
              type="button"
              onClick={() =>
                goTo("/wind-analysis")
              }
            >

              <span className="quick-icon">
                💨
              </span>

              <span className="quick-text">

                <strong>
                  Wind Analysis
                </strong>

                <small>
                  Analyze wind potential
                </small>

              </span>

              <span className="arrow">
                →
              </span>

            </button>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;
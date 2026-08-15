import "./dashboard.css";

function Dashboard({ user, onLogout, onNavigate }) {
  return (
    <div className="dashboard-page">

      {/* ================= SIDEBAR ================= */}
      <aside className="dashboard-sidebar">

        <div className="brand">

          <div className="brand-icons">
            <span>☀️</span>
            <span>🌬️</span>
          </div>

          <h1>Solar & Wind</h1>

          <p>Deployment Intelligence</p>

        </div>


        {/* NAVIGATION */}

        <nav className="sidebar-nav">

          <button
            className="nav-item active"
            onClick={() => onNavigate("dashboard")}
          >
            📊
            <span>Dashboard</span>
          </button>


          <button
            className="nav-item"
            onClick={() => onNavigate("solar")}
          >
            ☀️
            <span>Solar Analysis</span>
          </button>


          <button
            className="nav-item"
            onClick={() => onNavigate("wind")}
          >
            🌬️
            <span>Wind Analysis</span>
          </button>


          <button
            className="nav-item"
            onClick={() => onNavigate("sites")}
          >
            🗺️
            <span>Site Selection</span>
          </button>


          <button
            className="nav-item"
            onClick={() => onNavigate("predictions")}
          >
            📈
            <span>Predictions</span>
          </button>


          <button
            className="nav-item"
            onClick={() => onNavigate("reports")}
          >
            📄
            <span>Reports</span>
          </button>

        </nav>


        {/* LOGOUT */}

        <div className="sidebar-bottom">

          <button
            className="logout-btn"
            onClick={onLogout}
          >
            🚪
            <span>Logout</span>
          </button>

        </div>

      </aside>


      {/* ================= MAIN CONTENT ================= */}

      <main className="dashboard-main">

        {/* HEADER */}

        <header className="dashboard-header">

          <div>

            <h2>Dashboard</h2>

            <p>
              Renewable energy deployment overview
            </p>

          </div>


          <div className="user-profile">

            <div className="user-avatar">
              {user?.name?.charAt(0)?.toUpperCase() || "U"}
            </div>

            <div className="user-details">

              <strong>
                {user?.name || "User"}
              </strong>

              <span>
                {user?.email || ""}
              </span>

            </div>

          </div>

        </header>


        {/* ================= WELCOME ================= */}

        <section className="welcome-section">

          <div>

            <h1>
              Welcome back, {user?.name || "User"} 👋
            </h1>

            <p>
              Monitor and analyze renewable energy
              deployment opportunities.
            </p>

          </div>

        </section>


        {/* ================= STAT CARDS ================= */}

        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-icon solar-icon">
              ☀️
            </div>

            <div>

              <span>Solar Potential</span>

              <strong>77.6%</strong>

              <small>Good</small>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon wind-icon">
              🌬️
            </div>

            <div>

              <span>Wind Potential</span>

              <strong>82.2%</strong>

              <small>Excellent</small>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon site-icon">
              🗺️
            </div>

            <div>

              <span>Sites Analyzed</span>

              <strong>12</strong>

              <small>+3 this month</small>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon report-icon">
              📄
            </div>

            <div>

              <span>Reports</span>

              <strong>3</strong>

              <small>Generated</small>

            </div>

          </div>

        </section>


        {/* ================= CONTENT GRID ================= */}

        <section className="dashboard-grid">


          {/* ================= CHART ================= */}

          <div className="dashboard-card overview-card">

            <div className="card-header">

              <div>

                <h2>
                  Renewable Energy Overview
                </h2>

                <p>
                  Current deployment potential
                </p>

              </div>


              <select defaultValue="6">

                <option value="6">
                  Last 6 Months
                </option>

                <option value="12">
                  Last 12 Months
                </option>

              </select>

            </div>


            <div className="chart">

              <div className="chart-y">

                <span>100%</span>
                <span>80%</span>
                <span>60%</span>
                <span>40%</span>
                <span>20%</span>
                <span>0%</span>

              </div>


              <div className="chart-area">

                <div className="grid-line line1"></div>
                <div className="grid-line line2"></div>
                <div className="grid-line line3"></div>
                <div className="grid-line line4"></div>
                <div className="grid-line line5"></div>


                <div className="bars">

                  <div className="bar-group">

                    <div className="bar solar-bar b1">
                      <span>54%</span>
                    </div>

                    <div className="bar wind-bar w1">
                      <span>38%</span>
                    </div>

                    <small>Mar</small>

                  </div>


                  <div className="bar-group">

                    <div className="bar solar-bar b2">
                      <span>65%</span>
                    </div>

                    <div className="bar wind-bar w2">
                      <span>47%</span>
                    </div>

                    <small>Apr</small>

                  </div>


                  <div className="bar-group">

                    <div className="bar solar-bar b3">
                      <span>74%</span>
                    </div>

                    <div className="bar wind-bar w3">
                      <span>57%</span>
                    </div>

                    <small>May</small>

                  </div>


                  <div className="bar-group">

                    <div className="bar solar-bar b4">
                      <span>82%</span>
                    </div>

                    <div className="bar wind-bar w4">
                      <span>66%</span>
                    </div>

                    <small>Jun</small>

                  </div>


                  <div className="bar-group">

                    <div className="bar solar-bar b5">
                      <span>92%</span>
                    </div>

                    <div className="bar wind-bar w5">
                      <span>72%</span>
                    </div>

                    <small>Jul</small>

                  </div>


                  <div className="bar-group">

                    <div className="bar solar-bar b6">
                      <span>98%</span>
                    </div>

                    <div className="bar wind-bar w6">
                      <span>87%</span>
                    </div>

                    <small>Aug</small>

                  </div>

                </div>

              </div>

            </div>


            <div className="chart-legend">

              <span>
                <i className="legend-solar"></i>
                Solar
              </span>

              <span>
                <i className="legend-wind"></i>
                Wind
              </span>

            </div>

          </div>


          {/* ================= QUICK ACTIONS ================= */}

          <div className="dashboard-card quick-card">

            <div className="card-header">

              <div>

                <h2>Quick Actions</h2>

                <p>
                  Start a new analysis
                </p>

              </div>

            </div>


            <div className="quick-actions">


              <button
                className="quick-action"
                onClick={() => onNavigate("solar")}
              >

                <div className="quick-icon">
                  ☀️
                </div>

                <div>

                  <strong>
                    Solar Analysis
                  </strong>

                  <span>
                    Analyze solar potential
                  </span>

                </div>

                <b>→</b>

              </button>


              <button
                className="quick-action"
                onClick={() => onNavigate("wind")}
              >

                <div className="quick-icon">
                  🌬️
                </div>

                <div>

                  <strong>
                    Wind Analysis
                  </strong>

                  <span>
                    Analyze wind potential
                  </span>

                </div>

                <b>→</b>

              </button>


              <button
                className="quick-action"
                onClick={() => onNavigate("sites")}
              >

                <div className="quick-icon">
                  🗺️
                </div>

                <div>

                  <strong>
                    Find Best Site
                  </strong>

                  <span>
                    AI-powered site selection
                  </span>

                </div>

                <b>→</b>

              </button>


              <button
                className="quick-action"
                onClick={() => onNavigate("predictions")}
              >

                <div className="quick-icon">
                  📈
                </div>

                <div>

                  <strong>
                    Energy Predictions
                  </strong>

                  <span>
                    View future potential
                  </span>

                </div>

                <b>→</b>

              </button>


              <button
                className="quick-action"
                onClick={() => onNavigate("reports")}
              >

                <div className="quick-icon">
                  📄
                </div>

                <div>

                  <strong>
                    View Reports
                  </strong>

                  <span>
                    Download analysis reports
                  </span>

                </div>

                <b>→</b>

              </button>

            </div>

          </div>

        </section>


        {/* ================= BOTTOM SECTION ================= */}

        <section className="bottom-grid">


          <div className="dashboard-card activity-card">

            <div className="card-header">

              <div>

                <h2>Recent Activity</h2>

                <p>
                  Latest platform activity
                </p>

              </div>

            </div>


            <div className="activity-list">

              <div className="activity-item">

                <div className="activity-icon">
                  ☀️
                </div>

                <div>

                  <strong>
                    Solar analysis completed
                  </strong>

                  <span>
                    Visakhapatnam • Score 77.6%
                  </span>

                </div>

                <small>
                  Today
                </small>

              </div>


              <div className="activity-item">

                <div className="activity-icon">
                  🌬️
                </div>

                <div>

                  <strong>
                    Wind assessment completed
                  </strong>

                  <span>
                    Vizag • Score 82.2%
                  </span>

                </div>

                <small>
                  Yesterday
                </small>

              </div>


              <div className="activity-item">

                <div className="activity-icon">
                  🗺️
                </div>

                <div>

                  <strong>
                    Site selection completed
                  </strong>

                  <span>
                    3 recommended locations
                  </span>

                </div>

                <small>
                  2 days ago
                </small>

              </div>

            </div>

          </div>


          {/* RECOMMENDED SITE */}

          <div className="dashboard-card recommendation-card">

            <div className="card-header">

              <div>

                <h2>
                  Top Recommended Site
                </h2>

                <p>
                  AI-based recommendation
                </p>

              </div>

            </div>


            <div className="top-site">

              <div className="site-rank">
                #1
              </div>

              <div className="site-info">

                <h3>
                  Vizag North
                </h3>

                <p>
                  Solar + Wind
                </p>

                <span>
                  Estimated Capacity: 12.4 MW
                </span>

              </div>

              <div className="match-score">

                <strong>
                  98%
                </strong>

                <span>
                  Match
                </span>

              </div>

            </div>


            <button
              className="site-btn"
              onClick={() => onNavigate("sites")}
            >
              View All Recommended Sites →
            </button>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;
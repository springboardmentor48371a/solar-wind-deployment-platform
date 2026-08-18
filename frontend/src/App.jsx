import { useEffect, useState } from "react";
import Register from "./Register";
import Login from "./Login";
import CreateProject from "./CreateProject";
import SiteManagement from "./SiteManagement";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function App() {
  const [activeView, setActiveView] = useState("home");
  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(localStorage.getItem("access_token"))
  );
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [selectedProjectSites, setSelectedProjectSites] = useState([]);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardMessage, setDashboardMessage] = useState("");

  const showLogin = () => setActiveView("login");
  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
    setActiveView("dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsAuthenticated(false);
    setProjects([]);
    setSelectedProjectId("");
    setSelectedProjectSites([]);
    setActiveView("login");
  };

  const authHeaders = () => {
    const token = localStorage.getItem("access_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  const loadProjects = async () => {
    setDashboardLoading(true);
    setDashboardMessage("");

    try {
      const response = await fetch(`${API_BASE_URL}/projects`, {
        headers: authHeaders(),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          handleLogout();
          return;
        }
        setDashboardMessage(data.detail || "Unable to load dashboard data");
        return;
      }

      const nextProjects = data.projects || [];
      setProjects(nextProjects);

      if (!nextProjects.length) {
        setSelectedProjectId("");
        setSelectedProjectSites([]);
        setDashboardMessage("No projects yet. Create a project to get started.");
      } else {
        setSelectedProjectId((prev) => {
          if (prev && nextProjects.some((project) => project.project_id === prev)) {
            return prev;
          }
          return nextProjects[0].project_id;
        });
      }
    } catch {
      setDashboardMessage("Unable to connect to backend");
    } finally {
      setDashboardLoading(false);
    }
  };

  const loadSitesForProject = async (projectId) => {
    if (!projectId) {
      setSelectedProjectSites([]);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sites`, {
        headers: authHeaders(),
      });

      const data = await response.json();
      if (!response.ok) {
        if (response.status === 401) {
          handleLogout();
          return;
        }
        setDashboardMessage(data.detail || "Unable to load project sites");
        setSelectedProjectSites([]);
        return;
      }

      setSelectedProjectSites(data.sites || []);
    } catch {
      setDashboardMessage("Unable to connect to backend");
      setSelectedProjectSites([]);
    }
  };

  useEffect(() => {
    if (!isAuthenticated && ["dashboard", "create-project", "sites"].includes(activeView)) {
      setActiveView("login");
    }
  }, [activeView, isAuthenticated]);

  useEffect(() => {
    if (activeView === "dashboard" && isAuthenticated) {
      loadProjects();
    }
  }, [activeView, isAuthenticated]);

  useEffect(() => {
    if (activeView === "dashboard" && isAuthenticated) {
      loadSitesForProject(selectedProjectId);
    }
  }, [activeView, isAuthenticated, selectedProjectId]);

  const isAuthView = activeView === "register" || activeView === "login";
  const selectedProject = projects.find((project) => project.project_id === selectedProjectId);
  const selectedSite = selectedProjectSites[0];

  return (
    <main className={activeView === "home" ? "app-shell landing-page" : isAuthView ? "app-shell auth-layout" : "app-shell app-layout"}>
      <header className={activeView === "home" ? "topbar landing-header" : isAuthView ? "topbar auth-topbar" : "topbar"}>
        {activeView === "home" && (
          <div className="brand landing-brand">
            <span className="brand-mark" aria-hidden="true">SW</span>
            <span>Solar & Wind Deployment<small>Intelligence Platform</small></span>
          </div>
        )}
        {activeView !== "home" && (
          <button className="brand" type="button" onClick={() => setActiveView("home")}>
            <span className="brand-mark" aria-hidden="true">SW</span>
            <span>SolarWind<span>Platform</span></span>
          </button>
        )}

        {activeView === "home" ? (
          <nav className="landing-nav" aria-label="Account actions">
            <button className="register-pill" type="button" onClick={() => setActiveView("register")}>Register</button>
            <button className="login-pill" type="button" onClick={showLogin}>Log in</button>
          </nav>
        ) : (
          <nav className="app-nav" aria-label="Workspace navigation">
            {(activeView === "register" || activeView === "login") ? (
              <button className="back-home" type="button" onClick={() => setActiveView("home")}>Back to home</button>
            ) : (
              <>
                {isAuthenticated && <button className={activeView === "dashboard" ? "nav-link is-active" : "nav-link"} type="button" onClick={() => setActiveView("dashboard")}>Dashboard</button>}
                {isAuthenticated && <button className={activeView === "sites" ? "nav-link is-active" : "nav-link"} type="button" onClick={() => setActiveView("sites")}>Sites</button>}
                {isAuthenticated && <button className={activeView === "create-project" ? "nav-link is-active" : "nav-link"} type="button" onClick={() => setActiveView("create-project")}>Create Project</button>}
                {isAuthenticated && <button className="nav-link" type="button" onClick={handleLogout}>Logout</button>}
              </>
            )}
          </nav>
        )}
      </header>

      {activeView === "home" && (
        <section className="landing" aria-labelledby="page-title">
          <div className="landing-copy-block">
            <h1 id="page-title" className="landing-title">Intelligent Insights.<br /><span>Sustainable</span> Tomorrow.</h1>
            <p>AI-powered platform to analyze sites, predict energy potential,<br />and optimize solar and wind projects with confidence.</p>
          </div>
        </section>
      )}

      {activeView === "register" && (
        <section className="auth-page">
          <Register onSuccess={showLogin} />
        </section>
      )}

      {activeView === "login" && (
        <section className="auth-page">
          <Login onSuccess={handleLoginSuccess} onSwitchToRegister={() => setActiveView("register")} />
        </section>
      )}

      {activeView === "dashboard" && (
        <section className="gis-dashboard">
          <div className="gis-dashboard-header">
            <div>
              <p className="eyebrow">Dashboard</p>
              <h1>GIS Overview</h1>
            </div>

            <div className="dashboard-toolbar">
              <button type="button" className="button button-primary dashboard-action" onClick={() => setActiveView("create-project")}>Create Project</button>
              <button type="button" className="button button-secondary dashboard-action" onClick={() => setActiveView("sites")}>Manage Sites</button>
            </div>
          </div>

          <div className="gis-control-panel">
            <aside className="project-panel">
              <div className="panel-header-row">
                <span>Projects</span>
                <button type="button" className="tiny-button">All</button>
              </div>

              <ul className="project-list">
                {projects.map((project) => (
                  <li
                    key={project.project_id}
                    className={project.project_id === selectedProjectId ? "project-item active" : "project-item"}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedProjectId(project.project_id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        setSelectedProjectId(project.project_id);
                      }
                    }}
                  >
                    <div>
                      <strong>{project.project_name}</strong>
                      <small>{project.region} · {project.project_status?.toLowerCase() || "planning"}</small>
                    </div>
                    <span>{project.project_status || "Planning"}</span>
                  </li>
                ))}
              </ul>
            </aside>

            <div className="gis-map-panel">
              <div className="panel-header-row">
                <span>Regional site map</span>
                <button type="button" className="tiny-button">Live view</button>
              </div>

              <div className="map-surface" aria-label="Map overview">
                {selectedProjectSites.slice(0, 3).map((site, index) => (
                  <span
                    key={site.site_id}
                    className={`map-marker ${index === 0 ? "marker-one" : index === 1 ? "marker-two" : "marker-three"}`}
                    title={`${site.site_name} (${site.latitude}, ${site.longitude})`}
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>
                ))}
              </div>
            </div>

            <aside className="gis-detail-panel">
              <div className="detail-header">
                <span>Selected site</span>
                <small>{selectedProject ? selectedProject.project_name : "No project selected"}</small>
              </div>

              <div className="detail-card">
                <h3>{selectedSite ? selectedSite.site_name : "No sites found"}</h3>
                <p>Latitude {selectedSite ? selectedSite.latitude : "-"}</p>
                <p>Longitude {selectedSite ? selectedSite.longitude : "-"}</p>
                <div className="status-pill">{selectedSite?.site_status || "Add sites to view status"}</div>
              </div>

              <div className="summary-card">
                <span>Projects</span>
                <strong>{projects.length}</strong>
              </div>
              <div className="summary-card">
                <span>Sites</span>
                <strong>{selectedProjectSites.length}</strong>
              </div>
              <div className="summary-card">
                <span>Status</span>
                <strong>{dashboardLoading ? "Loading..." : selectedProject?.project_status || "Ready"}</strong>
              </div>
            </aside>
          </div>
          {dashboardMessage && <p className="form-message" aria-live="polite">{dashboardMessage}</p>}
        </section>
      )}

      {activeView === "create-project" && (
        <>
          <section className="hero view-hero"><p className="eyebrow">Create a project</p><h1>Start a new renewable portfolio</h1><p className="hero-copy">Define the project profile and region before adding sites and planning deployment.</p></section>
          <section className="view-content"><CreateProject /></section>
        </>
      )}

      {activeView === "sites" && (
        <>
          <section className="hero view-hero"><p className="eyebrow">Site intelligence</p><h1>Manage project sites</h1><p className="hero-copy">Choose a project, record its location, and build the data foundation for analysis.</p></section>
          <section className="view-content"><SiteManagement /></section>
        </>
      )}
    </main>
  );
}

export default App;

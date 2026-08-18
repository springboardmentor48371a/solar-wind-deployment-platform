import { useEffect, useState } from "react";

import { useAuth } from "../auth/AuthContext.jsx";
import { apiClient } from "../services/apiClient.js";

export default function DashboardPage() {
  const { currentUser } = useAuth();
  const [summary, setSummary] = useState({
    projects: 0,
    sites: 0,
    loading: true,
    error: "",
  });

  useEffect(() => {
    async function loadSummary() {
      try {
        const projects = await apiClient.getProjects();
        const siteGroups = await Promise.all(
          projects.map((project) => apiClient.getProjectSites(project.project_id)),
        );

        setSummary({
          projects: projects.length,
          sites: siteGroups.reduce((total, sites) => total + sites.length, 0),
          loading: false,
          error: "",
        });
      } catch (requestError) {
        setSummary((current) => ({
          ...current,
          loading: false,
          error: requestError.message || "Unable to load workspace summary.",
        }));
      }
    }

    loadSummary();
  }, []);

  return (
    <section className="dashboard-page">
      <section className="workspace-hero">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h2>Renewable Energy Deployment</h2>
          <p>
            Plan, evaluate and manage renewable energy sites from one workspace.
          </p>
        </div>
        <div className="hero-diagram" aria-hidden="true">
          <span className="sun-disc" />
          <span className="wind-line one" />
          <span className="wind-line two" />
          <span className="map-pin" />
        </div>
      </section>

      {summary.error && <p className="form-error">{summary.error}</p>}

      <section className="metric-grid" aria-label="Workspace summary">
        <article className="metric-card">
          <span>Projects</span>
          <strong>{summary.loading ? "..." : summary.projects}</strong>
          <p>Registered renewable deployment projects.</p>
        </article>
        <article className="metric-card">
          <span>Sites</span>
          <strong>{summary.loading ? "..." : summary.sites}</strong>
          <p>Candidate locations attached to your projects.</p>
        </article>
        <article className="metric-card">
          <span>Current User</span>
          <strong>{currentUser.full_name}</strong>
          <p>{currentUser.email}</p>
        </article>
        <article className="metric-card">
          <span>Role</span>
          <strong>{currentUser.role}</strong>
          <p>Account status: {currentUser.account_status}</p>
        </article>
      </section>

      <section className="insight-panel">
        <div>
          <p className="eyebrow">Environmental analysis</p>
          <h3>Environmental analytics will appear here once site data is available.</h3>
        </div>
        <p>
          This dashboard currently uses only your real projects, sites and user
          profile data.
        </p>
      </section>
    </section>
  );
}

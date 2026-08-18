import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ProjectTable from "../components/ProjectTable.jsx";
import { apiClient } from "../services/apiClient.js";

export default function ProjectsPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    setError("");
    setLoading(true);

    try {
      const data = await apiClient.getProjects();
      setProjects(data);
    } catch (requestError) {
      setError(requestError.message || "Unable to load projects.");
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(project) {
    const confirmed = window.confirm(
      `Delete "${project.project_name}"? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }

    setMessage("");
    setError("");
    setDeletingId(project.project_id);

    try {
      await apiClient.deleteProject(project.project_id);
      setProjects((current) =>
        current.filter((item) => item.project_id !== project.project_id),
      );
      setMessage("Project deleted.");
    } catch (requestError) {
      setError(requestError.message || "Unable to delete project.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section>
      <div className="page-title-row">
        <div className="page-heading">
          <p className="eyebrow">Projects</p>
          <h2>Renewable project portfolio</h2>
          <p>
            Manage solar, wind and clean-energy deployment workspaces with clear
            ownership and status.
          </p>
        </div>
        <Link className="button-link" to="/app/projects/new">
          + New Project
        </Link>
      </div>

      {message && <p className="form-success">{message}</p>}
      {error && <p className="form-error">{error}</p>}

      {loading ? (
        <section className="empty-state">
          <h2>Loading projects...</h2>
        </section>
      ) : projects.length === 0 ? (
        <section className="empty-state illustrated">
          <p className="eyebrow">No projects yet</p>
          <h2>No projects yet</h2>
          <p>
            Create your first renewable energy project and begin planning your
            deployment.
          </p>
          <div className="action-row">
            <Link className="button-link" to="/app/projects/new">
              + New Project
            </Link>
          </div>
        </section>
      ) : (
        <ProjectTable
          projects={projects}
          deletingId={deletingId}
          onDelete={handleDelete}
        />
      )}
    </section>
  );
}

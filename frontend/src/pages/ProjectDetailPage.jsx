import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import SiteTable from "../components/SiteTable.jsx";
import { apiClient } from "../services/apiClient.js";

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [sites, setSites] = useState([]);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [siteMessage, setSiteMessage] = useState("");
  const [siteError, setSiteError] = useState("");
  const [deletingSiteId, setDeletingSiteId] = useState(null);

  useEffect(() => {
    async function loadProject() {
      setError("");

      try {
        const [projectData, siteData] = await Promise.all([
          apiClient.getProject(projectId),
          apiClient.getProjectSites(projectId),
        ]);
        setProject(projectData);
        setSites(siteData);
      } catch (requestError) {
        setError(requestError.message || "Unable to load project.");
      }
    }

    loadProject();
  }, [projectId]);

  async function handleDelete() {
    const confirmed = window.confirm(
      `Delete "${project.project_name}"? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }

    setError("");
    setDeleting(true);

    try {
      await apiClient.deleteProject(project.project_id);
      navigate("/app/projects", { replace: true });
    } catch (requestError) {
      setError(requestError.message || "Unable to delete project.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleSiteDelete(site) {
    const confirmed = window.confirm(
      `Delete "${site.site_name}"? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }

    setSiteMessage("");
    setSiteError("");
    setDeletingSiteId(site.site_id);

    try {
      await apiClient.deleteSite(site.site_id);
      setSites((current) => current.filter((item) => item.site_id !== site.site_id));
      setSiteMessage("Site deleted.");
    } catch (requestError) {
      setSiteError(requestError.message || "Unable to delete site.");
    } finally {
      setDeletingSiteId(null);
    }
  }

  if (error) {
    return (
      <section className="empty-state">
        <p className="eyebrow">Project</p>
        <h2>{error}</h2>
        <Link className="button-link" to="/app/projects">
          Back to projects
        </Link>
      </section>
    );
  }

  if (!project) {
    return (
      <section className="empty-state">
        <h2>Loading project...</h2>
      </section>
    );
  }

  return (
    <section>
      <div className="page-title-row">
        <div className="page-heading">
          <p className="eyebrow">Project</p>
          <h2>{project.project_name}</h2>
          <p>
            {project.region} | {project.owner?.full_name ?? "Unknown owner"}
          </p>
        </div>
        <div className="action-row compact">
          <Link className="button-link" to={`/app/projects/${project.project_id}/edit`}>
            Edit
          </Link>
          <button
            type="button"
            className="secondary-button danger-button"
            disabled={deleting}
            onClick={handleDelete}
          >
            {deleting ? "Deleting..." : "Delete"}
          </button>
        </div>
      </div>

      <section className="project-overview">
        <article className="overview-card accent-wind">
          <span>Region</span>
          <strong>{project.region}</strong>
        </article>
        <article className="overview-card accent-solar">
          <span>Status</span>
          <strong>{project.project_status}</strong>
        </article>
        <article className="overview-card accent-environment">
          <span>Owner</span>
          <strong>{project.owner?.full_name ?? "Unknown"}</strong>
        </article>
      </section>

      <section className="detail-panel">
        <div className="section-heading-inline">
          <p className="eyebrow">Project Overview</p>
          <h3>Deployment context</h3>
        </div>
        <dl>
          <div>
            <dt>Description</dt>
            <dd>{project.description || "No description"}</dd>
          </div>
          <div>
            <dt>Region</dt>
            <dd>{project.region}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{project.project_status}</dd>
          </div>
          <div>
            <dt>Owner</dt>
            <dd>{project.owner?.full_name ?? "Unknown"}</dd>
          </div>
          <div>
            <dt>Created</dt>
            <dd>{formatDate(project.created_at)}</dd>
          </div>
          <div>
            <dt>Updated</dt>
            <dd>{formatDate(project.updated_at)}</dd>
          </div>
        </dl>
      </section>

      <section className="section-block">
        <div className="page-title-row">
          <div className="page-heading">
            <p className="eyebrow">Sites</p>
            <h2>Geographic assets</h2>
            <p>Candidate locations connected to this renewable project.</p>
          </div>
          <Link
            className="button-link"
            to={`/app/projects/${project.project_id}/sites/new`}
          >
            Add Site
          </Link>
        </div>

        {siteMessage && <p className="form-success">{siteMessage}</p>}
        {siteError && <p className="form-error">{siteError}</p>}

        {sites.length === 0 ? (
          <section className="empty-state illustrated">
            <p className="eyebrow">No sites added yet</p>
            <h2>No sites added yet</h2>
            <p>Add the first candidate site and begin capturing location details.</p>
            <div className="action-row">
              <Link
                className="button-link"
                to={`/app/projects/${project.project_id}/sites/new`}
              >
                Add Site
              </Link>
            </div>
          </section>
        ) : (
          <SiteTable
            projectId={project.project_id}
            sites={sites}
            deletingId={deletingSiteId}
            onDelete={handleSiteDelete}
          />
        )}
      </section>
    </section>
  );
}

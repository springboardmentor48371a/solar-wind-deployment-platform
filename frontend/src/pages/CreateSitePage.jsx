import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import SiteForm from "../components/SiteForm.jsx";
import { apiClient } from "../services/apiClient.js";

export default function CreateSitePage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function loadProject() {
      setLoadError("");

      try {
        const data = await apiClient.getProject(projectId);
        setProject(data);
      } catch (requestError) {
        setLoadError(requestError.message || "Unable to load project.");
      }
    }

    loadProject();
  }, [projectId]);

  async function handleSubmit(payload) {
    setSaveError("");
    setSubmitting(true);

    try {
      await apiClient.createSite(projectId, payload);
      navigate(`/app/projects/${projectId}`, { replace: true });
    } catch (requestError) {
      setSaveError(requestError.message || "Unable to create site.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <section className="empty-state">
        <p className="eyebrow">Add Site</p>
        <h2>{loadError}</h2>
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
      <div className="page-heading">
        <p className="eyebrow">Add Site</p>
        <h2>Add a candidate location</h2>
        <p>Search for a place or enter coordinates manually for this project.</p>
      </div>
      <SiteForm
        project={project}
        submitLabel="Save Site"
        submitting={submitting}
        error={saveError}
        onSubmit={handleSubmit}
      />
    </section>
  );
}

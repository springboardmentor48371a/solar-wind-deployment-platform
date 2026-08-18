import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import SiteForm from "../components/SiteForm.jsx";
import { apiClient } from "../services/apiClient.js";

export default function EditSitePage() {
  const { projectId, siteId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [site, setSite] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function loadData() {
      setLoadError("");

      try {
        const [projectData, siteData] = await Promise.all([
          apiClient.getProject(projectId),
          apiClient.getSite(siteId),
        ]);

        if (siteData.project_id !== projectId) {
          throw new Error("Site does not belong to this project.");
        }

        setProject(projectData);
        setSite(siteData);
      } catch (requestError) {
        setLoadError(requestError.message || "Unable to load site.");
      }
    }

    loadData();
  }, [projectId, siteId]);

  async function handleSubmit(payload) {
    setSaveError("");
    setSubmitting(true);

    try {
      await apiClient.updateSite(siteId, payload);
      navigate(`/app/projects/${projectId}/sites/${siteId}`, { replace: true });
    } catch (requestError) {
      setSaveError(requestError.message || "Unable to update site.");
    } finally {
      setSubmitting(false);
    }
  }

  if (loadError) {
    return (
      <section className="empty-state">
        <p className="eyebrow">Edit Site</p>
        <h2>{loadError}</h2>
        <Link className="button-link" to={`/app/projects/${projectId}`}>
          Back to project
        </Link>
      </section>
    );
  }

  if (!project || !site) {
    return (
      <section className="empty-state">
        <h2>Loading site...</h2>
      </section>
    );
  }

  return (
    <section>
      <div className="page-heading">
        <p className="eyebrow">Edit Site</p>
        <h2>{site.site_name}</h2>
        <p>Refine location and land details for this project site.</p>
      </div>
      <SiteForm
        initialValues={site}
        project={project}
        submitLabel="Update Site"
        submitting={submitting}
        error={saveError}
        onSubmit={handleSubmit}
      />
    </section>
  );
}

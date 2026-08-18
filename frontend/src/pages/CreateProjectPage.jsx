import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext.jsx";
import ProjectForm from "../components/ProjectForm.jsx";
import { apiClient } from "../services/apiClient.js";

export default function CreateProjectPage() {
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(payload) {
    setError("");
    setSubmitting(true);

    try {
      await apiClient.createProject(payload);
      navigate("/app/projects", { replace: true });
    } catch (requestError) {
      setError(requestError.message || "Unable to create project.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <div className="page-heading">
        <p className="eyebrow">Create Project</p>
        <h2>Start a renewable deployment plan</h2>
        <p>Capture the project region, ownership context and planning status.</p>
      </div>
      <ProjectForm
        ownerName={currentUser.full_name}
        submitLabel="Save Project"
        submitting={submitting}
        error={error}
        onSubmit={handleSubmit}
      />
    </section>
  );
}

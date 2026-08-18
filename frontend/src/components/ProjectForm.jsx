import { useState } from "react";
import { Link } from "react-router-dom";

const PROJECT_STATUSES = ["Planning", "Analysis", "Completed"];

export default function ProjectForm({
  initialValues,
  ownerName,
  submitLabel,
  submitting,
  error,
  onSubmit,
}) {
  const [formData, setFormData] = useState({
    project_name: initialValues?.project_name ?? "",
    description: initialValues?.description ?? "",
    region: initialValues?.region ?? "",
    project_status: initialValues?.project_status ?? "Planning",
  });

  function updateField(event) {
    setFormData((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({
      ...formData,
      description: formData.description || null,
    });
  }

  return (
    <section className="detail-panel project-form-panel">
      <div className="owner-note">
        <span>Owner</span>
        <strong>{ownerName}</strong>
        <p>The logged-in user is assigned as the project owner.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <label>
          Project Name
          <input
            name="project_name"
            value={formData.project_name}
            onChange={updateField}
            maxLength="150"
            required
          />
        </label>

        <label>
          Description
          <textarea
            name="description"
            value={formData.description}
            onChange={updateField}
            rows="5"
          />
        </label>

        <label>
          Region
          <input
            name="region"
            value={formData.region}
            onChange={updateField}
            maxLength="100"
            required
          />
        </label>

        <label>
          Project Status
          <select
            name="project_status"
            value={formData.project_status}
            onChange={updateField}
          >
            {PROJECT_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>

        {error && <p className="form-error">{error}</p>}

        <div className="action-row">
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : submitLabel}
          </button>
          <Link className="secondary-link" to="/app/projects">
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}

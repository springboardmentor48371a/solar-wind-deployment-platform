import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function CreateProject({ onSuccess }) {
  const [formData, setFormData] = useState({
    project_name: "",
    description: "",
    region: "",
  });

  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const token = localStorage.getItem("access_token");

    if (!token) {
      setMessage("Please login first.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/projects`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setMessage(
          `Project created successfully! Project ID: ${data.project_id}`
        );

        setFormData({
          project_name: "",
          description: "",
          region: "",
        });
        onSuccess?.();
      } else {
        setMessage(data.detail || "Project creation failed");
      }
    } catch {
      setMessage("Unable to connect to backend");
    }
  };

  return (
    <section className="panel panel-project">
      <div className="panel-heading">
        <span className="step-number">03</span>
        <div>
          <p className="panel-kicker">Build your pipeline</p>
          <h2>Create a project</h2>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field-grid">
          <label className="field field-wide">Project name
            <input type="text" name="project_name" placeholder="e.g. Chennai rooftop portfolio" value={formData.project_name} onChange={handleChange} required />
          </label>
          <label className="field field-wide">Project description <span>Optional</span>
            <textarea name="description" placeholder="Briefly describe the project scope" value={formData.description} onChange={handleChange} />
          </label>
          <label className="field field-wide">Region
            <input type="text" name="region" placeholder="e.g. Tamil Nadu, India" value={formData.region} onChange={handleChange} required />
          </label>
        </div>
        <button className="button button-solar" type="submit">Create project <span aria-hidden="true">→</span></button>
      </form>

      {message && <p className="form-message" aria-live="polite">{message}</p>}
    </section>
  );
}

export default CreateProject;

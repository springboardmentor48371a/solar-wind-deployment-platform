import { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const emptySite = {
  project_id: "",
  site_name: "",
  latitude: "",
  longitude: "",
  area_acres: "",
  elevation: "",
  existing_infrastructure: "",
  land_ownership: "",
  address: "",
  site_status: "Draft",
  notes: "",
};

function SiteManagement() {
  const [formData, setFormData] = useState(emptySite);
  const [projects, setProjects] = useState([]);
  const [sites, setSites] = useState([]);
  const [message, setMessage] = useState("");

  const authHeaders = () => ({
    "Content-Type": "application/json",
    Authorization: `Bearer ${localStorage.getItem("access_token")}`,
  });

  const loadSites = async (projectId) => {
    if (!projectId) {
      setSites([]);
      return;
    }

    const response = await fetch(`${API_BASE_URL}/projects/${projectId}/sites`, {
      headers: authHeaders(),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Unable to load sites");
    setSites(data.sites);
  };

  const loadProjects = async () => {
    if (!localStorage.getItem("access_token")) {
      setMessage("Sign in first, then click Refresh projects.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/projects`, { headers: authHeaders() });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to load projects");
      setProjects(data.projects);
      setMessage(data.projects.length ? "Projects loaded. Choose one to manage its sites." : "Create a project first, then refresh this list.");
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((current) => ({ ...current, [name]: value }));
    if (name === "project_id") {
      loadSites(value).catch((error) => setMessage(error.message));
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const payload = {
        ...formData,
        latitude: Number(formData.latitude),
        longitude: Number(formData.longitude),
        area_acres: formData.area_acres ? Number(formData.area_acres) : null,
        elevation: formData.elevation ? Number(formData.elevation) : null,
      };
      const response = await fetch(`${API_BASE_URL}/sites`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Site creation failed");
      setMessage("Site created successfully.");
      setFormData((current) => ({ ...emptySite, project_id: current.project_id }));
      await loadSites(payload.project_id);
    } catch (error) {
      setMessage(error.message || "Unable to connect to backend");
    }
  };

  const handleDelete = async (siteId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sites/${siteId}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Unable to delete site");
      setMessage("Site deleted successfully.");
      await loadSites(formData.project_id);
    } catch (error) {
      setMessage(error.message);
    }
  };

  return (
    <section className="panel panel-sites">
      <div className="panel-heading">
        <span className="step-number">04</span>
        <div>
          <p className="panel-kicker">Site intelligence</p>
          <h2>Manage project sites</h2>
        </div>
      </div>

      <div className="site-toolbar">
        <p>Select a project, record the site coordinates, then add resource data in the next phase.</p>
        <button className="text-button" type="button" onClick={loadProjects}>Refresh projects</button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="field-grid">
          <label className="field field-wide">Project
            <select name="project_id" value={formData.project_id} onChange={handleChange} required>
              <option value="">Select a project</option>
              {projects.map((project) => <option key={project.project_id} value={project.project_id}>{project.project_name} · {project.region}</option>)}
            </select>
          </label>
          <label className="field field-wide">Site name
            <input name="site_name" placeholder="e.g. North warehouse roof" value={formData.site_name} onChange={handleChange} required />
          </label>
          <label className="field">Latitude
            <input name="latitude" type="number" step="any" min="-90" max="90" placeholder="e.g. 13.0827" value={formData.latitude} onChange={handleChange} required />
          </label>
          <label className="field">Longitude
            <input name="longitude" type="number" step="any" min="-180" max="180" placeholder="e.g. 80.2707" value={formData.longitude} onChange={handleChange} required />
          </label>
          <label className="field">Area (acres)
            <input name="area_acres" type="number" step="any" min="0" placeholder="e.g. 2.5" value={formData.area_acres} onChange={handleChange} />
          </label>
          <label className="field">Elevation (m)
            <input name="elevation" type="number" step="any" placeholder="e.g. 176" value={formData.elevation} onChange={handleChange} />
          </label>
          <label className="field">Status
            <select name="site_status" value={formData.site_status} onChange={handleChange}>
              <option>Draft</option><option>Under review</option><option>Approved</option>
            </select>
          </label>
          <label className="field">Existing Infrastructure
            <input name="existing_infrastructure" placeholder="Grid, roads, substations" value={formData.existing_infrastructure} onChange={handleChange} />
          </label>
          <label className="field field-wide">Land Ownership
            <input name="land_ownership" placeholder="Owned, leasehold, or acquisition status" value={formData.land_ownership} onChange={handleChange} />
          </label>
          <label className="field field-wide">Address
            <input name="address" placeholder="Street, city, state" value={formData.address} onChange={handleChange} />
          </label>
          <label className="field field-wide">Notes
            <textarea name="notes" placeholder="Land conditions, access, constraints, or observations" value={formData.notes} onChange={handleChange} />
          </label>
        </div>
        <button className="button button-primary" type="submit">Add site <span aria-hidden="true">→</span></button>
      </form>

      {message && <p className="form-message" aria-live="polite">{message}</p>}

      {formData.project_id && <div className="site-list">
        <h3>Saved sites <span>{sites.length}</span></h3>
        {sites.length === 0 ? <p className="empty-state">No sites saved for this project yet.</p> : sites.map((site) => (
          <article className="site-item" key={site.site_id}>
            <div><h4>{site.site_name}</h4><p>{site.latitude}, {site.longitude} · {site.site_status}</p></div>
            <button className="delete-button" type="button" onClick={() => handleDelete(site.site_id)}>Remove</button>
          </article>
        ))}
      </div>}
    </section>
  );
}

export default SiteManagement;

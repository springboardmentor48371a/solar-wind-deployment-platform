import { Link } from "react-router-dom";

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function ProjectTable({ projects, deletingId, onDelete }) {
  return (
    <div className="table-wrap">
      <table className="project-table">
        <thead>
          <tr>
            <th>Project Name</th>
            <th>Region</th>
            <th>Status</th>
            <th>Owner</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((project) => (
            <tr key={project.project_id}>
              <td>
                <strong>{project.project_name}</strong>
                <span className="table-subtext">
                  {project.description || "No description"}
                </span>
              </td>
              <td>{project.region}</td>
              <td>
                <span className={`status-pill status-${project.project_status.toLowerCase()}`}>
                  {project.project_status}
                </span>
              </td>
              <td>{project.owner?.full_name ?? "Unknown"}</td>
              <td>{formatDate(project.created_at)}</td>
              <td>
                <div className="table-actions">
                  <Link to={`/app/projects/${project.project_id}`}>View</Link>
                  <Link to={`/app/projects/${project.project_id}/edit`}>Edit</Link>
                  <button
                    type="button"
                    className="text-button danger"
                    disabled={deletingId === project.project_id}
                    onClick={() => onDelete(project)}
                  >
                    {deletingId === project.project_id ? "Deleting..." : "Delete"}
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

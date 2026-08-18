import { Link } from "react-router-dom";

function displayValue(value) {
  return value === null || value === undefined || value === "" ? "Not set" : value;
}

export default function SiteTable({ projectId, sites, deletingId, onDelete }) {
  return (
    <div className="table-wrap">
      <table className="project-table">
        <thead>
          <tr>
            <th>Site Name</th>
            <th>Location</th>
            <th>Region</th>
            <th>Land Area</th>
            <th>Elevation</th>
            <th>Land Type</th>
            <th>Ownership</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {sites.map((site) => (
            <tr key={site.site_id}>
              <td>
                <strong>{site.site_name}</strong>
                <span className="table-subtext">Project site asset</span>
              </td>
              <td>
                <strong>{displayValue(site.region)}</strong>
                <span className="coordinate-text">
                  {site.latitude}, {site.longitude}
                </span>
              </td>
              <td>{displayValue(site.region)}</td>
              <td>{displayValue(site.land_area)}</td>
              <td>{displayValue(site.elevation)}</td>
              <td>{displayValue(site.land_type)}</td>
              <td>{displayValue(site.ownership)}</td>
              <td>
                <div className="table-actions">
                  <Link to={`/app/projects/${projectId}/sites/${site.site_id}`}>
                    View
                  </Link>
                  <Link to={`/app/projects/${projectId}/sites/${site.site_id}/edit`}>
                    Edit
                  </Link>
                  <button
                    type="button"
                    className="text-button danger"
                    disabled={deletingId === site.site_id}
                    onClick={() => onDelete(site)}
                  >
                    {deletingId === site.site_id ? "Deleting..." : "Delete"}
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

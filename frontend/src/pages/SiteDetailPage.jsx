import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { apiClient } from "../services/apiClient.js";

function displayValue(value) {
  return value === null || value === undefined || value === "" ? "Not set" : value;
}

function displayDataValue(value, unit = "") {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }
  return `${value}${unit ? ` ${unit}` : ""}`;
}

function formatDate(value) {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function getSourceStatus(record) {
  if (record?.data_sources) {
    return record.data_sources;
  }

  const hasNasaData = [
    record?.solar_irradiance,
    record?.temperature,
    record?.rainfall,
    record?.humidity,
    record?.cloud_cover,
  ].some((value) => value !== null && value !== undefined);
  const hasWindData = [record?.wind_speed, record?.wind_direction].some(
    (value) => value !== null && value !== undefined,
  );

  return {
    "NASA POWER": hasNasaData ? "available" : "Not available in stored record",
    "Global Wind Atlas": hasWindData
      ? "available"
      : "Global Wind Atlas unavailable",
  };
}

export default function SiteDetailPage() {
  const { projectId, siteId } = useParams();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [site, setSite] = useState(null);
  const [environmentalRecords, setEnvironmentalRecords] = useState([]);
  const [environmentalMessage, setEnvironmentalMessage] = useState("");
  const [environmentalError, setEnvironmentalError] = useState("");
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function loadData() {
      setError("");

      try {
        const [projectData, siteData] = await Promise.all([
          apiClient.getProject(projectId),
          apiClient.getSite(siteId),
        ]);

        if (String(siteData.project_id) !== String(projectId)) {
          throw new Error("Site does not belong to this project.");
        }

        const environmentalData = await apiClient.getEnvironmentalData(siteId);

        setProject(projectData);
        setSite(siteData);
        setEnvironmentalRecords(environmentalData);
      } catch (requestError) {
        setError(requestError.message || "Unable to load site.");
      }
    }

    loadData();
  }, [projectId, siteId]);

  async function handleDelete() {
    const confirmed = window.confirm(
      `Delete "${site.site_name}"? This cannot be undone.`,
    );
    if (!confirmed) {
      return;
    }

    setError("");
    setDeleting(true);

    try {
      await apiClient.deleteSite(site.site_id);
      navigate(`/app/projects/${projectId}`, { replace: true });
    } catch (requestError) {
      setError(requestError.message || "Unable to delete site.");
    } finally {
      setDeleting(false);
    }
  }

  async function handleCollectEnvironmentalData() {
    setEnvironmentalMessage("");
    setEnvironmentalError("");
    setCollecting(true);

    try {
      const record = await apiClient.collectEnvironmentalData(site.site_id);
      setEnvironmentalRecords((current) => [record, ...current]);
      setEnvironmentalMessage("Environmental data collected successfully.");
    } catch (requestError) {
      setEnvironmentalError(
        requestError.message || "Unable to collect environmental data.",
      );
    } finally {
      setCollecting(false);
    }
  }

  if (error) {
    return (
      <section className="empty-state">
        <p className="eyebrow">Site</p>
        <h2>{error}</h2>
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

  const latestEnvironmentalRecord = environmentalRecords[0] ?? null;
  const sourceStatus = getSourceStatus(latestEnvironmentalRecord);

  return (
    <section>
      <div className="page-title-row">
        <div className="page-heading">
          <p className="eyebrow">Site</p>
          <h2>{site.site_name}</h2>
          <p>{displayValue(site.region)} | {project.project_name}</p>
        </div>
        <div className="action-row compact">
          <Link
            className="button-link"
            to={`/app/projects/${projectId}/sites/${site.site_id}/edit`}
          >
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

      <section className="project-overview site-overview">
        <article className="overview-card accent-wind">
          <span>Location</span>
          <strong>{displayValue(site.region)}</strong>
          <p className="coordinate-text">
            {site.latitude}, {site.longitude}
          </p>
        </article>
        <article className="overview-card accent-environment">
          <span>Land Area</span>
          <strong>{displayValue(site.land_area)}</strong>
        </article>
        <article className="overview-card accent-solar">
          <span>Elevation</span>
          <strong>{displayValue(site.elevation)}</strong>
        </article>
      </section>

      <section className="detail-panel">
        <div className="section-heading-inline">
          <p className="eyebrow">Site details</p>
          <h3>Location and land profile</h3>
        </div>
        <dl>
          <div>
            <dt>Project</dt>
            <dd>{project.project_name}</dd>
          </div>
          <div>
            <dt>Latitude</dt>
            <dd>{site.latitude}</dd>
          </div>
          <div>
            <dt>Longitude</dt>
            <dd>{site.longitude}</dd>
          </div>
          <div>
            <dt>Region</dt>
            <dd>{displayValue(site.region)}</dd>
          </div>
          <div>
            <dt>Land Area</dt>
            <dd>{displayValue(site.land_area)}</dd>
          </div>
          <div>
            <dt>Elevation</dt>
            <dd>{displayValue(site.elevation)}</dd>
          </div>
          <div>
            <dt>Land Type</dt>
            <dd>{displayValue(site.land_type)}</dd>
          </div>
          <div>
            <dt>Ownership</dt>
            <dd>{displayValue(site.ownership)}</dd>
          </div>
        </dl>
      </section>

      <section className="section-block">
        <div className="page-title-row">
          <div className="page-heading">
            <p className="eyebrow">Environmental Data</p>
            <h2>Raw site conditions</h2>
            <p>
              Collected provider data is stored for later AI assessment without
              scoring or prediction.
            </p>
          </div>
          <button
            type="button"
            disabled={collecting}
            onClick={handleCollectEnvironmentalData}
          >
            {collecting ? "Collecting..." : "Collect Environmental Data"}
          </button>
        </div>

        {collecting && (
          <p className="form-success">Collecting environmental data...</p>
        )}
        {environmentalMessage && <p className="form-success">{environmentalMessage}</p>}
        {environmentalError && <p className="form-error">{environmentalError}</p>}

        {!latestEnvironmentalRecord ? (
          <section className="empty-state illustrated">
            <p className="eyebrow">No environmental data collected yet.</p>
            <h2>No environmental data collected yet.</h2>
            <p>
              Use the collection workflow to request real environmental values
              for this registered site.
            </p>
          </section>
        ) : (
          <>
            <section className="environment-grid">
              <article className="environment-card accent-solar">
                <span>Solar Resource</span>
                <dl>
                  <div>
                    <dt>Solar Irradiance</dt>
                    <dd>
                      {displayDataValue(
                        latestEnvironmentalRecord.solar_irradiance,
                        "kWh/m2/day",
                      )}
                    </dd>
                  </div>
                </dl>
              </article>

              <article className="environment-card accent-wind">
                <span>Wind Resource</span>
                <dl>
                  <div>
                    <dt>Wind Speed</dt>
                    <dd>
                      {displayDataValue(latestEnvironmentalRecord.wind_speed, "m/s")}
                    </dd>
                  </div>
                  <div>
                    <dt>Wind Direction</dt>
                    <dd>
                      {displayDataValue(
                        latestEnvironmentalRecord.wind_direction,
                        "degrees",
                      )}
                    </dd>
                  </div>
                </dl>
              </article>

              <article className="environment-card accent-wind">
                <span>Weather</span>
                <dl>
                  <div>
                    <dt>Temperature</dt>
                    <dd>
                      {displayDataValue(latestEnvironmentalRecord.temperature, "C")}
                    </dd>
                  </div>
                  <div>
                    <dt>Rainfall</dt>
                    <dd>{displayDataValue(latestEnvironmentalRecord.rainfall, "mm")}</dd>
                  </div>
                  <div>
                    <dt>Humidity</dt>
                    <dd>{displayDataValue(latestEnvironmentalRecord.humidity, "%")}</dd>
                  </div>
                  <div>
                    <dt>Cloud Cover</dt>
                    <dd>
                      {displayDataValue(latestEnvironmentalRecord.cloud_cover, "%")}
                    </dd>
                  </div>
                </dl>
              </article>

              <article className="environment-card accent-environment">
                <span>Terrain & Environment</span>
                <dl>
                  <div>
                    <dt>Terrain Slope</dt>
                    <dd>
                      {displayDataValue(
                        latestEnvironmentalRecord.terrain_slope,
                        "degrees",
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Vegetation Index</dt>
                    <dd>
                      {displayDataValue(latestEnvironmentalRecord.vegetation_index)}
                    </dd>
                  </div>
                  <div>
                    <dt>Protected Area</dt>
                    <dd>
                      {latestEnvironmentalRecord.protected_area === null ||
                      latestEnvironmentalRecord.protected_area === undefined
                        ? "Not available"
                        : latestEnvironmentalRecord.protected_area
                          ? "Yes"
                          : "No"}
                    </dd>
                  </div>
                </dl>
              </article>

              <article className="environment-card accent-solar">
                <span>Infrastructure</span>
                <dl>
                  <div>
                    <dt>Nearest Substation Distance</dt>
                    <dd>
                      {displayDataValue(
                        latestEnvironmentalRecord.nearest_substation_distance,
                        "km",
                      )}
                    </dd>
                  </div>
                  <div>
                    <dt>Road Distance</dt>
                    <dd>
                      {displayDataValue(latestEnvironmentalRecord.road_distance, "km")}
                    </dd>
                  </div>
                </dl>
              </article>

              <article className="environment-card">
                <span>Collection Time</span>
                <strong>{formatDate(latestEnvironmentalRecord.collected_at)}</strong>
              </article>
            </section>

            <section className="data-source-panel">
              <p className="eyebrow">Data Sources</p>
              <div>
                {Object.entries(sourceStatus).map(([name, statusText]) => (
                  <span key={name} className="source-chip">
                    <strong>{name}</strong>
                    {statusText === "available" ? "available" : statusText}
                  </span>
                ))}
              </div>
            </section>
          </>
        )}
      </section>

      <div className="action-row">
        <Link className="secondary-link" to={`/app/projects/${projectId}`}>
          Back to project
        </Link>
      </div>
    </section>
  );
}

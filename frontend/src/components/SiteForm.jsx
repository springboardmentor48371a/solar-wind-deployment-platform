import { useState } from "react";
import { Link } from "react-router-dom";

import { searchPlaces } from "../services/geocodingService.js";

export default function SiteForm({
  initialValues,
  project,
  submitLabel,
  submitting,
  error,
  onSubmit,
}) {
  const [placeQuery, setPlaceQuery] = useState("");
  const [placeResults, setPlaceResults] = useState([]);
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [placeLoading, setPlaceLoading] = useState(false);
  const [placeError, setPlaceError] = useState("");
  const [formData, setFormData] = useState({
    site_name: initialValues?.site_name ?? "",
    latitude: initialValues?.latitude?.toString() ?? "",
    longitude: initialValues?.longitude?.toString() ?? "",
    region: initialValues?.region ?? "",
    land_area: initialValues?.land_area?.toString() ?? "",
    elevation: initialValues?.elevation?.toString() ?? "",
    land_type: initialValues?.land_type ?? "",
    ownership: initialValues?.ownership ?? "",
  });
  const [validationError, setValidationError] = useState("");

  async function handlePlaceSearch() {
    const trimmedQuery = placeQuery.trim();

    if (trimmedQuery.length < 2) {
      setPlaceResults([]);
      setPlaceError("Enter at least two characters to search.");
      return;
    }

    setPlaceLoading(true);
    setPlaceError("");

    try {
      const results = await searchPlaces(trimmedQuery);
      setPlaceResults(results);
      setPlaceError(
        results.length
          ? ""
          : "No matching places found. You can enter coordinates manually.",
      );
    } catch (requestError) {
      setPlaceResults([]);
      setPlaceError("Place search is unavailable. You can enter coordinates manually.");
    } finally {
      setPlaceLoading(false);
    }
  }

  function updateField(event) {
    setFormData((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  }

  function handlePlaceSelect(place) {
    setSelectedPlace(place);
    setPlaceQuery(place.label);
    setPlaceResults([]);
    setPlaceError("");
    setFormData((current) => ({
      ...current,
      latitude: place.latitude.toString(),
      longitude: place.longitude.toString(),
      region: current.region || place.region || "",
    }));
  }

  function parseOptionalNumber(value) {
    return value === "" ? null : Number(value);
  }

  function validate() {
    const latitude = Number(formData.latitude);
    const longitude = Number(formData.longitude);
    const landArea = parseOptionalNumber(formData.land_area);

    if (!formData.site_name.trim()) {
      return "Site name is required.";
    }

    if (!Number.isFinite(latitude) || latitude < -90 || latitude > 90) {
      return "Latitude must be between -90 and 90.";
    }

    if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
      return "Longitude must be between -180 and 180.";
    }

    if (landArea !== null && (!Number.isFinite(landArea) || landArea < 0)) {
      return "Land area must not be negative.";
    }

    return "";
  }

  function handleSubmit(event) {
    event.preventDefault();
    const nextValidationError = validate();
    setValidationError(nextValidationError);

    if (nextValidationError) {
      return;
    }

    onSubmit({
      site_name: formData.site_name,
      latitude: Number(formData.latitude),
      longitude: Number(formData.longitude),
      region: formData.region || null,
      land_area: parseOptionalNumber(formData.land_area),
      elevation: parseOptionalNumber(formData.elevation),
      land_type: formData.land_type || null,
      ownership: formData.ownership || null,
    });
  }

  return (
    <section className="detail-panel project-form-panel site-form-panel">
      <div className="owner-note">
        <span>Project</span>
        <strong>{project.project_name}</strong>
        <p>This site will remain associated with this project.</p>
      </div>

      <form onSubmit={handleSubmit}>
        <label>
          Site Name
          <input
            name="site_name"
            value={formData.site_name}
            onChange={updateField}
            maxLength="150"
            required
          />
        </label>

        <div className="place-search">
          <div className="section-heading-inline">
            <p className="eyebrow">Location search</p>
            <h3>Search for a location</h3>
          </div>
          <div className="place-search-row">
            <label>
              Search for a location
              <input
                type="search"
                value={placeQuery}
                onChange={(event) => {
                  setPlaceQuery(event.target.value);
                  setSelectedPlace(null);
                }}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    event.preventDefault();
                    handlePlaceSearch();
                  }
                }}
                placeholder="Vijayawada, Andhra Pradesh"
                autoComplete="off"
                aria-describedby="place-search-status"
              />
            </label>
            <button
              type="button"
              className="secondary-button"
              disabled={placeLoading}
              onClick={handlePlaceSearch}
            >
              {placeLoading ? "Searching..." : "Search"}
            </button>
          </div>

          <div id="place-search-status" className="place-search-status" aria-live="polite">
            {placeLoading && "Searching places..."}
            {!placeLoading && placeError}
          </div>

          {placeResults.length > 0 && (
            <div className="place-results" role="listbox" aria-label="Place search results">
              {placeResults.map((place) => (
                <button
                  key={place.id}
                  type="button"
                  className="place-result"
                  onClick={() => handlePlaceSelect(place)}
                  role="option"
                >
                  <span>{place.label}</span>
                  <small>
                    {place.latitude}, {place.longitude}
                  </small>
                </button>
              ))}
            </div>
          )}

          {selectedPlace && (
            <div className="selected-place">
              <span>Selected location</span>
              <strong>{selectedPlace.label}</strong>
              <dl>
                <div>
                  <dt>Latitude</dt>
                  <dd>{selectedPlace.latitude}</dd>
                </div>
                <div>
                  <dt>Longitude</dt>
                  <dd>{selectedPlace.longitude}</dd>
                </div>
              </dl>
            </div>
          )}

          <p className="attribution">
            Location search by OpenStreetMap Nominatim. Manual coordinates can be
            used if search is unavailable.
          </p>
        </div>

        <div className="form-grid">
          <label>
            Latitude
            <input
              name="latitude"
              type="number"
              value={formData.latitude}
              onChange={updateField}
              min="-90"
              max="90"
              step="any"
              required
            />
          </label>

          <label>
            Longitude
            <input
              name="longitude"
              type="number"
              value={formData.longitude}
              onChange={updateField}
              min="-180"
              max="180"
              step="any"
              required
            />
          </label>
        </div>

        <label>
          Region
          <input
            name="region"
            value={formData.region}
            onChange={updateField}
            maxLength="100"
          />
        </label>

        <div className="form-grid">
          <label>
            Land Area
            <input
              name="land_area"
              type="number"
              value={formData.land_area}
              onChange={updateField}
              min="0"
              step="any"
            />
          </label>

          <label>
            Elevation
            <input
              name="elevation"
              type="number"
              value={formData.elevation}
              onChange={updateField}
              step="any"
            />
          </label>
        </div>

        <label>
          Land Type
          <input
            name="land_type"
            value={formData.land_type}
            onChange={updateField}
            maxLength="100"
          />
        </label>

        <label>
          Ownership
          <input
            name="ownership"
            value={formData.ownership}
            onChange={updateField}
            maxLength="100"
          />
        </label>

        {(validationError || error) && (
          <p className="form-error">{validationError || error}</p>
        )}

        <div className="action-row">
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : submitLabel}
          </button>
          <Link className="secondary-link" to={`/app/projects/${project.project_id}`}>
            Cancel
          </Link>
        </div>
      </form>
    </section>
  );
}

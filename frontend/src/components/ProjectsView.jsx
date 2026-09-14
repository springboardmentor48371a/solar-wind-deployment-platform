import { useState, useEffect, useCallback } from 'react'
import {
  listProjects,
  createProject,
  deleteProject,
  listSites,
  createSite,
  updateSiteStatus,
  deleteSite,
  previewLocation,
} from '../api'
import EnvSummary from './EnvSummary'
import PredictionPanel from './PredictionPanel'
import './ProjectsView.css'

const SITE_STATUSES = [
  { value: 'under_review', label: 'Under Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
]

function TypeBadge({ energyType }) {
  const t = (energyType || 'solar').toLowerCase()
  if (t === 'wind') return <span className="type-badge type-badge--wi">WI</span>
  if (t === 'hybrid') return <span className="type-badge type-badge--hy">HY</span>
  return <span className="type-badge type-badge--so">SO</span>
}

function ProjectStatusPill({ status }) {
  const s = status || 'planning'
  const isGreen = s === 'active' || s === 'completed'
  const isRed = s === 'cancelled'
  const pillClass = isGreen
    ? 'status-pill--green'
    : isRed
    ? 'status-pill--red'
    : 'status-pill--peach'

  return <span className={`status-pill ${pillClass}`}>{s.replace(/_/g, ' ')}</span>
}

export default function ProjectsView({ user }) {
  const canCreateProject = ['energy_planner', 'project_manager'].includes(user.role)
  const canDeleteProject = ['energy_planner', 'project_manager'].includes(user.role)
  const canCreateSite = ['gis_analyst', 'energy_planner', 'project_manager'].includes(user.role)
  const canDeleteSite = ['energy_planner', 'project_manager'].includes(user.role)
  const canUpdateStatus = user.role === 'project_manager'

  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [sites, setSites] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)

  const [showProjectForm, setShowProjectForm] = useState(false)
  const [showSiteForm, setShowSiteForm] = useState(false)

  const [projectForm, setProjectForm] = useState({ name: '', description: '' })
  const [siteForm, setSiteForm] = useState({
    name: '',
    latitude: '',
    longitude: '',
    energy_type: 'solar',
    land_ownership: 'unknown',
    notes: '',
    status: 'under_review',
  })

  // Location detection preview state
  const [preview, setPreview] = useState(null)
  const [previewing, setPreviewing] = useState(false)
  const [previewError, setPreviewError] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [projectSearch, setProjectSearch] = useState('')
  const [siteSearch, setSiteSearch] = useState('')

  const loadProjects = useCallback(async () => {
    const res = await listProjects()
    setProjects(res.data)
    if (res.data.length > 0 && !selectedProject) {
      setSelectedProject(res.data[0])
    }
  }, [selectedProject])

  const loadSites = useCallback(async (projectId) => {
    const res = await listSites(projectId)
    setSites(res.data)
  }, [])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  useEffect(() => {
    if (selectedProject) {
      loadSites(selectedProject.id)
    }
  }, [selectedProject, loadSites])

  const handleCreateProject = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createProject(projectForm)
      setShowProjectForm(false)
      setProjectForm({ name: '', description: '' })
      loadProjects()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initialize new project')
    }
  }

  const handleDeleteProject = async (id) => {
    if (!window.confirm('Are you sure you want to delete this project and all affiliated sites?')) return
    await deleteProject(id)
    setSelectedProject(null)
    setSites([])
    loadProjects()
  }

  // Step 1: Detect location coordinates
  const handlePreview = async (e) => {
    e.preventDefault()
    setPreviewError('')
    setPreview(null)
    setPreviewing(true)
    try {
      const res = await previewLocation(
        parseFloat(siteForm.latitude),
        parseFloat(siteForm.longitude)
      )
      setPreview(res.data)
    } catch (err) {
      setPreviewError(
        err.response?.data?.detail || 'Could not verify location. Please verify latitude/longitude format.'
      )
    } finally {
      setPreviewing(false)
    }
  }

  // Step 2: Confirm and create site
  const handleCreateSite = async () => {
    setError('')
    setSubmitting(true)
    try {
      await createSite({
        name: siteForm.name,
        project_id: selectedProject.id,
        latitude: parseFloat(siteForm.latitude),
        longitude: parseFloat(siteForm.longitude),
        energy_type: siteForm.energy_type,
        land_ownership: siteForm.land_ownership,
        notes: siteForm.notes || null,
      })
      setShowSiteForm(false)
      setSiteForm({
        name: '',
        latitude: '',
        longitude: '',
        energy_type: 'solar',
        land_ownership: 'unknown',
        notes: '',
        status: 'under_review',
      })
      setPreview(null)
      loadSites(selectedProject.id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create site')
    } finally {
      setSubmitting(false)
    }
  }

  const handleStatusChange = async (siteId, status) => {
    await updateSiteStatus(siteId, status, null)
    loadSites(selectedProject.id)
  }

  const handleDeleteSite = async (siteId) => {
    if (!window.confirm('Are you sure you want to remove this site?')) return
    await deleteSite(siteId)
    if (selectedSite?.id === siteId) setSelectedSite(null)
    loadSites(selectedProject.id)
  }

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(projectSearch.toLowerCase()) ||
    (p.description || '').toLowerCase().includes(projectSearch.toLowerCase())
  )

  const filteredSites = sites.filter((s) =>
    s.name.toLowerCase().includes(siteSearch.toLowerCase())
  )

  const closeSiteForm = () => {
    setShowSiteForm(false)
    setSiteForm({
      name: '',
      latitude: '',
      longitude: '',
      energy_type: 'solar',
      land_ownership: 'unknown',
      notes: '',
      status: 'under_review',
    })
    setPreview(null)
    setPreviewError('')
    setError('')
  }

  return (
    <div className="projects-view">
      {error && (
        <div style={{ backgroundColor: 'var(--color-pill-red-bg)', color: 'var(--color-pill-red-text)', padding: '10px 14px', borderRadius: 'var(--radius-badge)', fontSize: '13px' }}>
          {error}
        </div>
      )}

      <div className="projects-view__layout">
        {/* Left Column: Project Catalog */}
        <div className="projects-col">
          <div className="projects-col__header">
            <span className="projects-col__eyebrow">Project Portfolios ({projects.length})</span>
            {canCreateProject && (
              <button
                type="button"
                className="btn-primary"
                style={{ padding: '5px 12px', fontSize: '12px' }}
                onClick={() => setShowProjectForm(true)}
              >
                + New
              </button>
            )}
          </div>

          <input
            type="text"
            className="search-input"
            placeholder="Search projects..."
            value={projectSearch}
            onChange={(e) => setProjectSearch(e.target.value)}
          />

          {projects.length === 0 && (
            <div style={{ padding: '24px 16px', background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', border: '1px solid var(--color-border)', fontSize: '13px', color: 'var(--color-text-secondary)', textAlign: 'center' }}>
              No project portfolios configured yet.
            </div>
          )}

          {projects.length > 0 && filteredProjects.length === 0 && (
            <div style={{ padding: '24px 16px', background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', border: '1px solid var(--color-border)', fontSize: '13px', color: 'var(--color-text-secondary)', textAlign: 'center' }}>
              No matches for &ldquo;{projectSearch}&rdquo;
            </div>
          )}

          {filteredProjects.map((p) => {
            const isSelected = selectedProject?.id === p.id
            return (
              <div
                key={p.id}
                className={`project-item ${isSelected ? 'project-item--selected' : ''}`}
                onClick={() => {
                  setSelectedProject(p)
                  setSelectedSite(null)
                }}
              >
                <div className="project-item__header">
                  <div className="project-item__name">{p.name}</div>
                  {canDeleteProject && (
                    <button
                      type="button"
                      className="project-item__delete-btn"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteProject(p.id)
                      }}
                      title="Delete Project"
                    >
                      &times;
                    </button>
                  )}
                </div>
                {p.description && (
                  <div className="project-item__desc">{p.description}</div>
                )}
                <div>
                  <ProjectStatusPill status={p.status} />
                </div>
              </div>
            )
          })}
        </div>

        {/* Right Column: Sites within Selected Project */}
        <div className="sites-col">
          {selectedProject ? (
            <>
              <div className="sites-col__header">
                <div>
                  <div className="sites-col__title">{selectedProject.name}</div>
                  {selectedProject.description && (
                    <div className="sites-col__desc">{selectedProject.description}</div>
                  )}
                </div>
                {canCreateSite && (
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={() => setShowSiteForm(true)}
                  >
                    + Add Site
                  </button>
                )}
              </div>

              <input
                type="text"
                className="search-input"
                placeholder="Search sites..."
                value={siteSearch}
                onChange={(e) => setSiteSearch(e.target.value)}
              />

              {sites.length === 0 && (
                <div style={{ padding: '36px 20px', background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', border: '1px solid var(--color-border)', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                  No candidate sites cataloged under this project. Click <strong>+ Add Site</strong> to define coordinates.
                </div>
              )}

              {sites.length > 0 && filteredSites.length === 0 && (
                <div style={{ padding: '36px 20px', background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', border: '1px solid var(--color-border)', textAlign: 'center', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                  No matches for &ldquo;{siteSearch}&rdquo;
                </div>
              )}

              {filteredSites.map((site) => {
                const isSelected = selectedSite?.id === site.id
                return (
                  <div
                    key={site.id}
                    className={`site-card ${isSelected ? 'site-card--active' : ''}`}
                    onClick={() => setSelectedSite(isSelected ? null : site)}
                  >
                    <div className="site-card__top">
                      <div className="site-card__identity">
                        <TypeBadge energyType={site.energy_type} />
                        <div>
                          <div className="site-card__name">{site.name}</div>
                          <div className="site-card__meta">
                            {site.energy_type} &middot; {site.latitude.toFixed(4)}&deg;, {site.longitude.toFixed(4)}&deg;
                            {site.elevation && ` · ${site.elevation}m`}
                          </div>
                        </div>
                      </div>

                      <div className="site-card__actions">
                        {canUpdateStatus && (
                          <select
                            className="site-card__select"
                            value={site.status}
                            onChange={(e) => {
                              e.stopPropagation()
                              handleStatusChange(site.id, e.target.value)
                            }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            {SITE_STATUSES.map((s) => (
                              <option key={s.value} value={s.value}>
                                {s.label}
                              </option>
                            ))}
                          </select>
                        )}

                        {canDeleteSite && (
                          <button
                            type="button"
                            className="site-card__delete-btn"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteSite(site.id)
                            }}
                            title="Delete Site"
                          >
                            &times;
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Expandable Environmental & ML Details */}
                    {isSelected && (
                      <div onClick={(e) => e.stopPropagation()}>
                        <EnvSummary siteId={site.id} energyType={site.energy_type} />
                        <PredictionPanel siteId={site.id} energyType={site.energy_type} />
                      </div>
                    )}
                  </div>
                )
              })}
            </>
          ) : (
            <div style={{ padding: '36px', background: 'var(--color-surface)', borderRadius: 'var(--radius-card)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)', textAlign: 'center', fontSize: '13px' }}>
              Select a project from the left sidebar to view its candidate deployment sites.
            </div>
          )}
        </div>
      </div>

      {/* New Project Modal */}
      {showProjectForm && (
        <div className="modal-overlay" onClick={() => setShowProjectForm(false)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">New Project Portfolio</div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setShowProjectForm(false)}
              >
                &times;
              </button>
            </div>
            <form onSubmit={handleCreateProject}>
              <div className="modal-field">
                <label className="modal-label">Portfolio / Project Name</label>
                <input
                  className="modal-input"
                  value={projectForm.name}
                  onChange={(e) =>
                    setProjectForm({ ...projectForm, name: e.target.value })
                  }
                  placeholder="e.g. Tamil Nadu Coastal Solar & Wind Phase I"
                  required
                />
              </div>
              <div className="modal-field">
                <label className="modal-label">Description &amp; Objective</label>
                <input
                  className="modal-input"
                  value={projectForm.description}
                  onChange={(e) =>
                    setProjectForm({ ...projectForm, description: e.target.value })
                  }
                  placeholder="Scope, regional target, or feasibility notes"
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowProjectForm(false)}
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Create Project
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Site Modal */}
      {showSiteForm && (
        <div className="modal-overlay" onClick={closeSiteForm}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                Add Site to &ldquo;{selectedProject?.name}&rdquo;
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={closeSiteForm}
              >
                &times;
              </button>
            </div>

            {!preview ? (
              /* Step 1: Input Coordinates */
              <form onSubmit={handlePreview}>
                <div className="modal-field">
                  <label className="modal-label">Site Identifier</label>
                  <input
                    className="modal-input"
                    value={siteForm.name}
                    onChange={(e) =>
                      setSiteForm({ ...siteForm, name: e.target.value })
                    }
                    placeholder="e.g. Ramanathapuram Sector 4"
                    required
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div className="modal-field">
                    <label className="modal-label">Latitude</label>
                    <input
                      className="modal-input"
                      type="number"
                      step="any"
                      value={siteForm.latitude}
                      onChange={(e) =>
                        setSiteForm({ ...siteForm, latitude: e.target.value })
                      }
                      placeholder="e.g. 9.3639"
                      required
                    />
                  </div>
                  <div className="modal-field">
                    <label className="modal-label">Longitude</label>
                    <input
                      className="modal-input"
                      type="number"
                      step="any"
                      value={siteForm.longitude}
                      onChange={(e) =>
                        setSiteForm({ ...siteForm, longitude: e.target.value })
                      }
                      placeholder="e.g. 78.8395"
                      required
                    />
                  </div>
                </div>

                <div className="modal-field">
                  <label className="modal-label">Technology Focus</label>
                  <select
                    className="modal-select"
                    value={siteForm.energy_type}
                    onChange={(e) =>
                      setSiteForm({ ...siteForm, energy_type: e.target.value })
                    }
                  >
                    <option value="solar">Solar PV</option>
                    <option value="wind">Wind Turbine</option>
                    <option value="hybrid">Solar-Wind Hybrid</option>
                  </select>
                </div>

                <div className="modal-field">
                  <label className="modal-label">Land Ownership Model</label>
                  <select
                    className="modal-select"
                    value={siteForm.land_ownership}
                    onChange={(e) =>
                      setSiteForm({ ...siteForm, land_ownership: e.target.value })
                    }
                  >
                    <option value="unknown">Unspecified / Unknown</option>
                    <option value="government">Government / Public Land</option>
                    <option value="private">Private Ownership</option>
                    <option value="community">Community / Common Pool</option>
                  </select>
                </div>

                <div className="modal-field">
                  <label className="modal-label">Notes &amp; Constraints</label>
                  <input
                    className="modal-input"
                    value={siteForm.notes}
                    onChange={(e) =>
                      setSiteForm({ ...siteForm, notes: e.target.value })
                    }
                    placeholder="Substation distance, terrain notes, etc."
                  />
                </div>

                {previewError && (
                  <div style={{ backgroundColor: 'var(--color-pill-red-bg)', color: 'var(--color-pill-red-text)', padding: '8px 12px', borderRadius: 'var(--radius-badge)', fontSize: '12px', marginBottom: '12px' }}>
                    {previewError}
                  </div>
                )}

                <div className="modal-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={closeSiteForm}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={previewing}
                  >
                    {previewing ? 'Detecting Geography...' : 'Detect Location &rarr;'}
                  </button>
                </div>
              </form>
            ) : (
              /* Step 2: Confirm Detected Location */
              <div>
                <div className="modal-location-preview">
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
                    Auto-Detected Geographic Boundary
                  </div>
                  <div className="modal-location-title">
                    {preview.city ? `${preview.city}, ` : ''}
                    {preview.state ? `${preview.state}, ` : ''}
                    {preview.country}
                  </div>
                  <div className="modal-location-desc">{preview.display_name}</div>
                  {preview.elevation !== null && (
                    <div style={{ fontSize: '12px', color: 'var(--color-text-primary)', marginTop: '8px', fontWeight: 500 }}>
                      Terrain Elevation: <strong>{preview.elevation}m</strong>
                    </div>
                  )}
                </div>

                <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: '16px' }}>
                  Confirm adding site <strong>{siteForm.name}</strong> to portfolio?
                </p>

                {error && (
                  <div style={{ backgroundColor: 'var(--color-pill-red-bg)', color: 'var(--color-pill-red-text)', padding: '8px 12px', borderRadius: 'var(--radius-badge)', fontSize: '12px', marginBottom: '12px' }}>
                    {error}
                  </div>
                )}

                <div className="modal-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => {
                      setPreview(null)
                      setPreviewError('')
                    }}
                  >
                    &larr; Re-enter Coordinates
                  </button>
                  <button
                    type="button"
                    className="btn-primary"
                    onClick={handleCreateSite}
                    disabled={submitting}
                  >
                    {submitting ? 'Registering...' : 'Confirm & Save Site'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

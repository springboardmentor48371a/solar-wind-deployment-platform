import { useState, useEffect } from 'react'
import { listProjects, createProject, deleteProject, listSites, createSite, updateSiteStatus, deleteSite, previewLocation } from '../api'
import EnvSummary from './EnvSummary'
import PredictionPanel from './PredictionPanel'

const SITE_STATUSES = ['under_review', 'approved', 'rejected']

const Badge = ({ value, colors }) => (
  <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12, background: (colors[value] || '#6b7280') + '20', color: colors[value] || '#6b7280', fontWeight: 600, textTransform: 'capitalize' }}>
    {value?.replace(/_/g, ' ')}
  </span>
)

const inputStyle = { width: '100%', padding: '7px 10px', border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13, marginTop: 4 }
const labelStyle = { fontSize: 12, color: '#6b7280', display: 'block', marginTop: 10 }

export default function ProjectsView({ user }) {
  const canCreateProject = ['energy_planner', 'project_manager', 'administrator'].includes(user.role)
  const canDeleteProject = user.role === 'administrator'
  const canUpdateStatus = ['energy_planner', 'project_manager', 'administrator'].includes(user.role)

  const [projects, setProjects] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [sites, setSites] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)

  const [showProjectForm, setShowProjectForm] = useState(false)
  const [showSiteForm, setShowSiteForm] = useState(false)

  const [projectForm, setProjectForm] = useState({ name: '', description: '' })
  const [siteForm, setSiteForm] = useState({ name: '', latitude: '', longitude: '', energy_type: 'solar', land_ownership: 'unknown', notes: '', status: 'under_review' })

  // Preview state
  const [preview, setPreview] = useState(null)
  const [previewing, setPreviewing] = useState(false)
  const [previewError, setPreviewError] = useState('')
  const [confirmed, setConfirmed] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => { loadProjects() }, [])
  useEffect(() => { if (selectedProject) loadSites(selectedProject.id) }, [selectedProject])

  const loadProjects = async () => {
    const res = await listProjects()
    setProjects(res.data)
    if (res.data.length > 0 && !selectedProject) setSelectedProject(res.data[0])
  }

  const loadSites = async (projectId) => {
    const res = await listSites(projectId)
    setSites(res.data)
  }

  const handleCreateProject = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createProject(projectForm)
      setShowProjectForm(false)
      setProjectForm({ name: '', description: '' })
      loadProjects()
    } catch (err) { setError(err.response?.data?.detail || 'Failed to create project') }
  }

  const handleDeleteProject = async (id) => {
    if (!confirm('Delete this project?')) return
    await deleteProject(id)
    setSelectedProject(null)
    setSites([])
    loadProjects()
  }

  // Step 1 — preview coordinates
  const handlePreview = async (e) => {
    e.preventDefault()
    setPreviewError('')
    setPreview(null)
    setConfirmed(false)
    setPreviewing(true)
    try {
      const res = await previewLocation(parseFloat(siteForm.latitude), parseFloat(siteForm.longitude))
      setPreview(res.data)
    } catch (err) {
      setPreviewError(err.response?.data?.detail || 'Could not detect location. Check your coordinates.')
    } finally {
      setPreviewing(false)
    }
  }

  // Step 2 — confirm and create site
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
      setSiteForm({ name: '', latitude: '', longitude: '', energy_type: 'solar', land_ownership: 'unknown', notes: '', status: 'under_review' })
      setPreview(null)
      setConfirmed(false)
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
    if (!confirm('Delete this site?')) return
    await deleteSite(siteId)
    if (selectedSite?.id === siteId) setSelectedSite(null)
    loadSites(selectedProject.id)
  }

  const closeSiteForm = () => {
    setShowSiteForm(false)
    setSiteForm({ name: '', latitude: '', longitude: '', energy_type: 'solar', land_ownership: 'unknown', notes: '', status: 'under_review' })
    setPreview(null)
    setPreviewError('')
    setConfirmed(false)
    setError('')
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Projects & Sites</h2>
        {canCreateProject && (
          <button onClick={() => setShowProjectForm(true)} style={{ padding: '7px 14px', fontSize: 12, border: 'none', borderRadius: 6, cursor: 'pointer', background: '#111', color: '#fff' }}>+ New Project</button>
        )}
      </div>

      {error && <p style={{ color: '#dc2626', fontSize: 12, marginBottom: 12 }}>{error}</p>}

      <div style={{ display: 'flex', gap: 20 }}>
        {/* Projects list */}
        <div style={{ width: 240, flexShrink: 0 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#9ca3af', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Projects</div>
          {projects.length === 0 && <p style={{ fontSize: 12, color: '#9ca3af' }}>No projects yet.</p>}
          {projects.map(p => (
            <div key={p.id} onClick={() => { setSelectedProject(p); setSelectedSite(null) }}
              style={{ padding: '10px 12px', borderRadius: 8, marginBottom: 4, cursor: 'pointer', border: '1px solid', borderColor: selectedProject?.id === p.id ? '#111' : '#e5e7eb', background: selectedProject?.id === p.id ? '#f9fafb' : '#fff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{p.name}</div>
                {canDeleteProject && (
                  <button onClick={(e) => { e.stopPropagation(); handleDeleteProject(p.id) }}
                    style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: 12, padding: 0 }}>✕</button>
                )}
              </div>
              <Badge value={p.status} colors={{ planning: '#6b7280', active: '#16a34a', completed: '#2563eb', on_hold: '#ca8a04' }} />
            </div>
          ))}
        </div>

        {/* Sites list */}
        <div style={{ flex: 1 }}>
          {selectedProject ? (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 15, fontWeight: 700 }}>{selectedProject.name}</div>
                  {selectedProject.description && <div style={{ fontSize: 12, color: '#9ca3af' }}>{selectedProject.description}</div>}
                </div>
                <button onClick={() => setShowSiteForm(true)} style={{ padding: '7px 14px', fontSize: 12, border: 'none', borderRadius: 6, cursor: 'pointer', background: '#111', color: '#fff' }}>+ Add Site</button>
              </div>

              {sites.length === 0 && <p style={{ fontSize: 12, color: '#9ca3af' }}>No sites yet.</p>}

              {sites.map(site => (
                <div key={site.id}
                  style={{ background: '#fff', border: '1px solid', borderColor: selectedSite?.id === site.id ? '#111' : '#e5e7eb', borderRadius: 8, padding: 14, marginBottom: 10, cursor: 'pointer' }}
                  onClick={() => setSelectedSite(selectedSite?.id === site.id ? null : site)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{site.name}</div>
                      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                        {site.energy_type} · {site.latitude}, {site.longitude}
                        {site.elevation && ` · ${site.elevation}m`}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      {canUpdateStatus && (
                        <select value={site.status}
                          onChange={(e) => { e.stopPropagation(); handleStatusChange(site.id, e.target.value) }}
                          onClick={e => e.stopPropagation()}
                          style={{ fontSize: 11, padding: '3px 6px', border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer' }}>
                          {SITE_STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                        </select>
                      )}
                      <button onClick={(e) => { e.stopPropagation(); handleDeleteSite(site.id) }}
                        style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: 13 }}>✕</button>
                    </div>
                  </div>
                  {selectedSite?.id === site.id && (
                    <div onClick={e => e.stopPropagation()}>
                      <EnvSummary siteId={site.id} energyType={site.energy_type} />
                      <PredictionPanel siteId={site.id} energyType={site.energy_type} />
                    </div>
                  )}
                </div>
              ))}
            </>
          ) : (
            <p style={{ fontSize: 13, color: '#9ca3af' }}>Select a project to view its sites.</p>
          )}
        </div>
      </div>

      {/* Create Project Modal */}
      {showProjectForm && (
        <Modal title="New Project" onClose={() => { setShowProjectForm(false); setProjectForm({ name: '', description: '' }) }}>
          <form onSubmit={handleCreateProject}>
            <label style={labelStyle}>Project Name</label>
            <input style={inputStyle} value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} placeholder="e.g. Tamil Nadu Solar Farm" required />
            <label style={labelStyle}>Description</label>
            <input style={inputStyle} value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} placeholder="Optional" />
            <ModalActions onClose={() => setShowProjectForm(false)} label="Create Project" />
          </form>
        </Modal>
      )}

      {/* Add Site Modal */}
      {showSiteForm && (
        <Modal title={`Add Site to "${selectedProject?.name}"`} onClose={closeSiteForm}>
          {!preview ? (
            // Step 1 — enter coordinates
            <form onSubmit={handlePreview}>
              <label style={labelStyle}>Site Name</label>
              <input style={inputStyle} value={siteForm.name} onChange={e => setSiteForm({ ...siteForm, name: e.target.value })} placeholder="e.g. Ramanathapuram Site A" required />
              <div style={{ display: 'flex', gap: 8 }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Latitude</label>
                  <input style={inputStyle} type="number" step="any" value={siteForm.latitude} onChange={e => setSiteForm({ ...siteForm, latitude: e.target.value })} placeholder="e.g. 9.3639" required />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Longitude</label>
                  <input style={inputStyle} type="number" step="any" value={siteForm.longitude} onChange={e => setSiteForm({ ...siteForm, longitude: e.target.value })} placeholder="e.g. 78.8395" required />
                </div>
              </div>
              <label style={labelStyle}>Energy Type</label>
              <select style={inputStyle} value={siteForm.energy_type} onChange={e => setSiteForm({ ...siteForm, energy_type: e.target.value })}>
                <option value="solar">Solar</option>
                <option value="wind">Wind</option>
                <option value="hybrid">Hybrid</option>
              </select>
              <label style={labelStyle}>Land Ownership</label>
              <select style={inputStyle} value={siteForm.land_ownership} onChange={e => setSiteForm({ ...siteForm, land_ownership: e.target.value })}>
                <option value="unknown">Unknown</option>
                <option value="government">Government</option>
                <option value="private">Private</option>
                <option value="community">Community</option>
              </select>
              <label style={labelStyle}>Notes</label>
              <input style={inputStyle} value={siteForm.notes} onChange={e => setSiteForm({ ...siteForm, notes: e.target.value })} placeholder="Optional" />
              {previewError && <p style={{ color: '#dc2626', fontSize: 12, marginTop: 8 }}>{previewError}</p>}
              <ModalActions onClose={closeSiteForm} label={previewing ? 'Detecting location...' : 'Detect Location →'} disabled={previewing} />
            </form>
          ) : (
            // Step 2 — confirm detected location
            <div>
              <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 14, marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: '#6b7280', marginBottom: 6 }}>Detected Location</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#111' }}>{preview.city ? `${preview.city}, ` : ''}{preview.state ? `${preview.state}, ` : ''}{preview.country}</div>
                <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>{preview.display_name}</div>
                {preview.elevation !== null && (
                  <div style={{ fontSize: 12, color: '#6b7280', marginTop: 6 }}>Elevation: <strong>{preview.elevation}m</strong> · Auto-detected</div>
                )}
              </div>
              <p style={{ fontSize: 13, color: '#374151', marginBottom: 16 }}>
                Is this the correct location for <strong>{siteForm.name}</strong>?
              </p>
              {error && <p style={{ color: '#dc2626', fontSize: 12, marginBottom: 8 }}>{error}</p>}
              <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                <button onClick={() => { setPreview(null); setPreviewError('') }}
                  style={{ padding: '8px 16px', border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff', fontSize: 13 }}>
                  ← Edit Coordinates
                </button>
                <button onClick={handleCreateSite} disabled={submitting}
                  style={{ padding: '8px 16px', border: 'none', borderRadius: 6, cursor: 'pointer', background: '#111', color: '#fff', fontSize: 13 }}>
                  {submitting ? 'Creating...' : 'Confirm & Create Site'}
                </button>
              </div>
            </div>
          )}
        </Modal>
      )}
    </div>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#fff', borderRadius: 10, padding: 24, width: 440, maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <span style={{ fontWeight: 700, fontSize: 15 }}>{title}</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#9ca3af' }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function ModalActions({ onClose, label, disabled }) {
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
      <button type="button" onClick={onClose} style={{ padding: '8px 16px', border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff', fontSize: 13 }}>Cancel</button>
      <button type="submit" disabled={disabled} style={{ padding: '8px 16px', border: 'none', borderRadius: 6, cursor: 'pointer', background: '#111', color: '#fff', fontSize: 13, opacity: disabled ? 0.6 : 1 }}>{label}</button>
    </div>
  )
}

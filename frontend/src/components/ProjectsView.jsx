import { useState, useEffect } from 'react'
import { listProjects, createProject, deleteProject, updateProject, listRegions, createRegion, listSites, createSite, updateSiteStatus, deleteSite } from '../api'
import EnvSummary from './EnvSummary'

const STATUS_COLORS = { planned: '#6b7280', under_review: '#ca8a04', approved: '#2563eb', deployed: '#16a34a', rejected: '#dc2626' }
const SITE_STATUSES = ['planned', 'under_review', 'approved', 'deployed', 'rejected']

const Badge = ({ value, colors }) => (
  <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 12, background: (colors[value] || '#6b7280') + '20', color: colors[value] || '#6b7280', fontWeight: 600, textTransform: 'capitalize' }}>
    {value?.replace(/_/g, ' ')}
  </span>
)

export default function ProjectsView({ user }) {
  const canCreateProject = ['energy_planner', 'project_manager', 'administrator'].includes(user.role)
  const canDeleteProject = user.role === 'administrator'
  const canCreateRegion = user.role === 'administrator'
  const canUpdateStatus = ['energy_planner', 'project_manager', 'administrator'].includes(user.role)

  const [projects, setProjects] = useState([])
  const [regions, setRegions] = useState([])
  const [selectedProject, setSelectedProject] = useState(null)
  const [sites, setSites] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)

  // Modals
  const [showProjectForm, setShowProjectForm] = useState(false)
  const [showSiteForm, setShowSiteForm] = useState(false)
  const [showRegionForm, setShowRegionForm] = useState(false)

  // Forms
  const [projectForm, setProjectForm] = useState({ name: '', description: '', region_id: '' })
  const [siteForm, setSiteForm] = useState({ name: '', latitude: '', longitude: '', elevation: '', land_area: '', energy_type: 'solar', land_ownership: 'unknown' })
  const [regionForm, setRegionForm] = useState({ name: '', country: '', state: '' })
  const [error, setError] = useState('')

  useEffect(() => { loadProjects(); loadRegions() }, [])
  useEffect(() => { if (selectedProject) loadSites(selectedProject.id) }, [selectedProject])

  const loadProjects = async () => {
    const res = await listProjects()
    setProjects(res.data)
    if (res.data.length > 0 && !selectedProject) setSelectedProject(res.data[0])
  }

  const loadRegions = async () => {
    const res = await listRegions()
    setRegions(res.data)
  }

  const loadSites = async (projectId) => {
    const res = await listSites(projectId)
    setSites(res.data)
  }

  const handleCreateProject = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createProject({ ...projectForm, region_id: parseInt(projectForm.region_id) })
      setShowProjectForm(false)
      setProjectForm({ name: '', description: '', region_id: '' })
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

  const handleCreateSite = async (e) => {
    e.preventDefault()
    setError('')
    try {
      await createSite({ ...siteForm, project_id: selectedProject.id, latitude: parseFloat(siteForm.latitude), longitude: parseFloat(siteForm.longitude), elevation: siteForm.elevation ? parseFloat(siteForm.elevation) : null, land_area: siteForm.land_area ? parseFloat(siteForm.land_area) : null })
      setShowSiteForm(false)
      setSiteForm({ name: '', latitude: '', longitude: '', elevation: '', land_area: '', energy_type: 'solar', land_ownership: 'unknown' })
      loadSites(selectedProject.id)
    } catch (err) { setError(err.response?.data?.detail || 'Failed to create site') }
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

  const handleCreateRegion = async (e) => {
    e.preventDefault()
    try {
      await createRegion(regionForm)
      setShowRegionForm(false)
      setRegionForm({ name: '', country: '', state: '' })
      loadRegions()
    } catch (err) { setError(err.response?.data?.detail || 'Failed to create region') }
  }

  const inputStyle = { width: '100%', padding: '7px 10px', border: '1px solid #e5e7eb', borderRadius: 6, fontSize: 13, marginTop: 4 }
  const labelStyle = { fontSize: 12, color: '#6b7280', display: 'block', marginTop: 10 }

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ fontSize: 18, fontWeight: 700 }}>Projects & Sites</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {canCreateRegion && (
            <button onClick={() => setShowRegionForm(true)} style={{ padding: '7px 14px', fontSize: 12, border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff' }}>+ Region</button>
          )}
          {canCreateProject && (
            <button onClick={() => setShowProjectForm(true)} style={{ padding: '7px 14px', fontSize: 12, border: 'none', borderRadius: 6, cursor: 'pointer', background: '#111', color: '#fff' }}>+ New Project</button>
          )}
        </div>
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
              <div style={{ fontSize: 13, fontWeight: 600 }}>{p.name}</div>
              <Badge value={p.status} colors={{ planning: '#6b7280', active: '#16a34a', completed: '#2563eb', on_hold: '#ca8a04' }} />
              {canDeleteProject && (
                <button onClick={(e) => { e.stopPropagation(); handleDeleteProject(p.id) }}
                  style={{ float: 'right', background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: 12 }}>✕</button>
              )}
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
                <div key={site.id} style={{ background: '#fff', border: '1px solid', borderColor: selectedSite?.id === site.id ? '#111' : '#e5e7eb', borderRadius: 8, padding: 14, marginBottom: 10, cursor: 'pointer' }}
                  onClick={() => setSelectedSite(selectedSite?.id === site.id ? null : site)}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{site.name}</div>
                      <div style={{ fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                        {site.energy_type} · {site.latitude}, {site.longitude}
                        {site.land_area && ` · ${site.land_area} ha`}
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <Badge value={site.status} colors={STATUS_COLORS} />
                      {canUpdateStatus && (
                        <select value={site.status} onChange={(e) => { e.stopPropagation(); handleStatusChange(site.id, e.target.value) }}
                          onClick={e => e.stopPropagation()}
                          style={{ fontSize: 11, padding: '3px 6px', border: '1px solid #e5e7eb', borderRadius: 4, cursor: 'pointer' }}>
                          {SITE_STATUSES.map(s => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                        </select>
                      )}
                      <button onClick={(e) => { e.stopPropagation(); handleDeleteSite(site.id) }}
                        style={{ background: 'none', border: 'none', color: '#dc2626', cursor: 'pointer', fontSize: 13 }}>✕</button>
                    </div>
                  </div>

                  {/* Environmental summary — expanded */}
                  {selectedSite?.id === site.id && (
                    <div onClick={e => e.stopPropagation()}>
                      <EnvSummary siteId={site.id} />
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
        <Modal title="New Project" onClose={() => setShowProjectForm(false)}>
          <form onSubmit={handleCreateProject}>
            <label style={labelStyle}>Project Name</label>
            <input style={inputStyle} value={projectForm.name} onChange={e => setProjectForm({ ...projectForm, name: e.target.value })} required />
            <label style={labelStyle}>Description</label>
            <input style={inputStyle} value={projectForm.description} onChange={e => setProjectForm({ ...projectForm, description: e.target.value })} />
            <label style={labelStyle}>Region</label>
            <select style={inputStyle} value={projectForm.region_id} onChange={e => setProjectForm({ ...projectForm, region_id: e.target.value })} required>
              <option value="">Select region</option>
              {regions.map(r => <option key={r.id} value={r.id}>{r.name}, {r.country}</option>)}
            </select>
            {regions.length === 0 && <p style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>No regions available. Ask an admin to create one first.</p>}
            <ModalActions onClose={() => setShowProjectForm(false)} label="Create Project" />
          </form>
        </Modal>
      )}

      {/* Create Site Modal */}
      {showSiteForm && (
        <Modal title={`Add Site to "${selectedProject?.name}"`} onClose={() => setShowSiteForm(false)}>
          <form onSubmit={handleCreateSite}>
            <label style={labelStyle}>Site Name</label>
            <input style={inputStyle} value={siteForm.name} onChange={e => setSiteForm({ ...siteForm, name: e.target.value })} required />
            <div style={{ display: 'flex', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Latitude</label>
                <input style={inputStyle} type="number" step="any" value={siteForm.latitude} onChange={e => setSiteForm({ ...siteForm, latitude: e.target.value })} required />
              </div>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Longitude</label>
                <input style={inputStyle} type="number" step="any" value={siteForm.longitude} onChange={e => setSiteForm({ ...siteForm, longitude: e.target.value })} required />
              </div>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Elevation (m)</label>
                <input style={inputStyle} type="number" step="any" value={siteForm.elevation} onChange={e => setSiteForm({ ...siteForm, elevation: e.target.value })} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={labelStyle}>Land Area (ha)</label>
                <input style={inputStyle} type="number" step="any" value={siteForm.land_area} onChange={e => setSiteForm({ ...siteForm, land_area: e.target.value })} />
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
            <ModalActions onClose={() => setShowSiteForm(false)} label="Add Site" />
          </form>
        </Modal>
      )}

      {/* Create Region Modal */}
      {showRegionForm && (
        <Modal title="New Region" onClose={() => setShowRegionForm(false)}>
          <form onSubmit={handleCreateRegion}>
            <label style={labelStyle}>Region Name</label>
            <input style={inputStyle} value={regionForm.name} onChange={e => setRegionForm({ ...regionForm, name: e.target.value })} required />
            <label style={labelStyle}>Country</label>
            <input style={inputStyle} value={regionForm.country} onChange={e => setRegionForm({ ...regionForm, country: e.target.value })} required />
            <label style={labelStyle}>State / Province</label>
            <input style={inputStyle} value={regionForm.state} onChange={e => setRegionForm({ ...regionForm, state: e.target.value })} />
            <ModalActions onClose={() => setShowRegionForm(false)} label="Create Region" />
          </form>
        </Modal>
      )}
    </div>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
      <div style={{ background: '#fff', borderRadius: 10, padding: 24, width: 420, maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <span style={{ fontWeight: 700, fontSize: 15 }}>{title}</span>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 18, color: '#9ca3af' }}>✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

function ModalActions({ onClose, label }) {
  return (
    <div style={{ display: 'flex', gap: 8, marginTop: 20, justifyContent: 'flex-end' }}>
      <button type="button" onClick={onClose} style={{ padding: '8px 16px', border: '1px solid #e5e7eb', borderRadius: 6, cursor: 'pointer', background: '#fff', fontSize: 13 }}>Cancel</button>
      <button type="submit" style={{ padding: '8px 16px', border: 'none', borderRadius: 6, cursor: 'pointer', background: '#111', color: '#fff', fontSize: 13 }}>{label}</button>
    </div>
  )
}

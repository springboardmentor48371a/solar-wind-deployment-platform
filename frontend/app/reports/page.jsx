'use client'

import { useEffect, useState } from 'react'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'

const SECTIONS = [
  { key: 'summary', label: 'Executive Summary' },
  { key: 'suitability', label: 'Site Suitability' },
  { key: 'solar', label: 'Solar Potential' },
  { key: 'wind', label: 'Wind Potential' },
  { key: 'financial', label: 'Investment Analytics' },
  { key: 'environmental', label: 'Environmental & Demographic' },
  { key: 'infrastructure', label: 'Infrastructure Proximity' },
  { key: 'weather', label: 'Weather / Climate' },
  { key: 'satellite', label: 'Satellite Imagery Summary' },
]

export default function ReportBuilder() {
  const [projects, setProjects] = useState([])
  const [projectId, setProjectId] = useState('')
  const [selected, setSelected] = useState(['summary', 'suitability'])
  const [templates, setTemplates] = useState([])
  const [templateName, setTemplateName] = useState('')
  const [saving, setSaving] = useState(false)
  const [downloading, setDownloading] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.get('/projects/'), api.get('/report-templates')])
      .then(([projectsRes, templatesRes]) => {
        setProjects(projectsRes.data)
        setTemplates(templatesRes.data)
        if (projectsRes.data.length > 0) setProjectId(String(projectsRes.data[0].id))
      })
      .finally(() => setLoading(false))
  }, [])

  const toggleSection = (key) => {
    setSelected((prev) => (prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]))
  }

  const downloadBlob = async (url, filename) => {
    setError('')
    try {
      const res = await api.get(url, { responseType: 'blob' })
      const blobUrl = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = blobUrl
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(blobUrl)
    } catch (err) {
      setError('Could not generate that report — make sure the project has at least one site.')
    }
  }

  const generateCustom = async () => {
    if (!projectId || selected.length === 0) return
    setDownloading('custom')
    await downloadBlob(
      `/projects/${projectId}/reports/custom?sections=${selected.join(',')}`,
      `custom_report_${projectId}.pdf`
    )
    setDownloading('')
  }

  const generateExecutiveSummary = async () => {
    if (!projectId) return
    setDownloading('exec')
    await downloadBlob(`/projects/${projectId}/reports/executive-summary`, `executive_summary_${projectId}.pdf`)
    setDownloading('')
  }

  const generateFromTemplate = async (templateId, name) => {
    if (!projectId) return
    setDownloading(`t${templateId}`)
    await downloadBlob(`/projects/${projectId}/reports/from-template/${templateId}`, `${name.replace(/\s+/g, '_')}_${projectId}.pdf`)
    setDownloading('')
  }

  const saveTemplate = async () => {
    if (!templateName || selected.length === 0) return
    setSaving(true)
    setError('')
    try {
      const res = await api.post('/report-templates', { name: templateName, sections: selected, is_executive_summary: false })
      setTemplates((prev) => [res.data, ...prev])
      setTemplateName('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save template')
    } finally {
      setSaving(false)
    }
  }

  const deleteTemplate = async (id) => {
    await api.delete(`/report-templates/${id}`)
    setTemplates((prev) => prev.filter((t) => t.id !== id))
  }

  return (
    <AppShell title="Report Builder" subtitle="Custom reports, executive summaries, and reusable templates.">
      {error && <div className="error-banner mb-4">{error}</div>}

      {loading ? (
        <div className="card"><span className="spinner" /> Loading…</div>
      ) : projects.length === 0 ? (
        <div className="card text-ink-faint text-sm py-6 text-center">Create a project first to generate reports.</div>
      ) : (
        <>
          <div className="card mb-4">
            <label className="label">Project</label>
            <select className="input" value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>

          <div className="card mb-4">
            <h3 className="mb-3">Custom Report Sections</h3>
            <div className="grid sm:grid-cols-2 gap-2 mb-4">
              {SECTIONS.map((s) => (
                <label key={s.key} className="flex items-center gap-2 text-sm py-1 cursor-pointer">
                  <input type="checkbox" checked={selected.includes(s.key)} onChange={() => toggleSection(s.key)} />
                  {s.label}
                </label>
              ))}
            </div>
            <div className="flex gap-2.5 flex-wrap items-center">
              <button className="btn" disabled={downloading === 'custom' || selected.length === 0} onClick={generateCustom}>
                {downloading === 'custom' ? 'Generating…' : 'Generate PDF'}
              </button>
              <button className="btn-secondary" disabled={downloading === 'exec'} onClick={generateExecutiveSummary}>
                {downloading === 'exec' ? 'Generating…' : 'Generate Executive Summary'}
              </button>
              <div className="flex-1" />
              <input
                className="input !w-48 !py-1.5"
                placeholder="Save as template…"
                value={templateName}
                onChange={(e) => setTemplateName(e.target.value)}
              />
              <button className="btn-ghost btn-sm" disabled={saving || !templateName || selected.length === 0} onClick={saveTemplate}>
                {saving ? 'Saving…' : 'Save Template'}
              </button>
            </div>
          </div>

          <div className="card">
            <h3 className="mb-3">Saved Templates</h3>
            {templates.length === 0 ? (
              <div className="text-ink-faint text-sm py-4 text-center">No saved templates yet.</div>
            ) : (
              <div className="flex flex-col gap-2">
                {templates.map((t) => (
                  <div key={t.id} className="flex items-center justify-between py-1.5 border-b border-border last:border-0">
                    <div>
                      <div className="font-semibold text-sm">{t.name}</div>
                      <div className="text-ink-faint text-xs">{t.sections.join(', ')}</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        className="btn-ghost btn-sm"
                        disabled={downloading === `t${t.id}`}
                        onClick={() => generateFromTemplate(t.id, t.name)}
                      >
                        {downloading === `t${t.id}` ? 'Generating…' : 'Generate'}
                      </button>
                      <button className="btn-secondary btn-sm" onClick={() => deleteTemplate(t.id)}>Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </AppShell>
  )
}

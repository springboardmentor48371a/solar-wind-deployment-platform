'use client'

import { useEffect, useState } from 'react'
import api from '../../../lib/api'
import AppShell from '../../../components/AppShell'
import { useToast } from '../../../lib/ToastContext'
import { getErrorMessage } from '../../../lib/errorMessage'

const TYPES = [
  { value: 'financial_modeling', label: 'Financial Modeling Tools' },
  { value: 'project_management', label: 'Project Management Tools' },
  { value: 'scada_iot', label: 'SCADA / IoT Platforms' },
  { value: 'power_simulation', label: 'Power System Simulation' },
  { value: 'third_party_analytics', label: 'Third-Party Analytics' },
]

const emptyForm = {
  integration_type: 'project_management',
  name: '',
  endpoint_url: '',
  auth_header_name: '',
  auth_header_value: '',
}

export default function AdminIntegrations() {
  const { showToast } = useToast()
  const [items, setItems] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [testingId, setTestingId] = useState(null)

  const load = () => api.get('/integrations/').then((res) => setItems(res.data)).finally(() => setLoading(false))

  useEffect(() => {
    load()
  }, [])

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const handleCreate = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await api.post('/integrations/', {
        ...form,
        auth_header_name: form.auth_header_name || null,
        auth_header_value: form.auth_header_value || null,
      })
      setForm(emptyForm)
      load()
    } catch (err) {
      showToast(getErrorMessage(err, 'Could not create integration connection'), 'error')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    try {
      await api.delete(`/integrations/${id}`)
      load()
      showToast('Integration removed.', 'success')
    } catch (err) {
      showToast(getErrorMessage(err, 'Could not remove integration'), 'error')
    }
  }

  const handleTest = async (id) => {
    setTestingId(id)
    try {
      await api.post(`/integrations/${id}/test`)
      load()
      showToast('Test event sent.', 'success')
    } catch (err) {
      showToast(getErrorMessage(err, 'Test failed — check the endpoint URL and try again.'), 'error')
    } finally {
      setTestingId(null)
    }
  }

  return (
    <AppShell
      title="Integrations"
      subtitle="Financial modeling, project management, SCADA/IoT, power simulation, and analytics connectors."
    >
      {error && <div className="error-banner mb-4">{error}</div>}

      <div className="card mb-4">
        <h3 className="mb-3">Add a connection</h3>
        <p className="text-ink-muted text-sm mb-3">
          Generic webhook connector — point it at any compatible endpoint (Zapier, a Jira webhook,
          an MQTT-to-HTTP bridge, Segment, a custom SCADA gateway). Events fire as an HTTP POST
          with a JSON body.
        </p>
        <form onSubmit={handleCreate}>
          <div className="grid sm:grid-cols-2 gap-3.5">
            <div>
              <label className="label">Integration Type</label>
              <select className="input" value={form.integration_type} onChange={update('integration_type')}>
                {TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Connection Name</label>
              <input className="input" value={form.name} onChange={update('name')} required placeholder="e.g. Jira Project Sync" />
            </div>
          </div>
          <label className="label">Endpoint URL</label>
          <input className="input" value={form.endpoint_url} onChange={update('endpoint_url')} required placeholder="https://hooks.example.com/..." />
          <div className="grid sm:grid-cols-2 gap-3.5">
            <div>
              <label className="label">Auth Header Name (optional)</label>
              <input className="input" value={form.auth_header_name} onChange={update('auth_header_name')} placeholder="Authorization" />
            </div>
            <div>
              <label className="label">Auth Header Value (optional)</label>
              <input className="input" type="password" value={form.auth_header_value} onChange={update('auth_header_value')} placeholder="Bearer …" />
            </div>
          </div>
          <div className="mt-4">
            <button type="submit" disabled={submitting} className="btn">
              {submitting && <span className="spinner" />}
              {submitting ? 'Creating…' : 'Add Connection'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h3 className="mb-3">Connections</h3>
        {loading ? (
          <div className="text-ink-faint text-sm py-6 text-center"><span className="spinner" /> Loading…</div>
        ) : (
          <div className="overflow-x-auto">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Type</th>
                  <th>Endpoint</th>
                  <th>Last Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((it) => (
                  <tr key={it.id}>
                    <td><strong>{it.name}</strong></td>
                    <td>{TYPES.find((t) => t.value === it.integration_type)?.label || it.integration_type}</td>
                    <td className="text-ink-faint text-xs font-mono truncate max-w-[220px]">{it.endpoint_url}</td>
                    <td>
                      {it.last_status ? (
                        <span className={`badge ${it.last_status === 'ok' ? '' : 'badge-red'}`}>{it.last_status}</span>
                      ) : (
                        <span className="text-ink-faint text-xs">never tested</span>
                      )}
                    </td>
                    <td>
                      <div className="flex gap-2 justify-end flex-wrap">
                        <button className="btn-ghost btn-sm" disabled={testingId === it.id} onClick={() => handleTest(it.id)}>
                          {testingId === it.id ? 'Testing…' : 'Test'}
                        </button>
                        <button className="btn-secondary btn-sm" onClick={() => handleDelete(it.id)}>Remove</button>
                      </div>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr><td colSpan={5}><div className="text-ink-faint text-sm py-6 text-center">No integrations connected yet.</div></td></tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  )
}

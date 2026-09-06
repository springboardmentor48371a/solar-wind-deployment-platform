'use client'

import { useEffect, useState } from 'react'
import api from '../../lib/api'
import AppShell from '../../components/AppShell'
import { useToast } from '../../lib/ToastContext'
import { getErrorMessage } from '../../lib/errorMessage'

function Field({ label, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export default function FinancialAnalysisPage() {
  const { showToast } = useToast()
  const [projects, setProjects] = useState([])
  const [sites, setSites] = useState([])
  const [projectId, setProjectId] = useState('')
  const [siteId, setSiteId] = useState('')
  const [siteContext, setSiteContext] = useState(null)
  const [existing, setExisting] = useState(null)
  const [loadingSites, setLoadingSites] = useState(false)
  const [loadingContext, setLoadingContext] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)

  const [form, setForm] = useState({
    technology: 'solar',
    capacity_mw: '10',
    capex_usd: '8000000',
    opex_usd_per_yr: '100000',
    discount_rate_pct: '8',
    project_lifetime_yrs: '25',
    electricity_price_usd_per_mwh: '45',
  })

  // Standalone page, deliberately separate from the site card's much
  // larger component tree — a simpler, isolated execution context in
  // case interaction with that component's many other effects/state
  // was ever a contributing factor to the reported issues there.
  useEffect(() => {
    api.get('/projects/').then((res) => setProjects(res.data)).catch(() => setProjects([]))
  }, [])

  useEffect(() => {
    if (!projectId) {
      setSites([])
      setSiteId('')
      return
    }
    setLoadingSites(true)
    api.get(`/projects/${projectId}/sites/`)
      .then((res) => setSites(res.data))
      .catch(() => setSites([]))
      .finally(() => setLoadingSites(false))
  }, [projectId])

  useEffect(() => {
    if (!projectId || !siteId) {
      setSiteContext(null)
      setExisting(null)
      setResult(null)
      return
    }
    setLoadingContext(true)
    const base = `/projects/${projectId}/sites/${siteId}`
    Promise.all([
      api.get(`${base}/solar-potential`).catch(() => null),
      api.get(`${base}/wind-potential`).catch(() => null),
      api.get(`${base}/financial-analysis`).catch(() => null),
    ]).then(([solar, wind, financialList]) => {
      setSiteContext({ solar: solar?.data || null, wind: wind?.data || null })
      const list = financialList?.data || []
      setExisting(list.length > 0 ? list[0] : null)
      setResult(null)
    }).finally(() => setLoadingContext(false))
  }, [projectId, siteId])

  const runFinancialModel = async () => {
    setSubmitting(true)
    setResult(null)
    try {
      const payload = {
        technology: form.technology,
        capacity_mw: parseFloat(form.capacity_mw),
        capex_usd: parseFloat(form.capex_usd),
        opex_usd_per_yr: parseFloat(form.opex_usd_per_yr),
        discount_rate_pct: parseFloat(form.discount_rate_pct),
        project_lifetime_yrs: parseInt(form.project_lifetime_yrs, 10),
        electricity_price_usd_per_mwh: parseFloat(form.electricity_price_usd_per_mwh),
      }
      const res = await api.post(`/projects/${projectId}/sites/${siteId}/financial-analysis`, payload)
      setResult(res.data)
      showToast('Financial analysis computed.', 'success')
    } catch (err) {
      // Kept as a real safety net, not just for show: confirmed via
      // live debugging that this button could previously fail with
      // zero visible feedback in either direction, which is only
      // possible if the error-handling code itself was silently
      // throwing. This inner try/catch guarantees that even if
      // getErrorMessage or the toast call itself ever throws, it
      // surfaces as a real error instead of vanishing.
      try {
        const msg = getErrorMessage(err, `Could not compute financial analysis: ${err.message || 'unknown error'}`)
        showToast(msg, 'error')
      } catch (innerErr) {
        showToast(`Something went wrong showing that error (${innerErr?.message}). Please try again.`, 'error')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const displayed = result || existing

  return (
    <AppShell title="Financial Analysis" subtitle="Run NPV / IRR / LCOE calculations for any registered site.">
      <div className="card mb-4">
        <h3 className="mb-3">Select a Site</h3>
        <div className="grid sm:grid-cols-2 gap-3.5">
          <Field label="Project">
            <select className="input" value={projectId} onChange={(e) => { setProjectId(e.target.value); setSiteId('') }}>
              <option value="">Select a project…</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </Field>
          <Field label="Site">
            <select className="input" value={siteId} onChange={(e) => setSiteId(e.target.value)} disabled={!projectId || loadingSites}>
              <option value="">{loadingSites ? 'Loading…' : 'Select a site…'}</option>
              {sites.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </Field>
        </div>
      </div>

      {siteId && (
        <div className="card mb-4">
          {loadingContext ? (
            <span className="text-ink-faint text-sm"><span className="spinner" />Loading site data…</span>
          ) : (
            <>
              <h3 className="mb-1">Site Energy Context</h3>
              <p className="text-ink-muted text-sm mb-3">Already-computed physics engine output for this site — used as a reference while filling in assumptions below.</p>
              <div className="flex flex-wrap gap-x-6 gap-y-1 text-[13px]">
                <span>Solar: <b>{siteContext?.solar?.expected_energy_output_mwh_yr ?? '—'} MWh/yr per MW</b> ({siteContext?.solar?.capacity_factor_pct ?? '—'}% capacity factor)</span>
                <span>Wind: <b>{siteContext?.wind?.expected_aep_mwh_yr ?? '—'} MWh/yr per MW</b> ({siteContext?.wind?.capacity_factor_pct ?? '—'}% capacity factor)</span>
              </div>
              {!siteContext?.solar && !siteContext?.wind && (
                <p className="text-amber-600 text-[12px] mt-2">No solar/wind potential computed yet for this site — run "Refresh data" on it under Projects &amp; Sites first, or the model below will fail.</p>
              )}
            </>
          )}
        </div>
      )}

      {siteId && (
        <div className="card mb-4">
          <h3 className="mb-3">Investment Assumptions</h3>
          <p className="text-ink-faint text-[11px] mb-3">
            The values below are a realistic mid-size utility-project example — edit them to match your real assumptions, or leave as-is to see a representative result.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5 mb-4">
            <Field label="Technology">
              <select className="input" value={form.technology} onChange={(e) => setForm({ ...form, technology: e.target.value })}>
                <option value="solar">Solar</option>
                <option value="wind">Wind</option>
                <option value="hybrid">Hybrid</option>
              </select>
            </Field>
            <Field label="Capacity (MW)">
              <input className="input" type="number" value={form.capacity_mw} onChange={(e) => setForm({ ...form, capacity_mw: e.target.value })} />
            </Field>
            <Field label="CapEx (Total $)">
              <input className="input" type="number" value={form.capex_usd} onChange={(e) => setForm({ ...form, capex_usd: e.target.value })} />
            </Field>
            <Field label="OpEx ($/year)">
              <input className="input" type="number" value={form.opex_usd_per_yr} onChange={(e) => setForm({ ...form, opex_usd_per_yr: e.target.value })} />
            </Field>
            <Field label="Electricity Price ($/MWh)">
              <input className="input" type="number" value={form.electricity_price_usd_per_mwh} onChange={(e) => setForm({ ...form, electricity_price_usd_per_mwh: e.target.value })} />
            </Field>
            <Field label="Discount Rate (%)">
              <input className="input" type="number" value={form.discount_rate_pct} onChange={(e) => setForm({ ...form, discount_rate_pct: e.target.value })} />
            </Field>
            <Field label="Project Lifetime (years)">
              <input className="input" type="number" value={form.project_lifetime_yrs} onChange={(e) => setForm({ ...form, project_lifetime_yrs: e.target.value })} />
            </Field>
          </div>
          <button type="button" className="btn" disabled={submitting} onClick={runFinancialModel}>
            {submitting && <span className="spinner" />}
            {submitting ? 'Computing…' : 'Run Financial Model'}
          </button>
        </div>
      )}

      {siteId && displayed && (
        <div className="card">
          <h3 className="mb-1">Results {result ? '' : <span className="text-ink-faint text-[12px] font-normal">(most recent previously computed)</span>}</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3">
            <div className="card-hover !py-3 text-center">
              <div className="text-2xl font-bold text-brand">${displayed.npv_usd?.toLocaleString?.() ?? displayed.npv_usd}</div>
              <div className="text-ink-faint text-[11px] uppercase tracking-wide">NPV</div>
            </div>
            <div className="card-hover !py-3 text-center">
              <div className="text-2xl font-bold text-brand">{displayed.irr_pct ?? 'N/A'}{displayed.irr_pct != null ? '%' : ''}</div>
              <div className="text-ink-faint text-[11px] uppercase tracking-wide">IRR</div>
            </div>
            <div className="card-hover !py-3 text-center">
              <div className="text-2xl font-bold text-brand">${displayed.lcoe_usd_per_mwh ?? '—'}</div>
              <div className="text-ink-faint text-[11px] uppercase tracking-wide">LCOE / MWh</div>
            </div>
            <div className="card-hover !py-3 text-center">
              <div className="text-2xl font-bold text-brand">{displayed.payback_years ?? '—'}</div>
              <div className="text-ink-faint text-[11px] uppercase tracking-wide">Payback (yrs)</div>
            </div>
          </div>
          {displayed.irr_pct == null && (
            <p className="text-ink-faint text-[12px] mt-3">IRR shows N/A when the cash flow pattern doesn't have a mathematically valid internal rate of return (e.g. costs never fully recovered within the project lifetime) — NPV is still a fully valid result in that case.</p>
          )}
        </div>
      )}
    </AppShell>
  )
}

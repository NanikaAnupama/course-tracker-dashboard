import { useEffect, useState } from 'react'
import { fetchJson } from '../api'
import { STATUS_COLORS } from '../theme'
import { fmtPct } from '../utils'

// `reloadKey` lets a long-lived caller (the sidebar) re-fetch after a failure —
// pages remount on navigation, but App-level fetches otherwise run only once.
export function useApi(path, reloadKey = 0) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  useEffect(() => {
    let alive = true
    setState({ data: null, error: null, loading: true })
    fetchJson(path)
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState({ data: null, error, loading: false }))
    return () => { alive = false }
  }, [path, reloadKey])
  return state
}

export function Loading({ label = 'Loading data…' }) {
  return (
    <div className="state">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  )
}

export function ErrorState({ error }) {
  return (
    <div className="state">
      <h3>Could not load data</h3>
      <p>{String(error?.message || error)}. The SharePoint link may be blocked — try Refresh in a minute.</p>
    </div>
  )
}

export function Card({ title, sub, right, children, className = '' }) {
  return (
    <div className={`card ${className}`}>
      {(title || right) && (
        <div className="card-head">
          <div>
            {title && <h3 className="card-title">{title}</h3>}
            {sub && <p className="card-sub">{sub}</p>}
          </div>
          {right}
        </div>
      )}
      {children}
    </div>
  )
}

export function KpiCard({ icon, tint, label, value, suffix, note, dir }) {
  return (
    <div className="kpi">
      <div className="kpi-icon" style={{ background: `${tint}18`, color: tint }}>{icon}</div>
      <div>
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">
          {value}
          {suffix && <small> {suffix}</small>}
        </div>
        {note && <div className={`kpi-note ${dir || ''}`}>{note}</div>}
      </div>
    </div>
  )
}

export function SubTabs({ tabs, active, onChange }) {
  return (
    <div className="subtabs" role="tablist">
      {tabs.map((t) => (
        <button
          key={t}
          role="tab"
          aria-selected={active === t}
          className={`subtab ${active === t ? 'active' : ''}`}
          onClick={() => onChange(t)}
        >
          {t}
        </button>
      ))}
    </div>
  )
}

// Recharts custom tooltip — list of {name, value, color} rows with optional total.
export function ChartTip({ active, payload, label, total, unit = '' }) {
  if (!active || !payload || !payload.length) return null
  const rows = payload.filter((p) => p.value !== 0 || payload.length === 1)
  const sum = payload.reduce((a, p) => a + (Number(p.value) || 0), 0)
  return (
    <div className="tip">
      <div className="tip-title">{label}</div>
      {rows.map((p) => (
        <div className="tip-row" key={p.dataKey || p.name}>
          <span className="dot" style={{ background: p.color || p.fill }} />
          {p.name}
          <span className="v">{Number(p.value).toLocaleString()}{unit}</span>
        </div>
      ))}
      {total && payload.length > 1 && (
        <div className="tip-foot"><span>Total</span><span>{sum.toLocaleString()}{unit}</span></div>
      )}
    </div>
  )
}

export function PctBar({ pct, color = 'var(--accent)' }) {
  const clamped = Math.max(0, Math.min(100, pct))
  return (
    <div className="pbar">
      <div className="pbar-track">
        <div className="pbar-fill" style={{ width: `${clamped}%`, background: color }} />
      </div>
      <span className="pbar-num">{fmtPct(pct)}</span>
    </div>
  )
}

export function StatusChip({ status, colors = STATUS_COLORS }) {
  const c = colors[status] || '#64748b'
  return (
    <span className="chip" style={{ background: `${c}16`, color: c }}>
      <span className="dot" style={{ background: c }} />
      {status}
    </span>
  )
}

export function Legend({ items }) {
  return (
    <div className="legend-row">
      {items.map(({ name, color }) => (
        <span className="legend-item" key={name}>
          <span className="dot" style={{ background: color }} />
          {name}
        </span>
      ))}
    </div>
  )
}

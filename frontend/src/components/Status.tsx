'use client'
import { useEffect, useState } from 'react'
import { useApp } from './AppProvider'

type St = { backend: string; model: { name: string; ready: boolean }; documents: number; lastUpdate: string | null; dataLabel: string }
const EPS = [['GET', '/api/status'], ['GET', '/api/profile'], ['GET', '/api/readings?days=14'], ['GET', '/api/alerts'], ['POST', '/api/assistant/ask']]

const fmtDate = (iso?: string | null) => {
  if (!iso) return '…'
  const d = new Date(iso)
  const day = d.getUTCDate()
  const month = d.toLocaleString('en-GB', { month: 'short', timeZone: 'UTC' })
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  return `${day} ${month} ${d.getUTCFullYear()}, ${hh}:${mm} UTC`
}

export default function Status() {
  const { off } = useApp()
  const [s, setS] = useState<St | null>(null), [err, setErr] = useState(false)
  useEffect(() => {
    fetch('/api/status', { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then(setS)
      .catch(() => setErr(true))
  }, [])

  const up = s?.backend === 'running'
  const cards: [string, string, string][] = [
    ['Backend', s ? (up ? 'Running' : s.backend === 'degraded' ? 'Degraded' : 'Unreachable') : err ? 'Unreachable' : 'Checking…', up ? 'ok' : s || err ? 'watch' : 'mut'],
    ['Local model', s ? (s.model?.ready ? `Ready (${s.model.name})` : 'Not ready (offline)') : '…', s?.model?.ready ? 'ok' : 'mut'],
    ['Documents indexed', s ? `${s.documents} sample entries` : '…', 'ok'],
    ['Last data update', s ? fmtDate(s.lastUpdate) : '…', 'acc'],
    ['Data label', s?.dataLabel ?? 'SIMULATED', 'sim'],
    ['Network', off ? 'Offline: all features local' : 'Online: local features unaffected', off ? 'ok' : 'acc'],
  ]
  return (
    <section className="view on" id="status">
      <h1>System status</h1>
      <p className="sub">Everything the astronaut needs runs on this device.</p>
      <div className="sg" id="sg" style={{ marginBottom: 16 }}>
        {cards.map(([a, b, c]) => <div className="card" key={a}><p>{a}</p><h3 style={{ color: `var(--${c})` }}>{b}</h3></div>)}
      </div>
      <div className="card">
        <h2 style={{ fontSize: 18, marginBottom: 6 }}>API contract v1</h2>
        <div id="eps">{EPS.map(([m, p]) => <div className="ep" key={p}><b style={{ width: 46 }}>{m}</b><code>{p}</code></div>)}</div>
        <p className="note">These routes proxy to the FastAPI backend. When the backend is unreachable, they serve an explicit offline state or labelled simulated data so the UI stays honest.</p>
      </div>
    </section>
  )
}
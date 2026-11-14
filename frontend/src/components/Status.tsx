'use client'
import { useEffect, useState } from 'react'
import { useApp } from './AppProvider'

type St = { backend: string; model: { name: string; ready: boolean }; documents: number; lastUpdate: string; dataLabel: string }
const EPS = [['GET', '/api/status'], ['GET', '/api/profile'], ['GET', '/api/readings?days=14'], ['GET', '/api/alerts'], ['POST', '/api/assistant/ask']]

export default function Status() {
  const { off } = useApp()
  const [s, setS] = useState<St | null>(null), [err, setErr] = useState(false)
  useEffect(() => { fetch('/api/status').then((r) => r.json()).then(setS).catch(() => setErr(true)) }, [])
  const cards: [string, string, string][] = [
    ['Backend', s ? 'Running' : err ? 'Unreachable' : 'Checking…', s ? 'ok' : err ? 'watch' : 'mut'],
    ['Local model', s ? (s.model.ready ? `Ready (${s.model.name})` : 'Not ready') : '…', s?.model.ready ? 'ok' : 'mut'],
    ['Documents indexed', s ? `${s.documents} sample entries` : '…', 'ok'],
    ['Last data update', s ? '14 Nov 2026, 08:00 UTC' : '…', 'acc'],
    ['Data label', s?.dataLabel ?? 'SIMULATED', 'sim'],
    ['Network', off ? 'Offline: all features local' : 'Online: local features unaffected', off ? 'ok' : 'acc'],
  ]
  return (
    <section className="view on" id="status">
      <h1>System status</h1><p className="sub">Everything the astronaut needs runs on this device.</p>
      <div className="sg" id="sg" style={{ marginBottom: 16 }}>{cards.map(([a, b, c]) => <div className="card" key={a}><p>{a}</p><h3 style={{ color: `var(--${c})` }}>{b}</h3></div>)}</div>
      <div className="card"><h2 style={{ fontSize: 18, marginBottom: 6 }}>API contract v1</h2>
        <div id="eps">{EPS.map(([m, p]) => <div className="ep" key={p}><b style={{ width: 46 }}>{m}</b><code>{p}</code></div>)}</div>
        <p className="note">These routes are implemented as Next.js route handlers returning simulated data. Swap their bodies for the FastAPI backend when it is ready.</p></div>
    </section>
  )
}

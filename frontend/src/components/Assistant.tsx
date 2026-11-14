'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { D, KB, answer, buildAlerts, type Answer } from '@/lib/data'
import { useApp } from './AppProvider'
import { ARR, Ico, cv } from './ui'

type Msg = { id: number; role: 'u' | 'a'; text?: string; cites?: number[]; typing?: boolean; offline?: boolean; known?: boolean }
let uid = 0

export default function Assistant() {
  const { off, ver, pendingQ, setPendingQ } = useApp(); void ver
  const [msgs, setMsgs] = useState<Msg[]>([{ id: uid++, role: 'a', text: 'Hi! Ask me why an alert appeared. I answer only from the local library and show my sources.' }])
  const [q, setQ] = useState(''), [src, setSrc] = useState<number | null>(null)
  const log = useRef<HTMLDivElement>(null), closeBtn = useRef<HTMLButtonElement>(null)

  const ask = useCallback(async (text: string) => {
    if (!text.trim()) return
    const tid = uid++, reading = { hr: D[29].hr, sleep: D[29].sleep }
    setMsgs((m) => [...m, { id: uid++, role: 'u', text }, { id: tid, role: 'a', typing: true }])
    let a: Answer | null = null
    if (!off) {
      try { const r = await fetch('/api/assistant/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: text, reading }) }); if (r.ok) a = await r.json() } catch {}
    }
    a = a ?? answer(text, reading)
    const res = a, wait = new Promise((r) => setTimeout(r, 900))
    await wait
    setMsgs((m) => m.map((x) => (x.id === tid ? { id: tid, role: 'a', text: res.text, cites: res.cites, known: res.known, offline: off } : x)))
  }, [off])

  useEffect(() => { if (pendingQ) { ask(pendingQ); setPendingQ(null) } }, [pendingQ, ask, setPendingQ])
  useEffect(() => { log.current?.scrollTo({ top: 1e9 }) }, [msgs])
  useEffect(() => {
    if (src === null) return
    closeBtn.current?.focus()
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') setSrc(null) }
    addEventListener('keydown', k); return () => removeEventListener('keydown', k)
  }, [src])

  const send = () => { ask(q); setQ('') }
  return (
    <section className="view on" id="assistant">
      <h1>AI assistant</h1><p className="sub">Answers come from the local scientific library and cite their sources.</p>
      <div className="card">
        <div className="pill" id="mode" style={{ ...cv('var(--ok)'), marginBottom: 12 }}>{off ? 'Offline: answered from local library' : 'Demo response mode'}</div>
        <div className="chat" id="chat" ref={log} role="log" aria-live="polite" aria-label="Conversation">
          {msgs.map((m) => (
            <div key={m.id} className={'b ' + m.role}>
              {m.typing ? <span className="dots" aria-label="Assistant is typing"><span /><span /><span /></span> : <>
                {m.text}
                {m.cites?.map((i) => <button key={i} className="cite" aria-label={`Open source ${i + 1}`} onClick={() => setSrc(i)}>{i + 1}</button>)}
                {m.known && <div className="note">{m.offline ? 'Answered offline from the local library. ' : ''}Demo response. Decision support only.</div>}
              </>}
            </div>
          ))}
        </div>
        <div className="chips" id="chips">{buildAlerts().map((a) => <button key={a.id} onClick={() => ask(a.q)}>{a.q}</button>)}</div>
        <div className="inp">
          <input id="q" placeholder="Ask about an alert or an indicator" aria-label="Ask the assistant" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') send() }} />
          <button className="btn" id="send" onClick={send}>Ask<Ico d={ARR} cls="ar" /></button>
        </div>
        <p className="note">Decision support only. This is not a medical diagnosis. Demo answers are scripted; Cesar’s retrieval pipeline will replace them.</p>
      </div>
      <aside className={'drawer' + (src !== null ? ' on' : '')} id="dr" aria-label="Source" aria-hidden={src === null}>
        <button className="btn o" id="drx" ref={closeBtn} style={{ float: 'right' }} tabIndex={src === null ? -1 : 0} onClick={() => setSrc(null)}>Close</button>
        {src !== null && <div id="drc"><h2 style={{ fontSize: 18, margin: '36px 0 8px' }}>{KB[src].t}</h2><p className="pill" style={cv('var(--acc)')}>{KB[src].s}</p>
          <p style={{ marginTop: 14, color: 'var(--mut)' }}>Placeholder excerpt. Curated papers from Ammara’s list will appear here once Cesar indexes the library.</p></div>}
      </aside>
    </section>
  )
}

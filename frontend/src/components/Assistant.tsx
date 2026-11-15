'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import { D, KB, answer, buildAlerts, type Answer, type Citation } from '@/lib/data'
import { useApp } from './AppProvider'
import { ARR, Ico, cv } from './ui'

type Msg = {
  id: number
  role: 'u' | 'a'
  text?: string
  cites?: number[]
  citations?: Citation[]
  mode?: string
  typing?: boolean
  offline?: boolean
  known?: boolean
}
type Chip = { q: string; alertId?: string }
type ApiAnswer = Answer & { mode?: string; suggestions?: string[] }

let uid = 0

const mockCitation = (i: number): Citation => ({
  title: KB[i]?.t ?? 'Unknown source',
  source: KB[i]?.s ?? '',
  url: '',
  excerpt: 'Placeholder excerpt. Curated papers from Ammara’s list will appear here once Cesar indexes the library.',
})

export default function Assistant() {
  const { off, ver, pendingQ, setPendingQ, pendingAlertId, setPendingAlertId } = useApp(); void ver
  const [msgs, setMsgs] = useState<Msg[]>([{ id: uid++, role: 'a', text: 'Hi! Ask me why an alert appeared. I answer only from the local library and show my sources.' }])
  const [q, setQ] = useState('')
  const [src, setSrc] = useState<Citation | null>(null)
  const [lastMode, setLastMode] = useState<string | null>(null)
  const [chips, setChips] = useState<Chip[]>(() => buildAlerts().map((a) => ({ q: a.q, alertId: a.id })))
  const log = useRef<HTMLDivElement>(null), closeBtn = useRef<HTMLButtonElement>(null)
  const msgsRef = useRef(msgs)
  msgsRef.current = msgs
  const handledPendingQ = useRef<string | null>(null)

  const ask = useCallback(async (text: string, alertId?: string) => {
    if (!text.trim()) return
    const tid = uid++, reading = { hr: D[29].hr, sleep: D[29].sleep }
    const history = msgsRef.current
      .filter((m) => !m.typing && m.text && m.id > 0)
      .slice(-6)
      .map((m) => ({ role: m.role === 'u' ? 'user' : 'assistant', content: m.text }))
    setMsgs((m) => [...m, { id: uid++, role: 'u', text }, { id: tid, role: 'a', typing: true }])
    let a: ApiAnswer | null = null
    if (!off) {
      try {
        const r = await fetch('/api/assistant/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: text, alert_id: alertId, reading, history }),
        })
        if (r.ok) a = await r.json()
      } catch {}
    }
    const res: ApiAnswer = a ?? answer(text, reading)
    if (res.mode) setLastMode(res.mode)
    if (Array.isArray(res.suggestions) && res.suggestions.length > 0) setChips(res.suggestions.map((s) => ({ q: s })))
    setMsgs((m) => m.map((x) => (x.id === tid
      ? { id: tid, role: 'a', text: res.text, cites: res.cites, citations: res.citations, mode: res.mode, known: res.known, offline: off }
      : x)))
  }, [off])

  useEffect(() => {
    // Guard against StrictMode / re-renders running this effect twice for the same pendingQ
    if (!pendingQ) { handledPendingQ.current = null; return }
    if (handledPendingQ.current === pendingQ) return
    handledPendingQ.current = pendingQ
    const alertId = pendingAlertId ?? undefined
    setPendingQ(null)
    setPendingAlertId(null)
    ask(pendingQ, alertId)
  }, [pendingQ, pendingAlertId, ask, setPendingQ, setPendingAlertId])
  useEffect(() => { log.current?.scrollTo({ top: 1e9 }) }, [msgs])
  useEffect(() => {
    if (src === null) return
    closeBtn.current?.focus()
    const k = (e: KeyboardEvent) => { if (e.key === 'Escape') setSrc(null) }
    addEventListener('keydown', k); return () => removeEventListener('keydown', k)
  }, [src])

  const openSource = (m: Msg, i: number) => {
    setSrc(m.citations?.[i] ?? mockCitation(i))
  }

  const send = () => { ask(q); setQ('') }
  const modeLabel = off
    ? 'Offline: answered from local library'
    : lastMode === 'llm'
    ? 'LLM + RAG (S1–S9)'
    : lastMode === 'retrieval_only'
    ? 'Retrieval-only RAG (S1–S9)'
    : 'Demo response mode'

  return (
    <section className="view on" id="assistant">
      <h1>AI assistant</h1>
      <p className="sub">Answers come from the local scientific library and cite their sources.</p>
      <div className="card">
        <div className="pill" id="mode" style={{ ...cv('var(--ok)'), marginBottom: 12 }}>{modeLabel}</div>
        <div className="chat" id="chat" ref={log} role="log" aria-live="polite" aria-label="Conversation">
          {msgs.map((m) => (
            <div key={m.id} className={'b ' + m.role}>
              {m.typing ? (
                <span className="dots" aria-label="Assistant is typing"><span /><span /><span /></span>
              ) : (
                <>
                  {m.text}
                  {m.cites?.map((i) => (
                    <button
                      key={i}
                      className="cite"
                      aria-label={`Open source ${i + 1}`}
                      onClick={() => openSource(m, i)}
                    >
                      {i + 1}
                    </button>
                  ))}
                  {m.known && (
                    <div className="note">
                      {m.citations?.length
                        ? `${m.mode === 'llm' ? 'Generated by LLM grounded in' : 'Retrieved from'} ${m.citations.length} source${m.citations.length > 1 ? 's' : ''} of the scientific library. `
                        : m.offline
                          ? 'Answered offline from the local library. '
                          : 'Demo response. '}
                      Decision support only.
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
        <div className="chips" id="chips">
          {chips.map((c) => (
            <button key={c.q} onClick={() => ask(c.q, c.alertId)}>{c.q}</button>
          ))}
        </div>
        <div className="inp">
          <input
            id="q"
            placeholder="Ask about an alert or an indicator"
            aria-label="Ask the assistant"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') send() }}
          />
          <button className="btn" id="send" onClick={send}>Ask<Ico d={ARR} cls="ar" /></button>
        </div>
        <p className="note">Decision support only. This is not a medical diagnosis. Grounded in Ammara’s curated scientific sources (S1–S9).</p>
      </div>
      <aside className={'drawer' + (src !== null ? ' on' : '')} id="dr" aria-label="Source" aria-hidden={src === null}>
        <button className="btn o" id="drx" ref={closeBtn} style={{ float: 'right' }} tabIndex={src === null ? -1 : 0} onClick={() => setSrc(null)}>Close</button>
        {src !== null && (
          <div id="drc">
            <h2 style={{ fontSize: 18, margin: '36px 0 8px' }}>{src.title}</h2>
            {src.source && <p className="pill" style={cv('var(--acc)')}>{src.source}</p>}
            {src.excerpt && <p style={{ marginTop: 14, color: 'var(--mut)' }}>{src.excerpt}</p>}
            {src.url && (
              <p style={{ marginTop: 14 }}>
                <a href={src.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--acc)' }}>
                  Open source ↗
                </a>
              </p>
            )}
          </div>
        )}
      </aside>
    </section>
  )
}

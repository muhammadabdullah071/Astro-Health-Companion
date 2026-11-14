'use client'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { buildAlerts, cap } from '@/lib/data'
import { useApp } from './AppProvider'
import { ARR, CHAT, Ico, Tilt, cv } from './ui'

export default function Alerts() {
  const { ver, setPendingQ, toast } = useApp(); void ver
  const router = useRouter(), [f, setF] = useState<'all' | 'watch' | 'notice'>('all')
  const list = buildAlerts().filter((a) => f === 'all' || a.s === f)
  return (
    <section className="view on" id="alerts">
      <h1>Health alerts</h1><p className="sub">Each alert names the rule that fired, so nothing is a black box.</p>
      <div className="tabs" id="af" role="group" aria-label="Filter alerts">{(['all', 'watch', 'notice'] as const).map((k) => <button key={k} className={k === f ? 'on' : ''} aria-pressed={k === f} onClick={() => setF(k)}>{cap(k)}</button>)}</div>
      <div id="alist">
        {list.length ? list.map((a) => (
          <Tilt key={a.id} className="card al" style={cv(`var(--${a.s})`)}>
            <span className="pill" style={cv(`var(--${a.s})`)}>{cap(a.s)}</span>
            <div><h3>{a.n}</h3><p>{a.m}. 14 Nov 2026, 08:00 UTC.</p><p className="note rule">Rule: {a.rule}</p></div>
            <button className="btn" onClick={() => { setPendingQ(a.q); toast('Question sent to the assistant'); router.push('/assistant') }}><Ico d={CHAT} cls="bi" />Ask the assistant<Ico d={ARR} cls="ar" /></button>
          </Tilt>
        )) : <p className="sub">No alerts match this filter.</p>}
      </div>
    </section>
  )
}

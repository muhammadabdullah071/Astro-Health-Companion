'use client'
import Link from 'next/link'
import { useRef, useState, type PointerEvent } from 'react'
import { D, KEYS, M, buildAlerts, cap, col, fd, stat, summary, type Key } from '@/lib/data'
import { useApp } from './AppProvider'
import { ARR, BELL, CountUp, Ecg, Ico, Tilt, cv } from './ui'
import { useEffect } from 'react'

function Chart() {
  const [ck, setCk] = useState<Key>('hr'), [cr, setCr] = useState(14)
  const box = useRef<HTMLDivElement>(null), [tip, setTip] = useState<{ x: number; y: number; t: string } | null>(null)
  const m = M[ck], d = D.slice(-cr), W = 720, H = 260, L = 44, R = 12, T = 14, B = 26, v = d.map((r) => r[ck])
  let mn = Math.min(m.lo, ...v) - (ck === 'hr' ? 4 : 0.3), mx = Math.max(m.hi, ...v) + (ck === 'hr' ? 4 : 0.3)
  if (ck === 'spo2') mx = 100.5
  const X = (i: number) => L + (i * (W - L - R)) / (d.length - 1), Y = (y: number) => T + ((mx - y) / (mx - mn)) * (H - T - B)
  const mv = (e: PointerEvent<SVGRectElement>) => {
    const b = e.currentTarget.getBoundingClientRect(), cb = box.current!.getBoundingClientRect()
    const i = Math.max(0, Math.min(d.length - 1, Math.round(((e.clientX - b.left) / b.width) * (d.length - 1))))
    setTip({ x: b.left - cb.left + (i / (d.length - 1)) * b.width, y: (Y(v[i]) / H) * b.height, t: `${fd(d[i].t)}: ${v[i].toFixed(m.d)} ${m.u}` })
  }
  return (
    <div className="card">
      <h2 style={{ fontSize: 18, marginBottom: 12 }}>Trends</h2>
      <div className="tabs" role="group" aria-label="Indicator">{KEYS.map((k) => <button key={k} className={k === ck ? 'on' : ''} aria-pressed={k === ck} onClick={() => setCk(k)}>{M[k].l}</button>)}</div>
      <div className="tabs" role="group" aria-label="Range">{[7, 14, 30].map((n) => <button key={n} className={n === cr ? 'on' : ''} aria-pressed={n === cr} onClick={() => setCr(n)}>{n} days</button>)}</div>
      <div className="cw" ref={box}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${m.l} over the last ${cr} days`}>
          <rect x={L} y={Y(m.hi)} width={W - L - R} height={Y(m.lo) - Y(m.hi)} fill="var(--ok)" opacity=".08" />
          {[0, 1, 2, 3, 4].map((i) => { const y = mn + ((mx - mn) * i) / 4; return <g key={i}><line x1={L} x2={W - R} y1={Y(y)} y2={Y(y)} stroke="var(--line)" /><text x={L - 8} y={Y(y) + 4} textAnchor="end" fill="var(--mut)" fontSize="11">{y.toFixed(m.d)}</text></g> })}
          <line x1={L} x2={W - R} y1={Y(m.b)} y2={Y(m.b)} stroke="var(--mut)" strokeDasharray="5 4" />
          <text x={W - R} y={Y(m.b) - 6} textAnchor="end" fill="var(--mut)" fontSize="11">your baseline</text>
          <polyline key={ck + cr} className="ln" pathLength={1} fill="none" stroke="var(--ln)" strokeWidth="2.5" strokeLinejoin="round" points={v.map((y, i) => `${X(i)},${Y(y)}`).join(' ')} />
          {v.map((y, i) => stat(ck, y)[0] !== 'ok' && <circle key={i} cx={X(i)} cy={Y(y)} r="5" fill="var(--sim)" />)}
          <text x={L} y={H - 6} fill="var(--mut)" fontSize="11">{fd(d[0].t)}</text>
          <text x={W - R} y={H - 6} textAnchor="end" fill="var(--mut)" fontSize="11">{fd(d[d.length - 1].t)}</text>
          <rect x={L} y="0" width={W - L - R} height={H} fill="transparent" onPointerMove={mv} onPointerLeave={() => setTip(null)} />
        </svg>
        <div className="tip" style={{ left: tip?.x, top: tip?.y, opacity: tip ? 1 : 0 }}>{tip?.t}</div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { ver } = useApp(); void ver
  const x = D[D.length - 1], al = buildAlerts(), hr = Math.round(x.hr), warn = x.hr > 75
  const [loading, setLoading] = useState(true)
  useEffect(() => { const t = setTimeout(() => setLoading(false), 500); return () => clearTimeout(t) }, [])
  return (
    <section className="view on" id="dashboard">
      <h1>Good morning, Commander</h1>
      <p className="sub">Mission day 142. Last update 14 Nov 2026, 08:00 UTC. All readings are simulated.</p>
      <Tilt className="card hero" k={6}>
        <div><div className="lb" style={{ color: 'var(--mut)' }}>Resting heart rate</div><div className="big"><span id="hrBig">{hr}</span> <small>bpm</small></div>
          <span className="pill" id="hrPill" style={{ ...cv(warn ? 'var(--watch)' : 'var(--ok)'), marginTop: 10 }}>{warn ? `Watch: ${hr - 62} bpm above baseline` : 'In range'}</span></div>
        <Ecg id="ecg" hr={hr} />
      </Tilt>
      <div className="grid g4" id="cards" style={{ marginBottom: 16 }}>
        {KEYS.map((k) => {
          const v = x[k], [s, txt] = stat(k, v), m = M[k], pts = D.slice(-14).map((r) => r[k]), mn = Math.min(...pts), mxx = Math.max(...pts)
          return (
            <Tilt key={k} className={'card m' + (loading ? ' skel' : '')}>
              <div className="lb">{m.l}</div>
              <div className="v num"><CountUp v={v} d={m.d} /> <small>{m.u}</small></div>
              <div className="st" style={{ color: col(s) }}>{txt}</div>
              <svg viewBox="0 0 120 36" preserveAspectRatio="none" aria-hidden="true"><polyline fill="none" stroke={col(s)} strokeWidth="2" strokeLinejoin="round" points={pts.map((y, i) => `${(i * 120) / 13},${34 - ((y - mn) / (mxx - mn || 1)) * 30}`).join(' ')} /></svg>
            </Tilt>
          )
        })}
      </div>
      <div className="grid g2">
        <Chart />
        <div className="grid" style={{ alignContent: 'start' }}>
          <div className="card"><h2 style={{ fontSize: 18, marginBottom: 8 }}>Daily summary</h2><p>{summary(x)}</p><p className="note">Generated from rules, not a diagnosis.</p></div>
          <div className="card"><h2 style={{ fontSize: 18, marginBottom: 8 }}>Active alerts</h2>
            {al.length ? al.slice(0, 2).map((a) => <p key={a.id} style={{ marginBottom: 8 }}><span className="pill" style={cv(`var(--${a.s})`)}>{cap(a.s)}</span> {a.n}</p>) : <p className="note">No active alerts.</p>}
            <Link href="/alerts" className="btn o" style={{ marginTop: 10, textDecoration: 'none' }}><Ico d={BELL} cls="bi" />See all alerts<Ico d={ARR} cls="ar" /></Link></div>
        </div>
      </div>
    </section>
  )
}

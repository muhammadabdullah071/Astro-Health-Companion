'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { LBL, type ScKey } from '@/lib/data'
import { useApp } from './AppProvider'
import { Logo, cv } from './ui'

const ICO: Record<string, string> = {
  dashboard: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z',
  alerts: 'M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9M10 21h4',
  assistant: 'M21 12a8 8 0 01-11.6 7.1L3 21l1.9-5.4A8 8 0 1121 12z',
  status: 'M3 12h4l3-8 4 16 3-8h4',
}
const NAMES: Record<string, string> = { dashboard: 'Dashboard', alerts: 'Alerts', assistant: 'Assistant', status: 'Status' }
const SUN = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
const MOON = <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" /></svg>

function Intro() {
  const path = usePathname(), [st, setSt] = useState<'no' | 'in' | 'out'>('no')
  const done = useCallback(() => {
    setSt('out'); document.documentElement.classList.remove('introing')
    try { sessionStorage.setItem('ahc-intro', '1') } catch {}
    setTimeout(() => setSt('no'), 800)
  }, [])
  useEffect(() => {
    let seen = false
    try { seen = sessionStorage.getItem('ahc-intro') === '1' } catch {}
    if (seen || path !== '/' || matchMedia('(prefers-reduced-motion:reduce)').matches) return
    setSt('in'); document.documentElement.classList.add('introing')
    const t = setTimeout(done, 1900)
    addEventListener('keydown', done, { once: true })
    return () => { clearTimeout(t); removeEventListener('keydown', done) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  if (st === 'no') return null
  return (
    <div id="intro" className={st === 'out' ? 'out' : ''} aria-hidden="true" onClick={done}>
      <div className="iw"><Logo size={88} draw /><b>Astro-Health Companion</b><small>INITIALISING MISSION SYSTEMS</small><div className="ib2"><i /></div></div>
    </div>
  )
}

export default function Shell({ children }: { children: ReactNode }) {
  const a = useApp(), path = usePathname(), router = useRouter()
  const v = path === '/' ? 'home' : path.slice(1).split('/')[0]
  const [qi, setQi] = useState(''), [ci, setCi] = useState(0)

  const go = (p: string) => () => router.push(p)
  const askQ = (q: string) => () => { a.setPendingQ(q); router.push('/assistant') }
  const CMD: [string, () => void][] = [
    ['Go to Home', go('/')], ['Go to Dashboard', go('/dashboard')], ['Go to Alerts', go('/alerts')], ['Go to Assistant', go('/assistant')], ['Go to Status', go('/status')],
    ['Toggle theme', a.toggleTheme], ['Toggle offline mode', a.toggleOff], ['Open demo controls', () => a.setDemo(true)], ['Ask: Why was my heart rate flagged?', askQ('Why was my heart rate flagged?')],
  ]
  const cf = CMD.filter((c) => c[0].toLowerCase().includes(qi.toLowerCase()))
  const run = (c?: [string, () => void]) => { if (c) { a.setPalette(false); c[1]() } }

  useEffect(() => {
    const k = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); a.setPalette(!a.palette) }
      else if (e.key === 'Escape') { a.setPalette(false); a.setDemo(false) }
      else if (e.key === 'd' && !e.ctrlKey && !e.metaKey && !/INPUT|TEXTAREA|BUTTON/.test((document.activeElement as HTMLElement)?.tagName ?? '')) a.setDemo(!a.demo)
    }
    addEventListener('keydown', k); return () => removeEventListener('keydown', k)
  })
  useEffect(() => { if (a.palette) { setQi(''); setCi(0) } }, [a.palette])

  const tg = (id: string, label: string, on: boolean, set: (b: boolean) => void) => (
    <label className="tg" key={id}><span>{label}</span><input type="checkbox" id={id} checked={on} onChange={(e) => set(e.target.checked)} /></label>
  )

  return (
    <div className="shell" data-v={v}>
      <div className="aurora" aria-hidden="true"><i /><i /><i /></div>
      <Intro />
      <header className="top">
        <Link className="brand" href="/" style={{ color: 'inherit', textDecoration: 'none' }}>
          <Logo />
          <span style={{ lineHeight: 1.05 }}>Astro-Health<small style={{ display: 'block', font: '600 10.5px var(--fb)', letterSpacing: '.14em', color: 'var(--mut)' }}>COMPANION</small></span>
        </Link>
        <div className="sp" />
        <span className="pill hide" style={cv('var(--sim)')}>Simulated</span>
        <button className="pill" id="net" style={cv(a.off ? 'var(--ok)' : 'var(--acc)')} title="Toggle to preview offline mode" onClick={a.toggleOff}>
          {a.off ? <><span className="lg">Offline mode: running locally</span><span className="sm">Offline</span></> : 'Online'}
        </button>
        <button className="ib" id="kbtn" aria-label="Open command palette" style={{ width: 'auto', padding: '0 12px', fontSize: 12.5, fontWeight: 600 }} onClick={() => a.setPalette(true)}>Ctrl K</button>
        <button className="ib" id="theme" aria-label={'Switch to ' + (a.theme === 'dark' ? 'light' : 'dark') + ' theme'} onClick={a.toggleTheme}>{a.theme === 'dark' ? SUN : MOON}</button>
      </header>
      <nav className="nav" aria-label="Main">
        {Object.keys(NAMES).map((k) => (
          <Link key={k} href={'/' + k} className={v === k ? 'on' : ''} aria-current={v === k ? 'page' : undefined}>
            <svg viewBox="0 0 24 24"><path d={ICO[k]} /></svg>{NAMES[k]}
          </Link>
        ))}
      </nav>
      <main>{children}</main>

      <div className={'toast' + (a.toastOn ? ' on' : '')} role="status">{a.toastMsg}</div>
      <button className="fab" id="fab" aria-label="Open demo controls" aria-expanded={a.demo} onClick={() => a.setDemo(!a.demo)}>Demo</button>
      <aside className={'dp' + (a.demo ? ' on' : '')} id="dp" aria-label="Demo controls">
        <h2 style={{ fontSize: 18, marginBottom: 4 }}>Demo controls</h2>
        <p className="note" style={{ margin: '0 0 10px' }}>Presenter tools. No backend needed.</p>
        <div className="chips">{(Object.keys(LBL) as ScKey[]).map((k) => <button key={k} onClick={() => a.scenario(k)}>{LBL[k]}</button>)}</div>
        {tg('t1', 'Live simulation', a.live, (b) => { a.setLive(b); a.toast(b ? 'Live simulation started' : 'Live simulation stopped') })}
        {tg('t2', 'Simulate offline', a.off, (b) => { if (b !== a.off) a.toggleOff() })}
        {tg('t3', 'Reduce motion', a.reduce, a.setReduce)}
        {tg('t4', '3D effects', a.fx, a.setFx)}
      </aside>
      <div className={'cp' + (a.palette ? ' on' : '')} id="cp" role="dialog" aria-modal="true" aria-label="Command palette" onClick={(e) => { if (e.target === e.currentTarget) a.setPalette(false) }}>
        <div className="cpb">
          <input id="cpi" placeholder="Type a command" aria-label="Command" value={qi} autoFocus={a.palette} ref={(el) => { if (el && a.palette) el.focus() }}
            onChange={(e) => { setQi(e.target.value); setCi(0) }}
            onKeyDown={(e) => {
              if (e.key === 'ArrowDown') { setCi(Math.min(cf.length - 1, ci + 1)); e.preventDefault() }
              else if (e.key === 'ArrowUp') { setCi(Math.max(0, ci - 1)); e.preventDefault() }
              else if (e.key === 'Enter') run(cf[ci])
            }} />
          <div>{cf.length ? cf.map((c, i) => <button key={c[0]} className={i === ci ? 'on' : ''} onClick={() => run(c)}>{c[0]}</button>) : <p className="note" style={{ padding: '12px 18px' }}>No matching command</p>}</div>
        </div>
      </div>
    </div>
  )
}

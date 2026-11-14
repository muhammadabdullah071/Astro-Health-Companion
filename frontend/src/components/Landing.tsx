'use client'
import Link from 'next/link'
import { useEffect, useRef, useState, type CSSProperties, type PointerEvent } from 'react'
import { D, HR_LIMIT } from '@/lib/data'
import { SLIDES } from '@/lib/slides'
import { useApp } from './AppProvider'
import Scene3D from './Scene3D'
import { ARR, BELL, CHAT, Ecg, Ico, Reveal, Tilt, cv } from './ui'

const FEATURES: [string, string, string, string][] = [
  ['var(--acc)', 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z', 'Live health dashboard', 'Heart rate, oxygen, sleep and temperature trends against a personal baseline.'],
  ['var(--watch)', 'M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9M10 21h4', 'Transparent alerts', 'Each alert shows the rule that fired, the measured value and the time.'],
  ['var(--notice)', 'M21 12a8 8 0 01-11.6 7.1L3 21l1.9-5.4A8 8 0 1121 12z', 'Evidence-grounded assistant', 'Ask why an alert appeared and get an answer with numbered sources.'],
  ['var(--ok)', 'M3 12h4l3-8 4 16 3-8h4', 'Offline by design', 'Data, library and assistant run on the device, so nothing waits for Earth.'],
]
const TEAM: [string, string, string, string, string[], string, boolean][] = [
  ['Abdullah', 'AB', 'Team lead and frontend', 'Designs the interface, writes the documentation and keeps the team on schedule.', ['Next.js', 'Documentation'], '#6FA0FF', true],
  ['Elthiero', 'EL', 'Backend and APIs', 'Builds the FastAPI services, the local database and the integration layer.', ['FastAPI', 'SQLite'], '#4FD6EE', false],
  ['Cesar', 'CE', 'Local AI and retrieval', 'Runs the offline assistant and the scientific retrieval pipeline.', ['Ollama', 'RAG'], '#A793FF', false],
  ['Ammara', 'AM', 'Medical research and submission', 'Defines health indicators and alert rules, and manages the NASA portal submission.', ['Health indicators', 'Alert rules'], '#FF7FA3', false],
  ['Sofia', 'SO', 'Data and datasets', 'Explores NASA open data and prepares the simulated datasets behind the demo.', ['NASA OSDR', 'Data analysis'], '#FFA866', false],
  ['Shubhi', 'SH', 'Testing and quality', 'Tests the alert logic, the API and the full offline demo flow.', ['Pytest', 'QA'], '#5BE2AE', false],
]
const HEAD = ['Health', 'awareness', 'for', 'crews', 'beyond', 'Earth’s', 'reach.']

function Carousel() {
  const { reduce } = useApp()
  const n = SLIDES.length
  const [ci, setCi] = useState(1), [hov, setHov] = useState(false)
  const x0 = useRef<number | null>(null), drag = useRef(false)
  const go = (i: number) => setCi(((i % n) + n) % n)
  useEffect(() => {
    if (hov || reduce) return
    const t = setTimeout(() => { if (!document.hidden) setCi((c) => (c + 1) % n) }, 5000)
    return () => clearTimeout(t)
  }, [ci, hov, reduce, n])
  return (
    <>
      <div className="cf" id="cf" tabIndex={0} aria-label="Mission gallery. Use the arrow keys or swipe." onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
        onKeyDown={(e) => { if (e.key === 'ArrowLeft') go(ci - 1); if (e.key === 'ArrowRight') go(ci + 1) }}
        onPointerDown={(e) => { x0.current = e.clientX; drag.current = false }}
        onPointerUp={(e) => { if (x0.current === null) return; const dx = e.clientX - x0.current; x0.current = null; if (Math.abs(dx) > 45) { drag.current = true; go(ci + (dx < 0 ? 1 : -1)); setTimeout(() => (drag.current = false), 60) } }}>
        {SLIDES.map((s, i) => {
          let o = (((i - ci) % n) + n) % n; if (o > n / 2) o -= n
          const a = Math.abs(o)
          const style: CSSProperties = { transform: `translateX(calc(-50% + ${o} * var(--sp))) translateZ(${-a * 160}px) rotateY(${-o * 36}deg) scale(${o ? 0.92 : 1})`, opacity: a > 2 ? 0 : a === 2 ? 0.35 : o ? 0.75 : 1, zIndex: 5 - a, filter: o ? 'blur(1.5px) saturate(.8)' : 'none', pointerEvents: a > 2 ? 'none' : 'auto' }
          return (
            <figure className={'cfc' + (o ? '' : ' act')} key={s.title} style={style} onClick={() => { if (!drag.current) go(i) }}
              onPointerMove={(e) => {
                if (o || reduce || e.pointerType === 'touch') return
                const el = e.currentTarget, b = el.getBoundingClientRect(), x = (e.clientX - b.left) / b.width, y = (e.clientY - b.top) / b.height, f = el.firstElementChild as HTMLElement
                f.style.setProperty('--ry', (x - 0.5) * 16 + 'deg'); f.style.setProperty('--rx', (0.5 - y) * 16 + 'deg'); f.style.setProperty('--gx', x * 100 + '%'); f.style.setProperty('--gy', y * 100 + '%')
              }}
              onPointerLeave={(e) => { const f = e.currentTarget.firstElementChild as HTMLElement; f.style.setProperty('--rx', '0deg'); f.style.setProperty('--ry', '0deg') }}>
              <div className="cfi" dangerouslySetInnerHTML={{ __html: s.svg + `<span class="cfm"><i></i>${s.chip}</span>` }} />
              <figcaption><b>{s.title}</b><span>{s.cap}</span></figcaption>
            </figure>
          )
        })}
      </div>
      <div className="row cfn"><button className="btn o" aria-label="Previous scene" onClick={() => go(ci - 1)}>Previous</button><button className="btn o" aria-label="Next scene" onClick={() => go(ci + 1)}>Next</button></div>
      <div className="cfd">{SLIDES.map((s, i) => <button key={s.title} className={i === ci ? 'on' : ''} aria-label={`Show scene ${i + 1}: ${s.title}`} onClick={() => go(i)} />)}</div>
      <div className="cfp"><i key={ci + '-' + hov} /></div>
    </>
  )
}

const SKY = "<div class='cta-sky' aria-hidden='true'><i style='left:32%;top:42%;animation-delay:0.3s'></i><i style='left:52%;top:65%;animation-delay:0.5s'></i><i style='left:10%;top:6%;animation-delay:1.2s'></i><i style='left:39%;top:11%;animation-delay:0.7s'></i><i style='left:70%;top:50%;animation-delay:0.8s'></i><i style='left:24%;top:17%;animation-delay:0.8s'></i><i style='left:5%;top:86%;animation-delay:2.4s'></i><i style='left:36%;top:28%;animation-delay:0.5s'></i><i style='left:39%;top:84%;animation-delay:2.6s'></i><i style='left:49%;top:15%;animation-delay:2.5s'></i><i style='left:45%;top:89%;animation-delay:1.2s'></i><i style='left:33%;top:26%;animation-delay:0.7s'></i><i style='left:37%;top:15%;animation-delay:2.8s'></i><i style='left:72%;top:42%;animation-delay:0.0s'></i><i style='left:39%;top:77%;animation-delay:2.1s'></i><i style='left:41%;top:69%;animation-delay:0.6s'></i><i style='left:56%;top:80%;animation-delay:0.9s'></i><i style='left:59%;top:24%;animation-delay:0.7s'></i><i style='left:35%;top:9%;animation-delay:0.2s'></i><i style='left:61%;top:84%;animation-delay:3.0s'></i><i style='left:68%;top:72%;animation-delay:1.9s'></i><i style='left:91%;top:47%;animation-delay:0.4s'></i><span class='pl'></span><svg class='rk' viewBox='0 0 40 100'><g class='fl'><path d='M14 62 Q20 98 26 62Z' fill='#FFC531'/><path d='M17 62 Q20 84 23 62Z' fill='#FF5A5F'/></g><path d='M20 2 C30 16 32 34 30 58 H10 C8 34 10 16 20 2Z' fill='#EAF0FF'/><circle cx='20' cy='30' r='6' fill='#1F5BFF' stroke='#9DB0DB' stroke-width='2'/><path d='M10 46 L0 70 L10 62Z M30 46 L40 70 L30 62Z' fill='#FF5A5F'/><path d='M14 58 H26 L20 70Z' fill='#9DB0DB'/></svg><svg class='rk r2' viewBox='0 0 40 100'><g class='fl'><path d='M14 62 Q20 98 26 62Z' fill='#FFC531'/><path d='M17 62 Q20 84 23 62Z' fill='#FF5A5F'/></g><path d='M20 2 C30 16 32 34 30 58 H10 C8 34 10 16 20 2Z' fill='#EAF0FF'/><circle cx='20' cy='30' r='6' fill='#1F5BFF' stroke='#9DB0DB' stroke-width='2'/><path d='M10 46 L0 70 L10 62Z M30 46 L40 70 L30 62Z' fill='#FF5A5F'/><path d='M14 58 H26 L20 70Z' fill='#9DB0DB'/></svg></div>"

export default function Landing() {
  const { reduce } = useApp(), hr = Math.round(D[29].hr), warn = D[29].hr > HR_LIMIT
  const scroll = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' })
  const mag = reduce ? {} : {
    onPointerMove: (e: PointerEvent<HTMLElement>) => { const b = e.currentTarget.getBoundingClientRect(); e.currentTarget.style.transform = `translate(${((e.clientX - b.left) / b.width - 0.5) * 10}px,${((e.clientY - b.top) / b.height - 0.5) * 8}px)` },
    onPointerLeave: (e: PointerEvent<HTMLElement>) => { e.currentTarget.style.transform = '' },
  }
  return (
    <section className="view on" id="home">
      <div className="lh" onPointerMove={(e) => { const b = e.currentTarget.getBoundingClientRect(); e.currentTarget.style.setProperty('--mx', e.clientX - b.left + 'px'); e.currentTarget.style.setProperty('--my', e.clientY - b.top + 'px') }}>
        <i className="sh" style={{ '--t': '10%', '--d': '1.2s' } as CSSProperties} /><i className="sh" style={{ '--t': '34%', '--d': '4.5s' } as CSSProperties} /><i className="sh" style={{ '--t': '62%', '--d': '8s' } as CSSProperties} />
        <div>
          <span className="pill" style={{ ...cv('var(--acc)'), marginBottom: 18 }}>NASA Space Apps 2026: Health Monitoring Software</span>
          <h1 className="hl">
            {HEAD.slice(0, 4).map((w, i) => <span key={w}><span className="w" style={{ '--i': i } as CSSProperties}>{w}</span>{' '}</span>)}
            <span className="g">{HEAD.slice(4).map((w, i) => <span key={w}><span className="w" style={{ '--i': i + 4 } as CSSProperties}>{w}</span>{i < 2 ? ' ' : ''}</span>)}</span>
          </h1>
          <p className="lead">Astro-Health Companion tracks vital trends, explains every alert with cited science, and keeps working when the link to Earth goes quiet.</p>
          <div className="row">
            <Link className="btn lg cta-glow" href="/dashboard" style={{ textDecoration: 'none' }} {...mag}>Launch the dashboard<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: 8, verticalAlign: -3 }}><path d="M5 12h14M13 6l6 6-6 6" /></svg></Link>
            <button className="btn lg o" onClick={() => scroll('how')} {...mag}>See how it works</button>
          </div>
        </div>
        <Scene3D />
        <div className="card dev" id="devfb">
          <div className="lb" style={{ color: 'var(--mut)', fontSize: 13.5 }}>Resting heart rate, demo reading</div>
          <div className="big" style={{ margin: '6px 0 4px' }}>{hr} <small>bpm</small></div>
          <Ecg id="ecg2" hr={hr} />
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
            <span className="pill" style={cv(warn ? 'var(--watch)' : 'var(--ok)')}>{warn ? 'Watch: above baseline' : 'In range'}</span><span className="pill" style={cv('var(--ok)')}>Offline ready</span>
          </div>
        </div>
      </div>
      <button className="scue" aria-label="Scroll to explore" onClick={() => scroll('msn')}>Scroll to explore<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9l6 6 6-6" /></svg></button>
      <Reveal className="trust"><div>Works offline</div><div>Every alert names its rule</div><div>Every answer cites sources</div><div>Simulated data, always labelled</div></Reveal>
      <Reveal className="sec" id="msn"><h2>Built for long missions</h2><p>The farther a crew travels, the more health decisions they make on their own.</p><Carousel /></Reveal>
      <Reveal className="sec"><h2>Everything a crew member needs to read their own health</h2><p>Four tools in one calm interface, built for long missions where help is far away.</p>
        <div className="fg">{FEATURES.map(([c, d, t, p]) => <Tilt className="card" key={t}><div className="ic" style={cv(c)}><svg viewBox="0 0 24 24"><path d={d} /></svg></div><h3>{t}</h3><p>{p}</p></Tilt>)}</div></Reveal>
      <Reveal className="sec" id="how"><h2>How it works</h2><p>From raw readings to a cited explanation in three steps.</p>
        <div className="st3">{[['Collect readings', 'Indicators are stored locally and compared with each astronaut’s own baseline.'], ['Flag unusual changes', 'Plain rules raise a Notice, Watch or Attention alert and say exactly why.'], ['Explain with science', 'The assistant searches the local library and answers with cited sources.']].map(([t, p], i) => <div className="card" key={t}><b>{i + 1}</b><h3>{t}</h3><p>{p}</p></div>)}</div></Reveal>
      <Reveal className="sec"><h2>Meet the team</h2><p>Six people across the world, building one integrated product.</p>
        <div className="tm">{TEAM.map(([n, i, r, d, t, c, l]) => (
          <Tilt className="card tc" key={n} style={cv(c)}><div className="th"><div className="av2">{i}</div><div><b>{n}</b><span>{r}</span></div>{l && <em>Lead</em>}</div><p>{d}</p><div className="tg2">{t.map((x) => <i key={x}>{x}</i>)}</div></Tilt>))}</div></Reveal>
      <Reveal className="card cta cta2">
        <div className="cta-sky-wrap" dangerouslySetInnerHTML={{ __html: SKY }} style={{ display: 'contents' }} />
        <div className="cta-in"><span className="pill" style={{ ...cv('#E4FF3A'), marginBottom: 14 }}>All systems go</span><h2>Ready for liftoff?</h2>
          <p>Check the dashboard, read what an alert means, or ask the assistant. Everything runs on the device.</p>
          <div className="row" style={{ justifyContent: 'center' }}>
            <Link className="btn lg o" href="/alerts" style={{ textDecoration: 'none' }}><Ico d={BELL} cls="bi" />See the alerts<Ico d={ARR} cls="ar" /></Link>
            <Link className="btn lg cta-glow" href="/assistant" style={{ textDecoration: 'none' }}><Ico d={CHAT} cls="bi" />Ask the assistant<Ico d={ARR} cls="ar" /></Link>
          </div></div>
      </Reveal>
      <p className="foot">Decision support only, not a medical diagnosis. All demo data is simulated.</p>
    </section>
  )
}

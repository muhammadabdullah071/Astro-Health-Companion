'use client'
import { useEffect, useRef, useState, type CSSProperties, type PointerEvent, type ReactNode } from 'react'
import { useApp } from './AppProvider'

export const cv = (c: string) => ({ '--c': c }) as CSSProperties

export function Tilt({ className = '', style, k = 12, id, children }: { className?: string; style?: CSSProperties; k?: number; id?: string; children: ReactNode }) {
  const { reduce } = useApp()
  const mv = (e: PointerEvent<HTMLDivElement>) => {
    if (reduce || e.pointerType === 'touch') return
    const el = e.currentTarget, b = el.getBoundingClientRect(), x = (e.clientX - b.left) / b.width, y = (e.clientY - b.top) / b.height
    el.style.setProperty('--ry', (x - 0.5) * k + 'deg'); el.style.setProperty('--rx', (0.5 - y) * k + 'deg')
    el.style.setProperty('--gx', x * 100 + '%'); el.style.setProperty('--gy', y * 100 + '%')
  }
  const lv = (e: PointerEvent<HTMLDivElement>) => { e.currentTarget.style.setProperty('--rx', '0deg'); e.currentTarget.style.setProperty('--ry', '0deg') }
  return <div id={id} className={'tilt ' + className} style={style} onPointerMove={mv} onPointerLeave={lv}>{children}</div>
}

const ecgPath = (() => {
  let p = 'M0 45'
  for (let x = 0; x < 1200; x += 150) p += ` L${x + 30} 45 L${x + 36} 39 L${x + 42} 45 L${x + 60} 45 L${x + 64} 51 L${x + 70} 8 L${x + 76} 62 L${x + 80} 45 L${x + 100} 45 L${x + 112} 35 L${x + 124} 45 L${x + 150} 45`
  return p
})()
export function Ecg({ id, hr }: { id?: string; hr: number }) {
  return <div className="ecg"><svg viewBox="0 0 1200 90" id={id} aria-hidden="true" style={{ animationDuration: ((6 * 78) / Math.max(40, hr)).toFixed(2) + 's' }}><path d={ecgPath} /></svg></div>
}

export function CountUp({ v, d }: { v: number; d: number }) {
  const { animKey, reduce } = useApp()
  const [shown, setShown] = useState(v)
  const running = useRef(false)
  useEffect(() => {
    if (reduce) { setShown(v); return }
    const s = performance.now(); let id = 0; running.current = true
    const f = (n: number) => {
      const p = Math.min(1, (n - s) / 900)
      setShown(v * (1 - Math.pow(1 - p, 3)))
      if (p < 1) id = requestAnimationFrame(f); else running.current = false
    }
    id = requestAnimationFrame(f)
    return () => { cancelAnimationFrame(id); running.current = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [animKey])
  useEffect(() => { if (!running.current) setShown(v) }, [v])
  return <span>{shown.toFixed(d)}</span>
}

export function Reveal({ className = '', id, children }: { className?: string; id?: string; children: ReactNode }) {
  const r = useRef<HTMLDivElement>(null), [on, setOn] = useState(false)
  useEffect(() => {
    const el = r.current; if (!el) return
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { setOn(true); io.disconnect() } }), { threshold: 0.12 })
    io.observe(el); return () => io.disconnect()
  }, [])
  return <div ref={r} id={id} className={className + ' rv' + (on ? ' in' : '')}>{children}</div>
}

export function Logo({ size = 34, draw = false }: { size?: number; draw?: boolean }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" aria-hidden="true">
      <circle cx="18" cy="18" r="17" fill="#1F4FD8" />
      <ellipse className={draw ? 'io' : undefined} cx="18" cy="18" rx="15" ry="5.5" fill="none" stroke="#fff" strokeOpacity={draw ? 0.7 : 0.55} strokeWidth="1.4" transform="rotate(-28 18 18)" />
      <path className={draw ? 'io' : undefined} d="M5 19h7l3-7 5 13 3-6h8" fill="none" stroke="#E4FF3A" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      {!draw && <circle cx="30" cy="9" r="2.4" fill="#fff" />}
    </svg>
  )
}

export const BELL = 'M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9M10 21h4'
export const CHAT = 'M21 12a8 8 0 01-11.6 7.1L3 21l1.9-5.4A8 8 0 1121 12z'
export const ARR = 'M5 12h14M13 6l6 6-6 6'
export function Ico({ d, cls }: { d: string; cls: 'bi' | 'ar' }) {
  return <svg className={cls} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={d} /></svg>
}

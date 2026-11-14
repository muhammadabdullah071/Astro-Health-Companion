'use client'
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { D, LBL, SC, buildAlerts, type Reading, type ScKey } from '@/lib/data'

type Ctx = {
  theme: 'dark' | 'light'; toggleTheme: () => void
  off: boolean; toggleOff: () => void
  reduce: boolean; setReduce: (b: boolean) => void
  fx: boolean; setFx: (b: boolean) => void
  live: boolean; setLive: (b: boolean) => void
  scenario: (k: ScKey) => void
  ver: number; animKey: number
  toast: (m: string) => void; toastMsg: string; toastOn: boolean
  pendingQ: string | null; setPendingQ: (q: string | null) => void
  pendingAlertId: string | null; setPendingAlertId: (id: string | null) => void
  palette: boolean; setPalette: (b: boolean) => void
  demo: boolean; setDemo: (b: boolean) => void
  readings: Reading[]
}
const C = createContext<Ctx | null>(null)
export const useApp = () => { const c = useContext(C); if (!c) throw new Error('AppProvider missing'); return c }

const clone = (rs: Reading[]) => rs.map((r) => ({ ...r }))

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [off, setOff] = useState(false), [reduce, setReduce] = useState(false), [fx, setFx] = useState(true), [live, setLive] = useState(false)
  const [ver, setVer] = useState(0), [animKey, setAnim] = useState(0)
  const [toastMsg, setMsg] = useState(''), [toastOn, setOn] = useState(false)
  const [pendingQ, setPendingQ] = useState<string | null>(null), [palette, setPalette] = useState(false), [demo, setDemo] = useState(false)
  const [pendingAlertId, setPendingAlertId] = useState<string | null>(null)
  const [readings, setReadings] = useState<Reading[]>(D)
  const th = useRef<ReturnType<typeof setTimeout>>(undefined)

  // Fetch backend readings once on mount. Falls back silently to seed `D`.
  useEffect(() => {
    let dead = false
    fetch('/api/readings', { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((rows: (Omit<Reading, 't'> & { t: string })[]) => {
        if (dead || !Array.isArray(rows) || rows.length === 0) return
        setReadings(rows.map((r) => ({ ...r, t: new Date(r.t) })))
      })
      .catch((e) => console.warn('[AppProvider] /api/readings fallback to seed:', e))
    return () => { dead = true }
  }, [])

  const toast = useCallback((m: string) => { setMsg(m); setOn(true); clearTimeout(th.current); th.current = setTimeout(() => setOn(false), 2200) }, [])

  // initial theme + OS reduced-motion preference
  useEffect(() => {
    const t = document.documentElement.getAttribute('data-theme')
    if (t === 'light' || t === 'dark') setTheme(t)
    if (matchMedia('(prefers-reduced-motion:reduce)').matches) setReduce(true)
  }, [])
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('ahc-theme', theme) } catch {}
  }, [theme])
  useEffect(() => { document.documentElement.classList.toggle('rm', reduce) }, [reduce])
  useEffect(() => {
    const hr = readings.length ? readings[readings.length - 1].hr : 62
    document.documentElement.style.setProperty('--bt', (60 / Math.max(40, Math.round(hr))).toFixed(2) + 's')
  }, [ver, readings])

  const scenario = useCallback((k: ScKey) => {
    SC[k]()                       // mutates seed D in place (unchanged)
    setReadings(clone(D))         // ← mirror into the exposed state
    setVer((v) => v + 1)
    setAnim((v) => v + 1)
    toast('Scenario: ' + LBL[k])
  }, [toast])

  useEffect(() => {
    if (!live) return
    const id = setInterval(() => {
      const x = D[29]
      const before = buildAlerts(D).length
      x.hr += (Math.random() - 0.45) * 3
      x.spo2 = Math.min(100, Math.max(93, x.spo2 + (Math.random() - 0.5) * 0.5))
      x.temp += (Math.random() - 0.5) * 0.05
      // Push the mutated last reading into the exposed state so Dashboard updates.
      setReadings((rs) => {
        if (rs.length === 0) return rs
        const next = rs.slice()
        const last = next[next.length - 1]
        next[next.length - 1] = { ...last, hr: x.hr, spo2: x.spo2, temp: x.temp }
        return next
      })
      setVer((v) => v + 1)
      if (buildAlerts(D).length > before) toast('New alert from live simulation')
    }, 5000)
    return () => clearInterval(id)
  }, [live, toast])

  const value = useMemo<Ctx>(() => ({
    theme,
    toggleTheme: () => { setTheme((t) => (t === 'dark' ? 'light' : 'dark')); toast(theme === 'dark' ? 'Light theme on' : 'Dark theme on') },
    off,
    toggleOff: () => { setOff((o) => !o); toast(off ? 'Back online' : 'Offline mode on: everything runs locally') },
    reduce, setReduce, fx, setFx, live, setLive,
    scenario, ver, animKey,
    toast, toastMsg, toastOn,
    pendingQ, setPendingQ,
    pendingAlertId, setPendingAlertId,
    palette, setPalette, demo, setDemo,
    readings,                    // ← was missing
  }), [theme, off, reduce, fx, live, scenario, ver, animKey, toast, toastMsg, toastOn, pendingQ, pendingAlertId, palette, demo, readings])  // ← readings added
  return <C.Provider value={value}>{children}</C.Provider>
}
'use client'
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { D, LBL, SC, buildAlerts, type ScKey } from '@/lib/data'

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
  palette: boolean; setPalette: (b: boolean) => void
  demo: boolean; setDemo: (b: boolean) => void
}
const C = createContext<Ctx | null>(null)
export const useApp = () => { const c = useContext(C); if (!c) throw new Error('AppProvider missing'); return c }

export function AppProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark')
  const [off, setOff] = useState(false), [reduce, setReduce] = useState(false), [fx, setFx] = useState(true), [live, setLive] = useState(false)
  const [ver, setVer] = useState(0), [animKey, setAnim] = useState(0)
  const [toastMsg, setMsg] = useState(''), [toastOn, setOn] = useState(false)
  const [pendingQ, setPendingQ] = useState<string | null>(null), [palette, setPalette] = useState(false), [demo, setDemo] = useState(false)
  const th = useRef<ReturnType<typeof setTimeout>>(undefined)

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
  useEffect(() => { document.documentElement.style.setProperty('--bt', (60 / Math.max(40, Math.round(D[29].hr))).toFixed(2) + 's') }, [ver])

  const scenario = useCallback((k: ScKey) => { SC[k](); setVer((v) => v + 1); setAnim((v) => v + 1); toast('Scenario: ' + LBL[k]) }, [toast])
  useEffect(() => {
    if (!live) return
    const id = setInterval(() => {
      const x = D[29], n = buildAlerts().length
      x.hr += (Math.random() - 0.45) * 3
      x.spo2 = Math.min(100, Math.max(93, x.spo2 + (Math.random() - 0.5) * 0.5))
      x.temp += (Math.random() - 0.5) * 0.05
      setVer((v) => v + 1)
      if (buildAlerts().length > n) toast('New alert from live simulation')
    }, 5000)
    return () => clearInterval(id)
  }, [live, toast])

  const value = useMemo<Ctx>(() => ({
    theme, toggleTheme: () => { setTheme((t) => (t === 'dark' ? 'light' : 'dark')); toast(theme === 'dark' ? 'Light theme on' : 'Dark theme on') },
    off, toggleOff: () => { setOff((o) => !o); toast(off ? 'Back online' : 'Offline mode on: everything runs locally') },
    reduce, setReduce, fx, setFx, live, setLive, scenario, ver, animKey, toast, toastMsg, toastOn, pendingQ, setPendingQ, palette, setPalette, demo, setDemo,
  }), [theme, off, reduce, fx, live, scenario, ver, animKey, toast, toastMsg, toastOn, pendingQ, palette, demo])
  return <C.Provider value={value}>{children}</C.Provider>
}

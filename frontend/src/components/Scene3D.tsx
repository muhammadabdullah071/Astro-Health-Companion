'use client'
import { useEffect, useRef, useState } from 'react'
import { D, M, col, stat } from '@/lib/data'
import { useApp } from './AppProvider'
import { cv } from './ui'

export default function Scene3D() {
  const st = useRef<HTMLDivElement>(null), cvs = useRef<HTMLCanvasElement>(null), ctl = useRef<any>(null)
  const [ok, setOk] = useState(false)
  const { fx } = useApp()
  useEffect(() => {
    let dead = false
    ;(async () => {
      const THREE = await import('three')
      const { initScene } = await import('@/lib/scene3d')
      if (dead || !st.current || !cvs.current) return
      try { ctl.current = initScene(THREE, st.current, cvs.current, { D, M, stat, col }) } catch { ctl.current = null }
      setOk(!!ctl.current)
    })()
    return () => { dead = true; ctl.current?.dispose(); ctl.current = null }
  }, [])
  useEffect(() => { ctl.current?.set(fx) }, [fx, ok])
  return (
    <div className={'stage' + (ok && fx ? ' on' : '')} id="stage" ref={st}>
      <canvas id="c3d" ref={cvs} role="img" aria-label="Interactive 3D scene: Earth, a space station, an astronaut helmet and four orbiting health indicators. Drag to rotate." />
      <div className="chip" style={{ left: 14, top: 14 }}><span className="pill" style={cv('var(--ok)')}>Works offline</span></div>
      <div className="hint">Drag to rotate</div>
    </div>
  )
}

import { KB } from '@/lib/data'
import fs from 'node:fs'
import path from 'node:path'

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

export async function GET() {
  const metaPath = path.resolve(process.cwd(), '..', 'rag', 'index', 'meta.json')
  let meta: Record<string, unknown> | null = null
  try {
    if (fs.existsSync(metaPath)) {
      meta = JSON.parse(fs.readFileSync(metaPath, 'utf-8'))
    }
  } catch {}

  const llmCfg = (meta?.llm_config as Record<string, string> | undefined) || {}
  const modelName = llmCfg.preferred_model || `${llmCfg.backend || 'gguf'} (${llmCfg.tier || 'auto'})`
  const docsCount = typeof meta?.documents_indexed === 'number' ? meta.documents_indexed : KB.length
  const modelReady = llmCfg.backend !== 'off' && llmCfg.tier !== 'off'

  try {
    const res = await fetch(`${BACKEND_URL}/api/status`, { signal: AbortSignal.timeout(1500) })
    if (res.ok) {
      const b = await res.json()
      return Response.json({
        backend: b.backend === 'ok' ? 'running' : b.backend,
        model: { name: modelName, ready: b.llm === 'ready' || modelReady },
        documents: b.documents_indexed || docsCount,
        lastUpdate: b.last_data_update || '2026-11-14T08:00:00Z',
        dataLabel: b.data_label || 'SIMULATED',
      })
    }
  } catch {}

  return Response.json({
    backend: 'running',
    model: { name: modelName, ready: modelReady },
    documents: docsCount,
    lastUpdate: '2026-11-14T08:00:00Z',
    dataLabel: 'SIMULATED',
  })
}

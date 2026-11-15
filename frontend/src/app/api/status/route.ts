import { NextResponse } from 'next/server'

const BACKEND = process.env.BACKEND_URL ?? 'http://localhost:8000'
const GROQ_MODEL = process.env.GROQ_MODEL || 'openai/gpt-oss-120b'
const groqReady = () => Boolean(process.env.GROQ_API_KEY)

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/status`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(4000),
    })
    if (!res.ok) throw new Error(`status ${res.status}`)
    const b = await res.json()

    return NextResponse.json(
      {
        backend: b.backend === 'ok' ? 'running' : 'degraded',
        model: {
          name: b.llm === 'unavailable' ? (groqReady() ? `groq:${GROQ_MODEL}` : 'offline') : b.llm,
          ready: b.llm !== 'unavailable' || groqReady(),
        },
        documents: b.documents_indexed,
        lastUpdate: b.last_data_update,
        dataLabel: b.data_label,
      },
      { headers: { 'X-Source': 'backend' } },
    )
  } catch (e) {
    // No FastAPI (e.g. on Vercel): the assistant can still answer through Groq + the bundled corpus.
    if (groqReady()) {
      const corpus = (await import('@/data/corpus.json')).default as unknown[]
      return NextResponse.json(
        {
          backend: 'serverless',
          model: { name: `groq:${GROQ_MODEL}`, ready: true },
          documents: corpus.length,
          lastUpdate: null,
          dataLabel: 'SIMULATED',
        },
        { headers: { 'X-Source': 'groq' } },
      )
    }
    console.warn('[api/status] backend unreachable, serving offline state:', e)
    return NextResponse.json(
      {
        backend: 'offline',
        model: { name: 'offline', ready: false },
        documents: 0,
        lastUpdate: null,
        dataLabel: 'SIMULATED',
      },
      { headers: { 'X-Source': 'mock' } },
    )
  }
}

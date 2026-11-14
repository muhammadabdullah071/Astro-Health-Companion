import { KB, answer } from '@/lib/data'
import { execFile } from 'node:child_process'
import path from 'node:path'
import { promisify } from 'node:util'

const execFileAsync = promisify(execFile)
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8000'

type RagCitation = { title: string; source: string; url: string; excerpt: string }
type RagResponse = {
  answer: string
  mode: 'llm' | 'retrieval_only'
  citations: RagCitation[]
  disclaimer?: string
}

async function askViaFastApi(question: string, alertId?: string): Promise<RagResponse | null> {
  try {
    const res = await fetch(`${BACKEND_URL}/api/assistant/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, ...(alertId ? { alert_id: alertId } : {}) }),
      signal: AbortSignal.timeout(45000),
    })
    if (res.ok) return (await res.json()) as RagResponse
  } catch {}
  return null
}

async function askViaLocalPython(question: string): Promise<RagResponse | null> {
  const repoRoot = path.resolve(process.cwd(), '..')
  const venvPyWin = path.join(repoRoot, 'backend', '.venv', 'Scripts', 'python.exe')
  const venvPyUnix = path.join(repoRoot, 'backend', '.venv', 'bin', 'python')
  for (const py of [venvPyWin, venvPyUnix, 'python', 'python3']) {
    try {
      const { stdout } = await execFileAsync(py, ['-m', 'rag.ask', '--question', question], {
        cwd: repoRoot,
        timeout: 45000,
        env: { ...process.env, ASK_TIMEOUT_SECONDS: '45' },
      })
      if (stdout) return JSON.parse(stdout) as RagResponse
    } catch {}
  }
  return null
}

export async function POST(req: Request) {
  const b = await req.json().catch(() => null)
  if (!b || typeof b.question !== 'string' || !b.question.trim() || b.question.length > 500)
    return Response.json({ error: 'question must be a non-empty string of at most 500 characters' }, { status: 400 })

  const question = b.question.trim()
  const ragRes = (await askViaFastApi(question, b.alert_id)) ?? (await askViaLocalPython(question))

  if (ragRes && typeof ragRes.answer === 'string') {
    const citations = Array.isArray(ragRes.citations) ? ragRes.citations : []
    return Response.json({
      text: ragRes.answer,
      answer: ragRes.answer,
      known: citations.length > 0,
      cites: citations.map((_, idx) => idx),
      citations,
      mode: ragRes.mode,
      sources: citations.map((c, idx) => ({
        id: idx,
        t: c.title,
        s: c.source,
        url: c.url,
        excerpt: c.excerpt,
      })),
    })
  }

  const num = (v: unknown, d: number) => (typeof v === 'number' && isFinite(v) ? v : d)
  const a = answer(question, { hr: num(b.reading?.hr, 62), sleep: num(b.reading?.sleep, 6.8) })
  return Response.json({ ...a, mode: 'demo', sources: a.cites.map((i) => ({ id: i, ...KB[i] })) })
}

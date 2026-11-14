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

function buildFollowUpSuggestions(question: string): string[] {
  const q = question.toLowerCase()
  if (q.includes('heart') || q.includes('hr') || q.includes('bpm') || q.includes('pulse')) {
    return [
      'When does a persistent heart rate deviation require escalation (HR-02)?',
      'How do I verify wearable sensor contact quality and artifacts?',
      'What does low sleep mean for me?',
      'Does skin temperature above baseline mean I have a fever?',
    ]
  }
  if (q.includes('sleep') || q.includes('fatigue') || q.includes('circadian')) {
    return [
      'What sleep countermeasures does S7 recommend for multi-night restriction?',
      'Why was my heart rate flagged?',
      'What does an SpO2 drop below baseline mean?',
      'What are the musculoskeletal exercise countermeasures in S9?',
    ]
  }
  if (q.includes('temp') || q.includes('fever') || q.includes('immune')) {
    return [
      'Why can wearable skin temperature not diagnose fever or infection?',
      'How do I verify wearable sensor contact quality and artifacts?',
      'Why was my heart rate flagged?',
      'What does low sleep mean for me?',
    ]
  }
  return [
    'Why was my heart rate flagged?',
    'What does low sleep mean for me?',
    'Does skin temperature above baseline mean I have a fever?',
    'What does an SpO2 drop below baseline mean?',
  ]
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
  const suggestions = buildFollowUpSuggestions(question)
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
      suggestions,
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
  return Response.json({ ...a, mode: 'demo', suggestions, sources: a.cites.map((i) => ({ id: i, ...KB[i] })) })
}

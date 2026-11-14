import { KB, answer } from '@/lib/data'
export async function POST(req: Request) {
  const b = await req.json().catch(() => null)
  if (!b || typeof b.question !== 'string' || !b.question.trim() || b.question.length > 500)
    return Response.json({ error: 'question must be a non-empty string of at most 500 characters' }, { status: 400 })
  const num = (v: unknown, d: number) => (typeof v === 'number' && isFinite(v) ? v : d)
  const a = answer(b.question, { hr: num(b.reading?.hr, 62), sleep: num(b.reading?.sleep, 6.8) })
  return Response.json({ ...a, mode: 'demo', sources: a.cites.map((i) => ({ id: i, ...KB[i] })) })
}

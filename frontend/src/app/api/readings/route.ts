import { D0 } from '@/lib/data'
export function GET(req: Request) {
  const n = Math.min(30, Math.max(1, Number(new URL(req.url).searchParams.get('days')) || 14))
  return Response.json({ dataLabel: 'SIMULATED', readings: D0.slice(-n).map((r) => ({ ...r, t: r.t.toISOString() })) })
}

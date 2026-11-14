import { KB } from '@/lib/data'
export function GET() {
  return Response.json({ backend: 'running', model: { name: 'demo-scripted', ready: true }, documents: KB.length, lastUpdate: '2026-11-14T08:00:00Z', dataLabel: 'SIMULATED' })
}

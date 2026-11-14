import { M } from '@/lib/data'
export function GET() {
  return Response.json({ name: 'Commander', missionDay: 142, baselines: { hr: M.hr.b, spo2: M.spo2.b, sleep: M.sleep.b, temp: M.temp.b }, dataLabel: 'SIMULATED' })
}

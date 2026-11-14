import { D0, buildAlerts } from '@/lib/data'
export function GET() { return Response.json({ alerts: buildAlerts(D0) }) }

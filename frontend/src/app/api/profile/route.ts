import { NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

// NOTE: lib/data.ts has no `profile` export, so the current mock shape lives
// in your existing route.ts. I pass the backend fields through with
// snake→camel conversion. If your Profile page expects different keys,
// keep the current mock verbatim and only add the fetch — the mapping below
// is a best guess based on the rest of the codebase.

type BackendProfile = {
  id: string;
  name: string;
  mission: string;
  mission_day: number;
  baseline_window_days: number;
  data_label: string;
};

const MOCK = {
  id: "ASTRO-01",
  name: "Simulated astronaut ASTRO-01",
  mission: "Simulated long-duration mission",
  missionDay: 30,
  baselineWindowDays: 7,
  dataLabel: "SIMULATED",
};

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/profile`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) throw new Error(`profile ${res.status}`);
    const b: BackendProfile = await res.json();

    return NextResponse.json({
      id: b.id,
      name: b.name,
      mission: b.mission,
      missionDay: b.mission_day,
      baselineWindowDays: b.baseline_window_days,
      dataLabel: b.data_label,
    });
  } catch (e) {
    console.warn("[api/profile] fallback to mock:", e);
    return NextResponse.json(MOCK);
  }
}
import { NextResponse } from "next/server";
import { D } from "@/lib/data";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

// backend → UI shape (Reading[] in lib/data.ts)
//   timestamp      → t     (ISO string; client does new Date(t))
//   heart_rate_bpm → hr
//   spo2_pct       → spo2
//   sleep_hours    → sleep
//   body_temp_c    → temp
type BackendReading = {
  timestamp: string;
  heart_rate_bpm: number;
  spo2_pct: number;
  sleep_hours: number;
  body_temp_c: number;
};

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/readings`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) throw new Error(`readings ${res.status}`);
    const body: { readings: BackendReading[] } = await res.json();

    return NextResponse.json(
      body.readings.map((r) => ({
        t: r.timestamp,
        hr: r.heart_rate_bpm,
        spo2: r.spo2_pct,
        sleep: r.sleep_hours,
        temp: r.body_temp_c,
      })),
    );
  } catch (e) {
    console.warn("[api/readings] fallback to mock:", e);
    return NextResponse.json(D); // Date is serialized to ISO string by JSON.stringify
  }
}
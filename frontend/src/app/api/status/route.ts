import { NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/status`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) throw new Error(`status ${res.status}`);
    const b = await res.json();

    return NextResponse.json(
      {
        backend: b.backend === "ok" ? "running" : "degraded",
        model: {
          name: b.llm === "unavailable" ? "offline" : b.llm,
          ready: b.llm !== "unavailable",
        },
        documents: b.documents_indexed,
        lastUpdate: b.last_data_update,
        dataLabel: b.data_label,
      },
      { headers: { "X-Source": "backend" } },
    );
  } catch (e) {
    console.warn("[api/status] backend unreachable, serving offline state:", e);
    return NextResponse.json(
      {
        backend: "offline",
        model: { name: "offline", ready: false },
        documents: 0,
        lastUpdate: null,
        dataLabel: "SIMULATED",
      },
      { headers: { "X-Source": "mock" } },
    );
  }
}
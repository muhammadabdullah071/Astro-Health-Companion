import { NextResponse } from "next/server";
import { D, buildAlerts, type Alert } from "@/lib/data";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

// backend alert → UI Alert (lib/data.ts)
//   id              → id
//   severity        → s   ('watch' | 'notice' already match)
//   rule            → n   (title)
//   message         → m   (detail text)
//   —               → q   (generic assistant prompt; no backend field)
//   rule_id + rule  → rule (identifier shown in the UI)
type BackendAlert = {
  id: string;
  rule_id: string;
  rule: string;
  severity: "watch" | "notice";
  message: string;
  next_step: string;
  source: string;
  [k: string]: unknown;
};

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/alerts`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) throw new Error(`alerts ${res.status}`);
    const body: { alerts: BackendAlert[] } = await res.json();

    const QUESTION_BY_RULE: Record<string, string> = {
      "HR-01":    "Why was my heart rate flagged?",
      "HR-02":    "Why is my heart rate still elevated?",
      "SPO2-01":  "Why is my oxygen below baseline?",
      "SLEEP-01": "What does low sleep mean for me?",
      "SLEEP-02": "Why is my sleep flagged?",
      "TEMP-01":  "Why is my skin temperature flagged?",
      "DATA-01":  "Why is my data flagged as unreliable?",
      "DATA-02":  "Why is my baseline not established?",
    };
    const alerts: Alert[] = body.alerts.map((b) => ({
      id: b.id,
      s: b.severity,
      n: b.rule,
      m: b.message,
      q: QUESTION_BY_RULE[b.rule_id] ?? "Why was this flagged?",
      rule: `[${b.rule_id}] ${b.rule}`,
    }));
    return NextResponse.json(alerts);
  } catch (e) {
    console.warn("[api/alerts] fallback to mock:", e);
    return NextResponse.json(buildAlerts(D));
  }
}
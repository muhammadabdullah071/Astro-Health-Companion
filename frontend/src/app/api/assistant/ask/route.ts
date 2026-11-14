import { NextResponse } from "next/server";
import { answer as mockAnswer, D } from "@/lib/data";

const BACKEND = process.env.BACKEND_URL ?? "http://localhost:8000";

// backend answer → UI Answer (lib/data.ts)
//   answer      → text
//   citations[] → cites: number[]  (indices; your UI resolves them against
//                                    lib/data.ts's KB array. Titles will
//                                    show KB's text, not the backend
//                                    citation titles — acceptable for demo,
//                                    or extend the Answer type to carry
//                                    the citation objects if you want the
//                                    real titles in the UI)
//   —           → known: true unless the backend's answer looks like a
//                 "can't answer" response
type BackendAnswer = {
  answer: string;
  mode: "llm" | "retrieval_only";
  citations: { title: string; source: string; url: string; excerpt: string }[];
  disclaimer: string;
};

export async function POST(req: Request) {
  let question = "";
  try {
    const body = await req.json();
    question = String(body?.question ?? "");

    const res = await fetch(`${BACKEND}/api/assistant/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      // backend ASK_TIMEOUT_SECONDS=20 — give it a small margin
      signal: AbortSignal.timeout(25_000),
    });
    if (!res.ok) throw new Error(`assistant ${res.status}`);
    const b: BackendAnswer = await res.json();

    return NextResponse.json({
      text: b.answer,
      cites: b.citations.map((_, i) => i),
      known: b.mode === "llm" || b.citations.length > 0,
      citations: b.citations,   // ← real citation objects, not just indices
    }, { headers: { "X-Source": "backend" } });
  } catch (e) {
    console.warn("[api/assistant/ask] fallback to mock:", e);
    const last = D[D.length - 1];
    return NextResponse.json(mockAnswer(question, { hr: last.hr, sleep: last.sleep }),
    { headers: { "X-Source": "mock" } });
  }
}
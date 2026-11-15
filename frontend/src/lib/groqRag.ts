// TypeScript port of the retrieval + prompt pipeline in rag/ask.py, answered by Groq.
// Used when the Python RAG module is unreachable (e.g. on Vercel). Keep in sync with rag/ask.py.
import corpusJson from '@/data/corpus.json'

type Doc = {
  id: string
  title?: string
  source?: string
  url?: string
  excerpt?: string
  abstract?: string
  keywords?: string[]
  chunks?: string[]
}
export type Citation = { title: string; source: string; url: string; excerpt: string }
export type HistoryTurn = { role?: string; content?: string; text?: string }
export type RagResult = { answer: string; mode: 'llm' | 'retrieval_only'; citations: Citation[] }

const corpus = corpusJson as unknown as Doc[]
export const NOT_FOUND = 'I cannot answer that from my sources.'

const STOPWORDS = new Set([
  'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'can', 'did', 'do', 'does',
  'for', 'from', 'had', 'has', 'have', 'how', 'i', 'in', 'is', 'it', 'its',
  'me', 'my', 'of', 'on', 'or', 'should', 'so', 'that', 'the', 'their', 'them',
  'there', 'these', 'this', 'to', 'was', 'what', 'when', 'where', 'which',
  'who', 'why', 'will', 'with', 'would', 'you', 'your', 'flagged', 'alert',
  'mean', 'explain', 'tell', 'about', 'happened', 'research', 'say', 'says',
])
const FOLLOWUP_CUES = new Set([
  'it', 'that', 'this', 'those', 'them', 'they', 'next', 'more', 'else',
  'persist', 'persists', 'persisted', 'continue', 'continues', 'again',
  'also', 'about', 'step', 'steps', 'action', 'actions', 'do',
])

const TOPIC_SUGGESTIONS: Record<string, string> = {
  heart_rate:
    'Repeat the resting heart-rate measurement under the same conditions after 5-10 minutes of quiet rest, ' +
    'verify wearable strap fit and optical contact quality, review recent sleep, hydration, and exercise load, ' +
    'and follow the EIMO escalation protocol if the deviation persists across consecutive days.',
  sleep:
    'Review crew schedule, recent workload, cabin light/noise environment, and fatigue logs; ' +
    'prioritize a protected rest window and apply mission-approved circadian and sleep countermeasures.',
  spo2:
    'Verify pulse-oximeter sensor placement, skin contact quality, and motion artifacts first; ' +
    'repeat the reading at rest and check for any respiratory or exertion symptoms per mission protocol.',
  temperature:
    'Check wrist sensor contact and ambient thermal conditions and repeat at the same site; ' +
    'if skin-temperature elevation persists or symptoms appear, take a manual core-temperature reading per medical protocol.',
  musculoskeletal:
    'Maintain scheduled resistive and aerobic countermeasure sessions and review exercise telemetry logs ' +
    'with the crew medical officer.',
  radiation:
    'Refer to dedicated onboard radiation dosimetry badges and mission shielding protocols rather than wearable vital-sign monitors.',
  general:
    'Repeat the measurement under standardized resting conditions, verify wearable sensor contact quality, ' +
    'review personal 7-day baseline trends, and consult the onboard EIMO medical checklist if deviations persist.',
}

const words = (text: string) => text.toLowerCase().match(/[a-z0-9_-]+/g) ?? []
const tokenize = (text: string) => new Set(words(text).filter((t) => t.length > 1 && !STOPWORDS.has(t)))
const intersect = (a: Set<string>, b: Set<string>) => new Set([...a].filter((x) => b.has(x)))

function inferSuggestion(question: string, citations: Citation[]): string {
  const q = question.toLowerCase()
  const has = (ws: string[]) => ws.some((w) => q.includes(w))
  if (has(['heart', 'hr', 'bpm', 'pulse', 'cardiovascular'])) return TOPIC_SUGGESTIONS.heart_rate
  if (has(['sleep', 'fatigue', 'circadian', 'night', 'rest', 'tired'])) return TOPIC_SUGGESTIONS.sleep
  if (has(['spo2', 'oxygen', 'saturation', 'hypoxia'])) return TOPIC_SUGGESTIONS.spo2
  if (has(['temp', 'temperature', 'fever', 'skin', 'celsius', 'immune'])) return TOPIC_SUGGESTIONS.temperature
  if (has(['bone', 'muscle', 'exercise', 'musculoskeletal', 'atrophy'])) return TOPIC_SUGGESTIONS.musculoskeletal
  if (has(['radiation', 'cosmic', 'dosimetry', 'shielding'])) return TOPIC_SUGGESTIONS.radiation
  const ids = new Set(citations.map((c) => c.title.split(':')[0].trim()))
  if (ids.has('S7')) return TOPIC_SUGGESTIONS.sleep
  if (ids.has('S6')) return TOPIC_SUGGESTIONS.temperature
  if (ids.has('S2')) return TOPIC_SUGGESTIONS.heart_rate
  if (ids.has('S9')) return TOPIC_SUGGESTIONS.musculoskeletal
  if (ids.has('S8')) return TOPIC_SUGGESTIONS.radiation
  return TOPIC_SUGGESTIONS.general
}

function bestChunk(doc: Doc, qTokens: Set<string>): string {
  if (doc.chunks?.length) {
    let best = String(doc.chunks[0]), bestScore = -1
    for (const ch of doc.chunks) {
      const s = String(ch).trim()
      if (!s) continue
      const overlap = intersect(qTokens, tokenize(s)).size
      if (overlap > bestScore) { bestScore = overlap; best = s }
    }
    return best.trim()
  }
  const abstract = (doc.abstract ?? '').trim()
  if (!abstract) return ''
  if (abstract.length <= 450) return abstract
  return abstract.slice(0, 450).replace(/\s+\S*$/, '') + '...'
}

function toCitation(doc: Doc, qTokens: Set<string>): Citation {
  const base = (doc.excerpt ?? '').trim()
  const snippet = bestChunk(doc, qTokens)
  const excerpt =
    snippet && !base.toLowerCase().includes(snippet.slice(0, 60).toLowerCase())
      ? `${base} Ingested source excerpt: ${snippet}`
      : base
  return { title: doc.title ?? '', source: doc.source ?? '', url: doc.url ?? '', excerpt }
}

export function retrieve(question: string, history: HistoryTurn[] = [], topK = 2): Citation[] {
  let qTokens = tokenize(question)
  const domain = new Set(corpus.flatMap((d) => (d.keywords ?? []).map((k) => k.toLowerCase())))
  const raw = new Set(words(question))

  // Follow-up questions ("what should I do next?") inherit the topic from recent turns.
  if (!intersect(qTokens, domain).size && [...raw].some((w) => FOLLOWUP_CUES.has(w)) && history.length) {
    for (const turn of history.slice(-4).reverse()) {
      const inherited = intersect(tokenize(String(turn.content ?? turn.text ?? '')), domain)
      if (inherited.size) { qTokens = new Set([...qTokens, ...inherited]); break }
    }
  }
  if (!intersect(qTokens, domain).size) return []

  const scored = corpus
    .map((doc) => {
      const kw = new Set((doc.keywords ?? []).map((k) => k.toLowerCase()))
      const chunksText = (doc.chunks ?? []).slice(0, 8).join(' ')
      const docTokens = new Set([...tokenize(`${doc.title ?? ''} ${doc.excerpt ?? ''} ${doc.abstract ?? ''} ${chunksText}`), ...kw])
      return { doc, score: 3 * intersect(qTokens, kw).size + intersect(qTokens, docTokens).size }
    })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score)
  return scored.slice(0, topK).map((x) => toCitation(x.doc, qTokens))
}

function buildPrompt(question: string, citations: Citation[], history: HistoryTurn[]): string {
  const context = citations.map((c, i) => `[${i + 1}] ${c.title} — ${c.source} (${c.url}): ${c.excerpt}`).join('\n')
  const turns = history
    .slice(-4)
    .map((t) => {
      const role = ['u', 'user', 'human'].includes(String(t.role ?? 'user').toLowerCase()) ? 'Astronaut' : 'Assistant'
      const content = String(t.content ?? t.text ?? '').trim()
      return content ? `${role}: ${content.slice(0, 260)}` : ''
    })
    .filter(Boolean)
  const historyBlock = turns.length ? `Previous Conversation Turns:\n${turns.join('\n')}\n\n` : ''
  return (
    'You are an offline astronaut health decision-support assistant. ' +
    'Keep your answer concise (3 to 5 sentences maximum) and follow these strict rules:\n' +
    '1. Use ONLY the provided scientific sources, alert details, and previous conversation context.\n' +
    '2. Cite sources inline as [1], [2].\n' +
    "3. State the plain-language explanation (and Rule ID if given) and ALWAYS include concrete " +
    "actionable suggestions ('Suggested next step: ...') from the provided protocol.\n" +
    '4. NEVER infer a medical diagnosis, fever, infection, hypoxia, arrhythmia, or immune/psychiatric ' +
    'condition from wearable indicators or skin temperature. Skin temperature is not core temperature.\n' +
    '5. If the alert is DATA-01 or DATA-02, state clearly that it is a data-quality or baseline-setup notice ' +
    'and infer no health event.\n' +
    "6. End with: 'This is a monitoring alert, not a diagnosis.'\n\n" +
    historyBlock +
    `Recommended Operational Suggestions: ${inferSuggestion(question, citations)}\n\n` +
    `Sources:\n${context}\n\nQuestion: ${question}\nAnswer:`
  )
}

function enforceGuardrails(text: string, question: string, citations: Citation[]): string {
  let out = text.trim().replace(/\s*This is a monitoring alert,\s*not a diagnosis\.?\s*$/i, '').trim()
  const step = inferSuggestion(question, citations)
  const low = out.toLowerCase()
  if (step && !low.includes('suggested next step') && !low.includes(step.slice(0, 20).toLowerCase()))
    out = `${out.replace(/[. ]+$/, '')}. Suggested next step: ${step}`
  if (!out.toLowerCase().includes('not a diagnosis')) out = `${out.replace(/[. ]+$/, '')}. This is a monitoring alert, not a diagnosis.`
  return out
}

function retrievalAnswer(question: string, citations: Citation[]): string {
  const refs = citations.map((_, i) => `[${i + 1}]`).join('')
  const excerpts = citations.map((c, i) => `[${i + 1}] ${c.excerpt}`).join(' ')
  return (
    `From the local scientific library ${refs}: ${excerpts} ` +
    `Suggested next step: ${inferSuggestion(question, citations)} ` +
    'Note: Curated sources provide spaceflight physiological context only and do not establish diagnostic thresholds.'
  )
}

async function groqGenerate(prompt: string): Promise<string | null> {
  const key = process.env.GROQ_API_KEY
  if (!key) return null
  try {
    const res = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
      body: JSON.stringify({
        model: process.env.GROQ_MODEL || 'openai/gpt-oss-120b',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.1,
        max_tokens: 800,
        ...(String(process.env.GROQ_MODEL || 'openai/gpt-oss').startsWith('openai/gpt-oss') ? { reasoning_effort: 'low' } : {}),
      }),
      signal: AbortSignal.timeout(20000),
    })
    if (!res.ok) { console.error('[groq] HTTP', res.status, await res.text().catch(() => '')); return null }
    const body = await res.json()
    const text = String(body?.choices?.[0]?.message?.content ?? '').replace(/<think>[\s\S]*?<\/think>/g, '').trim()
    return text || null
  } catch (e) {
    console.error('[groq] request failed', e)
    return null
  }
}

export const groqEnabled = () => Boolean(process.env.GROQ_API_KEY)

export async function askWithGroq(question: string, history: HistoryTurn[] = []): Promise<RagResult> {
  const citations = retrieve(question, history)
  if (!citations.length) return { answer: NOT_FOUND, mode: 'retrieval_only', citations: [] }
  const llm = await groqGenerate(buildPrompt(question, citations, history))
  if (llm) return { answer: enforceGuardrails(llm, question, citations), mode: 'llm', citations }
  return { answer: retrievalAnswer(question, citations), mode: 'retrieval_only', citations }
}

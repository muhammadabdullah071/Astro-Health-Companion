export type Key = 'hr' | 'spo2' | 'sleep' | 'temp'
export type Sev = 'ok' | 'notice' | 'watch'
export type Reading = { t: Date } & Record<Key, number>

export const M: Record<Key, { l: string; u: string; b: number; lo: number; hi: number; d: number }> = {
  hr: { l: 'Heart rate', u: 'bpm', b: 62, lo: 50, hi: 75, d: 0 },
  spo2: { l: 'Oxygen (SpO2)', u: '%', b: 97, lo: 94, hi: 100, d: 0 },
  sleep: { l: 'Sleep', u: 'h', b: 6.8, lo: 6, hi: 9, d: 1 },
  temp: { l: 'Body temperature', u: '°C', b: 36.7, lo: 36.1, hi: 37.2, d: 1 },
}
export const KEYS = Object.keys(M) as Key[]

// Seeded generator so server and client build the same simulated dataset.
let seed = 7
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647
export const D: Reading[] = Array.from({ length: 30 }, (_, i) => ({
  t: new Date(Date.UTC(2026, 9, 16 + i)),
  hr: 62 + (rnd() - 0.5) * 4 + (i >= 26 ? (i - 25) * 4.2 : 0),
  spo2: 97 + (rnd() - 0.5) * 1.6,
  sleep: 6.8 + (rnd() - 0.5) * 1.2 - (i >= 27 ? 1.2 : 0),
  temp: 36.7 + (rnd() - 0.5) * 0.3 + (i >= 27 ? (i - 26) * 0.1 : 0),
}))
export const D0: Reading[] = D.map((d) => ({ ...d }))

export const fd = (t: Date) => t.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })
export const stat = (k: Key, v: number): [Sev, string] => {
  const m = M[k]
  return v > m.hi || v < m.lo ? (k === 'sleep' ? ['notice', 'Notice: below range'] : ['watch', 'Watch: out of range']) : ['ok', 'In range']
}
export const col = (s: string) => `var(--${s})`
export const cap = (s: string) => s[0].toUpperCase() + s.slice(1)

// ---- Alert rules (every alert carries the rule text that fired it)
export type Alert = { id: string; s: 'watch' | 'notice'; n: string; m: string; q: string; rule: string }
export const HR_LIMIT = 75
export const buildAlerts = (data: Reading[] = D): Alert[] => {
  const x = data[data.length - 1], a: Alert[] = []
  if (x.hr > HR_LIMIT)
    a.push({ id: 'a1', s: 'watch', n: 'Resting heart rate above personal baseline', m: `${Math.round(x.hr)} bpm vs baseline 62 bpm`, q: 'Why was my heart rate flagged?',
      rule: `Watch when resting heart rate is above ${HR_LIMIT} bpm, the top of the normal range.` })
  if (x.sleep < 6) {
    let n = 0
    for (let i = data.length - 1; i >= 0 && data[i].sleep < 6; i--) n++
    a.push({ id: 'a2', s: 'notice', n: `Sleep under 6 hours for ${n} night${n > 1 ? 's' : ''}`, m: `${x.sleep.toFixed(1)} h last night vs baseline 6.8 h`, q: 'What does low sleep mean for me?',
      rule: 'Notice when last night’s sleep is under 6 hours.' })
  }
  if (x.temp > 36.85)
    a.push({ id: 'a3', s: 'notice', n: 'Body temperature drifting upward', m: `${x.temp.toFixed(1)} °C vs baseline 36.7 °C`, q: 'What should I do next?',
      rule: 'Notice when body temperature is above 36.85 °C, 0.15 °C over baseline.' })
  return a
}

// ---- Demo scenarios (mutate D in place, like the prototype)
export type ScKey = 'all' | 'norm' | 'hr' | 'sleep'
export const LBL: Record<ScKey, string> = { all: 'Multiple alerts', norm: 'Normal', hr: 'Elevated heart rate', sleep: 'Poor sleep' }
const norm = () => D.forEach((d, i) => {
  Object.assign(d, D0[i])
  if (i >= 26) { d.hr = 62 + (i % 3); d.sleep = 6.8 - (i % 2) * 0.2; d.temp = 36.7 + (i % 3) * 0.05 }
})
export const SC: Record<ScKey, () => void> = {
  all: () => D.forEach((d, i) => Object.assign(d, D0[i])),
  norm,
  hr: () => { norm(); D.forEach((d, i) => { if (i >= 26) d.hr = 62 + (i - 25) * 4.2 }) },
  sleep: () => { norm(); D.forEach((d, i) => { if (i >= 27) d.sleep = 5.6 }) },
}

export const summary = (x: Reading) => {
  const p: string[] = []
  if (x.hr > HR_LIMIT) p.push(`resting heart rate is ${Math.round(x.hr - 62)} bpm above baseline`)
  if (x.sleep < 6) p.push(`sleep is under 6 hours (${x.sleep.toFixed(1)} h)`)
  if (x.temp > 36.85) p.push('body temperature is drifting upward')
  return p.length ? `Today, ${p.join(', ')}. The other readings stay in range.` : 'All tracked readings are in range and close to your baseline.'
}

// ---- Assistant (scripted demo; replace with the RAG pipeline)
export const KB = [
  { t: 'Sample entry 1: Cardiovascular adaptation in spaceflight', s: 'NASA (sample)' },
  { t: 'Sample entry 2: Sleep and circadian health on long missions', s: 'PubMed (sample)' },
  { t: 'Sample entry 3: Using personal baselines for crew health', s: 'NASA (sample)' },
]
export type Answer = { text: string; cites: number[]; known: boolean }
export const answer = (q: string, r: { hr: number; sleep: number } = { hr: D[29].hr, sleep: D[29].sleep }): Answer => {
  const l = q.toLowerCase(), hr = Math.round(r.hr)
  if (/\b(heart|pulse|bpm)\b/.test(l))
    return { known: true, cites: [0, 2], text: hr > HR_LIMIT
      ? `Your resting heart rate is ${hr} bpm, ${hr - 62} bpm above your baseline of 62 bpm. The Watch rule fires above ${HR_LIMIT} bpm, the top of your normal range. Cardiovascular change is a monitored area on long missions.`
      : `Your resting heart rate is ${hr} bpm, inside your normal range of 50 to 75 bpm, so no alert is active for it.` }
  if (/\bsleep/.test(l))
    return { known: true, cites: [1], text: r.sleep < 6
      ? `You slept ${r.sleep.toFixed(1)} hours last night, under the 6 hour limit. Short sleep can affect mood and attention, so it is flagged as a Notice. Recheck after a full rest period.`
      : `You slept ${r.sleep.toFixed(1)} hours last night, inside your normal range, so no sleep alert is active.` }
  if (/\bnext\b|what should i do|\bnow what\b/.test(l))
    return { known: true, cites: [2, 0], text: 'Recheck your readings after rest, review your sleep and exercise logs, and contact the flight surgeon if the pattern continues.' }
  return { known: false, cites: [], text: 'I can’t answer that from my current sources. Try asking about an alert or one of your health indicators.' }
}

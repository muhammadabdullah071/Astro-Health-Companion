# Astro-Health Companion (Next.js)

Next.js 15 (App Router, TypeScript) port of the single-file HTML prototype. Same design, same simulated data.

```bash
npm install
npm run dev                  # http://localhost:3000
npm run build && npm start   # production build (registers the service worker)
```

## Structure
- `src/app/` routes: `/`, `/dashboard`, `/alerts`, `/assistant`, `/status` (hash routes became real routes)
- `src/app/api/*` the "API contract v1": `status`, `profile`, `readings?days=`, `alerts`, `assistant/ask` (simulated data)
- `src/lib/data.ts` metrics, seeded dataset, alert rules, scripted assistant, demo scenarios. Replace with real data here.
- `src/lib/scene3d.ts` the 3D Earth / station / helmet scene (three@0.128 pinned so it looks identical)
- `src/components/` Shell (header, nav, palette, demo panel), AppProvider (theme, offline, scenarios), one component per screen
- `public/sw.js`, `manifest.webmanifest` basic offline + installable PWA

## Changed from the prototype
- Alerts show the rule that fired. Rule text and the 75 bpm threshold now agree (the prototype said "15 bpm above baseline" but fired at 75).
- Assistant keyword bug fixed (`/next|do/` matched any word containing "do"). Answers use the live reading.
- Daily summary and sleep-alert night count are computed, not hard-coded. Status page reads `/api/status`.
- "Simulated" pill is visible on mobile. ARIA: `aria-pressed` on tabs, live chat log, drawer focus + Esc.
- three.js is bundled from npm, not a CDN script.

## v3 additions
- "Built for long missions": 6 animated scenes (orbit, Moon, Mars transit, medical bay, solar storm, comms delay) with 3D coverflow, tilt-on-hover, swipe, dots, progress bar and orbit rings
- "Ready for liftoff?": animated panel (rotating glowing border, launching rockets, planet, twinkling stars)
- All buttons: lift, shine sweep, icon wiggle and arrow slide; alert "Ask the assistant" buttons have icons

## Still to do
- Real backend (FastAPI) and retrieval pipeline behind the 5 routes; real source excerpts in the drawer
- Fonts still load from Google Fonts. Switch to `next/font` or self-host for a fully offline first load
- "Attention" severity (CSS exists, no rule produces it); per-astronaut profiles and editable baselines
- Tests (alert rules, API), focus trap in palette/drawer, service worker tested in a real browser

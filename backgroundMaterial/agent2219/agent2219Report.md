# Agent 2219 Report: In-App Trail Routing, Home Location, Live Navigation & Itinerary

**Agent:** 2219
**Date:** 2026-06-10
**Task:** Replace external-maps "directions to trail start" with the in-app bike-route builder; add start/destination options (current location, map pin, saved per-user "home"); integrate live navigation with GPS ride recording; add a transit-style itinerary (order, icon, name, difficulty from Trailforks, length, connector distances).

---

## 1. Task Overview

The app had two disconnected features: a route builder (Map tab) and "Directions to trail start" buttons that bounced users out to Apple/Google Maps. This work unifies them: directions are now built in-app, routes can start/end at the rider's saved home, and a live navigation mode records the ride while showing position, route-so-far, and a bus-style trail itinerary.

## 2. Decomposition

Three parallel streams with strict file ownership (see `task_decomposition.md`):
- **M1 Data & Backend** — Trailforks difficulty research + export pipeline + DB migration
- **M2 Mobile Libs & UI** — home lib, itinerary component, shared ride recorder
- **M3 Catalogue Editor** — difficulty field in the docs editor (added mid-flight per user note)
- **Main Agent** — `routing.ts`, `index.tsx`, `trail/[id].tsx` (the interdependent integration files)

Cross-stream API contracts were fixed up front so all streams could run concurrently.

## 3. Execution Summary

| Manager | Stream | Sub-subagents | Iterations | Final Status |
|---------|--------|---------------|------------|--------------|
| M1 | Data & Backend | S1, S2 (difficulty research), S3 (pipeline/schema) | 2 (S2 re-run after coordinator interrupt; method switched to direct URL fetch per user) | Complete |
| M2 | Mobile Libs & UI | S1 (home), S2 (itinerary), S3 (recorder) | 1 | Complete |
| M3 | Catalogue editor | — (solo) | 1 | Complete |
| Main | Integration | — | 1 | Complete |

Mid-run events:
- User directed difficulty research to fetch each trail's `trailUrl` directly (WebFetch passes Trailforks' Cloudflare; local curl does not). Relayed via coordinator interrupt; the interrupt briefly aborted the coordinator, which recovered and completed.
- Main Agent integration audit found 5 researched difficulties (backbreaker, mistapiskihkoman, nicocwasaskanos, kakwa, oyoyow) missing from the catalogue merge; applied them and re-ran the export. Final coverage **36/38** (nulls: soniyawahkesis, coalminer_s_daughter — no Trailforks pages).

## 4. Deliverables

| Deliverable | Path | Description |
|-------------|------|-------------|
| Route builder rework | `mobile/src/app/(tabs)/index.tsx` | Start = My location / Home / map pin; destination = trail tap / map pin / Home; deep-link `?destTrail=<id>`; save-pin-as-home; navigation mode |
| In-app directions | `mobile/src/app/trail/[id].tsx` | "Directions to trail start" routes in-app; external maps kept as ghost button; difficulty stat |
| Progress helper | `mobile/src/lib/routing.ts` | `nearestLegIndex()` — projects GPS fix onto route legs |
| Itinerary UI | `mobile/src/components/route-itinerary.tsx` | `RouteItinerary` (transit-style legs list) + `DifficultyBadge` (green/blue/black/dblblack) |
| Home location | `mobile/src/lib/home.ts`, `profile.tsx` | AsyncStorage + Supabase profile sync; profile card to set/clear |
| Shared recorder | `mobile/src/lib/rides.ts`, `ride.tsx` | `sharedRecorder` singleton + `addListener`; map navigation and Ride tab share one recording |
| Difficulty pipeline | `tools/export_trails_for_app.py`, `docs/catalogue.json`, `mobile/src/data/trails.json`, `supabase/seed.sql` | `pageContent.trailforks.difficulty` → app + seed |
| DB migration | `supabase/migrations/0002_home_and_difficulty.sql` | `profiles.home_lat/home_lng`, `trails.difficulty` |
| Editor field | `docs/index.html` | Difficulty select in Trailforks panel (load/save wired) |
| Trail type | `mobile/src/lib/trails.ts` | `difficulty: string | null` |

## 5. Issues and Decisions

- Trailforks scraping is Cloudflare-blocked from local shell; agent WebFetch works → research method switched per user directive.
- Coordinator interrupt caused a transient abort; recovered with no lost work (children persisted independently).
- Catalogue merge gap (5 trails) caught at Main Agent quality gate; fixed at assembly.
- `openDirections` retained (user rule: never remove features) as a secondary "Open in external maps" action.
- Finishing a ride from the map's End-navigation flow saves as private; share-level prompt remains a Ride-tab flow.

## 6. Verification

- `npx tsc --noEmit`: clean (twice — post-team, post-assembly).
- Linter: no errors across all 9 touched app files.
- Contract greps: all signatures match; catalogue JSON intact (38 models, literal syllabics, 37 difficulty insertions).

## 7. Assessment

**Craftsperson says:** Contracts-first parallelization worked; all streams landed compatible on first integration, typecheck clean, difficulty data quoted verbatim from Trailforks pages.
**Skeptic says:** Connector legs are straight-line (pre-existing limitation, real router noted in `routing.ts`); `nearestLegIndex` can land on a suppressed (<25 m) connector row leaving no highlight momentarily; purgatory's dblblack is from a secondary editorial source; navigation is untested on a physical device.
**Mover says:** Shipped — the remaining risks are cosmetic or pre-existing; on-device testing and the migration push (`supabase db push` / apply 0002) are the natural next steps.

---

*Agent 2219 — 2026-06-10*

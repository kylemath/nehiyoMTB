# EdmontonTrailMaps (placeholder brand)

Cross-platform (iOS + Android) trail companion for the Edmonton river-valley sign
set, built with **Expo / React Native + TypeScript + Expo Router** on a
**Supabase** backend (Postgres, Auth, Storage, row-level security).

The app is name-agnostic: change `APP_NAME` in `src/constants/brand.ts` and the
`name`/`slug`/`scheme` in `app.json` when the real brand lands.

## Features

- **Map tab** — all signed trails as colored polylines (from the 3D-printed sign
  catalogue's GPX data), your live location, and one-tap cycling directions to
  any trail start via the native maps app.
- **Bike route builder** — pick a start and destination, set a max detour
  (1/2/5/10 km), and the app threads the route through as many trails as
  possible without exceeding the budget (cheapest-insertion; connectors are
  straight lines for now — designed so a real cycling router can drop in later).
- **Sign hunt (gamified)** — photograph the physical signs at trail starts and
  ends. Photos are GPS- and time-tagged; captures within 75 m of a sign are
  verified and earn points. Scores roll up overall / weekly / weekend, and the
  backend supports special events with point multipliers.
- **Trail timing from photos** — a start-sign photo plus an end-sign photo on
  the same ride yields your trail time (photo timestamps are the clock, so no
  live upload is needed; photo-taking overhead is the same for everyone).
- **Ride logging** — record the GPS track of a ride, export it as GPX, and sync
  photo timestamps against the track to detect photo stops and estimate
  riding-only speed.
- **Leaderboards** — overall, this-week, and weekend boards (points and names
  only — never photos or locations).
- **Auth** — Google, X (Twitter), or email via Supabase Auth, with persisted
  sessions. A no-account guest mode keeps everything on-device.

## Data-use model (the product promise)

Every photo and ride asks the user one question before anything leaves the
phone, with three honest answers (see `src/constants/brand.ts` and the matching
RLS policies in `../supabase/migrations/0001_init.sql`):

| Level | Meaning |
|---|---|
| `private` | Proof-of-arrival only. Visible to nobody but the owner. |
| `contribute` | Shared **only** with the trail-mapping team to improve Edmonton trail maps and wayfinding. Never public. |
| `public` | Visible to other signed-in riders (sign photo galleries, ride lists, time boards). Reversible. |

Offline-first: captures and rides are always saved locally first; upload is
opt-in and per-item.

## Getting started

```bash
cd mobile
npm install
cp .env.example .env   # optional — fill in Supabase keys to enable sync
npx expo start         # then press i (iOS simulator) or a (Android), or scan with Expo Go
```

Without `.env` the app runs fully offline in guest mode — map, hunt, points,
rides, and times all work; only accounts/sync/leaderboards are disabled.

## Backend setup (Supabase)

1. Create a project at supabase.com.
2. Apply `../supabase/migrations/0001_init.sql`, then `../supabase/seed.sql`
   (regenerate the seed with `python3 ../tools/export_trails_for_app.py`).
3. Enable Google and Twitter providers under Auth → Providers, adding
   `edmontontrailmaps://auth/callback` as a redirect URL.
4. Put the project URL + anon key in `mobile/.env`.

See `../supabase/README.md` for details.

## Trail data

`src/data/trails.json` is generated from `docs/catalogue.json` (the source of
truth for the 3D-printed sign set) by `tools/export_trails_for_app.py`. Re-run
it whenever trails/signs change; it also regenerates the database seed.

## Project layout

```
src/app/            expo-router routes (sign-in, tabs, capture modal, trail detail)
src/components/     shared minimalist UI kit + share-level picker
src/constants/      brand tokens & data-use copy (single rename point)
src/lib/            supabase client, auth, geo, routing, captures, rides
src/data/           generated trail dataset
```

## Native notes

- Maps use `react-native-maps` (Apple Maps on iOS, Google Maps on Android). For
  a standalone Android build add a Google Maps API key under
  `android.config.googleMaps.apiKey` in `app.json`.
- Camera, location, and secure storage permissions are declared in `app.json`
  with honest usage strings.

# NehiyoMTB trail app

Cross-platform (iOS, Android and web) trail companion for the Edmonton river-valley sign
set, built with **Expo / React Native + TypeScript + Expo Router** on a
**Supabase** backend (Postgres, Auth, Storage, row-level security).

The display name lives in `APP_NAME` (`src/constants/brand.ts`) and `name` in
`app.json`. The slug, URL scheme and bundle ids still say `edmontontrailmaps`;
renaming those re-keys the OAuth redirect and any store listing, so do it
deliberately.

The web build is published with the website at **nehiyomtb.ca/app**.

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
- **Ride logging** — record the GPS track of a ride (keeps recording with the
  screen locked on iOS/Android; see below), export it as GPX, and sync
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

`docs/catalogue.json` on the website is the single source of truth for the
sign set (the catalogue editor and sign tools write it). On every launch the
app applies the last catalogue it cached, then fetches
`https://nehiyomtb.ca/catalogue.json` and caches that (`src/lib/catalogue.ts`).
Signs pushed to the site therefore appear in the app without a new build;
icons for signs newer than the build load from the site.

`src/data/trails.json` and `assets/trail-icons/` are the bundled snapshot used
on first launch and offline. Refresh them before a store build with
`python3 tools/export_trails_for_app.py` (it also regenerates the database
seed). Set `EXPO_PUBLIC_SITE_URL` to point the app at another copy of the site.

## Web build (nehiyomtb.ca/app)

The same screens run in the browser; the map uses MapLibre (the website's map
library) via `src/components/map.web.tsx`. To publish:

```bash
cd mobile
npm run export:site    # writes the static build to ../docs/app
```

Commit `docs/app` and GitHub Pages serves it. `docs/404.html` boots the app
for deep links such as `/app/map` or `/app/trail/kahkakiw`. Put the Supabase
keys in `mobile/.env` before exporting if the web build should sync accounts.

## Project layout

```
src/app/            expo-router routes (sign-in, tabs, capture modal, trail detail)
src/components/     shared minimalist UI kit + share-level picker
src/constants/      brand tokens & data-use copy (single rename point)
src/lib/            supabase client, auth, geo, routing, captures, rides
src/data/           generated trail dataset
```

## Background ride recording and installing on a phone

Ride recording uses a background location task (`src/lib/rides.ts`), so the
track keeps filling with the phone locked: Android shows a "Recording your
ride" notification, iOS shows the blue location pill. Riders are asked to
allow location **all the time**; if they decline, recording still works while
the app is open. The in-progress ride is saved every few seconds, so a crash
or the OS killing the app never loses the ride.

Background location does **not** work in Expo Go or in the browser build
(browsers stop GPS when the screen locks; the web build keeps the screen awake
while recording instead). To test it, install a real build:

```bash
cd mobile
npx eas build -p android --profile preview   # installable .apk (needs a free Expo account)
# or, with Android Studio installed and a phone plugged in:
npx expo run:android
```

For iPhone, `npx expo run:ios` (Xcode) or an EAS build with an Apple
developer account.

## Native notes

- Maps use `react-native-maps` (Apple Maps on iOS, Google Maps on Android). For
  a standalone Android build add a Google Maps API key under
  `android.config.googleMaps.apiKey` in `app.json`.
- Camera, location, and secure storage permissions are declared in `app.json`
  with honest usage strings.

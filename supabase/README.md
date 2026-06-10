# EdmontonTrailMaps backend (Supabase)

Postgres schema, row-level security, and storage policies for the mobile app in
`../mobile`.

## Apply

With the [Supabase CLI](https://supabase.com/docs/guides/cli):

```bash
supabase link --project-ref <your-project-ref>
supabase db push          # applies migrations/
psql "$DATABASE_URL" -f seed.sql   # or paste seed.sql into the SQL editor
```

Or paste `migrations/0001_init.sql` then `seed.sql` into the dashboard SQL
editor. Regenerate `seed.sql` from the sign catalogue any time with:

```bash
python3 ../tools/export_trails_for_app.py
```

## Auth providers

Dashboard → Authentication → Providers:

- **Email** — enabled by default.
- **Google** — add OAuth client ID/secret.
- **Twitter (X)** — add API key/secret.

Add the app redirect URL under Authentication → URL Configuration:
`edmontontrailmaps://auth/callback`.

## Security model

- **RLS everywhere.** Reference data (`trails`, `signs`, `events`) is
  world-readable and only writable by the service role. All user data
  (`sign_captures`, `rides`, `ride_photos`, `trail_times`) is owner-writable,
  and readable by others **only** when its row is marked `public`.
- **Share levels** (`private` / `contribute` / `public`) are enforced in the
  database, not just the UI. `contribute` rows are intentionally invisible to
  other users — maintainers pull them with the service role for trail-mapping
  work, which is exactly what the app promises users.
- **Storage**: `photos` and `gpx` buckets are private; objects live under
  `<user_id>/...` and policies allow owners full access. A photo or GPX becomes
  readable by other signed-in users only while its database row is `public`.
- **Scoring is server-side.** A trigger verifies capture proximity (75 m
  default per sign), enforces one scored capture per sign per day, and applies
  event multipliers — clients can't award themselves points.
- **Leaderboard views** expose names and points only, never photos, paths, or
  coordinates.

## Extending the game

- Add rows to `events` for special weekends/trails with point multipliers.
- Per-sign `base_points` and `capture_radius_m` are tunable in `signs`.
- `trail_times` is ready for GPS-synced times (`source = 'synced'`) including
  estimated photo overhead.

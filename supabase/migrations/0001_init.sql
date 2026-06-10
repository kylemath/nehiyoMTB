-- EdmontonTrailMaps — initial schema
-- Postgres + Supabase (auth, storage, RLS)

-- ---------------------------------------------------------------------------
-- Enums
-- ---------------------------------------------------------------------------

-- Three-tier data-use decision, surfaced verbatim in the app UI:
--   private    -> visible only to the owner (proof-of-arrival, never shared)
--   contribute -> shared with trail-system maintainers only, to improve
--                 Edmonton trail mapping / wayfinding (the "middle ground")
--   public     -> visible to all signed-in users
create type public.share_level as enum ('private', 'contribute', 'public');

create type public.sign_kind as enum ('start', 'end');

create type public.time_source as enum ('photos', 'gps', 'synced');

-- ---------------------------------------------------------------------------
-- Profiles
-- ---------------------------------------------------------------------------

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  username text unique check (username ~ '^[a-z0-9_]{3,24}$'),
  display_name text,
  avatar_url text,
  -- The user's default answer for new uploads; every upload can override it.
  default_share_level public.share_level not null default 'private',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

create policy "profiles are readable by signed-in users"
  on public.profiles for select to authenticated using (true);

create policy "users manage own profile"
  on public.profiles for all to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

-- Auto-create a profile row on signup.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, display_name, avatar_url)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    new.raw_user_meta_data->>'avatar_url'
  );
  return new;
end; $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------------------------------------------------------------------------
-- Trails & signs (reference data; written only by service role / migrations)
-- ---------------------------------------------------------------------------

create table public.trails (
  id text primary key,                 -- slug, e.g. 'walters_folly'
  sign_number int,
  title text not null,
  english_name text,
  cree_name text,
  cree_syllabics text,
  start_lat double precision,
  start_lng double precision,
  end_lat double precision,
  end_lng double precision,
  length_m double precision,
  track jsonb,                         -- [[lat,lng], ...] simplified polyline
  icon_url text,
  status text not null default 'published',
  created_at timestamptz not null default now()
);

alter table public.trails enable row level security;

create policy "trails are public reference data"
  on public.trails for select using (true);

create table public.signs (
  id text primary key,                 -- '<trail_id>:start' | '<trail_id>:end'
  trail_id text not null references public.trails (id) on delete cascade,
  kind public.sign_kind not null,
  lat double precision not null,
  lng double precision not null,
  base_points int not null default 10,
  -- How close (m) a tagged photo must be to count as verified.
  capture_radius_m int not null default 75,
  active boolean not null default true,
  unique (trail_id, kind)
);

alter table public.signs enable row level security;

create policy "signs are public reference data"
  on public.signs for select using (true);

-- Special events / games: a points multiplier on chosen trails for a window.
create table public.events (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  multiplier numeric not null default 2.0,
  trail_ids text[] not null default '{}',  -- empty array = all trails
  created_at timestamptz not null default now()
);

alter table public.events enable row level security;

create policy "events are public reference data"
  on public.events for select using (true);

-- ---------------------------------------------------------------------------
-- Sign captures (the treasure hunt)
-- ---------------------------------------------------------------------------

create table public.sign_captures (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  sign_id text not null references public.signs (id),
  -- Timestamp embedded in the photo (EXIF) — the authoritative game clock.
  captured_at timestamptz not null,
  device_lat double precision,
  device_lng double precision,
  accuracy_m double precision,
  -- Storage object path in the 'photos' bucket; null if user kept photo
  -- on-device only (location proof can still be recorded).
  photo_path text,
  share_level public.share_level not null default 'private',
  verified boolean not null default false,   -- set by trigger (distance check)
  points_awarded int not null default 0,     -- set by trigger
  created_at timestamptz not null default now()
);

create index sign_captures_user_idx on public.sign_captures (user_id, captured_at);
create index sign_captures_sign_idx on public.sign_captures (sign_id);

alter table public.sign_captures enable row level security;

create policy "users manage own captures"
  on public.sign_captures for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "public captures readable by signed-in users"
  on public.sign_captures for select to authenticated
  using (share_level = 'public');

-- Haversine distance in metres.
create or replace function public.haversine_m(
  lat1 double precision, lng1 double precision,
  lat2 double precision, lng2 double precision
) returns double precision language sql immutable as $$
  select 2 * 6371000 * asin(sqrt(
    sin(radians(lat2 - lat1) / 2) ^ 2 +
    cos(radians(lat1)) * cos(radians(lat2)) *
    sin(radians(lng2 - lng1) / 2) ^ 2
  ));
$$;

-- Server-side scoring: verify proximity, apply event multipliers, and award
-- points exactly once per (user, sign, calendar day).
create or replace function public.score_sign_capture()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  s public.signs%rowtype;
  dist double precision;
  mult numeric := 1.0;
  already int;
begin
  select * into s from public.signs where id = new.sign_id;

  if new.device_lat is not null and new.device_lng is not null then
    dist := public.haversine_m(new.device_lat, new.device_lng, s.lat, s.lng);
    new.verified := dist <= s.capture_radius_m;
  else
    new.verified := false;
  end if;

  select count(*) into already
  from public.sign_captures
  where user_id = new.user_id
    and sign_id = new.sign_id
    and captured_at::date = new.captured_at::date;

  if new.verified and already = 0 then
    select coalesce(max(multiplier), 1.0) into mult
    from public.events e
    where new.captured_at between e.starts_at and e.ends_at
      and (e.trail_ids = '{}' or s.trail_id = any (e.trail_ids));
    new.points_awarded := round(s.base_points * mult);
  else
    new.points_awarded := 0;
  end if;

  return new;
end; $$;

create trigger score_sign_capture
  before insert on public.sign_captures
  for each row execute function public.score_sign_capture();

-- ---------------------------------------------------------------------------
-- Rides & ride photos
-- ---------------------------------------------------------------------------

create table public.rides (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  started_at timestamptz not null,
  ended_at timestamptz,
  distance_m double precision,
  -- Storage object path of the recorded GPX in the 'gpx' bucket.
  gpx_path text,
  share_level public.share_level not null default 'private',
  created_at timestamptz not null default now()
);

create index rides_user_idx on public.rides (user_id, started_at);

alter table public.rides enable row level security;

create policy "users manage own rides"
  on public.rides for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "public rides readable by signed-in users"
  on public.rides for select to authenticated
  using (share_level = 'public');

create table public.ride_photos (
  id uuid primary key default gen_random_uuid(),
  ride_id uuid not null references public.rides (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  capture_id uuid references public.sign_captures (id) on delete set null,
  photo_path text,
  taken_at timestamptz not null,
  lat double precision,
  lng double precision,
  share_level public.share_level not null default 'private'
);

alter table public.ride_photos enable row level security;

create policy "users manage own ride photos"
  on public.ride_photos for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "public ride photos readable by signed-in users"
  on public.ride_photos for select to authenticated
  using (share_level = 'public');

-- ---------------------------------------------------------------------------
-- Trail times (start-sign photo -> end-sign photo on the same ride)
-- ---------------------------------------------------------------------------

create table public.trail_times (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  trail_id text not null references public.trails (id),
  ride_id uuid references public.rides (id) on delete set null,
  start_capture_id uuid references public.sign_captures (id),
  end_capture_id uuid references public.sign_captures (id),
  elapsed_s int not null check (elapsed_s > 0),
  -- Estimated seconds spent stopped taking photos (from GPS/photo sync);
  -- the same overhead applies to everyone, but we record it for transparency.
  photo_overhead_s int,
  source public.time_source not null default 'photos',
  share_level public.share_level not null default 'private',
  created_at timestamptz not null default now()
);

create index trail_times_trail_idx on public.trail_times (trail_id, elapsed_s);

alter table public.trail_times enable row level security;

create policy "users manage own trail times"
  on public.trail_times for all to authenticated
  using (user_id = auth.uid()) with check (user_id = auth.uid());

create policy "public trail times readable by signed-in users"
  on public.trail_times for select to authenticated
  using (share_level = 'public');

-- ---------------------------------------------------------------------------
-- Leaderboards
-- Aggregated points only — never exposes photo paths or raw GPS, regardless
-- of share level, because points are not location data.
-- ---------------------------------------------------------------------------

create or replace view public.leaderboard_overall
with (security_invoker = off) as
select
  p.id as user_id,
  coalesce(p.username, p.display_name, 'rider') as name,
  sum(c.points_awarded)::int as points,
  count(*) filter (where c.points_awarded > 0)::int as captures
from public.sign_captures c
join public.profiles p on p.id = c.user_id
group by p.id, p.username, p.display_name;

create or replace view public.leaderboard_weekly
with (security_invoker = off) as
select
  p.id as user_id,
  coalesce(p.username, p.display_name, 'rider') as name,
  sum(c.points_awarded)::int as points,
  count(*) filter (where c.points_awarded > 0)::int as captures
from public.sign_captures c
join public.profiles p on p.id = c.user_id
where c.captured_at >= date_trunc('week', now())
group by p.id, p.username, p.display_name;

create or replace view public.leaderboard_weekend
with (security_invoker = off) as
select
  p.id as user_id,
  coalesce(p.username, p.display_name, 'rider') as name,
  sum(c.points_awarded)::int as points,
  count(*) filter (where c.points_awarded > 0)::int as captures
from public.sign_captures c
join public.profiles p on p.id = c.user_id
where c.captured_at >= date_trunc('week', now())
  and extract(isodow from c.captured_at) in (6, 7)
group by p.id, p.username, p.display_name;

grant select on public.leaderboard_overall,
                public.leaderboard_weekly,
                public.leaderboard_weekend
to authenticated;

-- Fastest public times per trail.
create or replace view public.trail_time_board
with (security_invoker = on) as
select
  t.trail_id,
  tr.title,
  coalesce(p.username, p.display_name, 'rider') as name,
  t.elapsed_s,
  t.source,
  t.created_at
from public.trail_times t
join public.trails tr on tr.id = t.trail_id
join public.profiles p on p.id = t.user_id
where t.share_level = 'public';

grant select on public.trail_time_board to authenticated;

-- ---------------------------------------------------------------------------
-- Storage buckets & policies
-- ---------------------------------------------------------------------------

insert into storage.buckets (id, name, public) values
  ('photos', 'photos', false),
  ('gpx', 'gpx', false)
on conflict (id) do nothing;

-- Objects live at '<user_id>/<filename>' so ownership is enforced by path.
create policy "users write own photos"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'photos' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users read own photos"
  on storage.objects for select to authenticated
  using (bucket_id = 'photos' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users delete own photos"
  on storage.objects for delete to authenticated
  using (bucket_id = 'photos' and (storage.foldername(name))[1] = auth.uid()::text);

-- Photos attached to a *public* capture are readable by signed-in users,
-- powering the per-sign community photo galleries.
create policy "public capture photos readable"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'photos'
    and exists (
      select 1 from public.sign_captures c
      where c.photo_path = name and c.share_level = 'public'
    )
  );

create policy "users write own gpx"
  on storage.objects for insert to authenticated
  with check (bucket_id = 'gpx' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users read own gpx"
  on storage.objects for select to authenticated
  using (bucket_id = 'gpx' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "users delete own gpx"
  on storage.objects for delete to authenticated
  using (bucket_id = 'gpx' and (storage.foldername(name))[1] = auth.uid()::text);

create policy "public ride gpx readable"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'gpx'
    and exists (
      select 1 from public.rides r
      where r.gpx_path = name and r.share_level = 'public'
    )
  );

-- NOTE: 'contribute'-level photos and GPX are intentionally *not* readable by
-- other users. Maintainers access them with the service role for trail-system
-- mapping, exactly as described to the user at upload time.

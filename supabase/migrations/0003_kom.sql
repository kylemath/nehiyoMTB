-- NehiyoMTB — per-trail KOM (King/Queen of the Mountain) board + rewards
--
-- The top three riders on each trail can order the KOM edition of that
-- trail's sign for free. Ranks are computed ONLY from server-verified sign
-- captures (the score_sign_capture trigger checks the photo was taken within
-- the sign's capture radius), never from client-submitted trail_times, so a
-- rider can't type in a fast time.

-- ---------------------------------------------------------------------------
-- Verified runs: a verified start-sign capture followed by a verified
-- end-sign capture of the same trail by the same rider, within 3 hours.
-- Each start pairs with the first end after it. Implausibly fast runs
-- (average over 15 m/s ≈ 54 km/h) are dropped.
-- ---------------------------------------------------------------------------

create or replace view public.trail_verified_runs
with (security_invoker = off) as
select
  st.trail_id,
  s.user_id,
  s.id as start_capture_id,
  e.id as end_capture_id,
  s.captured_at as started_at,
  extract(epoch from (e.captured_at - s.captured_at))::int as elapsed_s
from public.sign_captures s
join public.signs st on st.id = s.sign_id and st.kind = 'start'
join lateral (
  select c.id, c.captured_at
  from public.sign_captures c
  join public.signs en on en.id = c.sign_id
  where en.trail_id = st.trail_id
    and en.kind = 'end'
    and c.user_id = s.user_id
    and c.verified
    and c.captured_at > s.captured_at
    and c.captured_at <= s.captured_at + interval '3 hours'
  order by c.captured_at
  limit 1
) e on true
join public.trails t on t.id = st.trail_id
where s.verified
  and (t.length_m is null
       or extract(epoch from (e.captured_at - s.captured_at)) >= t.length_m / 15.0);

revoke all on public.trail_verified_runs from anon, authenticated;

-- Best run per rider per trail, ranked. Exposes names and times only (no
-- photos or coordinates), like the points leaderboards.
create or replace view public.trail_kom_board
with (security_invoker = off) as
with best as (
  select distinct on (trail_id, user_id)
    trail_id, user_id, elapsed_s, started_at
  from public.trail_verified_runs
  order by trail_id, user_id, elapsed_s, started_at
)
select
  b.trail_id,
  b.user_id,
  coalesce(p.username, p.display_name, 'rider') as name,
  b.elapsed_s,
  b.started_at::date as ridden_on,
  rank() over (partition by b.trail_id order by b.elapsed_s, b.started_at)::int as rank
from best b
join public.profiles p on p.id = b.user_id;

grant select on public.trail_kom_board to authenticated;

-- ---------------------------------------------------------------------------
-- Rewards: one free KOM sign per rider per trail. Written only by the
-- claim-kom edge function (service role); riders can read their own.
-- ---------------------------------------------------------------------------

create table public.kom_rewards (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  trail_id text not null references public.trails (id),
  rank int not null,
  elapsed_s int not null,
  start_capture_id uuid references public.sign_captures (id),
  end_capture_id uuid references public.sign_captures (id),
  discount_code text not null,
  shopify_discount_id text,
  created_at timestamptz not null default now(),
  unique (user_id, trail_id)
);

alter table public.kom_rewards enable row level security;

create policy "riders read own kom rewards"
  on public.kom_rewards for select to authenticated
  using (user_id = auth.uid());

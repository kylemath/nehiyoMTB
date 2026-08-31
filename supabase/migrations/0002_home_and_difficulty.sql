-- EdmontonTrailMaps — home location + trail difficulty

-- ---------------------------------------------------------------------------
-- Profiles: optional home/staging location
-- ---------------------------------------------------------------------------

-- Where the rider usually starts from (e.g. their house or a trailhead
-- parking lot); used as the default origin for route planning.
alter table public.profiles add column home_lat double precision;
alter table public.profiles add column home_lng double precision;

-- ---------------------------------------------------------------------------
-- Trails: Trailforks difficulty rating
-- ---------------------------------------------------------------------------

-- Difficulty token sourced from Trailforks:
--   'green' | 'blue' | 'black' | 'dblblack', null when unrated.
alter table public.trails add column difficulty text;

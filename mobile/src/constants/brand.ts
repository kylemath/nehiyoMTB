/**
 * Brand tokens. The app is name-agnostic: change APP_NAME (and app.json
 * name/slug/scheme) when the real brand lands and everything follows.
 */
export const APP_NAME = 'EdmontonTrailMaps'; // placeholder brand
export const APP_TAGLINE = 'Ride. Find. Collect.';

export const Brand = {
  /** Deep pine — primary actions, trail lines */
  pine: '#1E5E46',
  /** Bright trail green — highlights, active states */
  moss: '#2E8B68',
  /** Warm sign amber — points, badges, treasure hunt */
  amber: '#E8A13C',
  /** Signal red — record button, alerts */
  ember: '#D9534F',
  /** Near-black ink and paper white for the minimalist base */
  ink: '#101512',
  paper: '#FAFAF7',
  /** Muted text */
  stone: '#6B7470',
  /** Hairline borders / dividers */
  mist: '#E4E7E3',
  /** Dark-mode surfaces */
  night: '#161B18',
  nightElement: '#222926',
} as const;

export const SHARE_LEVELS = ['private', 'contribute', 'public'] as const;
export type ShareLevel = (typeof SHARE_LEVELS)[number];

/** Shown verbatim wherever the user picks a share level — the app's data-use
 * promise in plain words. Keep these honest and in sync with backend policy
 * (see supabase/migrations/0001_init.sql). */
export const SHARE_LEVEL_INFO: Record<
  ShareLevel,
  { label: string; summary: string; detail: string }
> = {
  private: {
    label: 'Just for me',
    summary: 'Stays on your account. Nobody else can ever see it.',
    detail:
      'Stored privately as your proof of arrival. Not visible to other riders, not used for trail mapping. You can delete it any time.',
  },
  contribute: {
    label: 'Contribute to the trails',
    summary: 'Shared only with the trail-mapping team, never publicly.',
    detail:
      'Your GPX tracks and sign photos help improve Edmonton trail maps and wayfinding. Only the maintainers can access them; they are never shown to other riders and never sold.',
  },
  public: {
    label: 'Share with riders',
    summary: 'Visible to other signed-in riders in the app.',
    detail:
      'Appears in sign photo galleries, public ride lists and time boards. Includes the photo location and time. You can switch it back to private any time.',
  },
};

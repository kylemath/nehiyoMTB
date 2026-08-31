# S1 Report — Home Location (Sub-subagent S1, Manager M2, Coordinator 2219-C)

## What changed

| File | Change |
| --- | --- |
| `mobile/src/lib/home.ts` | NEW. Home-location library: `HomeLocation` type, `getHome`, `setHome`, `pullHomeFromProfile`. AsyncStorage key `etm.home.v1`, best-effort Supabase profile sync (`profiles.home_lat` / `home_lng`). |
| `mobile/src/app/(tabs)/profile.tsx` | Added a "Home location" card between the account card and the share-default card. Shows saved coords (5 decimals) or "Not set yet", a "Set to current location" button (expo-location foreground permission + `getCurrentPositionAsync`, matching `capture.tsx` / `index.tsx` patterns), a "Clear" button shown only when set, and copy noting home can also be set from a map pin in the route builder. `pullHomeFromProfile()` runs on mount. |

No other files touched (verified with `git status --porcelain` on owned files: only `M profile.tsx` and `?? home.ts`).

## Acceptance evidence

1. **Contract signatures** — `home.ts` exports exactly: `export type HomeLocation = { latitude: number; longitude: number }`, `export async function getHome(): Promise<HomeLocation | null>`, `export async function setHome(loc: HomeLocation | null): Promise<void>`, `export async function pullHomeFromProfile(): Promise<HomeLocation | null>`. Key constant is `'etm.home.v1'`.
2. **`setHome(null)` clears both stores** — null branch calls `AsyncStorage.removeItem(HOME_KEY)`, then (when `backendConfigured` and a session exists) updates `profiles` with `home_lat: null, home_lng: null` via `loc?.latitude ?? null`.
3. **No throws on network failure** — every Supabase interaction is inside `try/catch`; `getHome` also catches storage/JSON errors and returns null. Guest/offline: `backendConfigured` short-circuits before any network call; no session short-circuits the profile update/select. All paths resolve with the local value.
4. **Profile card** — card renders unconditionally (works for guests); coords shown with `.toFixed(5)`; "Set to current location" uses `Location.requestForegroundPermissionsAsync()` then `Location.getCurrentPositionAsync({})` (same pattern as `index.tsx` `ensureLocation`); permission denial shows an Alert instead of failing silently; "Clear" renders only when `home` is set; copy mentions the route-builder map pin. All pre-existing profile content (account card, share-level picker, data-policy card, sign-out button) untouched.
5. **File ownership** — only `mobile/src/lib/home.ts` (new) and `mobile/src/app/(tabs)/profile.tsx` (modified) changed.
6. **TypeScript clean** — `npx tsc --noEmit` in `mobile/` reports exactly one error, in `src/lib/trails.ts` (missing `difficulty` on `Trail` — M1's mid-edit, explicitly out of scope). Zero errors trace to `home.ts` or `profile.tsx`; workspace lints on both files are clean.

## Self-assessment

- **Craftsperson says:** The library mirrors the repo's established patterns exactly — AsyncStorage usage and key naming follow `auth.tsx` (`etm.guestMode.v1`), the profile update follows the existing `default_share_level` flow in `profile.tsx`, the location flow copies `capture.tsx`/`index.tsx`. The contract is implemented verbatim, so the Main Agent's route-builder code will link against it without friction.
- **Skeptic says:** `pullHomeFromProfile` treats remote as authoritative when both exist; if a guest sets home locally and then signs in to an account with an older remote home, the remote wins on next pull. There's no conflict timestamp — acceptable per spec ("return best value") but worth knowing. Also, the `profiles` row's `home_lat/home_lng` columns come from M1's migration `0002`; until that migration is applied, the update/select will error — which is caught and degrades to local-only, but sync silently no-ops. `getCurrentPositionAsync({})` uses default accuracy; home doesn't need High accuracy, so that's fine.
- **Mover says:** All six acceptance criteria are met with concrete evidence, the failure modes degrade gracefully by design, and the contract is frozen, so iterating further risks divergence from what the Main Agent is coding against. Shipping. With more time I'd add a last-write-wins timestamp to home sync and a small unit test for the JSON-parse guard.

# S3 Report — Shared Ride Recorder

**Agent:** Sub-subagent S3 (Shared Recorder), Manager M2, Coordinator 2219-C
**Date:** 2026-06-10

## What changed

### `mobile/src/lib/rides.ts`
- Added a private `listeners = new Set<(ride: LocalRide) => void>()` to `RideRecorder`.
- Added `addListener(fn): () => void` — registers a listener and returns an unsubscribe function that removes it from the set.
- Added a private `notify(ride)` helper that invokes the legacy `onUpdate` callback first, then every registered listener; the GPS watch callback now calls `this.notify(this.ride)` per fix instead of `this.onUpdate?.(this.ride)`.
- Exported `export const sharedRecorder = new RideRecorder()` at module level so live navigation and the Ride tab observe a single recording.

### `mobile/src/app/(tabs)/ride.tsx`
- `recorderRef` is now `useRef(sharedRecorder)` (the `RideRecorder` import was replaced with `sharedRecorder`; the ref pattern is preserved).
- `refresh` now also derives state from the shared recorder: `setRecording(recorderRef.current.ride != null)` and seeds `live` from the in-progress ride, so a recording started by live navigation appears when the tab gains focus.
- `useFocusEffect` wraps a `useCallback` that calls `refresh()`, subscribes via `recorderRef.current.addListener(...)` (updating `live` and forcing `recording` true on each fix), and returns the unsubscribe function as cleanup — no more overwriting `onUpdate`.
- `start()` no longer assigns `onUpdate`; live updates flow through the focus-scoped listener.
- Everything else (stop/pending-share flow, GPX export, upload, photo sync, trail times) untouched.

## Acceptance evidence

1. **`sharedRecorder` module-level singleton** — bottom of `mobile/src/lib/rides.ts`: `export const sharedRecorder = new RideRecorder();` (exact signature from the fixed contract).
2. **`addListener` + legacy `onUpdate`** — `addListener(fn: (ride: LocalRide) => void): () => void` adds to the `Set` and returns `() => { this.listeners.delete(fn); }`. `notify()` fires `this.onUpdate?.(ride)` and then iterates all listeners, so multiple listeners plus `onUpdate` all fire per GPS fix. A `Set` also makes double-registration and double-unsubscribe harmless.
3. **Ride tab behavior** — `ride.tsx` uses `useRef(sharedRecorder)`; `useFocusEffect(useCallback(...))` subscribes on focus and returns the unsubscribe for cleanup on blur/unmount; `refresh()` derives `recording` from `recorderRef.current.ride != null`, so a navigation-started recording shows the running timer/distance card on focus. The 1-second elapsed timer computes from `ride.startedAt`, so it is correct even for externally started recordings.
4. **Existing features intact** — `exportGpx` (Share of `rideToGpx`), `uploadRide` button, `syncPhotosWithRide` / `PhotoSyncSummary`, pending-ride share-level confirm flow, trail times, and past-rides list are all unchanged.
5. **File ownership** — `git status` on the two owned paths shows only `mobile/src/lib/rides.ts` and `mobile/src/app/(tabs)/ride.tsx` modified by this task; no other files were touched.
6. **TypeScript clean** — `npx tsc --noEmit` in `mobile/` reports only the known M1 mid-edit error (`difficulty` missing on `Trail` in `src/lib/trails.ts`). Zero errors trace to `rides.ts` or `ride.tsx`; IDE lints on both files are clean.

## Self-assessment

- **Craftsperson says:** The change is minimal and surgical — a Set-backed observer added to an existing class with one call-site change (`onUpdate?.()` → `notify()`), and the tab converted from owner to observer of the singleton. The focus-effect subscribe/unsubscribe pairing follows the standard expo-router `useFocusEffect` cleanup contract, and seeding `live` in `refresh()` means the UI is correct immediately on focus, not just after the next GPS fix.
- **Skeptic says:** The listener sets `recording` true on every fix, which is slightly redundant after the first fix, but it covers the case where navigation starts a recording while the Ride tab is already focused (no focus event fires then). `stop()` from the Ride tab while navigation is also listening means navigation listeners simply stop receiving fixes — acceptable, but the Main Agent should be aware that either side can stop the shared recording. I could not runtime-test GPS flow in this environment; verification is static (types, lints, code reading).
- **Mover says:** The contract is implemented exactly as specified, type-checks clean, and touches only owned files — shipping. With more time I'd add a `start`/`stop` lifecycle event to the listener API so observers don't have to poll `ride != null`, but that would change the fixed contract, so it's flagged for M2 rather than done.

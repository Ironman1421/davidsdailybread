# Phase 1 PWA quality review

Status: local browser review completed; native-device and release gates remain

Reviewed: 2026-08-04, beginning at PR #48 head `6cbe9a8`

Publication, deployment, provider mutation, live personal-data collection,
notification activation, and merge were outside this review and did not occur.

## Review environment

- Local-only HTTP origin at `127.0.0.1`; no public preview was created.
- Chromium desktop viewport at 1280 by 720.
- Responsive viewports at 390 by 844, 412 by 915, and the 320-pixel reflow
  boundary.
- Canonical archive, offline fallback, Tool Shelf, and Workflows surfaces.
- A temporary untracked server copy supplied one correction marker. It never
  changed the repository or canonical content.

Viewport checks are useful browser evidence, not substitutes for native Safari,
native Android Chrome, VoiceOver, or TalkBack.

## Passed locally

- The intended surfaces expose one manifest, one install launcher, one hidden
  install region, the approved theme, and no horizontal overflow at the tested
  desktop and mobile widths.
- The install panel states the complete morning, evening Field Guide, and
  **Loved by God** distinction. Opening it moves focus to the primary action;
  closing it returns focus to the launcher.
- The launcher and panel actions are semantic buttons. The final launcher and
  new offline-note targets measure at least 44 pixels high.
- Existing archive notes persisted through a reload and cleared through the
  existing control. The PWA layer did not migrate or delete them. Offline-page
  note font selection persisted and was reset after review.
- With the local server stopped, a cached archive reopened and an uncached URL
  received `/offline.html` while retaining the requested URL. The fallback
  carried the masthead, canonical links, notes, and full product distinction.
- A waiting worker left the active shell in place, presented a reader-controlled
  refresh action, stated that notes remain on the device, and reloaded only after
  that action.
- A network-delivered correction marker replaced the cached archive, remained
  available offline, and was replaced by the restored canonical network copy on
  the next online navigation.
- Tool Shelf and Workflows loaded at the 412-pixel viewport with their search
  controls, 22 and 14 catalog cards respectively, the install control, and no
  horizontal overflow.
- Browser console inspection reported no warnings or errors on the final
  desktop archive surface.

## Safe defects fixed during review

1. Canonical network-first fetches could still be satisfied by the browser HTTP
   cache. They now use `cache: "no-store"` before writing a successful response
   to bounded Cache Storage.
2. A changed worker reused the prior shell-cache name, and shell installation
   could reuse stale HTTP-cache assets. Cache generation `v2` now installs shell
   assets through `Request(..., { cache: "reload" })` and deletes only older
   app-owned cache generations after activation.
3. The new install launcher was about 18 pixels high, and panel actions were 40
   pixels high. The launcher, panel actions, and new offline-note controls now
   use 44-pixel minimum targets.

## Remaining release gates

- Install, launch, update, and offline review in physical iPhone Safari.
- Install, launch, update, and offline review in physical Android Chrome.
- VoiceOver and TalkBack reading order, control names, and focus review.
- Manual keyboard activation and 200-percent text/zoom review in a shipping
  browser. The automation harness verified focus but did not dispatch native
  Enter or Space button activation reliably.
- A normal non-publishing bake preview confirming generated home, category, and
  edition pages receive PWA wiring from templates. Historical editions must not
  be rewritten.
- CI on the exact follow-up commit and David's separate approval of the exact
  release and rollback. This record does not authorize merge or deployment.

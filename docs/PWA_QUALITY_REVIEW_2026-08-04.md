# Phase 1 PWA quality review

Status: local browser, physical iPhone install/launch, and isolated normal-bake
preview completed; secure-origin, Android, full screen-reader, and release gates
remain

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

## Physical iPhone Safari follow-up

Reviewed on 2026-08-04 at exact PR head
`feaf4ab6093e4fedca449983dd19addaa99c1ad5` using a paired physical
"iPhone 16" and Safari. The repository was served only on the private local
network over HTTP. The temporary server was stopped after the review; no public
preview, deployment, provider mutation, or production write occurred.

Passed on the physical handset:

- The PWA-wired canonical archive requested `/manifest.webmanifest`,
  `/pwa.css`, and `/pwa.js` from the exact working tree.
- The in-publication install launcher opened the app panel with the complete
  morning, evening Field Guide, and **Loved by God** distinction. Its controls
  remained comfortably touchable and the status supplied the correct Safari
  Share then Add to Home Screen instructions.
- Safari's native Add to Home Screen sheet used the manifest name `Daily Bread`,
  the approved bread icon, the root start URL, and **Open as Web App** mode.
- Spotlight found the installed `Daily Bread` app with the approved icon. It
  launched the current canonical homepage in standalone mode without Safari
  browser chrome.
- VoiceOver was enabled on the physical handset while the canonical archive and
  install panel were open. The layout remained stable and the semantic controls
  remained available. VoiceOver, Large Cursor, Caption Panel, and Speak Under
  Pointer were restored to their original off state after the review.

Material limits observed:

- The preserved August 4 generated homepage predates this branch's PWA template
  wiring. It does not yet request the manifest or PWA script. The installed app
  can display that canonical homepage, but the normal non-publishing bake gate
  must prove that newly generated home, category, and edition pages inherit the
  wiring without rewriting historical editions.
- A private-LAN HTTP address is not a trustworthy service-worker origin on
  iPhone. No `/service-worker.js` request occurred. With the temporary server
  stopped, an uncached navigation from the installed app received Safari's
  unable-to-connect screen rather than an offline page. Physical worker update,
  correction refresh, and offline recovery therefore remain untested; the
  server was restarted briefly to restore the app and then stopped.
- iPhone Mirroring did not expose dependable spoken output or reproduce native
  touch exploration and double-tap activation. A full VoiceOver reading-order,
  control-name, focus, and rotor audit was not claimed.
- No physical Android handset was available, so Android Chrome and TalkBack were
  not tested or simulated.

## Normal non-publishing bake preview

Reviewed on 2026-08-04 at exact PR head
`93ce1574da29b7a7865143d50b6aa42bece712a4`. The normal daily renderer was
invoked for both slots in an automatically deleted copy of the repository. It
used far-future fixture dates and no network. It did not invoke the local test
suite, rewrite a real edition, or modify the working tree.

- The morning daily path rendered the homepage, morning edition, all three
  category pages, archive, feed, archive JSON, and reader-state bookkeeping.
  Its plan kept intake `paused`, Ask the Baker and Crumb Board empty, and used
  only the reviewed house-satchel path.
- The evening daily path rendered the homepage, evening edition, archive, feed,
  archive JSON, and bounded evening catalog. It did not write morning category
  pages or reader state.
- The generated morning homepage, morning edition, three category pages,
  evening homepage, evening edition, and archive all carried the manifest,
  PWA stylesheet, Apple web-app metadata, and PWA script from the templates.
- Both far-future edition records retained the canonical
  `editions/YYYY-MM-DD-slot.html` archive paths.
- Tracked-file hashes and targeted canonical-output hashes matched before and
  after the preview. The real working tree remained clean.

This satisfies the normal non-publishing bake gate. It does not substitute for
CI and does not make the current generated homepage PWA-enabled before a future
authorized bake or release.

## Private HTTPS preview decision

A narrowly scoped Tailscale Serve preview is the preferred remaining physical
iPhone path, but it is not authorized by this review. Read-only checks found
the paired Mac and iPhone online in the same existing tailnet and an empty Serve
configuration on the Mac. Tailscale Serve can proxy a loopback-only local HTTP
server over tailnet-only HTTPS in the foreground; Tailscale Funnel is not
needed and must remain unused.

The tailnet does not currently advertise certificate domains. Enabling HTTPS
is therefore a provider mutation and requires David's separate approval.
Tailscale also documents that the device and tailnet certificate hostname is
recorded in the public Certificate Transparency ledger. Preview content and
access remain tailnet-private, but that hostname disclosure is not temporary.
No HTTPS feature, certificate, Serve route, or preview server was enabled as
part of this decision.

References: [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve)
and [Enabling HTTPS](https://tailscale.com/docs/how-to/set-up-https-certificates).

If approved, the review must use only exact head
`93ce1574da29b7a7865143d50b6aa42bece712a4`, bind the backend to loopback, run
Serve in the foreground, verify install/update/correction/offline behavior on
the physical iPhone, and then stop both processes and confirm the Serve
configuration is empty. It must not use Funnel, the Spark, background serving,
deployment, public intake, production data, or repository writes.

## Remaining release gates

- Physical iPhone Safari service-worker update, correction, and offline recovery
  on an approved trustworthy non-production origin. Install and standalone
  launch have passed on the exact reviewed build.
- Physical Android Chrome install, launch, update, and offline review when an
  Android handset is available.
- Native VoiceOver and TalkBack reading order, control names, focus, and rotor
  review. Mirroring is not a substitute for on-device screen-reader gestures and
  spoken output.
- Manual keyboard activation and 200-percent text/zoom review in a shipping
  browser. The automation harness verified focus but did not dispatch native
  Enter or Space button activation reliably.
- CI on the exact follow-up commit and David's separate approval of the exact
  release and rollback. This record does not authorize merge or deployment.

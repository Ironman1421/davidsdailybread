# Phase 1 PWA quality review

Status: local browser, generated-home bootstrap, physical iPhone
install/launch/update/correction/offline, isolated normal-bake preview, native
keyboard activation, and 200-percent zoom completed; clean first-route iPhone
offline, Android, full auditory screen-reader, and release gates remain

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

This satisfied the normal non-publishing bake gate at that exact head. It did
not substitute for CI or, by itself, make the then-current generated homepage
PWA-enabled; the later bootstrap follow-up below addresses that separate gap.

## Generated-home bootstrap and native local follow-up

Reviewed on 2026-08-04 beginning from PR #48 head
`0d8835853a766c949c2fe035948c728dfcfcf9eb`. The current morning renderer input
was mechanically rehydrated in an isolated repository copy from the canonical
August 4 morning edition and category pages, with Scripture verified against
the repository dataset. The normal daily renderer then produced the current
morning output. No editorial text was hand-edited.

The first isolated render changed only the five expected current-morning
surfaces: the homepage, August 4 morning edition, and Tech & AI, Markets, and
Science pages. Archive HTML and JSON, RSS, bakery state, and the evening catalog
remained byte-identical. The generated-page diff was limited to the reviewed
PWA metadata, styles, script, product-rhythm language, and an existing
production-template category-card height rule. Those five generated files were
then adopted mechanically from a final isolated render. No historical edition,
archive contract, feed, reader-intake state, or production evidence changed.

Native keyboard review in Chrome exposed one material focus defect: after the
collapsed **More** control, Tab could still enter links in its visually hidden
panel. The panel now uses `inert` with synchronized `aria-hidden` state while
collapsed. Native Tab, Enter, and Space then passed: Enter expanded the panel,
Space collapsed it, and the next Tab bypassed the hidden links for the lead
story. An executable PWA contract records the collapsed-state requirement.

Safari was reviewed at its native 200-percent page-zoom level from masthead
through footer. The product distinction, At a Glance panel, dense lead-story
copy, cards, Scripture blocks, notes, buttons, and footer all reflowed without
horizontal scrolling, clipping, overlap, or loss of controls. Safari was
restored to actual size after the review, and the loopback preview was stopped.

This follow-up clears the generated-home bootstrap, native-keyboard, and
200-percent zoom gates locally. It does not substitute for exact-head CI or the
remaining physical-device and auditory checks.

## Private HTTPS physical follow-up

Reviewed on 2026-08-04 at exact PR head
`a9ff2bf36abf247fccc842a3e177adc8ca55ed26` after its pull-request Merge gate
passed. David separately approved a one-time Tailscale Serve preview and
accepted disclosure of the Mac's certificate hostname in the public
Certificate Transparency ledger. The exact commit was extracted to a temporary
directory and its complete 258-file hash inventory was verified before use.

The backend bound only to `127.0.0.1:8787`. Tailscale Serve proxied it over
tailnet-only HTTPS in the foreground. The optional Funnel consent was explicitly
cleared before HTTPS was enabled, and Funnel was never configured or used. No
deployment, production write, public reader intake, notification activation,
credential installation, or live-data collection occurred.

Passed on the physical iPhone:

- Safari trusted the HTTPS certificate and loaded the exact manifest, worker,
  approved icons, and PWA assets. Manifest and worker hashes matched the exact
  extracted commit.
- Add to Home Screen used the `Daily Bread` name, approved icon, root start URL,
  and **Open as Web App** mode. The exact HTTPS install launched the canonical
  August 4 homepage in standalone mode.
- After the standalone app visited the PWA-wired Chronicles page, that app's own
  storage registered and activated the service worker.
- A temporary, visibly labeled correction marker and cache-generation change
  were made only in the extracted preview. The corrected page replaced the
  prior page, and the installed app presented the reader-controlled **A fresher
  app shell is ready** panel with **Refresh now** and the notes-preservation
  statement.
- Activating the update reloaded the page. With both Serve and the loopback
  backend stopped, an offline reload in the exact HTTPS app retained the revised
  page and visible correction marker. This exercises network-first correction
  freshness, the waiting-worker handoff, and offline retention on physical
  iPhone Safari.

One material bootstrap gap was observed on this exact head. Immediately after
installation, before the standalone app visited any PWA-wired page, the first
route-down cold start received Safari's unable-to-connect screen. The generated
homepage bootstrap has since been repaired locally through the normal renderer,
but a clean exact-head HTTPS reinstall must still prove first-route worker
registration and offline startup end to end.

VoiceOver was already enabled on the handset during this HTTPS follow-up and
was left unchanged. The installed publication, update action, and corrected
offline page remained visually stable and operable through iPhone Mirroring.
Mirroring still did not expose dependable spoken announcements or native touch
exploration, so a full auditory label, reading-order, focus, and rotor audit is
not claimed.

After the rehearsal, the temporary correction and worker change were removed;
all 258 extracted-file hashes again matched the exact commit. Both foreground
processes were stopped, port 8787 had no listener, and `tailscale serve status
--json` returned `{}`. The approved tailnet HTTPS feature and its certificate
hostname remain enabled, but no Serve route remains.

## Remaining release gates

- After exact-head CI passes, remove both test Home Screen installs and obtain
  fresh, exact-head approval for one private HTTPS rehearsal. Install cleanly,
  take the first route offline before visiting another page, and prove immediate
  post-install cold start. Then repeat the bounded update and correction checks.
- Complete a short physical, on-device VoiceOver checklist with David operating
  native gestures and confirming the spoken announcements. Mirroring is not a
  substitute for auditory evidence.
- Physical Android Chrome install, launch, update, offline, and TalkBack review
  is explicitly deferred as an evidence gap until a borrowed physical Android
  is available. It is not a pass; this phase does not justify buying a handset or
  provisioning a device-testing service.
- CI on the exact follow-up commit and David's separate ready-for-review
  decision. The PR remains draft, and this record does not authorize merge or
  deployment.

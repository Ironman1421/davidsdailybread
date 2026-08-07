# Installable web app architecture

Status: production active on the canonical website

Owner and final decision-maker: David Friedhof

## Product boundary

The app is the existing responsive website made installable and mobile-capable.
It is not a separate editorial product and does not introduce a generic
Christian feature suite. Its governing distinction is:

- news and Scripture each morning;
- an evening Field Guide with useful tools and workflows; and
- **Loved by God**.

The website, `archive.json`, `feed.xml`, dated edition paths, source evidence,
and corrections remain canonical. The manifest starts at `/`, stays within `/`,
and creates no alternate content store or app-only edition path.

## First work package

This package adds a web app manifest, approved brand icons, service-worker
registration, accessible user-initiated install guidance, update guidance, a
branded offline fallback, and explicit cache boundaries. One responsive
codebase serves desktop, iPhone, and Android.

The package does not add accounts, a hosted community, prayer sharing, push
subscriptions, notifications, background sync, address collection, analytics,
credentials, external services, or app-store metadata.

## Cache and correction policy

| Resource | Online behavior | Offline behavior | Correction rule |
|---|---|---|---|
| HTML navigations, including dated editions | Network first, bypassing the browser HTTP cache | Last successful same-origin response, then `/offline.html` | Every revisit checks the canonical network copy before Cache Storage |
| `archive.json`, `feed.xml`, `evening-catalog.json` | Network first, bypassing the browser HTTP cache | Last successful response | Successful network responses replace prior cached data |
| Versioned app shell and approved brand assets | Cache first after a revalidated install fetch | Cached shell asset | A service-worker version change creates a fresh shell cache |
| Cross-origin sources and fonts | Browser network behavior | No service-worker copy | The app never mirrors third-party content |
| URLs with query strings | Fetched but never written to Cache Storage | Clean-path fallback only | Query values and fragments are never persisted |

Only successful same-origin basic responses may enter runtime caches. Failed,
redirected, opaque, cross-origin, and `no-store` responses are not cached. Cache
cleanup is limited to cache names owned by this app.

## Updates and corrections

The worker does not call `skipWaiting()` during install. A waiting update is
shown to the reader with a refresh action, preventing an unannounced shell swap
mid-read. A new cache generation installs shell assets with browser-cache
revalidation before it can wait for activation. Canonical pages and data bypass
the browser HTTP cache and remain network-first even when the shell is old, so
a service-worker update is not required to receive an edition correction. The
app never deletes or rewrites canonical history.

## Notes and saved material

Existing note keys remain `ddb-note:*` and `ddb-note-style:*` in `localStorage`.
Neither the registration script nor the service worker reads, migrates, clears,
uploads, or measures them. Cache upgrades touch Cache Storage only. Chronicles
continues to own note discovery and its four export controls.

This package does not introduce a saved-item schema. Saved-item portability is
a later Phase 1 package that must coexist with existing note keys and define
export and deletion before it stores new personal history.

## Install behavior

Installation is always reader-initiated. Supporting browsers receive their
native install prompt only after the reader chooses the Install app control.
iPhone and iPad readers receive Safari's Share, then Add to Home Screen
instructions. Other browsers receive honest browser-menu guidance. The controls
use buttons, focus-visible states, status text, and an `aria-live` region. The
installed display uses the same URLs and responsive HTML.

## Reminder boundary

No reminder or notification is activated in this package. A later quiet
reminder design must be optional, time-bounded, preference-controlled, free of
sensitive prayer text, and separately reviewed before any notification API or
provider is used.

## Release gate

The normal renderer, desktop keyboard and zoom behavior, physical iPhone
install/offline/update/correction flow, short physical VoiceOver check,
service-worker correction boundary, and independent review are recorded in
`docs/PWA_QUALITY_REVIEW_2026-08-04.md`. Physical Android/TalkBack, a
comprehensive auditory review, and the heading-hierarchy follow-up remain
explicit evidence gaps rather than passes.

The service-worker install-path repair at
`ba23154ece0c31d820687c181cacc0b615db2bdc` passed targeted contracts, the full
suite, exact-head CI, CodeQL, and independent review. David accepted the lack of
a repeated physical-device cycle after that repair on 2026-08-04. He authorized
publication and GitHub Pages deployment in principle, subject to a separate
approval naming the final immutable release-record SHA. That approval was later
granted: PR 48 exact head `17967c5b494a9cf94cfa7d0549851ec19d5b4807`
merged as `40df44b9fa68a5721cb20473d859ca76d76eb628`, and Pages build
1132904965 completed. The current shell refresh in PR 61 merged as
`9e419f4f7bf6b5655e8282188265ecd8650544ba`, and Pages build 1133942429
completed. Any later runtime change reopens only the affected evidence gate.

The generated home and category pages must continue to receive their PWA links
through the normal bake templates, never by hand editing rendered output.

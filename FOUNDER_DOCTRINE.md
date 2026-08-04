# David's Daily Bread founder operating doctrine

Status: active governing direction

Founder and final decision-maker: David Friedhof

Effective: 2026-08-04

Supersedes: the 2026-07-31 limits on strategy and local work for community,
accounts, participation, private messaging, and newsletter planning. The
production safety gates below remain in force.

## Mission

David's Daily Bread is a founder-led Christian media and learning project. It
exists to help believers grow in faith, understand technology wisely, pray for
one another, and use what they learn in service to others.

The project will pursue truth without hype, conviction without cruelty,
technology without worshiping it, and community without exploiting
vulnerability.

## Durable-moat direction

Code and interface design are useful, but they are not the durable advantage.
The project will build a mission-aligned network around six compounding assets:

1. trust earned through sourced work, theological consistency, and responsible
   moderation;
2. a daily rhythm of learning, reflection, prayer, and service;
3. reader-owned personal history, including notes, saved material, prayer, and
   service records;
4. trusted relationships among participants;
5. useful, carefully governed contributions that improve the product for
   others; and
6. distribution that brings people from approved social channels back to the
   canonical home.

The software exists to help people grow, pray, and serve together. It must not
turn spiritual vulnerability into engagement bait, advertising profiles, or a
mechanism for transferring control away from David.

## Current operating model

- The website, archive, and RSS are the permanent canonical home.
- The publication's governing product distinction is news and Scripture each
  morning, an evening Field Guide with useful tools and workflows, and the
  exact public brand statement **Loved by God**. The installable web app is the
  website made installable and mobile-capable, not a separate editorial product
  or a generic Christian feature suite.
- X and other individually approved social channels are for discovery,
  discussion, and audience growth. They point people back to durable work on
  the website and do not replace it.
- The product may grow from a publication into a carefully moderated
  participation network with an installable web app, member accounts, personal
  archives, prayer, contribution, trusted-group, and later native-app
  capabilities under `docs/GROWTH_ROADMAP.md`.
- The project remains founder-led and founder-directed. Listening, comments,
  suggestions, prayer, and future contributions do not transfer governance.
- David retains final control over the mission, theology, editorial direction,
  partnerships, product direction, channels, and monetization.
- The first 1,000 genuinely engaged people who return for faith, technology,
  prayer, and service remain the first proof gate, not the ceiling of the
  mission or the end of the roadmap.
- The evening Field Guide should be a force multiplier for ordinary readers.
  Tools and workflows earn space by offering broad, recurring or compounding
  usefulness. Trend strength validates a candidate but does not make a narrow
  novelty eligible.

## Work authorized by the 2026-08-04 decision

David authorizes research, product strategy, architecture, design, local
prototyping, implementation, and testing for every phase of the durable-moat
roadmap. This includes:

- broader social distribution and participation loops;
- an installable web app first, followed by evidence-gated native mobile apps
  and a later desktop decision;
- member accounts and portable personal archives;
- carefully moderated public and trusted-circle prayer;
- contribution, reputation, reporting, blocking, and moderation systems;
- open posting and private/direct communication designs that remain disabled
  until their later safety gates are met; and
- newsletter strategy and local product-integration prototypes.

This reverses the prior prohibition on planning or building these capabilities
locally. It does not itself publish a page, send a message or email, provision a
service, install a credential, accept provider terms, spend money, import data,
or open a production community surface.

## Current production boundaries

Until David explicitly records a different decision in the repository:

- Do not form a nonprofit, recruit a governing board, or give outside parties
  authority over the project.
- Do not deploy or activate custom community software, member accounts, a
  hosted social feed, open posting, trusted groups, or private/direct messaging
  until the applicable roadmap exit gate, security review, moderation owner,
  incident path, rollback, and exact activation decision are recorded.
- Until a hosted prayer surface is separately activated, prayer interaction may
  occur only as a carefully moderated discussion on an approved existing
  channel. Every prayer surface must protect privacy, prohibit identifying
  details about other people, financial solicitation, romantic recruitment,
  coercion, and medical claims that replace professional care, and remain
  subject to David's moderation and removal decisions.
- New Ask the Baker, Letters to the King, and Crumb Board submissions are
  closed to the public until the private intake boundary is verified and David
  explicitly approves the cutover. The site-side closure is deployed: public
  submission controls and active intake endpoints are absent, Counter sync is a
  retained no-op, `counter.csv` is absent at the repository tip, and the four
  Chronicles exports remain. Local implementation and reopening plans are
  authorized. External provider changes, private-store provisioning, deletion,
  history rewriting, and live data migration remain separate decisions.
  Existing reviewed reader material remains an editorial queue, not a community
  feed or private messaging surface.
- Newsletter strategy and local integration prototypes may proceed, but no
  issue drafting, test send, sending-address configuration, list operation,
  credential installation, scheduling, provider mutation, or production send
  is authorized. The existing signup page remains unchanged unless separately
  approved.
- Cloudflare Workers + D1 is selected only for provider-specific local audience
  measurement implementation and an unprovisioned canary plan. No Cloudflare
  account, resource, credential, endpoint, canary execution, deployment,
  activation, production collection, baseline start, or spend is authorized by
  that selection.

## Privacy and moderation law

- Personal notes, prayer journals, and spiritual-history data are private by
  default, exportable by the reader, and deletable subject to any plainly
  disclosed public-record boundary.
- Do not sell or license personal or spiritual data, use it for behavioral
  advertising, or build a cross-site identity graph.
- A reader must choose the audience for a prayer or contribution before it is
  shared. Public is never the default for sensitive material.
- Every interactive surface requires consent language, retention and deletion
  rules, rate limits, reporting, blocking where relationships exist, moderator
  tools, an incident path, and a tested kill switch before activation.
- Private/direct messaging is a later capability, not a launch prerequisite.
  It requires a dedicated abuse and age-safety review and may remain omitted if
  its risks exceed its mission value.
- The project will report network health using return, helpful participation,
  successful moderation, prayer and service outcomes voluntarily shared in
  aggregate, and participant well-being signals. Time-on-site and posting
  volume are not ends in themselves.

## How new work is approved

Contributors and AI agents may now research, design, draft specifications,
prototype, implement, and test locally across the roadmap within an assigned
task. They may not infer permission to publish, send, spend money, provision
services, install credentials, accept provider terms, enter partnerships,
change theology, collect live personal data, open an external surface, or
expand governance. Silence, an old plan, a completed phase, a live signup form,
or unfinished infrastructure is not activation approval.

Each phase in `docs/GROWTH_ROADMAP.md` has evidence and safety exit gates.
Passing a gate makes the next phase eligible for a scoped founder decision. It
does not automatically authorize external action. Production activation must
name the exact surface, reviewed commit or package, operator, data boundary,
moderation coverage, cost ceiling, rollback, and measurement window.

## Authority and continuity

This doctrine governs mission, ownership, strategic direction, authorized local
work, and the production boundaries above. `BRAND.md` remains authoritative for
reader-visible brand and house style; `docs/PRODUCT_SPEC.md`,
`docs/DISTRIBUTION_SPEC.md`, `docs/GROWTH_ROADMAP.md`, runbooks, contracts, and
tests implement the doctrine and must not contradict it. `BAKE.md` remains the
complete procedure for an already-approved daily bake.

When documents conflict within this scope, this doctrine wins. A future change
requires David's explicit decision and a repository update that reconciles the
affected specifications, machine-readable guards, and tests.

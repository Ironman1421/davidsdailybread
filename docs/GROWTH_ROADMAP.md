# Durable moat roadmap

Status: active founder direction; local work authorized; external activation gated

Owner and final decision-maker: David Friedhof

Effective: 2026-08-04

Machine-readable contract: `operations/durable-moat-roadmap.contract.json`

## Objective

Build David's Daily Bread into a trusted Christian learning, prayer, and service
network whose value compounds with every healthy returning participant. The
code can be copied. The community's trust, daily rhythm, personal history,
relationships, contributions, and accumulated operating judgment cannot be
copied quickly.

The first 1,000 genuinely engaged people remain the first proof gate. They are
not the ceiling. The former one-million-followers-in-six-months target is no
longer the active operating goal. Reach will be reforecast from measured return,
healthy participation, and responsible moderation.

The exact public mission remains:

> Grow in faith. Understand technology wisely. Pray for one another. Use what
> you learn in service to others.

David may remain off camera. The website, archive, and RSS are the permanent
home and canonical record. Social channels bring people into the network and
host bounded experiments, but they do not own the mission, the archive, or the
community's durable history.

The publication remains news and Scripture each morning, an evening Field
Guide with useful tools and workflows, and **Loved by God**. The installable app
is this canonical website made mobile-capable, not a separate editorial product
or a generic Christian feature suite.

## The moat

### Trust

Sourced journalism, honest caveats, theological consistency, corrections,
privacy, and visible moderation earn confidence over time. Growth that weakens
trust destroys the moat it is supposed to create.

### Daily ritual

Morning understanding, evening practical guidance, personal reflection, prayer,
and service form a recognizable daily rhythm. Notifications and apps may support
that rhythm, but compulsive engagement mechanics may not replace it.

### Personal history

Notes, saved stories, tools, workflows, prayer journals, answered-prayer records,
and service reflections become more useful as they accumulate. This history is
reader-owned, private by default, exportable, and deletable within disclosed
public-record limits.

### Relationships

Trusted prayer and service relationships create genuine network effects. The
product should help people become known and supported without exposing
vulnerability or requiring a public identity.

### Contributions and reputation

Questions, prayers, testimonies, workflows, corrections, and acts of service can
improve the experience for others. Reputation reflects consistent helpfulness
and safety, never popularity alone. No pay-to-rank spiritual status is allowed.

### Distribution

X is the current discovery and discussion channel. Other channels may be added
one at a time after a format demonstrates healthy return. Canonical editions,
source receipts, and participant invitations all lead back to the permanent
home.

## Authorization model

David's 2026-08-04 decision authorizes research, strategy, architecture, design,
local implementation, fixtures, threat modeling, and tests for all phases below.
It reverses the former ban on planning or locally building custom community
software, member accounts, social feeds, open posting, private messaging, apps,
and newsletter product integration.

It does not authorize publishing, deployment, a test or production send,
provider mutation, account or resource creation, terms acceptance, credential
installation, live personal-data collection, partnership outreach, spending, or
opening a community surface. Each external action requires the scoped founder
decision defined by `FOUNDER_DOCTRINE.md`.

No spend is authorized by this roadmap.

## Phase 0: govern and measure

Purpose: make the mission, safety law, baseline, and ownership explicit before
network features create operational pressure.

Authorized work:

- reconcile doctrine, product, distribution, security, contracts, and tests;
- retain the website, archive, RSS, X, morning edition, and evening Field Guide;
- finish privacy-safe audience measurement locally and prepare its separately
  approved canary path;
- define account, personal-history, prayer-audience, moderation, age-safety,
  deletion, portability, and incident boundaries;
- establish one network-health scorecard with unknown values recorded as null;
  and
- produce installable-web-app architecture without deploying it.

Exit evidence:

- the governing documents and machine-readable contract agree;
- every proposed live data class has a purpose, owner, retention rule, deletion
  behavior, export behavior, and prohibited use;
- moderation roles, response expectations, escalation, kill switches, and a
  no-continuous-monitoring notice are specified;
- the current audience baseline is either measured under the approved contract
  or plainly recorded as unknown; and
- no unresolved high-severity reader-data exposure is carried into a new
  collection surface.

Passing this phase permits David to consider scoped external canaries. It does
not activate them automatically.

The 2026-08-04 readiness record is
`docs/PHASE_0_READINESS_2026-08-04.md`. It identifies satisfied prerequisites
and only the material gaps that keep this exit gate open.

## Phase 1: strengthen ritual and discovery

Purpose: make the existing product easier to return to, install, save, and share
before asking readers to join an empty network.

Authorized local work:

- an installable progressive web app using the canonical site and archive;
- offline reading, saved-item and notes portability, accessible install
  guidance, and optional quiet reminder designs;
- X broadcasts and manually approved replies under their existing contracts;
- one approved social-format experiment at a time, derived from canonical work;
- a public, carefully moderated prayer-thread playbook for approved existing
  channels; and
- newsletter retention strategy and local integration prototypes, with sending
  and provider operations disabled.

Exit evidence:

- returning use improves without a material correction, privacy, or reliability
  regression;
- at least two recurring formats show repeat value;
- public prayer pilots, if separately activated, have named moderation windows,
  published rules, incident records, and a sustainable workload;
- installability and core use pass accessibility and mobile-quality review; and
- discovery measures site return rather than follower count alone.

## Phase 2: accounts and private personal value

Purpose: give each participant durable personal value before exposing social
features.

Authorized local work:

- optional member accounts with a guest path where practical;
- a portable personal archive for notes, saved material, prayer journals,
  answered-prayer markers, and service reflections;
- clear audience choices for every prayer or contribution;
- verified deletion, export, account recovery, session revocation, abuse rate
  limits, and minimum-data profiles;
- the private reader-intake cutover specified by `docs/READER_STORE_SPEC.md`;
  and
- notification preferences that default to quiet and never reveal sensitive
  prayer text on a lock screen.

Exit evidence before any live account activation:

- independent security and privacy review of the exact implementation;
- successful deletion, export, recovery, authorization, rate-limit, logging,
  backup, and rollback tests;
- no spiritual text, relationship graph, or unpublished contribution appears in
  public repositories, ordinary logs, analytics, or advertising systems;
- the private reader store and intake cutover pass their own activation gate;
- a named operator and support path exist; and
- David approves the exact reviewed release, provider, cost ceiling, notice,
  and data-processing boundary.

## Phase 3: moderated participation and prayer network

Purpose: create the first true network effect through safe contribution and
trusted prayer relationships.

Authorized local work:

- carefully moderated public prayer requests with public never selected by
  default;
- small trusted prayer circles with invite, leave, remove, report, and block
  controls;
- reviewed questions, testimonies, corrections, workflows, and service prompts;
- helpfulness and trust signals resistant to popularity gaming;
- moderator queues, context, audit receipts, rate controls, appeals, and
  emergency shutdown; and
- aggregated measures of return, helpful participation, moderation health, and
  voluntarily shared prayer or service outcomes.

Activation gates:

- Phase 2 is healthy and stable;
- community rules prohibit identifying details about other people, financial
  solicitation, romantic recruitment, coercion, targeted harassment, political
  campaigning disguised as prayer, and medical claims that replace professional
  care;
- crisis copy states that the service is not continuously monitored or an
  emergency service and provides reviewed routes to immediate help;
- moderator coverage and response expectations are realistic at the proposed
  cohort size;
- the first cohort is bounded and invite-controlled;
- kill-switch and abuse drills pass; and
- David approves the exact cohort, surface, rules, moderators, duration, and
  rollback.

Open member posting can begin only inside the approved bounded cohort. Passing a
pilot does not authorize an unlimited public feed.

## Phase 4: native mobile and carefully expanded network

Purpose: deepen the daily rhythm when platform capabilities justify a native
app.

Candidate capabilities:

- iOS and Android apps sharing the canonical content and account model;
- privacy-safe notifications, widgets, offline access, and media capture only
  when they provide clear mission value;
- expanded trusted circles, church or service cohorts, and contribution tools;
  and
- private/direct messaging only if the dedicated abuse, age-safety, encryption,
  reporting, retention, and moderation review concludes that it should exist.

Exit evidence:

- the installable web app has demonstrated a platform limitation that native
  software can materially solve;
- Phase 3 retention and network health remain strong across multiple cohorts;
- notification opt-out, uninstall, deletion, moderation, and support behavior
  are healthy;
- app-store, payments, privacy-label, review, and incident ownership are
  documented; and
- David approves each store account, release, cost, and public listing.

Private messaging is optional. It is not evidence of maturity and may be
permanently omitted.

## Phase 5: durable institutions and desktop decision

Purpose: extend the network only where the community has demonstrated a real
need and responsible operating capacity.

Possible work:

- church, ministry, study, and service partnerships with clear authority and
  data boundaries;
- facilitator tools, group exports, and interoperable resources;
- a desktop app only if study, Chronicles, creation, or moderation workflows
  demonstrate value that the web app cannot deliver; and
- sustainable monetization that never sells spiritual data, exploits prayer,
  privileges wealthy participants in community standing, or transfers founder
  control.

Nonprofit formation, a governing board, and outside governance remain separate
founder decisions. Network scale does not require surrendering mission control.

## Network-health scorecard

Review by cohort and surface, with unknown values recorded as null:

- qualified engaged returning people and cohort retention;
- completion of morning, evening, reflection, prayer, and service rhythms;
- saved or exported personal value without inspecting private content;
- helpful contributions, constructive responses, and repeat trusted-circle
  participation;
- invitation acceptance and healthy relationship persistence without growth
  pressure;
- moderation queue age, reports, blocks, removals, appeals, repeat abuse, and
  moderator workload;
- privacy requests, deletion completion, security incidents, and unsupported
  claims;
- voluntarily shared answered-prayer and service outcomes in aggregate; and
- production time, reliability, accessibility, and approved cost.

Never optimize for raw time-on-site, posting volume, outrage, streak anxiety,
public vulnerability, or notification opens at the expense of well-being.
Never buy followers, use engagement pods, fabricate urgency, or pay people for
spiritual testimony.

## Immediate portfolio

The active work order is:

1. complete Phase 0 reconciliation and safety architecture;
2. continue the current X discovery system and mission-led canonical product;
3. design and implement the installable web app locally;
4. prepare the private account, personal-history, and reader-intake boundaries;
5. prepare a bounded moderated prayer pilot; and
6. defer native mobile, private messaging, desktop, partnerships, and formal
   organization until their evidence gates.

This is full speed in direction and local execution, with production exposure
released deliberately one safe, measurable layer at a time.

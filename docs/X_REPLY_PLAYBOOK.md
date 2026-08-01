# X reply-led growth playbook

Status: active strategy; blocked pending live-account readiness checks
Decision owner: David
Last reconciled: 2026-07-31

## Strategy decision and hard boundary

Credible-account replies are the primary near-term acquisition channel for
David's Daily Bread on X. Canonical morning and evening posts remain the profile
credibility layer and permanent source receipts. Replies earn discovery by
adding something useful inside conversations that already have qualified
attention.

This is not a volume or attention-hijacking strategy. A reply must make the
parent conversation better for its existing audience. Profile visits and
follows are an outcome of usefulness, not a call to action inside the reply.

Every reply requires David's explicit approval of the exact parent URL and
exact reply text. AI may help scout, rank, research, and draft. It may not post,
like, follow, quote-post, mention, message, create or edit an X List, or otherwise
mutate X. An authorized human posts the approved text through X's official UI
and reads the receipt back. No external interaction is authorized for an AI
agent and no reply-posting credential is installed.

Browser scripting, scraping, headless browsing, DOM automation, automated X
browsing, and non-API collection from X are prohibited, including for read-only
scouting. Human scouts use manual X Search or an existing manually curated X
List. A future service may use an official read-only X API only after a separate
review approves its access, data handling, cost, and credentials. It still may
not post.

This boundary is load bearing. X's April 2026 automation rules prohibit
non-API automation such as scripting the X website, disallow unsolicited
keyword-triggered automated replies, and require prior written, explicit X
approval for an AI reply bot. Human approval of a batch does not authorize a
bot or an evergreen campaign. The manual phase continues unless X grants that
specific approval and this contract is revised through a reviewed pull request.

## Operating readiness gate

The lab remains blocked until David or an authorized operator records all of
these checks without placing account secrets in the repository or an approval
card:

- Profile conversion is ready: the exact positioning promise, recognizable
  faceless mark and banner, pinned sourced briefing, working canonical-site
  link, and recent morning and evening posts are all present.
- The current X Premium tier is recorded as `none`, `basic`, `premium`, or
  `premium_plus`; this is an inventory check, not authority to buy a plan.
- Post Activity Dashboard access is recorded as `available` or `unavailable`.
  Missing access does not permit a guessed metric and does not authorize an ads
  account, paid campaign, or subscription.
- Each operator is named and authorized by David, is signed into the correct DDB
  account in the official X UI, and has checked MFA and recovery readiness.
- The session is secure: credentials are not shared or copied into prompts,
  drafts, logs, tickets, or the repository; no script, scraper, browser-control
  agent, or automation extension is operating on X.

The machine-readable baseline deliberately records these checks as
`not_assessed` and `blocked_pending_readiness`. Do not infer readiness from this
document.

## Target watchlist and verification

Credibility matters more than raw follower count. Candidate parent posts must
be public, current, relevant to a DDB beat, and attributable to one of these
tiers:

1. `primary_source`: companies, laboratories, regulators, public agencies,
   journals, universities, standards bodies, or named project maintainers;
2. `subject_matter_expert`: identifiable researchers, engineers, investors,
   economists, clinicians, operators, or creators with relevant work;
3. `credible_reporter`: a reporter or publication with attributable reporting,
   corrections practice, and a track record on the beat; or
4. `trusted_institution`: a durable professional, scientific, or civic
   institution publishing material within its remit.

Maintain the watchlist as a private research artifact. Seed organization and
institution accounts from current official directories in these categories:

- government agencies, regulators, central banks, statistical agencies, and
  multilateral organizations;
- universities, public research institutes, and national laboratories;
- journals, scholarly publishers, and professional or scientific societies;
- standards bodies, open-source foundations, and project-maintainer
  organizations; and
- companies' official corporate, research, engineering, and investor-relations
  accounts.

For each seed, record the exact handle, tier, beat, official-directory or
organization-owned source URL, X label or affiliation observed, checked time,
and last proactive DDB reply. Recheck the evidence before presenting a card.
An X gold check, grey check, or organization affiliation badge is a useful
current signal for the applicable organization or government account. A blue
check primarily indicates an X Premium subscription and is not by itself proof
that an individual is notable, authentic, or currently employed as claimed.

Do not describe an individual expert or reporter as verified unless a current
source on that person's owned domain or employer's domain identifies the exact
X handle. Otherwise record `not_claimed`; assess the post on its attributable
evidence without making a verification claim. Never convert an inference,
search result, stale biography, or display-name match into identity proof.

Do not target the same account more than once in any rolling 72 hours or more
than twice in any rolling 14 days. Continue a conversation only when the
account responds, and do not treat those responsive exchanges as new proactive
targets.

Exclude anonymous rumor accounts, rage bait, follow-for-follow requests,
engagement pods, tragedy pile-ons, private-person disputes, unverified breaking
claims, promotional contests, partisan dogpiles, and conversations where the
brand's contribution would be redundant or opportunistic.

## The five permitted reply shapes

Each reply has exactly one declared shape:

- `sourced_addition`: one material fact or primary-source detail missing from
  the parent conversation;
- `plain_language_translation`: make a technical or financial point useful to
  a non-specialist without distorting it;
- `practical_application`: explain what a real person can try, verify, or watch
  next;
- `evidence_based_caveat`: add a respectful limitation, denominator, competing
  explanation, or uncertainty; or
- `specific_question`: ask a precise, informed question whose answer would add
  value for the thread.

Generic praise, jokes without substance, summaries of the parent post,
contrarianism for attention, dunking, flattery, and "great thread" variants are
not reply shapes. Every factual assertion needs a fetched supporting source.

## BREAD quality gate

Score each draft from zero to two on each BREAD dimension. Zero means it fails;
one means present but weak; two means strong and specific.

- **B — Builds the conversation:** gives the existing audience a useful next
  fact, translation, application, caveat, or answerable question.
- **R — Relevant:** directly addresses the parent and a DDB beat without
  hijacking attention.
- **E — Evidence-grounded:** every factual claim is supported, certainty matches
  the source, and inference is labeled.
- **A — Appropriate:** clear, warm, concise, safe, and free of engagement bait,
  pile-ons, or performative correction.
- **D — Distinct:** adds something not already prominent in the parent thread
  and is not reused or substantially similar to another DDB reply.

Only a 9/10 or 10/10 draft may reach David. BREAD is not compensatory: any
failed safety, sourcing, relevance, target-frequency, or context check rejects
the candidate regardless of its total.

## 100-point opportunity score and priority

Score the parent opportunity before drafting:

| Component | Points | Question |
| --- | ---: | --- |
| Relevance | 20 | Is this directly inside a DDB beat and useful to the audience? |
| Incremental value | 25 | Can DDB add a material point not already prominent? |
| Source confidence | 20 | Is the parent attributable and can the reply use strong support? |
| Conversation timing | 15 | Is the post current and the conversation still open to value? |
| Target credibility | 10 | Does current evidence support the target tier and identity? |
| Operational safety | 10 | Is the context low-risk and feasible within all hard controls? |

The components must sum to the recorded total. A score below 75 is rejected,
not rounded up. Operational priorities are:

- `P1`: 90–100, highest-value and time-sensitive; surface first in the current
  staffed window;
- `P2`: 80–89, strong; surface after P1 while context remains live; and
- `P3`: 75–79, eligible but fragile; surface only if it still clears every check
  and no higher-quality candidate would be displaced.

Priority affects review order, never the daily cap, safety rules, or approval
standard. Do not pad a window or quota with a lower-scoring candidate.

## Reply construction rules

- Keep the initial operating limit at 280 characters even if the account later
  gains access to longer posts.
- Lead with the useful contribution. Do not begin with the account's handle,
  praise, a greeting, or an explanation of DDB.
- Use the DDB voice: clear, grounded, warm, concise, and free of em dashes.
- Match certainty to the evidence. Label inference and uncertainty plainly.
- Do not quote a source beyond the project's quotation limits.
- Use no hashtag unless the hashtag is intrinsic to the event or standard.
- Do not ask for a follow, like, repost, subscription, click, or DM.
- Do not tag an additional account unless that account is directly involved and
  the tag is necessary for meaning.
- During the first 30 operating days, include no DDB link unless the parent
  author directly requests the source or the reply would otherwise be
  unverifiable. The profile and pinned canonical post perform conversion.
- Never paste the same or substantially similar reply into multiple threads.
- One DDB reply per parent post. The tighter account-frequency limits above also
  apply.

## Candidate and approval workflow

Scouting is read-only and manual. The private approval card validates against
`distribution/x-reply-approval-card.schema.json` and contains:

```text
Candidate: XR-YYYYMMDD-NNN; schema version 1
Target: @account (credibility tier, beat)
Verification: claim basis, current evidence URL or not_claimed, checked time
Parent: exact X URL and observed timestamp
Why this conversation: one sentence
Reply shape: one of the five permitted values
Draft: exact proposed reply
Support: fetched primary or attributable source URL(s)
Scouting: manual-x-search or manual-x-list
BREAD: B/R/E/A/D component scores and total, minimum 9/10
Opportunity: six component scores, total out of 100, priority P1/P2/P3
Checks: live parent, relevance, sensitive context, duplicate, claims, no CTA,
        target frequency
Profile: all five conversion-readiness checks and checked time
Capabilities: Premium tier, Post Activity Dashboard availability, checked time
Operator: name, authorization, correct account, secure session, MFA/recovery,
          no credential sharing, official UI only, no scripting/scraping/
          automated X browsing
Length: N/280
Approval scope: exact parent and exact text; silence rejects; edits reapprove
Approval expires: timestamp, no more than 60 minutes after context check
```

David responds with an exact decision: approve the candidate ID, approve edited
text, reject, or defer. Silence is rejection. Approval applies only to the shown
parent URL and exact reply text, expires after 60 minutes, and is void if the
parent is edited, deleted, materially overtaken by events, or surrounded by new
sensitive context. Any target or text change after approval requires approval
again.

The operator rechecks the parent, target frequency, correct DDB account, and
approval expiry; posts once through X's official UI; reads the published reply
back; and records the receipt. A mismatch is deleted once and corrected only if
the correction can be made without duplicate spam. Never retry blindly.

Immediately after publication, the operator manually opens the parent
conversation and inspects whether the reply is visible, hidden, or behind
"Show probable spam." Repeat this inspection at the 24-hour and seven-day
snapshots. A hidden or probable-spam result is a guardrail event, not a weak
impression result to optimize around.

The private candidate queue is transient and stores unposted drafts for at most
24 hours. Only published replies enter the public reply ledger. Rejected,
deferred, or expired draft text is never committed to
`distribution/x-replies.json`; count only its disposition reason privately.

## Discovery windows, cadence, and staffing

Recommended discovery windows are 7:00–8:00 a.m., 11:30 a.m.–12:30 p.m., and
4:00–5:00 p.m. Pacific. These are DDB operating windows, not X-published safe
limits or performance guarantees. They are opportunities to find current posts,
not quotas.

The default implementation staffs two approval windows and caps publication at
four approved replies per Pacific day. Publish fewer, including zero, whenever
fewer candidates clear every gate. Never publish more than two proactive
replies in any rolling hour.

Six replies in one day require all three discovery/approval windows to be
separately staffed, an updated machine-readable baseline, and David's explicit
approval of that staffing change. Until then the hard cap remains four. Six is
never a target to pad. No plan above six/day is approved in this version.

Do not scale volume until at least 50 published replies have complete measured
snapshots and the operating-readiness, visibility, accuracy, and policy signals
remain clean. At that point David may approve a separately staffed six/day test;
the third window remains mandatory. Any later volume proposal requires a new
reviewed contract.

Pause proactive replies for 24 hours after an account warning or anti-spam
challenge. Stop immediately for a policy notice, credential concern, factual
correction involving a reply, hidden reply, or probable-spam placement. Diagnose
before resuming; do not work around limits.

## Measurement and experimental validity

Every published reply validates against
`distribution/x-replies.schema.json` and is recorded in
`distribution/x-replies.json`. Capture at publication, 24 hours, and seven
days:

- impressions, likes, child replies, and reposts on the reply;
- reply-level `userProfileClicks` and `directFollows` when X exposes them in
  Post Activity Dashboard;
- whether the target author liked, replied, reposted, quoted, hid, or deleted
  the reply;
- the manual visible/hidden/probable-spam inspection;
- account follower count immediately before the approval window and after 24
  hours, plus account-window profile visits when exposed;
- approval latency, discovery-to-publish latency, reply shape, target tier,
  beat, discovery window, opportunity score, and operator; and
- any correction, negative-feedback, spam, or policy signal.

Missing analytics are `null`, never zero. X defines post-level Follows as people
who began following directly from the post and User profile clicks as clicks on
the author's name, handle, or profile photo. Use those reply-level measures as
the strongest available conversion signal. Account-window profile visits and
follower changes remain secondary attribution because other account activity
shares the same window.

Do not claim that one reply caused an account-window follower change. The
snapshot's `attribution` field describes that window delta and is normally
`unknown` or `temporal`; use `platform_reported` only if X explicitly attributes
the follower change. `directFollows` is the separate reply-level conversion
field. X notes that Post Activity data can fluctuate while stabilizing, so
preserve each capture time rather than overwriting earlier snapshots.

Weekly decisions use medians and the 75th percentile, not only the best outlier.
Compare reply shapes only after each compared shape has at least eight measured
observations. Match or stratify comparisons on target tier, discovery window,
opportunity-score band, and qualitative opportunity quality; where those cannot
be held reasonably stable, label the result directional rather than causal.
Change one named variable where practical and predeclare the hypothesis,
decision date, and stop rule.

After at least 50 measured replies, keep the two strongest reply shapes only if
the controlled comparison supports that decision; otherwise collect more data.
After 100, decide whether reply-led X growth is producing enough qualified
profile conversion to deserve more scouting capacity. It does not inherit
budget merely because replies are being published.

## Primary X references and DDB inferences

Current X facts used by this contract:

- [X automation rules](https://help.x.com/en/rules-and-policies/x-automation)
  (updated April 2026): website scripting, automated-reply, and AI reply-bot
  rules.
- [X authenticity policy](https://help.x.com/en/rules-and-policies/authenticity):
  inauthentic engagement, reply misuse, and reach restrictions.
- [X replies and mentions](https://help.x.com/en/using-x/mentions-and-replies):
  reply ranking, hidden replies, and probable-spam surfaces.
- [X Post Activity Dashboard](https://business.x.com/en/help/campaign-measurement-and-analytics/tweet-activity-dashboard):
  post-level user-profile-click and direct-follow definitions and availability.
- [X profile labels and checkmarks](https://help.x.com/en/rules-and-policies/profile-labels):
  current meanings of blue, gold, grey, and affiliation signals.
- [X Lists](https://help.x.com/en/using-x/x-lists) and
  [X advanced search](https://help.x.com/en/using-x/x-advanced-search): the
  official manual discovery surfaces.
- [X API search documentation](https://docs.x.com/x-api/posts/search/introduction):
  the only future automated scouting path contemplated here, subject to a
  separate read-only review.

The BREAD threshold, 100-point score, 72-hour/14-day target limits, Pacific
windows, four/day cap, three-window condition for six/day, eight-observation
comparison floor, and 50-measured-reply scaling gate are conservative DDB
operating inferences. X does not publish them as safe limits or guarantees.

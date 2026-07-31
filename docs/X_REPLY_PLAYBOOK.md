# X reply-led growth playbook

Status: active strategy; manual operation required
Decision owner: David
Last reconciled: 2026-07-31

## Strategy decision

Credible-account replies are the primary near-term acquisition channel for
David's Daily Bread on X. Canonical morning and evening posts remain the profile
credibility layer and permanent source receipts. Replies earn discovery by
adding something useful inside conversations that already have qualified
attention.

This is not a volume or attention-hijacking strategy. A reply must make the
parent conversation better for its existing audience. Profile visits and
follows are an outcome of usefulness, not a call to action inside the reply.

Every reply requires David's explicit approval. During this phase, the system
may discover posts, rank opportunities, research context, and draft replies,
but it does not post, like, follow, quote-post, mention, or otherwise mutate X.
David or an operator acting on his exact item-level approval posts manually
through the official X interface. No API credential is installed for replies.

This boundary is load bearing. X prohibits unsolicited automated replies and
requires prior written approval for an AI-powered automated reply bot. Human
approval of a batch does not authorize a bot or an evergreen campaign. The
manual phase continues unless X grants written approval and this specification
is separately revised through a reviewed pull request.

## Target selection

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

Priority score, highest first:

- direct relevance to technology, markets, science, AI tools, or workflows;
- DDB can add a sourced fact, useful translation, practical implication, or
  fair caveat that is not already prominent in the thread;
- the parent is recent enough that the conversation is still active;
- the account and post are credible, safe, and not engagement bait; and
- the reply can stand alone without forcing a DDB link.

Exclude anonymous rumor accounts, rage bait, follow-for-follow requests,
engagement pods, tragedy pile-ons, private-person disputes, unverified breaking
claims, promotional contests, partisan dogpiles, and conversations where the
brand's contribution would be redundant or opportunistic. Do not target the
same account repeatedly merely because it is large.

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
- One DDB reply per parent post and at most one proactive reply to the same
  account per day. Continue a conversation only when the account responds.

## Candidate and approval workflow

Scouting is read-only. Each approval card contains:

```text
Candidate: XR-YYYYMMDD-NNN
Target: @account (credibility tier, beat)
Parent: exact X URL and observed timestamp
Why this conversation: one sentence
Reply shape: one of the five permitted values
Draft: exact proposed reply
Support: fetched primary or attributable source URL(s)
Checks: relevance, parent still live, sensitive-content scan, duplicate scan
Length: N/280
Approval expires: timestamp, no more than 60 minutes after context check
```

David responds with an exact decision: approve the candidate ID, approve edited
text, reject, or defer. Silence is rejection. Approval applies only to the shown
parent URL and exact reply text, expires after 60 minutes, and is void if the
parent is edited, deleted, materially overtaken by events, or surrounded by new
sensitive context. Any text change after approval requires approval again.

The operator checks the parent once more, posts through X's official interface,
reads the published reply back, and records the receipt. A mismatch is deleted
once and corrected only if the correction can be made without duplicate spam.
Never retry blindly.

The private candidate queue is transient and stores unposted drafts for at most
24 hours. Only published replies enter the public reply ledger. Rejected or
expired drafts are counted by reason but their text is not committed to this
public repository.

## Cadence and scaling gates

Start conservatively because the account baseline is five followers:

- Days 1 to 14: propose up to 10 candidates and publish 4 to 6 approved replies
  per day across at least two approval windows. Never publish more than two
  proactive replies in an hour.
- Days 15 to 30: increase to 6 to 10 published replies per day only if the first
  two weeks show no spam labeling, hidden replies, blocks, policy warnings, or
  rising negative feedback.
- After day 30: test 10 to 15 only when reply impressions and qualified profile
  conversion rise without a lower approval rate or quality signal. More volume
  is not itself a milestone.

Pause proactive replies for 24 hours after an account warning or anti-spam
challenge. Stop immediately for a policy notice, credential concern, factual
correction involving a reply, or repeated probable-spam placement. Diagnose
before resuming; do not work around limits.

## Measurement

Every published reply validates against
`distribution/x-replies.schema.json` and is recorded in
`distribution/x-replies.json`. Capture at publication, 24 hours, and seven
days:

- impressions, likes, child replies, and reposts on the reply;
- whether the target author liked, replied, reposted, quoted, hid, or deleted
  the reply;
- account follower count immediately before the approval window and after 24
  hours;
- profile visits for the same window when X exposes them;
- approval latency, discovery-to-publish latency, reply shape, target tier, and
  beat; and
- any correction, negative-feedback, spam, or policy signal.

Do not claim that one reply caused a follower when X supplies no causal
attribution. Record follower deltas as temporal windows and mark attribution as
`unknown`, `temporal`, or `platform_reported`.

Weekly decisions use:

- median reply impressions and the 75th percentile, not only the best outlier;
- qualified interactions from target authors and subject-matter participants;
- profile visits and follower delta per approval window;
- performance by reply shape, target tier, beat, timing, and operator;
- approval rate and median approval latency; and
- corrections, hidden/probable-spam replies, blocks, and policy events.

After 50 published replies, keep the two strongest reply shapes and revise or
pause the weakest. After 100, decide whether reply-led X growth is producing
enough qualified profile conversion to deserve more scouting capacity. It does
not inherit budget merely because replies are being published.

## Profile conversion prerequisite

Replies create curiosity; the profile must close it. Before scaling beyond six
replies per day, verify that the profile has:

- the exact DDB positioning promise;
- a recognizable faceless mark and banner;
- a pinned post that shows one excellent sourced briefing without hype;
- a working canonical site link; and
- recent morning and evening posts that demonstrate both franchises.

## Primary policy references

- [X automation rules](https://help.x.com/en/rules-and-policies/x-automation)
- [X authenticity and spam policy](https://help.x.com/en/rules-and-policies/authenticity)
- [X reply behavior and ranking](https://help.x.com/en/using-x/mentions-and-replies)
- [X organic community-management guidance](https://business.x.com/en/basics/organic-best-practices)

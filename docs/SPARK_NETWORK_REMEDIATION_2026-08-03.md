# Spark Ethernet and Wi-Fi failover remediation, 2026-08-03

Status: complete. Configuration, controlled tests, physical cable replacement,
and the restarted 24-hour observation all passed.

Owner and approver: David Friedhof

Approval evidence: task message beginning, "I explicitly approve the audited
Spark Ethernet repair and Wi-Fi failover work before any networking changes
begin."

Audited source: the Tailscale DNS warning and reversible remediation section of
`docs/PRODUCTION_HOST_REPOSITORY_HYGIENE_AUDIT_2026-08-02.md` at preserved
commit `f7f076c5a480e2c19ef6dd3ec12bdf5fb4661859`.

## Baseline and recovery evidence

The existing Spark state was captured before mutation at:

`/home/david/.local/state/ddb-pc-012/20260803T142939Z`

The directory contains 15 mode-`0600` files under a mode-`0700` directory.
`sha256sum -c SHA256SUMS` passed. The manifest hash is:

`c453a087f9a5e15d0414dd739b0baf981e52a1588054056f3cb891ae1c7ff644`

The capture includes NetworkManager profiles and devices, IPv4 and IPv6 routes,
neighbors, resolver state, Tailscale state, Ethernet link and counters, network
journals, DDB timers, and failed user units. NetworkManager did not expose a
saved Wi-Fi profile before this change.

The wired baseline and current preferred path are:

- interface `enP7s7`;
- profile `Wired connection 3`, UUID
  `8ea68ba4-5720-3a60-9b2a-20a12da91c3c`;
- IPv4 default route metric 100;
- 2500 Mb/s, full duplex, link detected;
- zero inspected transmit, receive, alignment, MAC, and TCAM-drop errors.

The journal confirms the two audited carrier losses on 2026-08-01: one lasting
120 seconds and one lasting 38 seconds. No later carrier loss was found before
the controlled test.

## Change made

A system NetworkManager profile named `DDB Wi-Fi Failover` was created on
`wlP9s9`. Its UUID is `bcd9bbe9-0e70-4822-8bd8-9f1026e0e50a`. The exact SSID
contains a trailing space; no Wi-Fi or Spark account password was printed,
written to this repository, or copied into the evidence report.

The saved profile has:

- `connection.autoconnect=yes`;
- `ipv4.route-metric=600`;
- `ipv6.route-metric=600`.

With both links active, Ethernet remains preferred at metric 100 and Wi-Fi is
the backup at metric 600.

## Controlled failover and failback

Before the test, Wi-Fi-bound probes reached the router and a public IP. Router
DNS, MagicDNS, and bidirectional Tailscale ping also passed.

An automatic Ethernet restore was scheduled before Ethernet was disconnected.
From `2026-08-03T14:38:44Z` through `2026-08-03T14:42:28Z`:

- Wi-Fi was the sole IPv4 default route at metric 600;
- SSH over Tailscale remained available;
- three external Tailscale probes reached Spark through its Wi-Fi address;
- router DNS and MagicDNS passed;
- Tailscale remained online;
- all seven DDB user timers remained present;
- there were no failed user units.

The scheduled Ethernet restore succeeded. Ethernet returned as the metric-100
preferred path while Wi-Fi remained active at metric 600. SSH, Tailscale, router
DNS, MagicDNS, timers, and failed-unit checks passed after failback.

## Rollback test and harness exception

The documented rollback boundary was tested by disabling only the new Wi-Fi
profile. The original Ethernet route, SSH, Tailscale, router DNS, and MagicDNS
all remained healthy.

The transient systemd command intended to re-enable Wi-Fi automatically did not
restore the profile. This was a test-harness quoting failure, not a network
outage or production-profile failure. The systemd unit was collected before it
retained a useful log. Direct restoration then succeeded in one privileged
command, returning the profile to `autoconnect=yes`, connected, and metric 600.
The failed harness is recorded here rather than hidden or treated as a passing
automatic-rollback test.

The permanent rollback remains simple and bounded: set autoconnect off and
deactivate only `DDB Wi-Fi Failover`. Restoring the approved state is the inverse:
set autoconnect on and activate that same profile. The existing Ethernet profile
was never modified.

## Current state before the physical repair

Post-change evidence is sealed at:

`/home/david/.local/state/ddb-pc-012/20260803T144723Z-post`

It contains 16 mode-`0600` files with manifest hash:

`91dc884e94cf2bf8571c1aa62038d6ae6a69dd8de3008f664fc814b99996bbda`

Tailscale still reports its DNS-forward warning even though router DNS,
MagicDNS, bidirectional Tailscale ping, and SSH all pass. `accept-dns` remains
enabled; the audit explicitly forbids disabling it as a cosmetic workaround.

## Physical repair and replacement-cable baseline

David reported that he installed a Cat 5e Ethernet cable. NetworkManager
recorded the expected carrier loss at `2026-08-03T08:01:28-07:00`, link return
at `08:09:45-07:00`, and successful Ethernet activation at
`08:09:49-07:00`. The exact eero or switch port was not reported as changed.

The replacement link immediately negotiated at 2500 Mb/s, full duplex, with
autonegotiation enabled. Ethernet remained the preferred metric-100 route and
the connected Wi-Fi profile remained the metric-600 backup. Three router
probes and three public-IP probes had zero packet loss. Router DNS, MagicDNS,
SSH, Tailscale connectivity from the Mac through Spark's physical LAN endpoint,
all seven DDB timers, and the zero-failed-user-unit check passed.

The replacement-cable baseline is sealed at:

`/home/david/.local/state/ddb-pc-012/20260803T151441Z-cable-baseline`

It contains 19 mode-`0600` files under a mode-`0700` directory.
`sha256sum -c SHA256SUMS` passed. The manifest hash is:

`c144f168b393d65a5f1edf199c2ff261b3b087d28456a80d14fc984f1bcb9afd`

The cable-baseline counters contain one accumulated transmit error and 89
transmit drops after the deliberate unplug interval, compared with zero driver
transmit errors in the earlier sealed post-change snapshot. Receive errors,
receive drops, carrier errors, collisions, alignment errors, MAC errors, and
TCAM drops remain zero. The driver's separate `rx_mac_missed` lifetime counter
is 1,418,819, up 1,287 from the earlier post-change snapshot. The follow-up must
compare exact counter deltas against this cable baseline rather than treating
lifetime counters as new failures.

Tailscale still reports its DNS-forward warning even though the router DNS,
MagicDNS, Tailscale, and internet probes pass. This unchanged warning is being
observed, not hidden by disabling `accept-dns`.

## Twenty-four-hour observation completion

The final read-only check ran at `2026-08-04T15:38:56Z`, 24 hours, 29 minutes,
and 7 seconds after successful replacement-link activation. All three sealed
evidence directories remained mode `0700` with mode-`0600` files, all three
`SHA256SUMS` manifests passed, and their recorded manifest hashes were
unchanged.

NetworkManager journal evidence after `2026-08-03T15:09:49Z` contained zero
Ethernet carrier-down, disconnect, unavailable, link-loss, or activation-failure
events. Ethernet and Wi-Fi were connected. Ethernet remained preferred at
metric 100, while `DDB Wi-Fi Failover` remained connected with autoconnect
enabled and IPv4 and IPv6 metric 600. The Ethernet link remained 2500 Mb/s,
full duplex, with autonegotiation on and link detected.

Router DNS, MagicDNS, public-IP reachability, SSH over the existing Tailscale
route, Tailscale's Running and online state, all seven enabled and active DDB
timers, successful last service results, and zero failed user units passed.
Tailscale retained the previously documented DNS-forward health warning while
all direct DNS, MagicDNS, internet, SSH, and Tailscale connectivity checks
passed. `accept-dns` was not changed.

Exact deltas from the replacement-cable baseline were:

- RX: +439,582,481 bytes, +835,678 packets, and +101,480 multicast packets;
- TX: +109,472,825 bytes and +512,986 packets;
- RX errors, RX drops, RX missed errors, TX errors, TX drops, carrier errors,
  collisions, alignment errors, and TCAM drops: +0 each;
- the separate driver `rx_mac_missed` lifetime counter: +95,185, from 1,418,819
  to 1,514,004, while interface RX missed errors and drops remained zero.

The completion inspection changed no network, credential, service, timer, DNS,
Tailscale, publication, or production configuration. Every `DDB-PC-012`
completion gate now has recorded evidence, so the item is complete. No successor
was activated because the next pending queue item requires David's explicit
approval.

## Independent canonical closure verification

Before recording the completion on current `main`, a new read-only verification
ran at `2026-08-05T02:10:07Z`, 35 hours and 18 seconds after replacement-link
activation. All three sealed manifests and permissions still passed. The
NetworkManager journal still contained zero suspect Ethernet carrier events.
Ethernet remained connected and preferred at metric 100, at 2500 Mb/s full
duplex with autonegotiation and link detected. `DDB Wi-Fi Failover` remained
connected with autoconnect enabled and IPv4 and IPv6 metric 600.

Router reachability, public-IP reachability, router DNS, MagicDNS, SSH over the
existing Tailscale route, Tailscale Running and online state, all six currently
enabled DDB timers, successful last service results, and zero failed user units
passed. The intentionally disabled Counter timer remained disabled and inactive.
The previously documented Tailscale DNS-forward warning remained while direct
DNS and connectivity checks passed, and `accept-dns` remained enabled.

Traffic deltas from the replacement-cable baseline were RX +593,569,762 bytes,
+1,161,308 packets, and +151,104 multicast packets; TX +156,569,436 bytes and
+721,278 packets. RX errors, RX drops, RX missed errors, TX errors, TX drops,
carrier errors, collisions, alignment errors, MAC errors, and TCAM drops each
remained at a zero delta. The separate `rx_mac_missed` lifetime counter was
+141,259 while interface RX missed errors and drops remained zero.

This verification changed no network or production state. David separately
authorized the unified X Manager-to-DDB evening handoff to be placed next in
the deterministic queue; queueing does not authorize its implementation.

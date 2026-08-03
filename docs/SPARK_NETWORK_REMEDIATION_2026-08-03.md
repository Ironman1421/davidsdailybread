# Spark Ethernet and Wi-Fi failover remediation, 2026-08-03

Status: in progress; configuration and controlled tests complete, physical-path
inspection and the required 24-hour observation remain open.

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

## Current state and open gates

Post-change evidence is sealed at:

`/home/david/.local/state/ddb-pc-012/20260803T144723Z-post`

It contains 16 mode-`0600` files with manifest hash:

`91dc884e94cf2bf8571c1aa62038d6ae6a69dd8de3008f664fc814b99996bbda`

Tailscale still reports its DNS-forward warning even though router DNS,
MagicDNS, bidirectional Tailscale ping, and SSH all pass. `accept-dns` remains
enabled; the audit explicitly forbids disabling it as a cosmetic workaround.

Two completion gates remain open:

1. A person must inspect, reseat, or replace the Ethernet cable and its eero or
   switch port, then record what physical path changed. Remote evidence proves
   the link is currently healthy but cannot prove a physical repair.
2. The 24-hour observation starting `2026-08-03T14:47:23Z` must complete. Codex
   automation `complete-ddb-spark-24h-network-observation` is scheduled for
   2026-08-04 at 07:48 PDT to inspect carrier journals, routes, DNS, Tailscale,
   SSH, timers, link counters, and both evidence manifests.

`DDB-PC-012` remains `in_progress` until both gates have evidence.

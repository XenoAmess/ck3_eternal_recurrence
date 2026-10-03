# Government read-only semantic capture on CK3 1.20.0.3

## Observed cost and actual cadence

The Robert-only v30 window `m7-robert/v30-next-normal30-awaiting-gold-fix-01`
completed 30 actual game days in 30 formal `life-advance` turns without a natural
modal. Its timing window is 589.4469541 seconds. The completed run records
`production-source-3223af63`; the proposed leaf patch uses the current immutable
`production-source-db463118` government transport, whose full source is pinned
in the external delivery. This offline work earns no new live credit.

Every turn requested one day at speed 3 with `remote_enemy_route`. In the first
paused input, enemy army 67109295 is moving toward province 2640 with a complete
28-node route; Robert's controlled army is stationary in province 2614. The
existing `_life_advance_horizon_days` branch returns the one-day bound for a
non-retreating enemy with a move target, route, or moving state. The separate
timeline selector permits speed 3 for a complete disjoint remote route while
keeping the one-day bound. All 30 emitted horizon/policy pairs agree with those
existing rules. This is a current state input, not evidence of cadence regression.
No change to 1/7/30 cadence, speed, policy, native flags, or war execution is made.

| Measurement | Calls / records | Seconds |
| --- | ---: | ---: |
| Formal service, all turns | 30 | 581.3912099000881 |
| Planning before submit, contained in formal service | 30 | 542.5229930000787 |
| Dispatch and verification after submit, contained in formal service | 30 | 38.823841800010996 |
| `take_snapshot`, inclusive | 376 | 402.2512259 |
| Government query, inclusive and overlapping snapshots | 30 | 116.6739346 |
| Internal semantic snapshot, nested in other methods | 1,216 | 1.9733294 |
| Explicit history-omitted snapshot, nested in `take_snapshot` | 75 | 0.1375847 |
| External capture projection + serialization + writes | 669 | 2.9206097995629534 |
| Final checkpoint | 1 | 2.403257500001928 |

The Driver counters are **inclusive**. Government-query time includes its
snapshot reads; it must not be added to `take_snapshot` time. Likewise formal
planning is already included in formal service. External captures projected
468,488,296 bytes, but their measured write pipeline is under three seconds;
that volume is not evidence of a current bottleneck. The final preserved Driver
state reports 54,499,423 bytes and 4,533 history records; no history body was read
for this analysis.

## Minimal change

`query_government_runtime_adapter_private_v1` originally calls default
`driver.take_snapshot()` for `before` and `after`. Default public snapshots
deep-copy `_command_history` through `_history_snapshot()`. This query consumes
only the semantic frame: revision, native revision, paused/map state, actor,
date, snapshot ID, and build identity. Neither it nor its normalizer consumes
`native_command_history` or rollback-history fields.

Both reads now reuse the existing `take_internal_semantic_snapshot` method when
present, with the established `take_snapshot` fallback for compatible Drivers.
The request, native-result normalization, build/revision checks, living-player
check, and final paused/date/actor checks are preserved verbatim. Public
snapshot exports, historical receipts, persistence, and actual queries remain
unchanged. On the measured 30-turn route this removes 60 redundant full-history
copies. No measured percentage or wall-clock speedup is claimed before a new
ordinary production turn exercises the patched leaf.

```mermaid
flowchart LR
    F[Paused Robert semantic frame] --> B[Read before: existing semantic helper]
    B --> G[Same original revision / map / living actor checks]
    G --> Q[Original registered government query]
    Q --> N[Original native envelope / build / frame normalization]
    N --> A[Read after: same semantic helper]
    A --> C[Original paused / date / actor checks]
    C --> R[Government context for ordinary nonwar planning]
```

## Qualification and next validation

This is a Python leaf source change, `static-ready`, with one successful
`compile(..., 'exec')` syntax check of the exact proposed source. The existing
semantic helper already underlies qualified planning and native query callers;
no mirror tests or old suite was repeated. ROOT owns canonical application,
commit/push, new-head CI, and the next ordinary paused government query. That
actual query will validate the changed path without replaying old game stages.
Do not claim a new `production-live loop` or completed gameplay capability from
this optimization alone.

The whole-loop snapshot counter still includes other historical exports. This
bounded package deliberately fixes the two proven, unused history exports in
the government leaf. No additional caller is modified, and no new audit, gate,
or persistent cadence is introduced. The previous semantic/performance work at
`1b75` remains accepted; this finding is a newly measured leaf in the v30 window.

Evidence and source pins: external
`artifacts/g2-maintainer-2026-10-02/resume-12003/recent-loop-cost-12003/DELIVERY.json`,
`REPORT-FIELDS.json`, and `MEASURED-SUMMARY.json`. Exact game build is
1.20.0.3 / Steam build 25652598, EXE SHA-256
`94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`.

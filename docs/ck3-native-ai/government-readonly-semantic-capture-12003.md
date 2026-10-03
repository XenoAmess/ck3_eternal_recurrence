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

The initial Python leaf source qualification was `static-ready`, with one successful
`compile(..., 'exec')` syntax check of the exact proposed source. The existing
semantic helper already underlies qualified planning and native query callers;
no mirror tests or old suite was repeated. ROOT owns canonical application,
commit/push, new-head CI, and ordinary paused government queries. The new v32
closed-run qualification below validates the changed path without replaying old game stages.
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

## v32 actual production path qualification

After ROOT confirmed managed finite run 41074 CLOSED with exit code 0, a single
offline extraction read the new result, Driver timing aggregate, and the first
completed turn trace from
`m7-robert/v32-religion-type-tax-following-normal7-01`. The actual source is
`production-source-8cf176b4`; ROOT identifies managed CK3 PID 109732. The window
completed **7 actual days, 10 formal turns, and 0 natural modals**, ended paused at
raw date 53236344, and reports `normal-time-target-reached`. ROOT's saved campaign
accounting is 3,834 cumulative days / 681 continuation days / day-03 +586; those
days belong to the campaign runner, not to this optimization's credit.

The first formal turn is
`query-player-child-default-marriage-result-v1-private`, with zero time advance.
Its ordinary nonwar plan includes an **available** government context and native
adapter result for Robert 29829 at raw date 53236176. Public query revision is 2,
native revision is 5, and both queried and post snapshot IDs are `native:5`.
`same_frame_ready`, `core_adapter_ready`, and ordinary goal-context readiness are
true, with the same exact 1.20.0.3 EXE identity and no unavailable reason. This is
the changed government's actual production path returning through its original
normalizer and frame/build/actor checks; it is not an ACK substituted for a query.

| New v32 Driver aggregate | Count | Inclusive seconds |
| --- | ---: | ---: |
| Government query | 10 | 11.9845279 |
| Internal semantic snapshot, all callers | 355 | 0.5338419 |
| Public `take_snapshot`, all callers | 105 | 86.1559378 |
| Explicit history-omitted snapshot | 36 | 0.0493137 |

The timer window is 144.2540125 seconds. Counts and durations above are aggregate
and inclusive; overlapping methods must not be added. The published source has
two semantic reads per government query, so the 10 actual query calls imply 20
reads through that source path. **20 is a source-derived count, not an independent
per-caller timer**; 355 is the directly measured whole-Driver semantic count.
No additional caller or policy is modified.

The leaf has now passed actual production-path qualification. This adds no new
gameplay milestone, government policy, complete OODA loop, or G2/NW completion
credit. The prior v30 thirty-day window and this v32 seven-day window differ in
game state and formal action mix. Their durations are retained as observations,
without a controlled speedup percentage or an equal-condition wall-clock claim.
Existing cadence, timeline speed selection, native flags, and frame checks are
preserved. No old benchmark, fixture, L0 suite, SDK call, or game action was
repeated by the extractor.

Evidence:
`recent-loop-cost-12003/actual-v32-government-semantic-01/REPORT-FIELDS.json`,
`EXTRACTION-REPORT.json`, and `DELIVERY.json` pin the new result and single turn.
The report status is `production-live primitive` qualification for the changed
read-only query leaf; its new gameplay/loop-credit field remains false.

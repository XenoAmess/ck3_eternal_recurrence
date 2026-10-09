# Normal three-day route window (1.20.0.4)

Source baseline: `e5fd088cde640b0a1ea29ff40888af95d9300c95`. Root completed Native49 native and registered compound-consumer offline qualification on 2026-10-09. Readiness is **static-ready**; Native49 is not deployed and has no live qualification. Root owns execution. The actual HOT05 one-day result advanced raw date `53288568 -> 53288592` and watched zero armies. Its next Army query took 116.77 seconds. Repeating that granularity limits useful ordinary war progress.

## Native input tree sealed before policy

`RouteContactHorizonRequest` has no day-count operand. The `-h-1-` spelling means one hostile public Unit ID. `ReadRouteContactHorizon` in `ck3_12002_routes.cpp` constructs an exact one-day conflict window, but publishes each subject and hostile's complete committed route and corresponding arrival dates. `BuildTimelineIntervals` / `AppendContactConflicts` use closed occupancy and opposing-edge overlaps. A separate software window can replay those complete same-frame timelines for three days without changing the original H1 observation.

The adopted actual4 tactical daily sentinel binds the mapped core and Unit/Army/Combat storage directly. Its Arm operation accepts a positive whole-day deadline, speed 1–5, and at most 64 watched public Unit IDs. Post-original daily evaluation stops on deadline, native pause, unavailable or changed physical identity, route target, combat, retreat, and combat terminal markers. The existing Unit source proves `CUnit+0x20 -> Province+0x10`; the current fingerprint omits that actual position. Adding that witness lets an intermediate arrival stop this window even when the final route target stays unchanged.

```mermaid
flowchart TD
  A[Fresh same-frame H1 and complete route/arrival arrays] --> B[Rebuild closed province and opposing-edge intervals up to 3 days]
  B --> C[All relevant controlled routes and stationary positions covered]
  C --> D[Explicit 2 or 3 day ordinary step]
  D --> E[Existing native watched exactclock: subject, controlled siblings, hostiles]
  E --> F[Original daily update]
  F --> G{Deadline or actual Province/target/combat/retreat change or native pause?}
  G -->|yes| H[Pause and return actual elapsed days plus fresh state]
  G -->|no| F
  B -->|contact inside first day| I[Existing one-day contact policy]
  A -. future changed orders, modifiers, speed, AI choice .-> U[Not simulated by frozen-current-route projection]
```

## Counter-policy and scope

The normal moving-army policy may select an explicit window of at most three days only after recomputing the full chosen window from the same-frame arrays. A later contact reduces the number of complete contact-free days; closed contact endpoints are excluded. All controlled moving siblings require their existing same-frame route evidence, and stationary positions use the already observed Province plus the same hostile timelines. Missing longer-window evidence retains the existing one-day path.

Execution reuses the existing native tactical sentinel and its normal pause/event/result handling, watches the relevant public Unit IDs, and records actual elapsed days. It performs one resume. It does not write movement state or assume that three calendar days actually elapse. The post-original marker can observe combat after it begins; this package makes no promise to stop before battle. A native paused event or the existing Python decision-boundary observer can end the tranche early.

The frozen route calculation does not replay future native AI orders, changed commander movement values, route recalculation, or all native war decision inputs. Those are quality gaps, not claims of a full future battle forecast. The actual arrival marker closes the concrete omitted position witness. No new query, empty metadata leaf, strategic war prohibition, or full-month simulation is introduced.

## Actual Native49 offline qualification, 2026-10-09

Root sealed GREEN at **11:02:22 UTC**. The sole new native whole fixture and
sole registered compound consumer each ran once, with **four packets each**.
The compound uses the normal selector and real Driver execution entry with
offline seams: complete three-day route coverage selects a longer step,
second-day contact retains one-day progression, and a native position marker
ends a requested three-day tranche with its actual elapsed result. Prior H1,
route and clock qualifications were retained without old FIRST replay.

| Source role | Actual pin |
| --- | --- |
| Feature author | `70989fa30d07754a46457bbb0ffb59ecd42df449` |
| Root frozen source, new compiles and qualification | `65c0cc8fd10fc66e168785affa4fac5d14091651` |
| Published baseline for this documentation increment | `8024d9692d7564a300e96f6e3d76a161a407da79` |
| Three retained fixture provider objects | Native47 qualified `a2771c6016247e73d689c4bb8a825d334928bb44` |

The frozen native source is
`Z:/gbs-runtime49-route-window-root-source`. The canonical receipt retains
mixed object lineage; the documentation baseline does not retag those
compiled objects or the qualification source.

Attempt01 remains RED after **seven GREEN compiles** (six production owners
and one fixture; Bridge compile **16.3754996 s**), one fresh Runtime434 archive
(**0.4090565 s**) and DLL link (**0.8812579 s**). Its fixture link lacked
`Serialize`; attempt02's fixture link then lacked `Readprofile`, both LNK1120.
Neither attempt ran a FIRST. Root closed the actual fixture provider list
statically: the original five objects plus the already qualified Features333,
Render171 and Reader172 objects, **eight objects total**, with zero additional
project undefined symbols. That closure is retained in
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/runtime49-route-window-preparation/ROOT-FIXTURE-PROVIDER-STATIC-CLOSURE.json`.

Retry03 performed **zero compiles, zero archives and zero DLL links**. It
linked the closed fixture (**0.1295253 s**), ran the unique native FIRST
(**0.1341311 s**) and then the unique registered consumer FIRST
(**4.7848367 s**). Both were GREEN. The two earlier failed results remain
separate from the selected retry03 result.

The production closure is **734 owners**: Bridge299, Runtime434, Protocol1.
This increment replaces **Bridge3 + Runtime3**, retaining **728 owners** and
**502 compiler-command rows**. Runtime434 was freshly archived once in
attempt01. The retained GREEN DLL is **13,419,520 bytes**, Root-recorded SHA-256
`99d20042d57d895abd95d1bfee996075f2b1ce198d07b74aaea7ae0a39656c9c`.
No retained object or helper binary was recompiled or rehashed by this
qualification documentation work.

Canonical metadata is under
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/entry-live-fix49/`:
`ROOT-TACTICAL-DAILY-ROUTE-WINDOW-QUALIFICATION.json`,
`ROOT-PARENT-RUNTIME-INCREMENTAL-DLL.json`, and `manifest.json`.
The actual results are
`Z:/g2-native49-build01/attempt01/ROOT-NATIVE49-RESULT.json`,
`Z:/g2-native49-build01/attempt02/ROOT-NATIVE49-RESULT.json`, and
`Z:/g2-native49-build01/attempt03/ROOT-NATIVE49-RESULT.json`.

This is **static-ready, offline qualification only**. Native49 has no
deployment, live, fullEntry, action, action-day or G2 credit. Root's actual
Native48 Game result remains separate and does not establish Native49 live
behavior. The next capability step is Root's own deployed ordinary-campaign
route-window result with observed actual elapsed days and stop reason.

External source and cost ledger:
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261009/normal-route-horizon-efficiency/`.
October 9 / ISO 2026-W41. The source-author and documentation lanes performed
no compiler, test, FIRST, binary hash, SDK or Game execution.

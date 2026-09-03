# Phase 2 group dependency scan (2026-09-03)

## Scope and status

This is a **read-only static scan**.  It compares the acceptance fixture
`tools/fixtures/zg361_phase2_seed_bootstrap`, the byte-authoritative `none`
51-file overlay, the current `mod_zhongguo_style` source, and the disposable
group copies under
`Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903`.

No canonical source, release projection, or fixture was changed by this scan,
and **CK3 was not started**.  The group directories are independent variants
(each starts with the same 51-file `none` core); they are not cumulative
patches.  The `fixture` sibling in the bisect directory is acceptance-only and
is not counted as product content.

The old core is a byte overlay captured by the formal current-bridge GREEN
run, not a claim that the current checkout's 51 paths are byte-identical.  The
authoritative manifest and the core audit are
[`phase2-core-startup-projection-2026-09-03.json`](phase2-core-startup-projection-2026-09-03.json)
and [`phase2-core-projection-audit-2026-09-03.md`](phase2-core-projection-audit-2026-09-03.md).

## Direct fixture ABI gap

The fixture calls five public effects from
`tools/fixtures/zg361_phase2_seed_bootstrap/events/zga_phase2_seed_events.txt`
(lines 37, 40, 45, 112 and 114).  A token search of the old
`none/zhongguo_361` product tree found none of these definitions.  Their
current source definitions are:

| fixture call (line) | symbol absent from old 51 core | current definition (source line) | owning group | role |
| --- | --- | --- | --- | --- |
| `zga_phase2_seed_events.txt:37` | `zg361_b1_open_cycle_effect` | `common/scripted_effects/zg361_b1_runtime_effects.txt:1550` | `b1` | open the B1 manager cycle |
| `zga_phase2_seed_events.txt:40` | `zg361_ip_open_x_case_effect` | `common/scripted_effects/zg361_incident_platform_runtime_effects.txt:13306` | `incident` | public X-case entry over the supplied subject |
| `zga_phase2_seed_events.txt:45` | `zg361_we_open_portfolio_effect` | `common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt:84` | `workforce` | public workforce portfolio entry |
| `zga_phase2_seed_events.txt:112` | `zg361_b2_on_result_frozen_effect` | `common/scripted_effects/zg361_b2_runtime_effects.txt:143` | `b2` | consume a frozen result tuple |
| `zga_phase2_seed_events.txt:114` | `zg361_b2_on_notice_delivered_effect` | `common/scripted_effects/zg361_b2_runtime_effects.txt:351` | `b2` | consume the delivered notice tuple |

The many `zg361_result_*` and `zg361_b2_case_*` names in the fixture are
variables (state fields), not top-level scripted definitions; treating them as
missing files would be a false positive.

### Transitive symbols absent from the old core

The following is a strict top-level-definition scan of the current source.  It
follows custom effect/trigger/value references, strips comments, ignores CK3
built-ins, and does not follow delayed event IDs.  Counts are therefore a
conservative syntactic closure, not a claim that every branch executes in the
seed run.

* **B1 root — 28 definitions, 14 absent from old core.**  The missing set is
  eight B1 effects (`zg361_b1_classify_function_effect`,
  `zg361_b1_consume_manager_liabilities_as_subject_effect`,
  `zg361_b1_freeze_001_013_policy_effect`,
  `zg361_b1_freeze_135_145_policy_effect`,
  `zg361_b1_initialize_subject_case_effect`,
  `zg361_b1_open_cycle_effect`,
  `zg361_b1_register_common_superior_bank_effect`,
  `zg361_b1_snapshot_owner_bound_kpi_effect`), three shared kernel symbols
  (`zg361_case_kernel_full_guard_trigger`,
  `zg361_case_kernel_receipt_is_current_trigger`,
  `zg361_case_kernel_record_operation_effect`), and three value definitions
  (`zg361_b1_goal_adjustment_value`, `zg361_ip_next_cycle_kpi_value`,
  `zg361_mg_due_organization_kpi_value`).
* **Incident X root — 19 definitions, 17 absent.**  Eight incident effects
  (`zg361_ip_open_x_case_effect`,
  `zg361_ip_open_x_case_on_subject_effect`,
  `zg361_ip_capture_real_incident_effect`,
  `zg361_ip_freeze_x_probe_effect`,
  `zg361_ip_m192_apply_effect`, `zg361_ip_m195_apply_effect`,
  `zg361_ip_mark_x_not_applicable_effect`, `zg361_ip_x_dispatch_01_effect`)
  plus nine X/kernel symbols (`zg361_case_kernel_can_open_trigger`,
  `zg361_case_kernel_full_guard_trigger`,
  `zg361_case_kernel_initialize_case_effect`,
  `zg361_case_kernel_receipt_is_current_trigger`,
  `zg361_case_kernel_record_operation_effect`,
  `zg361_case_kernel_schedule_deadline_effect`,
  `zg361_case_kernel_transition_effect`,
  `zg361_case_x_open_effect`, `zg361_case_x_advance_01_effect`).
* **Workforce root — 236 definitions, 234 absent (conservative upper bound).**
  The closure includes all syntactic AB/AC/AD/AL branches, WAD helpers and
  workforce fact adapters.  The old-core gap is the workforce/domain body plus
  the seven shared kernel symbols
  (`can_open`, `full_guard`, `initialize`, `receipt_is_current`,
  `record_operation`, `schedule_deadline`, `transition`) and the 24
  `zg361_case_{ab,ac,ad,al}_{open,advance_*}` symbols.  A prior branch-pruned
  pass counted 207; 236 is intentionally retained here as the safer static
  upper bound and must not be read as a live execution count.
* **B2 result root — 15 definitions, all absent.**  These are the B2 result
  consumer and its `m069`, `m072`, `m078` and `m081` helpers.
* **B2 notice root — 27 definitions, 22 absent.**  The B2 notice helpers are
  absent, and the current notice path additionally references the newly added
  `zg361_b1_goal_adjustment_value` in `common/script_values/zg361_values.txt`.

The old-core comparison explains why mounting a domain file alone is not a
valid closure.  In particular, `case_kernel` is a shared ABI layer, while the
B1 KPI path also needs the incident and manager value definitions.  At file
granularity the smallest shared additions are:

| shared input | size | script lines | why it is needed |
| --- | ---: | ---: | --- |
| `common/scripted_effects/zg361_case_kernel_effects.txt` | 172,748 B | 5,494 | initialize/record/transition/deadline helpers |
| `common/scripted_triggers/zg361_case_kernel_triggers.txt` | 2,939 B | 105 | open/full/receipt/deadline guards |
| `common/script_values/zg361_values.txt` (current revision) | 12,071 B | — | supplies `zg361_b1_goal_adjustment_value` (the old overlay is 11,014 B) |
| `common/script_values/zg361_incident_platform_runtime_values.txt` | 6,427 B | 174 | supplies `zg361_ip_next_cycle_kpi_value` |
| `common/script_values/zg361_manager_governance_runtime_values.txt` | 3,522 B | 100 | supplies `zg361_mg_due_organization_kpi_value` |

The values above are source-file sizes; they are not proposed release edits.
For an A/B, copy only the required bytes into a disposable profile or mount a
whole named group plus the shared layer.  Do not alter the canonical tree based
on this static result alone.

## Group size ledger

The index and a fresh file walk agree on the following totals.  `script lines`
means lines in `.txt` and `.gui` files outside `localization`; `loc lines` is
all localization lines.  `new-file delta` excludes changed paths already in
the 51-file core.  This distinction matters for `generated` and `scoreboard`.

| variant | files | payload | script lines | loc lines | new files / bytes / script / loc |
| --- | ---: | ---: | ---: | ---: | --- |
| `none` | 51 | 7,137,587 B | 71,901 | 18,515 | baseline |
| `b2` | 62 | 7,454,751 B | 78,290 | 18,893 | 11 / 317,164 B / 6,389 / 378 |
| `manager` | 64 | 7,605,578 B | 80,579 | 18,578 | 13 / 467,991 B / 8,678 / 63 |
| `b1` | 62 | 7,729,464 B | 82,138 | 19,280 | 11 / 591,877 B / 10,237 / 765 |
| `incident` | 63 | 7,922,005 B | 87,159 | 19,253 | 12 / 784,418 B / 15,258 / 738 |
| `credit` | 62 | 8,613,911 B | 107,651 | 19,739 | 11 / 1,476,324 B / 35,750 / 1,224 |
| `feedback` | 62 | 8,650,254 B | 101,799 | 20,846 | 11 / 1,512,667 B / 29,898 / 2,331 |
| `career` | 73 | 8,760,961 B | 102,505 | 21,512 | 22 / 1,623,374 B / 30,604 / 2,997 |
| `phase3` | 62 | 9,196,582 B | 119,806 | 20,099 | 11 / 2,058,995 B / 47,905 / 1,584 |
| `workforce` | 152 | 12,906,558 B | 162,165 | 20,837 | 101 / 5,768,971 B / 90,264 / 2,322 |
| `scoreboard` | 51 | 13,711,851 B | 146,458 | 18,515 | 0 / 0 B / 0 / 0; 3 changed core paths (+6,574,264 B, +74,557 script) |
| `generated` | 53 | 14,082,062 B | 157,214 | 18,515 | 2 / 620,531 B / 11,879 / 0; 2 changed scoreboard paths (+6,323,944 B, +73,434 script) |
| `all-new` | 279 | 29,351,046 B | 442,263 | 31,363 | 228 / 15,612,722 B / 295,315 / 12,762; 21 changed core paths (+6,600,737 B, +75,047 script, +86 loc) |

The workforce 152-file total above is the current bisect index value; a stale
12,913,177-byte figure from an earlier disposable run must not be used.
Non-localization additions are the expected effect/event files (and two
workforce court-position files); each domain group also carries its language
localization fan-out.  `generated` adds compensation effect/event files and
changes the two generated scoreboard inputs; `scoreboard` changes those two
inputs plus `gui/zg361_scoreboard.gui`.

## File-level dependency map

The direct seed path is:

```text
seed.101 (real AI liege)
  ├─ B1  zg361_b1_open_cycle_effect
  ├─ IP  zg361_ip_open_x_case_effect(SUBJECT)
  └─ WE  zg361_we_open_portfolio_effect(SUBJECT)
seed.102 (real player, only when result tuple exists)
  ├─ B2  zg361_b2_on_result_frozen_effect
  └─ B2  zg361_b2_on_notice_delivered_effect
```

The smallest **logical** closure for these calls is therefore:

1. the old 51-file core;
2. the shared `case_kernel` effect + trigger files;
3. the B2 effect/event group (the smallest direct domain group);
4. B1 effect/event files, plus the three value definitions listed above;
5. incident effect/event files (and its value file if the KPI branch is
   followed);
6. workforce effect/event/court-position files, plus the shared central
   adapter when the AL/runner branch is reached.

At a whole-group boundary, B1's KPI references pull in the incident and
manager value files, and the workforce group is not self-contained without
`case_kernel`.  It is cheaper and more diagnostic to inject those small value
files explicitly than to mount every manager/incident event immediately.

The direct seed does **not** call phase3, career, feedback, credit, generated,
or scoreboard code before its visible card.  Those groups may be required by
later central stages, but adding them before the direct closure only increases
parser/load pressure and makes the first failing group ambiguous.  Their
individual event files must be tested after the direct closure is known.

Delayed event IDs are deliberately not treated as immediately executed calls
in the counts above.  Once a group reaches a real delayed event, follow its
`expire_deadline`/receipt guard and add the event's owning file in a separate
step; do not infer a successful transition from an event being scheduled.

## Recommended serial A/B order and verdict rule

CK3 launch remains an exclusive gate.  The following order keeps each run
small while preserving the ABI closure:

| order | disposable projection | purpose / expected first-failure signal |
| ---: | --- | --- |
| 0 | old exact `none` 51 | control: must reach `Frontend` and exit cleanly |
| 1 | `none` + case-kernel files | isolate shared ABI parser cost; no domain event is expected |
| 2 | previous + B2 | smallest visible seed consumer; a failure here points at B2 or its current core value dependency |
| 3 | previous + B1 + required value definitions | exercise cycle opener and distinguish B1/KPI closure |
| 4 | previous + incident | exercise X opener and its X/kernel closure |
| 5 | previous + workforce (+ central adapter when needed) | largest direct-path addition; likely load-pressure boundary |
| 6 | manager, then phase3, credit, feedback, career | later central branches, one group per run |
| 7 | generated, then scoreboard | defer the largest generated/GUI changes until domain closure is green |

For every run, record the exact projection tree, CK3 window/launcher mode,
`Frontend` observation, `error.log` classification, exit code, and cleanup
result.  **First failure** means the first projection that fails to reach
`Frontend` within the fixed harness timeout or emits a fatal loader/parser
error; a delayed fixture card or a non-fatal missing historical relation is
not by itself a load failure.  Keep the failed profile as evidence and do not
promote a group to the canonical release until a fresh controlled A/B and the
static checks agree.

## Evidence boundary

The broad 279-file product and no-scoreboard runs already stalled after roughly
880/881 `on_actions`, while the exact 51-file overlay reached `Frontend` and
exited with code 0.  This scan narrows the next experiment to the direct
dependency closure; it does **not** certify that any group is production-live,
 nor does it prove that the static closure is the only cause of the broad-load
 stall.  Runtime-error triage remains separate: fixture-only unknown effects
 must not be conflated with the current full-product projection.

# Phase 2 direct-union-v2 closure and workforce bisect (2026-09-03)

## Status and scope

This note records a read-only static analysis and disposable bisect inputs. It
does not change the canonical `mod_zhongguo_style` tree, does not alter the
acceptance fixture, and did not start CK3. The external `_runtime` trees are
reproducible working artifacts, not release content.

The analysis starts from the exact `direct-union-v2` product projection and
the five public effects called by the Phase 2 seed fixture. Custom scripted
effects, triggers, values, and event IDs were resolved by owner file. CK3
built-ins and variable/state names were excluded; delayed event IDs were
counted separately from immediately callable definitions.

## Inputs and runtime boundary

| input | files | bytes | identity |
| --- | ---: | ---: | --- |
| `direct-union-v2` disposable product | 201 | 15,245,061 | projection source `97f9c0f82ce7f5e8712ac21db8879b521c6828bd6c95cd5bb37fa80c4e7c5602` |
| exact `none` control core | 51 | 7,137,587 | old formal 51-file baseline |
| current full source freeze | 513 | 81,493,847 | static comparison only |
| current workforce group (index) | 152 | 12,906,558 | current value; the earlier 12,913,177 B figure is stale and must not be used |

The direct-v2 projection manifest is
`Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903\projection-direct-union-v2.json`.
Its projection hashes are:

* `source_tree_sha256`: `97f9c0f82ce7f5e8712ac21db8879b521c6828bd6c95cd5bb37fa80c4e7c5602`
* `formal_overlay_tree_sha256`: `4913ebb63e073ad5df114e94e92c8bd19dec409eb740d544bc4158765732dfbe`
* `file_list_sha256`: `821bb490ed6cbc2449f05cb82d58cabbd20d26d67ec17e7df8f8b0a08e750103`

The formal v1 run logged two unknown B1 triggers
(`zg361_b1_peer_submission_actor_trigger` and
`zg361_b1_peer_submission_recipient_trigger`). The matching v2 run has an
empty `error.log` (0 bytes, SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`) and
debug markers for `gui/frontend_main.gui` loading and `Total of : 881` events.
Its report still says `frontend.observed=false`; therefore this is loader/error
evidence, not a formal Frontend GREEN result.

## Direct fixture roots and ABI gap

The seed fixture calls these five effects that are absent from the old 51-file
core:

| fixture call | owner in direct-v2 | purpose |
| --- | --- | --- |
| `zg361_b1_open_cycle_effect` | `common/scripted_effects/zg361_b1_runtime_effects.txt` | open the B1 manager cycle |
| `zg361_ip_open_x_case_effect` | `common/scripted_effects/zg361_incident_platform_runtime_effects.txt` | open an X case |
| `zg361_we_open_portfolio_effect` | `common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt` | enter the workforce portfolio |
| `zg361_b2_on_result_frozen_effect` | `common/scripted_effects/zg361_b2_runtime_effects.txt` | consume the frozen result tuple |
| `zg361_b2_on_notice_delivered_effect` | `common/scripted_effects/zg361_b2_runtime_effects.txt` | consume the delivered notice tuple |

The fixture also asks for the two shared triggers
`zg361_is_celestial_liege_trigger` and `zg361_is_reviewable_vassal_trigger`.
Names such as `zg361_result_*` and `zg361_b2_case_*` in the fixture are state
variables, not missing top-level definitions.

## Minimal restricted closures

The following candidates use only owner files present in direct-v2 and retain
the old 51-file core. `zg361_triggers.txt` is a replacement of the old path,
not an additional file. Counts are static parser/load candidates, not live
execution claims.

### Callable closure (parser-first)

* 42 script files and 10,121,264 script bytes selected.
* Overlay: 66 product files, 14,430,022 bytes.
* Added beyond the old core: 15 new paths; replaced path:
  `common/scripted_triggers/zg361_triggers.txt`.
* Missing callable counts by fixed-point round: 75 (round 1), 3 (round 2),
  0 (round 3). The remaining 232 event IDs are deliberately not expanded in
  this candidate.

The 15 added paths are:

```text
common/script_values/zg361_manager_governance_runtime_values.txt
common/scripted_effects/zg361_b1_runtime_effects.txt
common/scripted_effects/zg361_b2_runtime_effects.txt
common/scripted_effects/zg361_case_kernel_effects.txt
common/scripted_effects/zg361_incident_platform_runtime_effects.txt
common/scripted_effects/zg361_manager_governance_runtime_effects.txt
common/scripted_effects/zg361_workforce_ad_fact_runtime_effects.txt
common/scripted_effects/zg361_workforce_appointment_fact_effects.txt
common/scripted_effects/zg361_workforce_attribution_fact_effects.txt
common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt
common/scripted_effects/zg361_workforce_exit_fact_effects.txt
common/scripted_effects/zg361_workforce_probation_fact_effects.txt
common/scripted_effects/zg361_workforce_rehire_fact_effects.txt
common/scripted_triggers/zg361_case_kernel_triggers.txt
common/scripted_triggers/zg361_manager_governance_runtime_triggers.txt
```

The reusable candidate is at
`Z:\ck3_mod_rewrite\_runtime\phase2-direct-union-v2-static-closure-r1-20260903\callable-core\zhongguo_361`.
The associated projection manifest is
`projection-callable-core.json` (SHA-256
`4a982c03f26121fffdf6d19fc9541a7de90823da054b818bf9ae61f7f7ae10ca`).
Its compatible source-tree digest is
`d493e3f3e3c76c8c0e7cdcf0cbda58cf36e5d0baae89cf16582b18969b6e58ed`; its
formal overlay digest is
`94848c5219583f561bb2bcb8b6e1cd2a8db820536b5639c0e0b310ad559382e5`.

The subsequent serial callable-core attempt is **RED**, which is consistent
with the intentionally omitted central owner above. Its `error.log` is 441 B
(SHA-256
`65c6f3c11320bc22c22879a218a14f7e66a513560fe06312ca65fddfaa03adf7`) and
contains exactly:

```text
else/else_if not following an if or else_if ... line 10711 (zg361_we_m275_hold_due_effect)
Unknown effect: zg361_p2c_schedule_m275_runner_requisition_effect ... line 10722
```

The run timed out without observing Frontend. This is a concrete parser/load
signal, not a reason to alter the canonical workforce file: the next narrow
diagnostic is to add the owning `zg361_phase2_central_runtime_effects.txt`
file to a fresh candidate and recompute its manifest.

### Callable + event-owner closure

* 57 script files and 10,493,252 script bytes selected.
* Overlay: 81 product files, 14,802,010 bytes.
* Added beyond the old core: 30 new paths; the same trigger replacement as
  above.
* Fixed-point rounds: `(75 callable, 200 event IDs)`, then
  `(3 callable, 32 event IDs)`, then `(0 callable, 7 event IDs)`, then clean.

The second candidate adds these 15 event/effect owners to the callable list:

```text
common/scripted_effects/zg361_workforce_normal_exit_fact_effects.txt
common/scripted_effects/zg361_workforce_remediation_fact_effects.txt
events/zg361_b1_runtime_events.txt
events/zg361_b2_runtime_events.txt
events/zg361_incident_platform_runtime_events.txt
events/zg361_manager_governance_runtime_events.txt
events/zg361_workforce_ad_fact_runtime_events.txt
events/zg361_workforce_appointment_fact_events.txt
events/zg361_workforce_attribution_fact_events.txt
events/zg361_workforce_endgame_runtime_events.txt
events/zg361_workforce_exit_fact_events.txt
events/zg361_workforce_normal_exit_fact_events.txt
events/zg361_workforce_probation_fact_events.txt
events/zg361_workforce_rehire_fact_events.txt
events/zg361_workforce_remediation_fact_events.txt
```

The reusable candidate is at
`Z:\ck3_mod_rewrite\_runtime\phase2-direct-union-v2-static-closure-r1-20260903\event-core\zhongguo_361`.
The associated projection manifest is
`projection-event-core.json` (SHA-256
`6505aacf02031c1ea70d2b3906664e2008139f8de45bbbdd0449f30f90ee8938`).
Its compatible source-tree digest is
`f25fe00faccc891f9a8a802ba39c14d29a92babf6283d6eb9decffa5268853db`; its
formal overlay digest is
`2ed2f8fbde21c55e5bdef1dd54e7e21debcba934e231678c44b31952a527ec74`.

## Full-source latent ABI (do not mount broadly by default)

Comparing direct-v2 against the current full source exposes one first-order
callable that is not in direct-v2:

```text
zg361_p2c_schedule_m275_runner_requisition_effect
  referenced by common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt
  owner: common/scripted_effects/zg361_phase2_central_runtime_effects.txt
```

Adding that owner file statically exposes the following additional callable
owners in the next round:

```text
common/scripted_effects/zg361_career_hc_runtime_effects.txt
common/scripted_effects/zg361_career_learning_runtime_effects.txt
common/scripted_effects/zg361_credit_project_runtime_effects.txt
common/scripted_effects/zg361_feedback_promotion_pip_runtime_effects.txt
common/scripted_effects/zg361_generated_compensation_runtime_effects.txt
common/scripted_effects/zg361_phase2_central_runtime_effects.txt
common/scripted_effects/zg361_phase3_metrics_delivery_runtime_effects.txt
common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt
```

Event-owner expansion then names these seven event files:

```text
events/zg361_career_hc_runtime_events.txt
events/zg361_career_learning_runtime_events.txt
events/zg361_credit_project_runtime_events.txt
events/zg361_feedback_promotion_pip_runtime_events.txt
events/zg361_generated_compensation_runtime_events.txt
events/zg361_phase2_central_runtime_events.txt
events/zg361_phase3_metrics_delivery_runtime_events.txt
```

The resulting full-source static closure is 68 script files for callable
resolution and 75 script files after event-owner expansion. It is a latent ABI
map only; it is intentionally not copied into a recommended overlay because it
would reintroduce the broad-load confounder. The exact round data is retained
in the external `analysis.json` beside the two candidate manifests.

The corrected exact workforce A+B diagnostic tree is already materialized at
`Z:\ck3_mod_rewrite\_runtime\phase2-workforce-split-exact-clean-20260903\mod_zhongguo_style`:
265 files / 15,938,098 bytes, with the monolith absent and the two part files
covering blocks 0–161 and 162–323. Its exact-pair manifest is
`Z:\ck3_mod_rewrite\_runtime\phase2-workforce-split-exact-20260903\manifest.json`
(`concat_matches_source=true`). This target is diagnostic only; the associated
serial run stopped at `Total of : 881` and did not reach history completion.

## Workforce top-level block segments

The disposable segment generator is checked in at
[`tools/phase2_workforce_block_segments.py`](../../tools/phase2_workforce_block_segments.py).
It reads bytes, finds complete top-level brace blocks while respecting CK3
comments and quoted strings, and writes new files. It never edits the source.
Every output starts with the exact six-line header and UTF-8 BOM from the
source. Ranges are zero-based and inclusive.

The first generated manifest (`phase2-workforce-block-bisect-20260903`) was
superseded after a BOM-offset defect was found. The corrected manifest is
external (not committed):

```text
Z:\ck3_mod_rewrite\_runtime\phase2-workforce-segments-corrected-20260903\manifest.json
SHA-256: 9caa5a082e5d08baf003bf93a4a4ba96ce975c07a57669963976ea26cb4d37ad
```

Source facts recorded by that manifest:

| field | value |
| --- | --- |
| source | `...direct-union-v2\common\scripted_effects\zg361_workforce_endgame_runtime_effects.txt` |
| bytes / SHA-256 | 4,636,271 / `926453fe4b3621b5381743d61f5d03ac29c1d498181702e05a9532739d334d8a` |
| BOM / header | UTF-8 BOM present / 563 bytes, 7 lines (including the BOM-bearing header line) |
| complete top-level blocks | 324 |
| source lines | 74,737 |
| generated outputs | 324 individual blocks + 21 chunks (16 each, final short) + 2 halves |

The first serial split is:

| segment | blocks | bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `halves/left.txt` | 0–161 | 1,638,031 | `823c746bec51bed5ffcc46b2810ff97f1058388e0bb8bb2d579c760a95ee1c65` |
| `halves/right.txt` | 162–323 | 2,981,381 | `8c6cfea5a613c12591f94a0ffd56049320da43213374bde53206f6e4e2a90de5` |

The largest blocks (useful when a half is RED and a finer split is needed) are:

| index | definition | source lines | bytes | block SHA-256 |
| ---: | --- | ---: | ---: | --- |
| 3 | `zg361_we_materialize_m360_route_a_from_central_effect` | 296–2902 | 478,356 | `1389d1e9ac36afb476bcad6004abeefd74c4881669cb62c3f48abde80866331e` |
| 4 | `zg361_we_materialize_m360_route_b_from_central_effect` | 2905–5509 | 469,546 | `fd3f9177c281a5e03cbc5e791e9c3d919a3ee8d90c2815e8cfaa9e73cffa3d6c` |
| 317 | `zg361_we_m360_route_a_effect` | 69623–70969 | 335,589 | `02ea7d9aaaa910859437abb2bcf5c629a6649d1b777ba315fd430077adf1b511` |
| 318 | `zg361_we_m360_route_b_effect` | 70972–72315 | 319,166 | `4f6bc5fa8d601bb40ada9863be4e875a4b2fbc7c1c5373db3dbc728a5a0c1b71` |

These are diagnostic size observations, not a reason to remove or edit a
definition. The normal order remains half → chunk → individual block so that
the first failing range is attributable.

Generate a fresh disposable snapshot or a selected range as follows:

```powershell
$src = 'Z:\ck3_mod_rewrite\_runtime\phase2-group-bisect-20260903\direct-union-v2\common\scripted_effects\zg361_workforce_endgame_runtime_effects.txt'
$out = 'Z:\ck3_mod_rewrite\_runtime\phase2-workforce-segments-rerun-20260903'
py tools/phase2_workforce_block_segments.py --source $src --output $out --chunk-size 16
py tools/phase2_workforce_block_segments.py --source $src --output "$out-left" --ranges 0-161
py tools/phase2_workforce_block_segments.py --source $src --output "$out-right" --ranges 162-323
```

Copy a selected file only into a *fresh disposable product root* at the same
relative path, then generate a matching hash-bound projection manifest. Never
replace the canonical workforce file. A selected segment intentionally omits
other definitions; missing-callable errors from such a segment are expected
and must be distinguished from a fatal parser/load error.

## Recommended serial A/B order

CK3 startup is an exclusive gate. Preparation and static manifest generation
may run in parallel, but only one CK3 launch may run at a time, with a fresh
profile and preserved report for each attempt.

1. **Control:** exact 51-file `none` core. Expected verdict is Frontend reached
   and clean exit.
2. **Parser closure:** mount `callable-core` (66 files). This tests the
   smallest fixed-point callable set without delayed events.
3. **Event closure:** mount `event-core` (81 files). This tests event-owner
   loading after callable names are present.
4. **Central first owner:** if a static or runtime failure specifically names
   the central ABI, add only `zg361_phase2_central_runtime_effects.txt` to a
   disposable copy and rerun; do not jump to all 15 omitted files.
5. **Central follow-up:** add the seven remaining callable-owner files one at
   a time (or as a recorded, single coherent group), then add the central event
   owner only when its event IDs are reached. Keep the first-failure boundary
   attributable.
6. **Workforce block bisect:** with the same non-workforce baseline, test
   blocks 0–161, then 162–323. Narrow the failing half with 16-block chunks,
   then individual blocks. Each replacement gets a new projection manifest.
7. **Later groups:** career, credit, feedback, phase3, generated, and
   scoreboard are deferred until the direct closure is understood; test one
   named group per run.

Use the existing projection/recovery runner syntax from
`docs/phase2-promo/phase2-product-projection-recovery.md`, passing both
`--product-source` and its matching `--product-projection-manifest`. Do not
reuse a manifest after changing a segment.

### First-failure rule

Record the first projection that either emits a fatal parser/loader error or
fails to observe `Frontend` within the fixed timeout. An empty `error.log`
without `Frontend` is a loader/stall result, not parser-clean. A missing event
or callable caused solely by an intentionally reduced segment is an expected
closure artifact, not proof of a source syntax defect. Preserve RED attempts
and keep them separate from the already observed v2 empty-error-log evidence.

## Verification performed

* `py -m py_compile tools/phase2_workforce_block_segments.py` — passed.
* Generator run against the pinned direct-v2 workforce file — passed; 324
  balanced blocks, the 563-byte BOM-bearing header was preserved, and the
  corrected manifest/hash set above was reproduced.
* Selected-range run for 0–161 — passed; output hash matches the corrected
  left-half hash `823c746bec51bed5ffcc46b2810ff97f1058388e0bb8bb2d579c760a95ee1c65`.
* Static closure fixed points and projection manifests were inspected from the
  external `analysis.json`/manifest files; no CK3 launch was performed.

The pre-fix manifest (`phase2-workforce-block-bisect-20260903`, header 560 B)
and its hashes are retained only as invalid historical evidence. This document
and the generator are the only committed deliverables from this read-only scan.
All candidate trees, manifests, logs, and segments remain in `_runtime` and are
intentionally excluded from Git.

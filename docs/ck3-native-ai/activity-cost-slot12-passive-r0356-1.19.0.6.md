# Activity cost: passive slot-12 raw capture after R0356

Exact CK3 1.19.0.6 Steam 23530548 `ck3.exe` SHA-256:
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The existing [cost and final-gate trace](activity-cost-slot12-r0346-boundary-1.19.0.6.md)
establishes the object and callsite. R0356's same-paused-frame stage-1 read
selected `feast_type_generic` with original IsShown, IsValid and stage-1
CanProgress all true. Its report is
`Z:\m6-activity-h3928-stage1-read-candidate-v2-20260929\operator-runs\feast-stage1-option-read-1\formal-report.txt`,
SHA-256 `562B9B2E9A01020CA593746872FFE733B030DBD6D08784E9B3F824305848BCD2`.
That proves a category Confirm opportunity. It does not prove a configured
price or permission to start the feast.

## Native read boundary

`ActivityPlanner` slot 12 at RVA `0x10AE180` calls the normal cost update
`0x10B2B30` at `0x10AE1AA`; the call return address is `0x10AE1AF`.
The update clears and recomputes the embedded `AccessCostBreakdown` object at
`planner+0x1AD8`. Its final loop calls `0x21C7B60` for each of ten raw
category aggregates. The copy address for index `i` is
`planner+0x1AD8+0x50+i*0x90+0x78`, `i=0..9`.

The default-OFF private flag
`XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1` installs an
exact-prologue detour while the primary thread is suspended at startup.
The detour calls the original update trampoline exactly once. **After** it
returns, it records a sample only when the caller return address is
`0x10AE1AF`, the game is paused, the caller is the application-main owner
thread, the played actor is present, and the planner is the exact feast
planner type. It copies all ten signed 64-bit aggregates. It does not invoke
the update on demand, select an option, progress planning, or start an
activity.

The private `query-activity-cost-slot12-raw-v1-private` command reports a
sample only if the current paused native snapshot and its bridge revision
agree, actor/date/thread match the captured frame, and the planner's owner,
activity type, stage, bytes `+0x1530..+0x1AD7`, and its bounded category and
cost-driving option rows still match the sample's configuration fingerprint.
The result identifies the normal slot-12 return
source and returns `raw_aggregate_i64[10]`. It deliberately emits
`resource_mapping=null` and `configured_cost=null`. A copied raw zero is
only a raw slot value; no index has a proven `gold` or other resource name.
The fingerprint covers the observed planner configuration region and the
`+0x1560/+0x156C` and `+0x1578/+0x1584` row vectors used by the native cost
path; it is not a claim that every game-side configuration field has been
mapped.

```mermaid
flowchart LR
  A[normal visible planner update] --> B[slot 12 calls 0x10B2B30]
  B --> C[original update returns]
  C --> D{caller = 0x10AE1AF and paused owner frame?}
  D -- yes --> E[copy 10 raw aggregates and identity]
  D -- no --> F[no sample]
  E --> G{same actor/date/planner/config at private query?}
  G -- yes --> H[raw indexed diagnostic only]
  G -- no --> I[unavailable]
  H -. resource index mapping unknown .-> J[configured cost and final Start]
```

## Next gate

Advance the already validated stage-1 category through its separate formal
action contract, then configure the planner in an owner-coordinated paused
candidate carrying this hook. A visible planner must perform the **normal**
slot-12 refresh after the final selection. A missing capture is reported as
`no_normal_refresh`, not a zero cost. At stage 5, compare an unambiguous
nonzero raw aggregate with the original GUI's
`CostBreakdown.GetCost('gold')` at
`game/gui/shared/value_breakdown.gui:800-803` in that exact configuration.
The GUI presents the planner's `AccessCostBreakdown` at
`window_activity_planner.gui:1744-1747` and `1978-1980`. The final button
uses `CanProgressPlanningStage` at `1762-1767` and `1987-1991`.
Only then bind named cost and separately read the stage-5 branch of
`0x10B0DA0`; the stage-1 true result is a different branch. Do not use
`ProgressPlanningStage` as a query, and do not promote this raw observer to
a formal cost or start capability.

The source package's exact ABI fixture checks the 14-byte refresh prologue
and the five-byte slot-12 call. Release/Debug focused tests exercise no
capture, wrong caller, valid raw capture, planner/row configuration mutation and date
change. They are source-level evidence only; this package did not launch CK3
or obtain a new live cost readback.

## Bounded operator entry

The default-OFF `native-auto-run --private-activity-cost-slot12-raw-read`
route sends `query-activity-cost-slot12-raw-v1-private` on one paused frame.
Combined with `--private-activity-feast-planner-open`, the operator first
uses the existing verified native opener and then requests the raw capture
without advancing a turn. Used alone, it queries an already open planner,
which allows a later configured stage-5 frame to be inspected without
reopening it. The operator verifies the exact private response schema,
unchanged actor/date/revision and no date-changing turn. A native
`no_normal_refresh` result remains RED, not a zero-price success. This is
operator wiring and focused fake-driver validation; it adds no live fee or
final-start evidence.

## R0359 paused live readback (2026-09-29)

The first exact-build live use of the private operator route used H3928,
`date_raw=53219928`, actor `29829`, and the paired R0343 driver. The source
was exact master `8e70959a3f83b4379cb143313e379e72776c4f74` (official
push CI `36527418273` success) with the Release DLL SHA-256
`3CA2E81EA4DF5270C16FAE406AD2BB0FDAA0D12EE2C9AF20F35EF2DF7159F295`.
The official paired no-launch preflight passed before R0359 started.

R0359 opened the feast planner and read the normal slot-12 return on the same
paused frame. The private response was `available`, with
`source=normal_slot12_return_0x10AE1AF`, `capture_sequence=128`,
`activity_key=activity_feast`, `planning_stage=1`, actor `29829`,
`date_raw=53219928`, and `snapshot_revision=3`. The source frame recorded
`revision=4/native_revision=3`; the operator reported `same_frame=true`.
There are exactly ten signed raw aggregates: index 0 is `10000000` and
indices 1–9 are `0`. `resource_mapping` and `configured_cost` are both
`null`. This proves a normal refresh and a live nonzero raw aggregate in the
stage-1 planner; it does not identify index 0 as gold or establish a payable
feast cost.

The bounded run returned `private_activity_cost_slot12_raw_observed`,
`read_only_observed`, `ok=true`. It recorded zero attempted turns and zero
gameplay actions, no date advance, unchanged save SHA-256
`A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C`,
and controlled process-tree cleanup. The [immutable formal report](Z:/m6actcostrawh3928v2_20260929/operator-runs/slot12-raw-read-1/formal-report.txt)
has SHA-256 `30EC3B42D88B51C1007EA9C32E9E4AD200EE267A28D9ECFD918EBA8D9C928E44`;
the [operator receipt](Z:/m6actcostrawh3928v2_20260929/operator-runs/slot12-raw-read-1/operator-receipt.json)
has SHA-256 `32DE37A5A0BF004D7DC7F9804185215492758D2CF19752424228126D8FDFC2AF`.

The next readback needs a configured later-stage planner and an independent
same-configuration comparison with the GUI `GetCost('gold')` value. Stage-5
final `CanProgressPlanningStage` remains separate. No typed Confirm, Start,
cost payment, or activity effect occurred in R0359.

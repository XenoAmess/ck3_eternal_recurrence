# Bounded feast stage-1 transition (CK3 1.19.0.6)

Exact executable SHA-256:
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
This is an exact-build source and disassembly result. No CK3 instance was
launched for this implementation, so the new action has no live qualification.
The R0356 selected `activity_feast` / `feast_type_generic` paused read is in
`activity-planning-stage1-option-identity-1.19.0.6.md`.

## Original decision tree and action boundary

The category Confirm button in
`game/gui/window_activity_planner.gui:922` calls
`ActivityPlanner.ProgressPlanningStage`. Its native `0x10B1330` stage-1
normal branch calls `0x10B1BD0(planner, 2)` at `0x10B13A1`, **then** tail
jumps to `0x10B1C90` at `0x10B13AE`. That second routine can recursively
advance stage 2 to 5 when its configuration rows pass, then validate the
temporary start command at stage 5 and invoke `0x10B1330` again. The latter
dispatches stage 5 to `0x10B1910`, which starts an activity. Therefore one
direct call to the full GUI operation is not bounded to stage 1.

The stage setter `0x10B1BD0(planner, 2)` itself writes `+0x1AD0=0`,
`+0x1AB0=2`, and `+0x1AB4=1`, calls the planner's primary vtable slot 25
(`0x10AEC20`), and clears `+0x1AC8` because the previous stage was 1. It
does not directly call the start path or change the selected activity type at
`+0x1530` or option rows at `+0x1560`. Slot 25 dispatches an event through
the global interface object with code `0x2B4F` and arguments `0x2F,0`; the
event's exact effects are not resolved here. The selected-special getter
`0x10AEAE0` reconstructs its result from the selected type's `+0xA88`
category and the option rows; it does not depend on cleared `+0x1AC8`.

```mermaid
flowchart LR
  A[Selected feast option, stage 1] --> B{Shown, Valid, CanProgress and same frame?}
  B -- no --> R[Reject without submit]
  B -- yes --> C[0x10B1BD0 planner, 2]
  C --> D[Stage 2 and selected option readback]
  D --> Q[Separate stage-2 selected-option query]
  D -. later separate contract .-> E[Cost and final CanStart]
  A -. full 0x10B1330 can auto advance .-> X[Stage 5 Start path]
```

## Private implementation

`XAR_CK3_ENABLE_G2_ACTIVITY_STAGE1_CONFIRM_PRIVATE_V1` defaults OFF and
requires the existing private stage-1 option reader. The typed request step
`confirm-activity-feast-stage1-v1-private` requires an expected revision,
date, actor, `activity_feast`, and `feast_type_generic`. The existing paused
application-main mailbox slot 59 executes it once. It reuses the original
`IsShown`, `IsValid`, and `CanProgressPlanningStage` evaluations on that frame,
requires the selected option, planner owner, widget, stage 1, and normal
`+0x1AD0=0` route, then calls only the stage setter. A separate native
diagnostic checks stage 2, widget visibility, same actor, feast identity,
effective selected option pointer and ID, and same paused frame. The game
snapshot before and after must match, including gold and date. The receipt
retains `submitted=true` even when the postcondition fails; a failed
postcondition is RED and does not authorize retry without fresh observation.
No pointer is serialized, and the step remains private and unadvertised.

The independent default-OFF
`XAR_CK3_ENABLE_G2_ACTIVITY_STAGE2_OPTION_READ_PRIVATE_V1` step
`query-activity-feast-stage2-option-v1-private` accepts the same expected
revision/date/actor/type/option keys. On a new mailbox request it checks the
stage-2 widget and owner, rereads the selected `activity_feast` and current
special-category row, invokes the original pure getter `0x10AEAE0`, resolves
the option's script identifier, and reports only
`feast_type_generic` as positive. This is separate from the action receipt.
The already-open feast opener can additionally reread stage-2 visibility
without dispatching another open operation.

This bounded helper is a stage transition, not activity Start. The new
source-level unit test verifies a positive stage transition, a separate
stage-2 option query, a failed retained-option postcondition, and rejection
of an invalid option or nonnormal stage route. Release bridge compilation and
focused test are static gates only. A frozen candidate still needs the R0356
paused scenario, independent stage-2 and resource readback, subsequent turn,
and required checkpoint/cold restore before any live ability claim. Stage-5
cost and final CanStart remain separate unknowns; the opaque slot-25 event
also remains a live observation item.

## R0360 first live Confirm: submitted false, reason pending

R0360 used the official H3928/raw53219928 pair with source master
`3e249604a7805acc72f5e583cae416997bbf0a2b`. The immutable
[`formal-report.txt`](Z:/m6-activity-h3928-confirm-candidate-20260929/operator-runs/feast-stage1-confirm-1/formal-report.txt)
has SHA-256
`D59B08B4D2514FA6D56EFC495E2EEE15BA1B8ECEF1E19060BBB2DB3244F5C01D`.
The planner opened and the separate stage-1 read found selected
`feast_type_generic`, shown, valid, able to progress, and
`generic_feast_confirm_ready=true` on native revision 3. The Confirm
receipt returned `precondition_rejected`, `submitted=false`,
`accepted=false`, `pending=false`; gold stayed at 120644281 raw and the
game snapshot/date stayed at raw53219928. The independent stage-2 read was
not called. The formal run is RED, with zero gameplay turns, unchanged
checkpoint save, and proven process-tree cleanup. There is no stage
transition or activity Start evidence.

The precondition result does not identify which later guard rejected it.
Offline bytes in the same frozen EXE confirm the setter signature at RVA
`0x10B1BD0` and planner vtable slot at RVA `0x41206B8` pointing to
`0x10AEC20`; those checks should not be presumed to be the live failure.
After the observed option, the remaining checks are a fresh planner
identity read, `planner+0x1AD0` read and zero comparison, and a fresh
same-frame read. A focused source change records a stable rejection reason
and the raw `+0x1AD0` byte when observed. It does not relax admission or
retry Confirm. These two fields appear only in a `precondition_rejected`
private receipt; a successful receipt keeps its previous schema shape.
Only a new, correctly paired candidate can establish the
actual failing guard and support a targeted action fix.

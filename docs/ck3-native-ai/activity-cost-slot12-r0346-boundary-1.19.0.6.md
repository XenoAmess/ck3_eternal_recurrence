# Activity planner cost and final gate: R0346 boundary

This is a bounded, read-only source trace against CK3 1.19.0.6 Steam
23530548, `ck3.exe` SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The source baseline was master `082aaf9e9915180c5fa4c3d4e13866267afbc18b`.
No CK3 instance was started and no planner state was changed for this trace.
The exact paired R0346 paused report at
`Z:\m6-activity-h3928-diag-20260929\operator-runs\h3928-diag-2\formal-report.txt`
has SHA-256
`3D440F9D2E9F79891D96C80A94096BA75A66BD53C8D80E82FDB53D5B382C3E73`:
planner present, widget attached but hidden, stage 2, HostView current key
null, configured cost unknown, final CanStart unknown. That readback supplies
neither a selected activity nor a refreshed cost.

## Cost object and normal refresh

`ActivityPlanner.AccessCostBreakdown` ultimately returns the address of the
embedded object at `planner+0x1AD8` (`0x10AB170`); it does not copy a price.
At `0x10B2B52..0x10B2B60`, the normal recomputation `0x10B2B30` first calls
`0x10AAFD0` to clear that object. `0x10AAFD0` clears ten row collections at
object offsets `+0x50 + i*0x90` (`i=0..9`) and the first `0x50` bytes. It
also clears same-shape objects at `planner+0x23E8` and `+0x2CF8` later in
`0x10B2B30`. The latter objects must not be mislabeled as the configured
total returned by `AccessCostBreakdown`.

For each of the ten categories in the first object, the final loop at
`0x10B2EA0..0x10B2EE0` calls `0x21C7B60`. That function walks the category's
`0x90`-byte rows, accumulates their 64-bit amounts at row `+0x78` in
separate branches according to row flag `+0x8E`, and writes a computed
64-bit aggregate at category `+0x78`. Its arithmetic uses `0x186A0`
(100,000); that constant alone does not identify a resource. Thus the
aggregate bytes have a bounded **copy location**:

```text
planner + 0x1AD8 + 0x50 + category_index * 0x90 + 0x78
category_index = 0..9
```

This trace does not bind indices 0..9 to `gold`, `prestige`, `piety` or the
other names accepted by GUI `CostBreakdown.GetCost(name)`. It also does not
prove that a category with no rows is an authoritative zero in the current
planner configuration. Neither raw index totals nor an empty container are
ready for a player budget decision.

Planner slot 12 at `0x10AE180` calls the recomputation at `0x10AE1AA`; the
call returns at `0x10AE1AF`. Inside the recomputation, the final category
aggregate is written before its `ret` at `0x10B2EFC`. The normal handler
update reaches slot 12 only after the planner's slot-7 widget visibility
gate (see `activity-planning-semantic-seam-1.19.0.6.md`). This trace found
no post-refresh generation, valid bit or timestamp in the cost object or
adjacent planner fields. R0346 had `widget_visible=false`, so the observed
paused query cannot establish that slot 12 ran after a type/configuration
selection. Reading ten zeros from that frame would invent a zero price.

A conventional passive hook could wrap the **entry** of `0x10B2B30`, call
its original trampoline exactly once, then copy the aggregates before
returning, while requiring the normal planner-slot-12 call site whose return
address is `0x10AE1AF`. That would observe a completed normal refresh without
calling the write function on demand. No such hook, same-frame configuration
binding or opened-planner live result exists in this package. Merely seeing
`widget_visible=true` or another paused heartbeat would not prove this
specific return occurred after selection.

## Final stage validator

The `CanProgressPlanningStage` evaluator `0x10B0DA0` dispatches on
`planner+0x1AB0`. Its exact jump table at `0x10B10C0` sends stage 5 to
`0x10B1018`; stage 2 goes to `0x10B0E0F`. At stage 5, `0x10B1018` makes a
temporary command from `planner+0x1530` via `0x10B10E0` and `0x18E1160`,
calls virtual slot `+0x30` at `0x10B108F`, then releases the temporary at
`0x10B1095..0x10B109C`. The command vtable at RVA `0x432E690` binds that
slot to `0x26C8070`, a jump to validator `0x219A8B0`. This is the original
GUI's final validation branch; a positive result at stage 2 is a different
gate. This source trace did not run the stage-5 branch on a paired paused
frame or establish a private caller's no-gameplay-effect postcondition.

## Next exact collection point

The current seam does **not** justify a configured-cost or `can_start`
collector. The next bounded source and live proof is:

1. In an owner-coordinated, paired paused scenario, use the original
   activity-type/handler event path to open a configured planner. Record the
   selected type, owner, actor, stage and configuration in the same frame.
2. Observe the **normal** slot-12 return at `0x10AE1AF` after selection and
   configuration. A passive after-return capture can copy the ten aggregates
   with the exact planner identity and configuration, without invoking the
   write-path `0x10B2B30` itself. Confirm the slot-7 visibility gate and
   handler update order in that scenario.
3. Bind the category indices to resource names through the original
   `CostBreakdown.GetCost(name)` callback or equivalent exact-build lookup,
   then compare copied values with an independent native/GUI result.
4. Only on an observed stage-5 frame, sample `0x10B0DA0` as the original
   final gate and verify no gameplay action or date change. Never invoke
   `ProgressPlanningStage` at stage 5 to answer a query: that is the start
   path.

Until these points close, `configured_cost` and final `can_start` remain
typed unknown. No new collector, action or public capability is qualified by
this source-only trace.

Reproduce the bounded disassembly from `ck3_autonomous_player/` with the
project's Python environment and the exact executable:

```text
native_bridge/research/disasm_ck3.py 0x10AAFD0 --size 0xA0
native_bridge/research/disasm_ck3.py 0x10B2B30 --size 0x3D0
native_bridge/research/disasm_ck3.py 0x21C7B60 --size 0xF0
native_bridge/research/disasm_ck3.py 0x10AE180 --size 0x40
native_bridge/research/disasm_ck3.py 0x10B0DA0 --size 0x330
native_bridge/research/disasm_ck3.py 0x26C8070 --size 0x10
```

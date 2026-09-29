# R0350 feast planner stage 1 boundary (CK3 1.19.0.6)

This is a bounded read-only continuation of the private feast planner work. The
exact `ck3.exe` SHA-256 is
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
No CK3 process was launched by this research. The inspected R0350 formal report
is `Z:\m6-activity-h3928-open-candidate-20260929\operator-runs\feast-open-1\formal-report.txt`,
SHA-256 `4978EC4C2EAC90C0D27E2E7F092D3579A3EAB89D181872220FFBCA40B9408CDB`.

## What R0350 actually observed

On actor 29829, native revision 3, raw date 53219928, the private event `0x65`
was dispatched. The native result read the same paused frame with the planner
attached, widget visible, and `planner+0x1AB0 = 1`. The candidate required
stage 2, so it returned `postcondition_failed`; the formal run stopped RED.
No activity start, date advance, or feast benefit was reported. The old result
serialized neither the selected planner type nor individual postcondition
booleans. Therefore the report alone cannot prove that the stage check was its
*only* failed predicate or certify the selected type as `activity_feast`.

## Original stage path

- `game/common/activities/activity_types/feast.txt:4155` defines
  `special_option_category = special_type`; its `special_type` options start
  near line 2922 and include `feast_type_generic` marked `default = yes`.
- Original planner event slot 18 (`0x10AE120`) calls `0x10AD7C0` to select the
  payload's type. `0x10AD808` copies its type pointer to `planner+0x1530`, and
  `0x10AD929` first sets stage 2. Within this same function, the positive
  category branch calls `0x10AEB40` at `0x10ADB31`.
- `0x10AEB40` checks the *selected type's* `+0xA88` category pointer. When it
  is non-null and the current stage is not already 1, `0x10AEB74` writes
  stage 1 and `0x10AEB7E` saves the previous stage at `+0x1AB4`. The function
  searches 16-byte rows at `planner+0x1560` (count `+0x156C`) for this category
  and stores the matched row in `planner+0x1AC8` if found. It is the only
  immediate-value writer of stage 1 to `+0x1AB0` found in the exact executable.
- The original GUI `game/gui/window_activity_planner.gui:62` shows the special
  option selection widget for
  `ActivityPlanner.IsPlanningStage('special_option_category')`. The option
  cards use `ActivityOption.IsShown` and `IsValid`, and call
  `ActivityPlanner.SelectOption` at line 886. Its category Confirm button
  calls `ActivityPlanner.ProgressPlanningStage` at line 922. Taken together,
  the native branch and GUI make stage 1 the expected special category screen
  for feast. This is not a final `can_start` state.
- `CanProgressPlanningStage` at `0x10B0DA0` uses the jump table at `0x10B10C0`:
  stage 1 goes to `0x10B0DE7`, stage 2 to `0x10B0E0F`, and stage 5 to
  `0x10B1018` (the final validator branch). Stage 1 reads selected
  `CActivityType+0xA88` and calls `0x10B1E60` to find its category row in
  `planner+0x1560`. The return checks row existence, not an observed player
  option's `IsValid` on the R0350 frame.
- `ProgressPlanningStage` at `0x10B1330` uses the table at `0x10B13D8`:
  stage 1 goes to `0x10B135C`; with the normal `+0x1AD0 == 0` branch it calls
  `0x10B1BD0(planner, 2)` at `0x10B13A1`. Stage 2 goes to `0x10B13B3` and
  stage 5 to `0x10B13C5 -> 0x10B1910`, which starts an activity. The latter
  must never be called as a read-only probe.

## Next private boundary

A corrected GUI-open postcondition may accept stage 1 for a type with
`+0xA88 != 0`, but only after separately proving the same actor/date/revision,
attached and visible widget, same planner owner, and `planner+0x1530` equal to
the unique freshly resolved `activity_feast` pointer. Report the copied stable
key or an explicit `selected_feast_verified` boolean. Do not reinterpret the
old RED as a successful open without that readback.

The next *read-only* collector should report the `special_type` category row
from `planner+0x1560`/`+0x156C`, its selected option pointer at row `+0x08`,
and stable option key; compare it to `feast_type_generic` and ask the original
`IsShown`/`IsValid` and `CanProgressPlanningStage` operations on the same paused
frame. A script `default = yes` does not prove the R0350 selection or legality.
Only if those checks are positive is a bounded private stage-1 Confirm through
the original `ProgressPlanningStage` route a candidate action. Its independent
postcondition is the same actor/date, selected feast and option retained,
planner visible at stage 2, no started activity, no deducted cost, and no date
advance. Stage-2/5 work needs its own configured-cost and final-validator
proof before any feast can start.

Reproduce the static spans with `native_bridge/research/disasm_ck3.py` at
`0x10AD7C0` (size `0x400`), `0x10AEB40` (size `0xD0`), `0x10B0DA0` (size
`0x330`), `0x10B1E60` (size `0x40`), and `0x10B1330` (size `0xB0`) against the
exact executable above. The jump tables contain absolute RVAs indexed 0..5.

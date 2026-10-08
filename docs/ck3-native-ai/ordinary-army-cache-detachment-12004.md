# Ordinary Army cache semantic projection, CK3 1.20.0.4

Research source: frozen `dac47ba428d524ff201c7aeff295c58243cfa820`.
Source candidate is not yet executed or qualified. Root owns the one FIRST.

R80 actual ordinary auto-turn 009 queried Army strength in 24.765689 seconds.
Following same-frame auto-turn 010 returned a small route-contact result in
24.914943 seconds, after war-termination auto-turn 008 took 0.194021 seconds.
These observed totals motivate checking the ordinary semantic projection.
They do not show how much time belongs to copies, native waits or other work.

The source has a deterministic duplicate: `_army_strength_cache_for_snapshot`
validates the complete rows against the paused frame and returns a detached
deep copy. `_with_one_life_episode` holds that new owned list in a local variable,
then deep-copies it again when assembling the semantic snapshot. Transferring
the local list directly into that new snapshot removes one full row-list copy
per successful cache projection. The first detach remains, so public snapshot
mutation cannot alter the Driver cache. All Army fields and nested leaves remain
present; query status, sequence, frame binding and persistence are unchanged.

The source-only compound `test_army_cache_local_detachment_first0` reuses complete
saved R80 SDK receipts for actual009 and its same-frame actual001 accepted
semantic snapshot. It seeds their existing normalized cache/frame materials,
then connects the real NativeDriver and ordinary Service planner to registered
`ck3_plan_turn`. It compares that route with a fixture restoration of only the
old second-copy expression, counts that redundant copy, checks complete rows,
and mutates an exported nested list to verify cache isolation. It adds no native
producer or synthetic large payload. Offline GREEN will qualify copy semantics
only; a later real ordinary turn is required for any live latency claim.

Original input paths:

- `Z:/ck3_mod_rewrite_process_assets/g2-background-20261008/managed-full-h9715-r80-abi42restore01/operator/gameplay-responses/009-r80-ordinary-auto03.json`
- `Z:/ck3_mod_rewrite_process_assets/g2-background-20261008/managed-full-h9715-r80-abi42restore01/operator/gameplay-responses/001-runtime32-r77-paused-snapshot.json`

The current Root SDK reader's file inbox dispatches MCP tools or exits the
client. It cannot install a Python profiling hook inside the separate MCP child.
Do not restart that SDK or replay a current frame solely for profiling.
## Root connected qualification

The sole registered ordinary-plan compound passed on source
`f13546e621d3beae7e2da86dd80dcbc97a1bc5dd`: Root wall time24.2779493 seconds,
unittest21.494 seconds. It reuses complete actual R80 Army009 and paused
Snapshot001 inputs through the real NativeDriver cache, Service planner and
registered `ck3_plan_turn`. Three successful semantic projections caused
three redundant full-row copies in the restored baseline and zero after the
change. All three required cache detachments and both required Driver/Service
plan detachments still execute. Complete Army fields, the normal plan and
public/cache ownership checks pass.

[Actual FIRST03](Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261008/r80-army-local-detach37/first03/ROOT-ACTUAL-RESULT.json)
and its compound evidence preserve the measurements. FIRST01's fixture placed
SDK public revision3 into native state instead of native revision2, so it never
reached the cache path. FIRST02 reached that path but counted `deepcopy(None)`
as a row copy before the helper returned a list. Both harness REDs remain;
their fixture-only corrections preserve the strict copy and field assertions.
The production change is static-ready. It has not yet been installed in R80,
and the actual25-second turn duration is not attributed wholly to this copy.

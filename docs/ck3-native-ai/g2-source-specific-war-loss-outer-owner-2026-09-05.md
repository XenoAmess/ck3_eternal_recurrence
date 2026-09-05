# G2 source-specific war-loss exclusive outer owner

Status: **deterministic orchestration static-ready / no live adapter / no
launch / live NO-GO**.

## Delivered ownership contract

`run_g2_source_specific_war_loss_outer_owner.py` is the outer composition seam
for one future serial CK3 acceptance. It does not contain a concrete process,
UI, debugger, injection or cleanup implementation. Those operations are
dependency-injected so their ordering and rejection rules can be tested
without starting or attaching CK3.

The admitted order is fixed:

1. acquire one exclusive CK3 launch slot;
2. start one normal-event process targeting `bookmark.1071.a`, with the outer
   owner named as its cleanup owner;
3. attach the source observer to that PID and obtain six executions;
4. require `original_breakpoint_byte_restored=true`,
   `debugger_detached=true`, `process_terminated=false`, and confirm that the
   same owned process is still alive;
5. pause that same PID after observer detach;
6. explicitly attach the bridge to that PID and verify its reported
   `bridge_pid`;
7. pass the exact driver object to
   `run_same_lifecycle_sequence`, which owns current/action/postwar sequencing
   but no process cleanup;
8. call the outer owner's final cleanup exactly once on GREEN or RED, then
   release the exclusive slot.

The tests reject an unsafe observer handoff before bridge attach, reject a
dead process after detach, reject a bridge PID mismatch, and prove that a
continuation exception still reaches exactly one outer cleanup. The happy
fixture records one PID at normal launch, observer capture, bridge binding and
lifecycle join, and observes the identical Python driver object at the
continuation boundary.

## Observer evidence and old-runner boundary

The frozen observer source
`raiktor_war_bound_private_capture_v1.cpp`, SHA-256
`A84601C5BB6927DEF52DF6B27E8602B8C2CAC0C6475A9F1A75B30085433848D8`,
does support a detach-only handoff:

- attach mode calls `DebugSetProcessKillOnExit(FALSE)`;
- a live breakpoint is restored to the original byte before exit;
- the surviving attach-mode process is released with
  `DebugActiveProcessStop`;
- `TerminateProcess` is confined to the non-attach branch.

This is a source-level deterministic proof, not a new live observation. A
future acceptance must still demonstrate the same fields and process liveness
in its fresh artifact.

The old `run_raiktor_war_bound_private_capture_v1.py` remains deliberately
excluded as an inner phase. Its standalone `finally` terminates the CK3
process it launched. Calling it from the new owner would break same-PID
continuation and create two cleanup owners. It is pinned for provenance only.

## Frozen preflight and NO-GO boundary

The manifest
`native_bridge/research/fixtures/g2_source_specific_war_loss_outer_owner_v1_manifest.json`
pins the outer/lifecycle runners, source observer/provider/contract, terms and
postwar continuations, exact CK3 and bookmark source, private bridge/injector,
and source capture executable. Its CLI checks every hash, verifies the
observer attach/non-attach branch shape, and requires unchanged process
inventory. The CLI cannot call the async orchestration seam or any CK3 API.

There is still no concrete exclusive normal-launch/observer/pause/bridge/
cleanup adapter and therefore no legal live command in this package. The next
CK3 attempt remains **NO-GO before launch** until that small platform adapter
is implemented and reviewed. No fixture, schema or source proof is classified
as live.

The no-launch CLI produced
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-outer-owner-static-20260905\preflight-r2.json`,
5,303 bytes, SHA-256
`5AC3D09AE9C6801568E7F9F2965763F4B4ED9B20489E025C4145F5944CDE630A`.
It reports `GREEN_STATIC_EXCLUSIVE_OUTER_OWNER_NO_LAUNCH` and all observer
source-proof booleans true. The unchanged before/after inventory was
`ck3.exe=1`, injector `=0`: that CK3 process pre-existed this command and was
neither started, attached nor cleaned by it. This is a shared CK3-gate
occupancy fact, not evidence from this package and not an all-zero cleanup
claim.

Consequently `source_specific_loss_ready`, `comparison_input_ready`,
three-way decision/action readiness and `GEN-034` remain false. T1 remains
**90%**.

Focused acceptance:

```powershell
py -B -m unittest \
  ck3_autonomous_player.tests.unit.test_g2_source_specific_war_loss_outer_owner \
  ck3_autonomous_player.tests.unit.test_g2_source_specific_war_loss_lifecycle \
  ck3_autonomous_player.tests.unit.test_raiktor_war_bound_private_capture_v1 \
  ck3_autonomous_player.tests.unit.test_raiktor_source_specific_war_loss_capture \
  ck3_autonomous_player.tests.unit.test_run_g2_postwar_cleanup_expiry_live_acceptance \
  ck3_autonomous_player.tests.unit.test_run_g2_postwar_cleanup_expiry_receipt
```

Run the same list under `py -O -B -m unittest`. This package does not modify a
CK3 effect file, so the effect-file sharding rule is not exercised and no
loader/file-size evidence changes.

# G2 source-specific war-loss same-lifecycle runner

Status: **static-ready / no launch / live not run**.

## Delivered seam

The offline package adds
`run_g2_source_specific_war_loss_lifecycle.py`. It is a deterministic,
caller-owned-driver continuation rather than a second CK3 launcher. A future
exclusive launch owner must first obtain the already specified six-execution
`bookmark.1071.a` capture, restore the breakpoint byte, detach the observer,
pause that same CK3 process, attach the private bridge, and pass that driver
and raw capture to `run_same_lifecycle_sequence`.

The sequence then:

1. normalizes the six exact `spawn_army` executions;
2. reads the same paused war frame twice through the existing terms query;
3. joins every captured persistent CRegiment, current CArmyRegiment and
   created CArmy generation to the observed current vector;
4. constructs a dynamic retention ticket bound to the capture PID, exact
   WarID, bridge connection generation and episode run ID;
5. invokes the extracted `_continue_private_sequence` on the same driver;
6. permits exactly one `surrender-war-<WarID>` mutation;
7. requires exact-generation destroyed cleanup, zero post soldiers, a proven
   boundary loss equal to the measured pre-termination total, and two equal
   persisted-expiry reads.

`run_g2_postwar_cleanup_expiry_live_acceptance.py` now exposes that continuation
after the pre-termination dual query. Its original cold-checkpoint entry still
calls the same code and retains its previous behavior.

No orphan/retain switch was added to the old capture runner. Its standalone
CLI still owns and cleans its CK3 process, so it cannot accidentally leave an
unmanaged process behind or be mistaken for a valid cross-process join.

## Identity and readiness boundary

The source observer has no bridge episode identity. The admissible join is
therefore:

- capture PID equals the bridge snapshot and postwar receipt PID;
- the exact full-generation WarID and all three generation sets match;
- current read, action and postwar reads retain one connection generation and
  one episode run ID;
- observer detachment and original breakpoint restoration precede the bridge
  continuation.

A future qualifying live result may set the private
`source_specific_loss_ready` and `comparison_input_ready` fields for this one
provider. It still cannot set the three-way outcome, decision, automatic
surrender or `GEN-034` gates because campaign dominance, an owner-authored
budget profile and a same-frame white-peace comparison remain absent.

At this static checkpoint every live/readiness field remains false and T1
remains **90%**. Unit fixtures exercise the identical validator but are not
classified as live evidence.

## Frozen no-launch manifest

The manifest is
`native_bridge/research/fixtures/g2_source_specific_war_loss_lifecycle_v1_manifest.json`.
It pins the existing source provider and observer, exact CK3 executable,
bookmark source, private cleanup/expiry bridge and injector, postwar adapter,
terms runner and the new lifecycle runner. Its CLI only verifies those inputs
and records unchanged process inventory; it cannot start or attach CK3.

The final no-launch receipt is
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-lifecycle-static-20260905\preflight-r2.json`,
4,727 bytes, SHA-256
`7DD775B94ECAF5A6EA848B4549E642D09FCB5F836B86B90AE12E698DD8A0D25F`.
It reports `GREEN_STATIC_SOURCE_SPECIFIC_LIFECYCLE_RUNNER` with
`ck3_started_or_attached=false`, `source_specific_loss_ready=false` and
`comparison_input_ready=false`.

Focused acceptance:

```powershell
py -B -m unittest \
  ck3_autonomous_player.tests.unit.test_g2_source_specific_war_loss_lifecycle \
  ck3_autonomous_player.tests.unit.test_run_g2_postwar_cleanup_expiry_live_acceptance \
  ck3_autonomous_player.tests.unit.test_run_g2_postwar_cleanup_expiry_receipt \
  ck3_autonomous_player.tests.unit.test_raiktor_source_specific_war_loss_capture \
  ck3_autonomous_player.tests.unit.test_prepare_g2_postwar_comparison_intake
```

Run the same list under `py -O -B -m unittest` before handing the package to an
exclusive live owner. No CK3 effect file is involved, so the effect-file
sharding rule is not exercised and no loader/file-size conclusion changes.

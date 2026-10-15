# P13 ordinary Feast diagnostic: omit unused command history

P13's ordinary `life-advance` planning may ask the private Feast planner for a
paused, read-only diagnostic twice: once before the prewar force query and once
after planning again from its new observation. In the P13 response samples
`0049`, `0074`, and `0096`, the overall `ck3_auto_turn` calls took 7.87, 13.36,
and 20.57 seconds. The two Feast attempts together took 0, 4.47, and 4.73
seconds respectively. These are nested planning timings, not additive delays.
The native query returned `unsupported native gameplay step` in the latter
two samples, and ordinary planning still selected `life-advance`.

The diagnostic transport formerly called `driver.take_snapshot()` both before
and after its native read. The default snapshot clones the complete, growing
`native_command_history` twice. The transport uses only paused-map, actor,
date, revision, snapshot ID, and exact-build provenance from these snapshots;
its returned diagnostic never contains command history. Both calls now set
`include_native_command_history=False`. The driver retains the same semantic
snapshot and returns an empty history plus an omission count. Payload, paused
frame, build, and error checks are unchanged. The ordinary Feast consumer still
receives the same diagnostic or the same error and retains its material,
event, progress, and rollback gates.

The existing unit tests verify that successful and rejected reads request two
or one history-free snapshots as appropriate. The external P13-versus-candidate
fixture additionally compared four transport outcomes and two calls through
the real `GameplayBridgeService._plan_private_feast_normal_v1` consumer,
including the P13 native RED and a valid Stage 3 observation. All six scenarios
matched. The external source and fixture are recorded in
`D:/codex-ck3-demos/2026-10-14-robert-30year/lifeadvance-feast-history-free01/DELIVERY.json`
(SHA-256 `1f55322ab5b663e24608a4cc61ae3b764289c717edce70ac4369b00e739a3f9a`).
This is a source-level optimization; no live P13 timing improvement has yet
been measured. P14 must freeze and verify its composed SDK source separately.

The observed P13 non-tactical life advances asked for six days at speed five
and paused after seven or eight actual days. The wait uses
`NativeState.wait_for_public_change` with a condition variable rather than a
fixed Python polling interval. The campaign's ten-day war-result clear target
is a weak guarantee; this change does not alter the requested horizon, speed,
or pause logic.

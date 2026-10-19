# C6 faction515 planning interruption

Machine: `xenoamess-full-tower-eb9d2c1186`. Exact observations and UTC are in the [software evidence](evidence/c6-faction515-predispatch-software01.json). The finite queue helper does not alter the SDK or gift ledger.

AUTO513 previously submitted gift `faction-gift-d29a273508614be4aa0fdfaba560667c`; its ACK remains verification-pending. MET514 still reported Native418/public351 at raw53153472. During AUTO515, the original faction planner waited for a newer same-date paused frame, verified it, then raised `PreSubmissionRevisionMismatchError`. This occurred during `Service.auto_turn`'s planning call, before selected execution, `before_submit`, receipt query or another gift send. M5 independently confirmed this source boundary. It does not prove the earlier gift's material result.

The finite [clear helper](../../tools/g2_saved_campaign/c6_faction515_predispatch_clear_v1.py) requires exact frozen515 input, current live queue metadata, same physical Game birth, unchanged governance/classifier and the exact original gift ledger bytes. It clears only queue pending220 and its retained planning halt, without granting cycle, date or business credit. The219 settled cycles,381 days, T0, endpoint, checkpoint and unresolved gift remain intact. Original515 error and frozen inputs remain available.

The [producer and qualifier](../../tools/g2_saved_campaign/prepare_c6_faction515_predispatch_v1.py) adds one finite branch to the unused existing dynamic preflight entrance; all older function ASTs are preserved except the original final function's delegation name. It executes the actual C6 outer dispatch and ordinary call/Clean validation path. A positive516 case performs zero RPC calls; unknown original response, changed pending cycle and foreign Game reject without consuming a sequence or writing. A subsequent software517 PLAN runs the original formal route against an explicitly modeled newer frame and selects the independent receipt, leaving the fixture ledger byte-identical. No live Driver, SAVE, Game or MCP operation is used.

The sole runtime operator may adopt the two reviewed candidates after preserving the old helper and confirming that this C6 process has not loaded it. Exact516 request:

```json
{"sequence":516,"command":"clear_zero_rpc_preflight_rejection","arguments":{"repair_kind":"faction515_presubmit_newer_paused_frame_for_readonly_PLAN"}}
```

After actual516 success, issue new ordinary `ck3_plan_turn`517 with empty arguments. Its original guards must validate current facts; failure remains a real halt. Do not replay515 or the earlier gift. The permanent SDK change is owned by M5 and is separate from this local bookkeeping repair.

Qualification command:

```text
py tools/g2_saved_campaign/prepare_c6_faction515_predispatch_v1.py --runtime-root D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/runtime --failure-packet D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c6-faction515-failure73/FROZEN.json --output-root D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/robert30-v20261019-campaign01/c6-faction515-clear-review01
```

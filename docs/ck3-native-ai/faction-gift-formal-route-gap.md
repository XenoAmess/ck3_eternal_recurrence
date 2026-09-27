# G2-M4 faction gift formal-route gap (2026-09-16)

This is a deterministic source-path blocker for the ordinary standard-feudal two-game-year governance gate, not a live faction-gift result. The frozen bounded preview does not advertise faction intervention.

On master `eb586f75`, `faction_gift_policy_v1.py` can rank one legal, budgeted targeting-faction member from complete same-frame typed observations. The existing native `FactionGiftMitigationActionV1` defines typed request, ACK and receipt, and its binder expects targeting rows, faction/member metrics, final gift preview, idempotency and submit callbacks. The normal production path does not expose those callbacks as a query/command: `bridge.cpp` has a default-OFF `DriveFactionGiftMitigationAsyncPrivateGlueV1` terminal heartbeat and diagnostic JSON, while `native_auto_run.py` has no faction gift selection/query/submit route. The public faction alert query is count/fixture-only. Thus a Python consumer wired now would have neither complete native inputs nor a command receipt.

The private CMake option `XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1` is OFF by default. Its conditional `target_sources` includes action, source adapter, binder, receivers and async glue, but omits `faction_gift_mitigation_integration_gate_v1.cpp`. This is a concrete build dependency for using that existing gate, not a reason to turn on public advertisement.

Next minimal implementation after the current sole `bridge.cpp`/CMake writer releases those files: expose one version-bound, paused private targeting row/member plus metric/preview query, then one typed one-shot send-gift-to-faction-member request and status/receipt route using the existing action/gate modules. Bind `native_driver.py`/service and only then `native_auto_run.py` to `faction_gift_policy_v1.py`. A real legal paused targeting-faction scene must prove formal observation, one chosen action, independent gold/opinion/faction requery, next-turn consumption and compatible checkpoint/cold restore before registration or capability advertising. Unknown fields and ACK alone remain evidence insufficient.

Evidence anchors: `ck3_autonomous_player/native_bridge/src/bridge.cpp` lines 861-957 and 2486-2506; `ck3_autonomous_player/native_bridge/CMakeLists.txt` lines 169-174 and 794-818; `ck3_autonomous_player/native_bridge/include/xar_bridge/faction_gift_mitigation_action_v1.hpp` and `src/faction_gift_mitigation_native_binder_v1.cpp`; `ck3_autonomous_player/src/xar_autoplayer/faction_gift_policy_v1.py`. No CK3, screen or UI was used to reach this source-path conclusion.

## Increment on remote master `e76283d1` (2026-09-16)

The earlier source-path assessment above describes the state before the private native route landed. Master `8d4094ce` added a default-OFF, private-only no-UI member query, typed one-shot gift submit, and same-process receipt query. The normal `native_auto_run` / `ck3_auto_turn` still has no formal faction gift consumer or public registration. The ordinary feudal paired R739 source has an independently observed targeting-faction count of zero and eight direct landed vassals, so it provides a valid known-empty branch, not a gift-positive scene.

The private same-process receipt binds its submitted ACK to process memory and later revision ordering. A real CK3 cold start loses that ACK; the current targeting vector may also omit the original faction and recipient. Treating its absence as a successful gift or a dissolved faction would permit repeated side effects. The next native read must use the persisted original faction and recipient IDs to query independent faction storage, recipient gift opinion/opinion, and player gold in the new paused process. It must distinguish applied from unchanged or unresolved without comparing revisions across processes. `faction_gift_cold_recovery_v1.hpp/.cpp`, `faction_gift_pending_v1.py`, and the scoped pure Python classifier specify this contract; they do not implement the native bridge receiver or turn-level submit. Public registration and capability advertising remain OFF. A gift-positive ordinary feudal paused scene, native readback, next formal turn, and real cold restore remain required live evidence.

## C41 source-path correction and paired recovery (2026-09-27)

The two assessments above are historical. At master `d861608e`, the default-OFF bounded route already connects `native_auto_run.py` and `GameplayBridgeService` to `plan_faction_gift_private_v1`, the same-frame native member preview, budgeted typed submit, durable pending ledger, independent same-process receipt and new-PID faction/recipient/resource recovery query. The public capability remains OFF. The existing real targeting-faction count of zero proves only the empty branch; no gift-positive formal action or postcondition has been observed.

C41 found a narrower deterministic recovery gap: an unresolved gift is stored at `state_dir/native-session/faction-gift-pending-v1.json`, but official `g2_preview_operator.py prepare-state` previously carried only the save, driver, construction and family sidecars to a new candidate. A new process started from such a pair would not see the pending gift identity and could not select its cold recovery query. The operator now accepts `--faction-gift-sidecar <old-state/native-session/faction-gift-pending-v1.json>` (or the same basename inside `--sample-dir`), pairs its actor, episode, date and pre-submit checkpoint SHA with the selected save and driver, then copies the unchanged bytes to the new native-session directory after no-launch rebind. Its receipt records source, SHA and request ID. This is a source-only paired-state fix; a future gift-positive paused frame must still prove actual gold/opinion/faction effect, next-turn consumption and new-PID classification. A missing or mismatched sidecar cannot be inferred from an empty targeting vector.

If a `--sample-dir` contains a valid ledger with `pending=null`, ordinary pairing continues without copying that historical resolved ledger. Explicitly passing a resolved ledger as `--faction-gift-sidecar` reports that no unresolved action was supplied.

## C98 pending same-date handoff (2026-09-27)

The C54 private M5 route already reaches the existing typed gift consumer and
checks its durable pending ledger before collecting another proposal. C98 found
a narrower production-path defect: when that ledger belongs to the current CK3
process but the public paused revision has not passed the revision recorded
before submit, `plan_faction_gift_private_v1` returned the original
`life-advance` plan. The exact-build native receipt requires a newer paused
revision **at the original game date**. A date advance in this state would make
same-process material verification unavailable while the gift remains pending.

The route now retains the pending identity and uses the native driver's
existing bounded `_wait_for_snapshot` to await a newer paused revision at the
same game date. When it arrives, it raises the existing pre-submission revision
mismatch signal so `native_auto_run` performs its one bounded readiness replan;
the M5 collector explicitly passes this signal through its broad source/receipt
error handlers, and the replan selects the already wired receipt query. A timeout or changed
date/actor returns a concrete RED with the pending ledger intact. It never
issues `life-advance` while the gift is unresolved. The initial source-path
test reproduced the old `life-advance` selection; focused tests now cover
same-date wait→replan→receipt and timeout→RED, including the actual
`GameplayBridgeService.plan_turn` M5 call path, in normal and optimized Python.
This is source/fixture evidence only. The preserved Robert roots checked for
C60 have targeting-faction count zero, so there is still no gift-positive
formal submit, independent gold/opinion/faction postcondition, next-turn
consumption or live cold-restore qualification.

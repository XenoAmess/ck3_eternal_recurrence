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

## H3388 archived Robert root: targeting faction observed (2026-09-28)

The earlier zero-count statement applies only to the roots checked for C60.
The immutable H3388 driver at
`Z:/h3388-source-freeze-20260928/source-pair/driver-state.json`
(SHA-256 `99C58301C212ABCDBBEDD74D92AE74FCFE23719B927377C93FE7C7D0F54C5C50`)
contains 640 successful `query-campaign-root-context-v1` commands: 592 report
`player_targeting_faction_count=0` and 48 report `1`. The first positive is
history index 3030/date raw 53218056. The latest positive is command index
3384, native revision 27/date raw 53218944, actor 29829, feudal government,
with 10 published direct landed vassal IDs. This is an actual targeting-faction
root, not a fabricated candidate. The paired H3388 checkpoint is at date raw
53218968, so the index-3384 count must be refreshed after loading that save;
it is not a same-frame H3388 gift preview.

The R0269 formal report
(`Z:/h3388-source-freeze-20260928/evidence/formal-report.txt`, SHA-256
`310F673EC9D13DD4DC2F6250B5773D41830AB1D3C0772CAFAF255936D7F1F8C0`)
has WarID 16777231 active throughout all 36 turns. Its 35 wartime M5
observations are `incomplete_war_cash`. The frozen H3326 candidate's
`native_private_flags_on` omits
`XAR_CK3_ENABLE_G2_FACTION_GIFT_MITIGATION_ASYNC_PRIVATE_GLUE_V1`, and its
operator command omits `--private-faction-gift-formal-trial`. The H3388 driver
history has no faction-gift private query, submit or receipt. Existing private
`plan_faction_gift_private_v1` only augments a `life-advance` plan; the formal
M5 gift producer is peaceful. Thus this archived positive count proves neither
a native-legal/affordable gift nor a missed approved wartime submit. It does
not change public advertisement or M4 qualification.

Next matching candidate: retain the H3388 save/driver/family pairing, build
the already present default-OFF private gift capability into a new DLL, and
enable the bounded private trial with a newly allocated round ID. Obtain a
fresh same-frame targeting root and exact native member/gift preview before
deciding whether there is a legal gift and a concrete mitigation objective.
Any wartime spending decision must consume the war cash/resource contract or
remain a documented comparison gap. Only a formal typed submit followed by
independent gold, recipient opinion, original-faction readback, next-turn
consumption and paired cold recovery can extend the live capability claim.

## R0309–R0310 private query failure (2026-09-28)

R0309 used a paired Robert paused save at date raw 53219496, actor 29829,
and read a fresh feudal targeting-faction count of 1 with ten direct landed
vassals. Its Python classifier returned `native_preview_not_terminal`, but
that classifier collapses several native statuses; the raw status was not
recorded. R0310 used the same paired lineage and a verified fresh application
main pump (epoch 9802→9830). The private query ran once and returned
`receiver_red`, `failure_flags=1`, `completion=unavailable`, with an empty
observation. It took no gameplay action or date advance. This is a native
frame-path RED before legal recipient, cost, opinion or benefit can be judged.
The paired R0310 readback is
`Z:/ck3_mod_rewrite_process_assets/nw-faction-h3694-pump-readonly-edc0434-20260928/evidence/R0310/faction-readback.json`.

At the R0310 DLL source commit `edc0434c`, `ExecuteFactionGiftMitigationAsyncMailboxV1`
sets the same `faction_gift_async_failure_frame` bit for an invalid execution
stamp, public revision, snapshot read/drift, direct targeting-row read,
native binder, or source observation capture. The existing result cannot
identify which check failed. The narrow private `frame_failure_stage` field
now preserves that branch while keeping the candidate unavailable and the
public capability off. A replacement exact-build DLL and one bounded paused
query are needed to identify the leaf; repeating the R0310 DLL would not add
evidence. No gift submit or M4 completion is claimed.

R0314 retried the integrated stage field on the validated Robert h3770
save/driver at raw date 53219568 and actor 29829. The verified fresh pump
(8373 to 8401) found public targeting count 1 and ten direct landed vassals.
The private query executed once, returned `receiver_red`, `failure_flags=1`,
and pinpointed `frame_failure_stage=direct_targeting_rows`; it published no
candidate, took no action, and advanced no game date. The readback is
`Z:/ck3_mod_rewrite_process_assets/nw-faction-robert-h3770-frame-stage-965a820-20260928/evidence/R0314/faction-readback.json`.
The public count proves the land-state source count, not that the private
reader accepted its faction identity, leader and member fields.

Source comparison found one exact contract mismatch: the canonical row
observer and `faction_targeting_row_observer_v1_abi.json` accept a nonzero
leader ID whose character resolver returns null as a legal nullable leader;
the private direct reader rejected the entire frame. The direct reader now
uses the same nullable rule, and records a typed private `direct_source_failure`
leaf if another source/span/identity check fails. The R0314 artifact does not
show which leaf failed, so this source correction and diagnostic require a
new exact-build paused read before closing that RED. Gift submit, formal
consumer, independent gold/opinion/faction postcondition, next turn and cold
restore remain unproven; public registration stays off.

R0317 used the integrated `047b75a9` private DLL on the paired Robert h3774
checkpoint at raw date 53219568. Its fresh application-main pump advanced
9334 to 9394, the public root showed one targeting faction and ten direct
landed vassals, and the private query executed once. It returned
`no_eligible_direct_vassal` with `failure_flags=2` (recipient selector only),
`frame_failure_stage=none` and `direct_source_failure=none`. The reader had
therefore accepted its complete bounded source, faction, leader and character
member scan; the R0314 native receiver RED is cleared for this exact frame.
The readback and verdict are under
`Z:/ck3_mod_rewrite_process_assets/nw-faction-robert-h3774-direct-leaf-047b75a-20260928/evidence/R0317/`;
their SHA-256 values are respectively
`7002BB52FE31920BF8EF1C5F15714C3A01D3BEAEB8DC99AD8EF49B37D4D46241`
and `71C34436CEA5E36D741699140E42AC237B2112E523747A88E51A920F8495AE83`.

In this exact source, `ReadDirectSourceSampleV1` checks every targeting row
and character member and compares two samples before publishing. The selector
then tests each accepted leader and member against the independently queried,
sorted direct-landed-vassal list. This makes R0317 a current-scene negative
for that narrow gift policy, not a missing native observation. The native
response does not serialize the raw faction/member IDs on this negative path,
so it does not prove the faction has no members or that no other character
could receive a gift. Final interaction legality, cost, material postcondition,
next turn and cold recovery were not exercised. R0317 took zero gameplay
actions and advanced zero game days; no formal gift loop is claimed.

## R0327 to H3928: expose the accepted private member rows (2026-09-29)

R0327 repeated the bounded private read at Robert h3911/raw 53219928. The
fresh root again had one targeting faction and ten direct landed vassals; the
native result was `no_eligible_direct_vassal`, `failure_flags=2`, with no
direct-source or frame failure. It took zero gameplay actions and advanced no
date. Its readback at
`Z:/ck3_mod_rewrite_process_assets/nw-faction-robert-h3911-opportunity-2eb9-20260928/evidence/R0327/faction-readback.json`
SHA-256 is `DA2054FE2CCB9344090DCFEECC8745FBE8C8860CB3A2C620ABB7926E017648F5`;
the verdict SHA-256 is
`7AAE4E4777C7A82E379431C9DEB8012E2E3B2E66ABBBA445192BE4B055252464`.
The no-recipient response still hid the faction's actual character member
IDs and supplied no `gift_interaction` CanSend preview. Its zeroed observation
must not be read as zero members, zero gold, or an illegal gift to every other
character. The same-frame semantic gold was 120644281 raw, with an active war;
future war cash commitments remained unobserved.

The later H3928 source pair (`A92073407D1CB2800EEF9C0C3EFEB9846D48398F679DC3163B71EF86C40CEC2C`
save, `9D381400574278BC4F1C736A48BB4B90CE1E12D8440A004AFBD1F5399A4204C0`
driver) is the same game date. Its last public root at h3918 still reports
one targeting faction and the same ten direct landed vassals, but its driver
contains no later private faction gift query. R0327's negative cannot be
silently carried to this later paused frame.

The private gift serializer now projects `direct_targeting_rows` from the
already accepted exact-build, twice sampled source. `ready` includes the
bound snapshot revision/date/player, each faction ID and target, nullable
leader, and full character member IDs, even when the direct landed selector
found no recipient. An incomplete or failed source emits `null`, not an empty
list. This changes no selection, native CanSend evaluation, submit route or
public capability. A new paired, read-only H3928 run must first identify the
actual members and join them to the current direct vassal list. Only a member
with a native final legal, positive and budgeted gift preview can proceed to
the existing formal consumer and its postcondition/next-turn/cold-restore
gates. This source change alone is static-ready and proves no new gift action.

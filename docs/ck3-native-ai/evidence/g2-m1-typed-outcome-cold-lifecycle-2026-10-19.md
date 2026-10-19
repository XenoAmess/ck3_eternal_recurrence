# Typed outcome lifetime across campaign cold starts

Source audit / plan only. HEAD `70137a36ea18d6d9f84375bfbef181927a90a5f9`.
machine_id: `xenoamess-full-tower-eb9d2c1186`; observed_at_utc: `2026-10-19T11:15:29.107733+00:00`.
Identity source: fresh `tools/ck3_live_run_id.py machine`. Source pins below matched HEAD.
No active SDK/COW, queue, Native29, Game, GUI, Driver or SAVE was changed/read by this audit. No RPC/build/test matrix was added.

The same campaign/episode does not give two Native revision counters a shared namespace. A durable request/ACK remains an immutable historical fact; a new current-state observation has its own source/owner frame. The two can legitimately have postNative 27 and original preNative 3138. A cold material observation is not a recovered native ACK or proof that the original command caused it.

## Actual C11 trigger and ownership

M5 owns prisoner producer/consumer, harness owns outer Queue classification. I independently read only the two owner-named closed files below (bounded <=256KiB each, exact size/SHA checked), not a live response directory:

- `D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/p51-fresh1066-v20261019-prepare01/c11-prisoner4286-failure85/FROZEN.json`: 11,940 B, SHA256 `3b8b99f588845ea9cf95637b9861ea34f0240cf2480e515186eb74e45ecdfaac`; same machine_id, source observed 2026-10-19T11:09:38.486609+00:00.
- Same closed root `p37-responses/4286-1-result.json`: 63,171 B, SHA256 `3d5ca2de50e1a20718dd51f3962ce77236820f842a09f5eb6b13ccfa909af27f`.
  `$.result.structured_content.result` is independent receipt schema, status applied/material_result=true, post_native_revision=27/post_date_raw=53189232.
  Its `source_pending` retains pre_native_revision=3138/pre_date_raw=53188032. This is not an SDK attempt to rewrite the old ACK into the new epoch.

M5 reports target45172 alive/free, actor40526, exact original action request prisoner-release-6180f156f98a4e15a76f563884f4053f; sidecar pending already null/resolved matched the SDK result. M5's own full proof is `docs/ck3-native-ai/evidence/prisoner-release4286-sdk-closed-proof-2026-10-19.json`, 4,317 B, SHA256 `7b0202db2808590956e6783189969496493d351082c8d161126aa2b636c44a3c` (owner-verified; I did not repeat its normalizer tests).

M5 traced this actual failure to external Queue `classify_existing_typed_v1` requiring current postNative >= original preNative. No prisoner SDK production gap is inferred from this failure.

Harness owner subsequently identified the original external Queue as runtime `root_p37c11_sdk_queue.py`, 267,955 B, SHA256 `71d5863c986ebea245c7f633fd3b6e9170fe92a8ee881f0ca652ac6771c8eb19`: the classifier at L820-L1010 covers later LIFE/child/feast/war overview/prisoner ransom/release; the prisoner receipt branch is L977-L1009, with the single offending comparison at L982. Governance uses separate `classify_governance_with_crown_v1`; family/faction have other canonical functions. This is owner-supplied call-chain scope; I did not open the live Queue or claim to audit those external branches.

The owner's finite recovery helper is repository source `tools/g2_saved_campaign/prisoner4286_cold_epoch_credit_v1.py`, 10,781 B, SHA256 `b7cfcc1224d82be978f7d42d1d07efa4027eead28b749e3e6797df3bed887cde` (file size/hash independently checked; header/constant pins read, not executed). It is scoped to sealed original Queue/4286/ACK/cold provenance and changes that one comparison, leaving other inputs/same-epoch guards intact. This audit does not modify or generalize that recovery. External classifier sibling branches need their own source proof before any future patch.

## Source-confirmed other call chains

### 1. LIFE focus/perk: explicit lost-ACK recovery gap

Call chain:

`lifestyle_formal_consumer.unresolved_lifestyle_perk_action` -> Service planning `_private_lifestyle_pending_v1` -> `Service._plan_private_lifestyle_trial_v1` -> `query_player_lifestyle_receipt_private_v1` -> Native .4 `HandlePlayerLifestyle12004`.

- Durable intent at Python transport L750-L760 records action UUID, target/kind, pre public revision, episode and source_frame. That source_frame is L562-L568: snapshot/public/native/date/player; it has no Game birth, connection generation or Native owner identifier. ACK is retained separately at L824-L830.
- `unresolved_lifestyle_perk_action` L24-L49 matches the episode and preserves unknown/submitted pending. It does not classify the old transport namespace.
- Service L4569-L4605 compares current public revision to old pre public revision to select a receipt; otherwise ordinary bounded advance can continue. Initial-focus gate L4034-L4053 requires its pending receipt, so this gap can also hold opening-focus completion.
- Python receipt L863-L887 requires both current public/native revisions to exceed their original pre values. This can reject before any readback after a counter reset. There is no cold material branch.
- The Native .4 state is more short-lived than a Game process: `bridge.cpp::RunConnectedSession` L15015 takes retained WorkerState, increments connection_generation at L15068, then declares **local** `PlayerLifestyleTransport12004 lifestyle_transport4{}` at L15098. The .4 handler uses it at L18308. Its header L6-L14 contains optional pending_ack and action_may_have_submitted.
- Native .4 receipt L506-L519 requires that in-memory pending_ack, matching action UUID/episode and a later Native revision. Therefore a normal pipe reconnection alone discards this .4 ACK slot, even if the Game PID and WorkerState revision survive. New Game also discards it. Waiting until numbers exceed the old values does not recreate the slot.

**Confirmed source gap, not claimed as a new actual C11 failure:** a persisted unresolved LIFE intent that survives in the retained history/checkpoint prefix can be routed permanently to an unavailable ACK verifier. On cold restore, native_driver L11919/L35288 truncates gameplay history to the checkpoint prefix; intents after that prefix are not automatically retained. Do not claim every old pending survives every restore. Within-prefix pending and same-PID reconnect remain the relevant cases.

Smallest future entry: add a namespace-aware LIFE pending disposition before choosing the old receipt path; use existing strict current focus/owned-perk query for cold/current material, with original cause/charges unverified. Retain the original pending/audit record. Do not hydrate a Native pending_ack from Python JSON, send the original selection again, or relabel a pre-owned perk as original-command causality.

### 2. Crown + construction publication barrier: process is not every owner epoch

Shared call chain: `Service._plan_turn_internal_without_readonly_retry_v1` -> `pending_material_publication_v1.classify_pending_material_v1` -> existing independent receipt routing.

Barrier L30-L64 treats Crown as same-process using PID+episode; construction uses PID+creation string+episode. When considered same-process it compares current Native revision <= old preNative and classifies await_publication. Later waiting scope correctly checks connection generation, but it does not fix the initial classification's missing original Native owner.

- Crown `_context` L39-L41 contains only PID+episode, not creation time or Native epoch. `plan_crown_authority_private_v1` L111-L126 chooses cold by that context. `read_crown_authority_receipt_private_v1` L235-L263 has a real cold current-law branch: original native receipt unavailable, material_result=false; it retains the old action in resolved/current-law observation and does not manufacture an enacted ACK. This is useful existing separation, not an absent new-Game path.
- A reused PID or actual same-PID worker/DLL reset can be misclassified warm by that context. A genuinely new PID is already routed cold. Do not widen this to say Crown always fails on cold launch.
- Construction `plan_construction_private` L300-L319 uses PID+creation to choose independent receipt on a new process. Transport L752-L800 deliberately bypasses old revision/proof comparisons for cold/recheck, while retaining actor/episode/date and original action identity. Applied receipts also have explicit fresh material rechecks after cold restoration or worker restart (L767-L770); this is an existing positive pattern.
- Construction still treats an **unresolved** submit in the same Game process as warm and requires current native_revision > original preNative (L774-L775) and proof_epoch > old preProof (L798-L799). An actual Native owner reset with that same PID/birth can leave it waiting for old counters. This is a conditional source risk; a mere pipe reconnect retaining WorkerState counters is not proof of that reset.

Smallest entry: qualify comparison namespace in the existing barrier and unresolved-receipt guard. Reuse the construction PID+creation normalization helper; do not “fix” this by dropping later-frame checks for warm receipts or removing actor/date/tuple guards. Original source counters stay immutable.

### 3. Faction gift: existing new-Game recovery, no same-Game owner classification

Call chain: `plan_faction_gift_private_v1` L267-L284 -> same-process receipt or explicit cold query -> ledger resolver.

- Runtime PID+creation is checked by `_same_pending_process`; malformed identity is rejected. Same process uses RECEIPT_STEP, different process COLD_RECOVERY_STEP. Warm reader L418-L440 forbids crossing process identity.
- Cold reader L447-L510 reads original faction/recipient independently, preserves original IDs, and passes loaded checkpoint/fresh world facts to `evaluate_faction_gift_cold_recovery_v1`. The latter returns applied, unchanged or unresolved; unchanged requires the exact pre-action checkpoint plus matching independent facts. A merely absent faction/negative material read does not authorize retry.
- Native `NonwarPrivateState12002` header L135+ owns gift state across MCP reconnections, and is embedded in WorkerState at bridge.cpp L12844. Its ACK lifetime differs from connection-local LIFE.
- .4 gift router L465-L496 requires its cached pending_ack or verified ACK/receipt pair. A true worker/DLL replacement in the same Game process loses that state, but the Python PID/birth split still selects warm. Cold function currently explicitly requires a replaced Game process. This is the concrete unhandled same-Game owner transition; it is not evidence that ordinary pipe reconnect loses gift state.
- Unresolved cold material currently preserves pending then raises a postcondition error. Whether the external runner safely holds that opportunity while other legal work continues is outside this repository-only audit; do not infer an actual campaign halt.

Smallest entry: distinguish “same Game” from “same producer-owned ACK state” at route selection, and allow a dedicated independent-material mode for a proven owner reset. Keep all cold classifier baseline/checkpoint requirements and default action_retry_allowed=false.

### 4. Family/child marriage: useful cross-Game model, same-worker distinction

Call chain: `plan_family_marriage_private` -> result private action -> `query_family_marriage_result_private`.

- Family planner L547-L576 explicitly compares Game PID+birth and schedules a cold read once in the new PID. When cold relation remains pending, it retains the exact pair/original pending, stores current checked PID/birth/revision, and lets ordinary routing continue without another proposal.
- `query_observed_first_heir_marriage_cold_result_private_v1` L175-L250 validates current actor, original pair/date, actual current first heir, current frame and a fresh native read. Its result deliberately has pre_native_revision=0 and current postNative; no old-counter ordering is required.
- Child selected/default route L157-L206 makes its old-preNative comparison conditional on **not cold**, and requires preNative=0 in cold results. An outer generic classifier that always requires postNative >= original preNative would wrongly reject these valid shapes too. That is a specific compatibility test to add; I have not inspected an external family Queue branch.
- Native family pending is in WorkerState (bridge.cpp L12876/L12893), unlike local LIFE. Same-worker reconnection can retain it. An actual same-PID worker reset is not identified by the Python PID/birth-only cold flag and can instead wait on old last_checked_native_revision or ask for a vanished journal.
- Cold relation present is a current material fact, not proof of an old proposal's acceptance callback. Absent relation remains unresolved; refusal/invalidated are not fabricated from absence. A changed first heir/actor correctly remains unavailable rather than silently retargeting the pending action.

Smallest entry: preserve the established cold result semantics and optional per-domain owner scope; route a proven same-Game worker replacement to independent pair material read, rather than pretending every new connection is a new worker.

## Minimal shared contract improvement (proposal, no code edit)

Use the existing planning-source-frame/identity helpers. Do not add a universal cache, identity builder, history rewrite, replay service or blanket skip of monotonic checks.

1. Preserve **origin**: original action UUID/target/actor, original request/ACK/source frame, Game PID+birth when actually observed, and producer ACK lifetime (connection vs worker) with its genuine owner marker when available. Never fill missing historical origin fields from the new current Game.
2. Preserve **observation** separately: fresh current source frame + current Game identity + query UUID/type, plus observation kind `native_ack_receipt` or `independent_current_material`. Native counters belong to this frame. A current closure must still match current actor/date/target and the domain's current Native normalizer; crossing epochs is not permission to accept arbitrary stale DTOs.
3. A tiny pure comparison qualification can return `same_namespace / different_namespace / unknown` and whether **numeric order is meaningful**. Only same namespace can compare old/new revision/proof counters. Game PID+birth change proves different process; same PID alone does not prove same producer. Native hello connection_generation is owned by the worker, but changes on reconnection and is not a universal durable worker UUID. Legacy hello can even use the Python-local fallback counter (native_driver L1130-L1142). Declare each producer's lifetime rather than conflating all three scopes.
4. Keep distinct booleans/verdicts: original_native_ack_verified, current_material_observed, attributed_to_original_command. A cold current-law/family/custody observation may establish current material while original command cause/payment remains unverified. Retain original source_pending and immutable historical ACK. The external typed classifier must consume the SDK's explicit observation mode and **current** binding before applying mode-specific rules, rather than re-deriving business materiality from cross-epoch integers.
5. Pending disposition is explicit, never a silent deletion: verified original receipt; current-material-only resolved while preserving original uncertainty; still unresolved; or excluded by a proven loaded-checkpoint lineage. Same calendar date, absent relation, timeout, new PID or a lost Native ACK alone does not authorize clearing an unknown action or resubmission. A pre-action restore classification requires the exact retained checkpoint/lineage proof, as the existing gift classifier already models.
6. While an action remains unresolved, block a second submission for that purpose. Reuse existing domain fallback/ordinary routing so a missing optional receipt does not monopolize war/event handling. Do not blind-clear a ledger just to make the queue progress. Domain-specific cost/refund, bilateral relation and actor-continuity predicates remain authoritative.

Recommended sequence: harness closes the already diagnosed C11 classifier error; next routine source update addresses LIFE's explicit connection-local ACK gap first; then add comparison qualification to existing publication barrier and domain-specific owner dispatch. Audit/patch one demonstrated path at a time. There is no evidence here to batch-edit every typed outcome contract.

Future focused source regressions, **not executed in this audit**:

- Same owner later-frame warm receipt accepted; same/older warm frame rejected.
- Different Game, current material postNative27 plus immutable old pre3138 accepted only with current binding/mode; stale wrong target/actor/date/owner still rejected.
- LIFE new pipe connection: no old Native ACK is imported and no old submit is replayed; current material-only read remains distinct from original charge attribution.
- Family same worker reconnect retains pending; worker replacement uses cold pair mode; cold absent relation stays pending; preNative0 is preserved.
- Older selected checkpoint: only exact lineage proof changes loaded-branch disposition; numeric/date coincidence does not.
- Unknown inflight/transport remains guarded by the existing client before any subsequent query. No retry/extra read should be emitted merely because this scope classifier says unknown.

## Source pins / retained limits

Repository source evidence is at HEAD above; every file below matched that commit when pinned. Line spans are explanatory locators, not a claim that the current C11 frozen SDK contains every master change. Adoption/flags still need their existing owner pins.

| Path relative to ck3_autonomous_player | Bytes | SHA256 |
| --- | ---: | --- |
| `src/xar_autoplayer/lifestyle_formal_consumer.py` | 14386 | `d971e1737acd5654a6fdd9c7219a3982a6bce3de44b0c95bc0fac735922b7df2` |
| `src/xar_autoplayer/bridge/player_lifestyle_private_transport_v1.py` | 42857 | `dafc1c198928b3f68fa88976f1431bf29c5abb00e20a6c437a1b7792f3f6a47b` |
| `src/xar_autoplayer/bridge/pending_material_publication_v1.py` | 5865 | `8d3ad2b0aa6c029036e2800684ac57e1c0204d45740c47abe6ba46ed6f0ba917` |
| `src/xar_autoplayer/construction_formal_consumer.py` | 38521 | `ed408b47b0e9de3851a79aa06b4abaa631f8d663c46ee02e51b777905e75af5c` |
| `src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py` | 66026 | `c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e` |
| `src/xar_autoplayer/crown_authority_formal_consumer_v1.py` | 14198 | `3b2afd8a93a4f82a20e3fd86396ac8bf83987303f3296a28e0b9578cd1420181` |
| `src/xar_autoplayer/bridge/faction_gift_formal_route_v1.py` | 25000 | `5e9d2ab946d92c34ccb3a794f16a62028d01f4572813168593a94eac43646b30` |
| `src/xar_autoplayer/faction_gift_pending_v1.py` | 13656 | `2152c3e2c7f48bad6864c06d43a6e32e731736a72e65df5b134250a156450293` |
| `src/xar_autoplayer/faction_gift_cold_recovery_contract_v1.py` | 7051 | `72b408eaa65728470ee75a252af704c0586affb1e81e8094d6adcb8487a44429` |
| `src/xar_autoplayer/family_marriage_formal_consumer.py` | 58216 | `49f96c1d2e60dbfa56a6c2dff731612583408b876a3e4a8085b1a7cf363c530d` |
| `src/xar_autoplayer/bridge/observed_heir_marriage_private_action_v1.py` | 15087 | `4c338e2ed6317dc4c9c3db70e4df80b0fc6581ff65b2f3d441301030f40b3c05` |
| `src/xar_autoplayer/bridge/player_child_matrilineal_private_action_v1.py` | 15698 | `d790445b46703c31aafbf948ff32938b5b0863e5e06006484236d193329a5954` |
| `src/xar_autoplayer/bridge/native_driver.py` | 1613844 | `2b6912a4ba680e4f8a03288f4735b9ce6ee56da6a2f7ae8f3cca2a1ace67d81c` |
| `src/xar_autoplayer/bridge/service.py` | 873470 | `bb1960b2f0eb2bf943f90100c8fe966ebb5adcd3409a157c3db863dbcb846b0f` |
| `native_bridge/src/bridge.cpp` | 1604573 | `3bbd294df570b20c9e33fbc038945fe0ce57c87e938cacbc2551727cc4144c16` |
| `native_bridge/include/xar_bridge/ck3_12004_lifestyle_transport.hpp` | 1301 | `eafbfc72849f3b0109d4937dfe83ae2602f42ed885da9b3d3d696747a00d7e60` |
| `native_bridge/src/ck3_12004_lifestyle_transport.cpp` | 34269 | `9d28d839a2f99c640b7e727cf9ebe1c23ad9087865bcc80575bff3895a17e341` |
| `native_bridge/include/xar_bridge/ck3_12002_nonwar_router.hpp` | 8526 | `8d69dda369f651478e374081b59802ade2101619b3a03fa2dcbcb928ad273692` |
| `native_bridge/src/ck3_12004_faction_gift_router.cpp` | 30680 | `6f442c40ebe17cdeb6436d8b280872fcdbd72eee56be288560c4d9e23056a7fe` |

Single new audit MD <=32KiB, charged to original other128MiB/review. Existing M1 source, ABI report and external closures remain frozen.
producer_closed: true; future_write_bytes: 0; allocated_bytes: null; physical_release_credit_bytes: 0; external_writes: 0.

# Existing typed war settlement actions, CK3 1.20.0.3

Prepared 2026-10-03 15:17 Asia/Shanghai from source e38eb9bd7757275746d0ffed1c630fc1540d087e and saved coordinator artifacts. This file-only lane binds Steam build 25652598 and EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. It does not operate SDK, game, pipe or window, and does not mutate shared Git.

The existing victory sender is complete and reusable for Robert's actual three defensive wars. No new native command, ABI scan, permit or compile flag is needed. The native score and end-war input tree is recorded in [war-end-conditions](war-end-conditions-1.20.0.3-2026-10-03.md); it precedes this execution recipe.

## Existing native submission

The `.3` factory gates the exact executable SHA and reuses the reviewed `.2` diplomacy and command implementations. The existing exact `.3` core-comparison is GREEN/UNCHANGED for both modules. `SubmitEnforceDemands`, `SubmitSurrenderWar` and `SubmitOfferWhitePeace` share the production submit path in `ck3_12002_diplomacy.cpp`. It resolves the full-generation WarID, rereads paused/alive/current player and side membership, requires current primary leadership, rebuilds the requested context, and reruns final CanSend at `0x307C040`.

For victory the native resolution constructor `0xCF57D0` takes `true` for **player victory on either physical side**. Robert defending therefore selects attacker-defeat. White peace separately rereads the loaded CB permission bit and constructs special index3. `0x2968170` constructs a 0x368 send packet; the existing owning clone is queued at `0x37F06F0`, command manager `image+0x5CC1240`, flags0x0E. Temporary and embedded contexts retain their established destruction lifecycle. Queue success is submission only.

## Current observed boundary

The saved date53236608 options are production-live primitives, not current action authorization: War16777231 is `individual_county_de_jure_cb`, War129 is `minor_religious_war`, and post-refusal War50331736 is `populist_war`. Robert29829 is primary defender in all three. Their observed victory and white-peace final CanSend values were false; surrender was mechanically legal. No termination was submitted by this lane. These saved negative rows are not reused as a future same-frame decision.

| Existing MCP | Current public scope | Readiness boundary |
|---|---|---|
| `ck3_enforce_demands(war_id=W, expected_revision=R)` | Any actual CB, current primary player, player-relative score100 | Default capability; fresh native context/CanSend still decides. |
| `ck3_offer_white_peace(war_id=W, expected_revision=R)` | Existing narrow primary-attacker claim/de-jure policy slices | Current Robert defender cases are not included; `.3` final recipient response is still unavailable. |
| `ck3_surrender_war(war_id=W, expected_revision=R)` | Existing de-jure/Raiktor/terminal attacker slices | Native legality does not implement current defender title-loss policy. |

This table separates mechanical native sender availability from typed policy readiness. It introduces no new combat restriction. Continue the military loop using current observations and use the existing victory action once native legal100score is observed.

## Future single-submission recipe

1. In the retained Root SDK session take a fresh paused snapshot, retaining exact executable identity, actor29829, episode `native-29829-2bc2d599f7f9`, full W, primary leadership and public revisionR. Query `ck3_query_war_termination_options(war_id=W, expected_revision=R)` and retain its same-frame metadata. Choose victory only when the actual player-relative total is100 and the victory context's native validator/available are true. This is the existing action's readiness, not a newly added gate.
2. Record pre-state gold/prestige/piety raw Q100000 from the snapshot and campaign root via `ck3_query_campaign_root_context_v1(expected_revision=R)`. Refresh public revision as required by the retained session. The root context covers the player's held-title partition and realm/vassal scope; it is not a generic arbitrary enemy-title holder query.
3. Call `ck3_enforce_demands(war_id=W, expected_revision=R)` exactly once using the fresh current revision. The production driver already waits for the exact old full W to disappear. A failed/timeout/uncertain receipt is retained; no blind second submission is inferred from it.
4. Independently take a new paused snapshot and `ck3_get_war_state()`. Require absence of exactly W, preserve other actual wars, and compare actor/episode/date with the submission context. War absence following the known victory request establishes the observed terminal transition; ACK alone does not. Retain any active event or succession/invalidation changes that affect attribution.
5. Read the actual material aftermath. Compare raw resources and held titles/realm/vassal scope using fresh snapshot and campaign root. For populist victory additionally use fresh faction alerts and, when its already available query permit is enabled, player prisoner collection to observe the old faction33554465 alert's removal and rebel70766 custody. A targeting-alert row disappearing does not itself expose the global faction object's destruction. These readbacks are observations, not prisoner actions. Save the resulting normal checkpoint once.

## Material outcome limits

All three present defender-victory CB blocks avoid conquest title transfer, but different resource and custody effects apply. De-jure defeat includes attacker reparations; minor religious defeat includes defender piety and attacker payment; populist defeat includes faction cleanup and attacker imprisonment. Reuse the exact installed-stock clauses in the end-conditions topic. Record only actual before/after fields: no guessed payment, prestige/fame, piety, truce, dread, legitimacy or individual custody claim.

Current general observations can verify Robert's gold/prestige/piety, own held-title partition, realm/vassal scope, war lifecycle and optional faction/prisoner changes. They do not expose every nonclaim target holder/liege transition, all attacker participants, exact opponent resources, generic truce set or every ancillary CB effect. In particular target2128 belongs to the wider realm: absence from Robert's own held-title list cannot prove its holder changed. Generic claim-only terms and historical H2743 data are not substitutes. Report an unobserved material field as unobserved without blocking the existing useful victory transition.

Negotiated white peace remains a scoped construction entry if it becomes useful and native legal: close the exact `.3` final recipient evaluator and extend the same options DTO, then implement the actual current-CB defender policy. Current defender surrender additionally needs the chosen dynamic loss scope. Neither gap requires duplicating the existing owned sender or stops current combat.

## Reused verification and report fields

The native diplomacy header, sender and `ck3_12002_diplomacy_test.cpp` hashes match their prior GREEN receipt. That fixture invokes actual production sender functions with native seams and checks both physical-side outcome polarity, CanSend rejection, full IDs, owned clone/queue and context destruction. Retained fixture binary SHA is `74d705ea6a89e82ab45078661437bf0f94c36968ebf3c688f1bf54849cfbbd4a`; it is a test executable, not the CK3 EXE. The reviewed `.3` reuse receipt establishes ABI compatibility, not live termination.

Existing NativeHeadlessGameplayDriver tests check exact old WarID disappearance for enforce and distinguish white-peace/surrender `submitted_pending` from applied. Registered MCP fixture actually calls enforce through a callback driver; it only lists the other two tools. These complementary fixtures are not one native-sender-to-SDK end-to-end run. No concrete production sender defect was found, so no fixture was repeated and no new component was created.

Completed: confirmed reusable mechanical senders and legal100score victory scope; delivered once-submission and independent material-readback recipe. Why: preserve military delivery pace using established primitives. Readiness: native/static-ready actions, existing Robert options production-live primitive; Robert termination remains live-pending, with no victory/OODA credit. Test/artifact: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-settlement-typed-action/ROOT-DELIVERY.json` indexes source hashes, retained native/ABI evidence and child reports. RED: no new capability defect; current defender negotiated/surrender observation/policy gaps remain documented. Next: continue combat and later enforce an observed native legal100score, collecting actual postconditions. Commit/push: coordinator-owned adoption pending; this lane changes only isolated external artifacts.

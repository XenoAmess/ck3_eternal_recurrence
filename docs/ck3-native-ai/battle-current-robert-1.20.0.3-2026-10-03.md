# Current Robert battle preparation, 2026-10-03

This reuses the root's actual saved paused frame `war-native-readiness/actual-paused-war-v34-01/015-ck3_take_snapshot.json`; the child performed no process/query/action. The exact packet SHA and selected fields are in the external `war-battle-phase/current-robert-observation.json`.

The frame binds `.3` EXE `94B55397...02A6`, Robert `29829`, PID `119724`, connection `3`, `native:5`, public revision `2` / native revision `5`, date `53236608`. Player CUnit `83886367` is controllable, regular, at `2614`, with an empty route, `in_combat=false`, `retreating=false`. Its actual strength read is `2334/2461`, 40 regiments. There is no observed current CombatID to supply to battle transition, terminal, or phase trace.

| War / enemy public CUnit | Current province / state | Actual strength | Contact implication |
| --- | --- | --- | --- |
| `16777231 / 50331920` | `2640 / sieging` | `1362/1899` | Current target defender candidate, not already in a battle. |
| `16777231 / 83886484` | `2640 / sieging` | `302/311` | Second current same-province candidate; preserve actual ordering from contact scope. |
| `16777231 / 67109295` | `3078 / moving` | `101/101` | Stored 22-node route ends `2640`; it does not prove an arrival day or future actual join. |
| `129 / 16777683` | `4573 / gathering` | `2305/2305` | Different active war; do not merge it into a contact participant set without native hostility/contact evidence. |

Actual support flags are true for battle-control/transition/terminal/reinforcement v1 and combat v2; false for full v3 and phase trace. This independently supports the source inventory's public/private distinction. It does **not** validate a `.3` battle frame or simulated odds.

The root can next select its desired approach with existing route/horizon/actual-contact tools and form a v2 request using target `2640`, observed final adjacent entry, player `[83886367]`, and currently compatible ordered defenders. These are query preparation inputs; no army move, date advance or engagement has been performed by the child. Refresh the public revision before execution. Historical target `2629` and old episode participant IDs are not current arguments.

No native component patch is required to read the existing battle primitives at this endpoint: there is no active battle tactical decision here. The four precise forecast construction entries remain in [battle-readiness-1.20.0.3-2026-10-03.md](battle-readiness-1.20.0.3-2026-10-03.md). Missing selected commander next-roll or resumed forecast fields should be built when an actual root decision requires them, without blocking the existing observed battle loop.

## 2026-10-03: subsequent post-refusal discovery supersedes the earlier no-CombatID frame

The earlier native5 table is a pre-refusal observation. Root's later native14 query discovered Combat1577058305 and native16 read its actual stored sides: rebel attackers `[251658381,473,474]`, old-war defenders `[50331920,83886484]`, Robert absent. See [the actual lifecycle](battle-hostile-existing-combat-discovery-1.20.0.3-2026-10-03.md). The terrain appendix below belongs to the separate hypothetical Robert-versus-rebel input scenario; its width is not the existing battle's width.

## v34 Robert: actual terrain and route-backed entry inputs (2026-10-03)

The root's paused combat-v2 capture at `native:14`, public revision `2`, date `53236608` returned `available` and `input_observation_ready=true` for the explicit hypothetical player CUnit `83886367` versus revolt CUnits `[251658381,473,474]`, common WarID `50331736`. CK3 remains `1.20.0.3` / Steam `25652598` / EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`; the adopted v34 freeze binds that identity because the v2 source wrapper's two build fields are null. This child only consumed the root's frozen files.

| Input | Actual native observation | Meaning |
| --- | --- | --- |
| Target terrain | Province `2640`: `mountains`; width multiplier `50000 / 100000` | Native terrain key and width multiplier are available; no map inference. |
| Entry crossing | `2634→2640`: `none` | The actual preview's final edge has neither river nor strait encoding. This is the hypothetical contact's specified entry edge, not a player arrival already performed. |
| Encounter defender | Explicit enemy side; primary defender owner `70766`; `holding_defender=false` | Native `IsHoldingDefender` result is available. Absence of a holding-defender predicate does not remove mountain terrain effects. |
| Hypothetical new-contact width | Base `2762`, final `1381` | Applies to this requested participant composition, fixed at contact with no reinforcements. |
| Existing combat | Combat `1577058305`, Province `2640`, phase `0`, day `0`; width `2412→1206`; base advantage `-1200000` Q100000 (`-12`), resolved `0` | Actual fields of an already active battle. They do not prove Robert is participating or predict the new-contact advantage. |

The route preview and horizon at `native:11` back the caller's `2634→2640` final edge, with player origin `2614`, route `[2618,2617,2632,2613,8752,2628,2626,2627,2633,2634,2640]` and final arrival date raw `53238744`. The horizon covers only `53236608..53236632` and is one-day contact-free; it does not guarantee the full journey or that the existing combat will persist until arrival. The v2 query itself honestly retains `actual_route_dependency=false`: the root selected its hypothetical entry from an independent actual route preview.

Native reuse entries are `ReadCombatCandidateProvince` → terrain helper `0x247E590` → terrain `+0x60`, and `ReadContactGeography` → entry adjacency kind (`0/1/2/3 = none/strait/river/large_river`) plus `IsHoldingDefender` `0x2C09D30`. The exact installed `common/terrain_types/00_terrains.txt:109..116` defines `combat_mountain` defender advantage `12` and width `0.5`. That stock definition is evidence of the rule input, not an observed decomposition of the current combat's `-12` base or a complete future player advantage. All four selected armies report absent candidate commanders with legitimate `0/0` contextual roll endpoints; source components cannot be invented to turn those observations into a win probability.

For present net advantage and actual stored-order sides, use the already available `ck3_query_battle_transition_v1(combat_id=1577058305, expected_revision=<fresh>)`; the underlying current fields are CCombat `int64 +0x6C8/+0x710`. The public v2 terrain DTO does not publish a full defender advantage-source breakdown. If a later decision needs that breakdown, extend the same battle observation DTO using the already recorded phase-constructor leaves. This remaining quality gap does not reintroduce a war authorization restriction or block the observed geometry inputs.

Evidence: `Z:/ck3_mod_rewrite_process_assets/g2-resume-20261003/war-battle-phase/actual-battle-discovery-v34-02/004-ck3_query_combat_simulation_inputs.json`; route `war-movement/actual-post-refusal-v34-01/010-ck3_execute_step.json`, horizon `012-ck3_execute_step.json`; complete exact pins and report fields in `battle-terrain-actual/REPORT-FIELDS.json`. Readiness: **production-live primitive** for the geometry input slice only. No new SDK call, date advance, army order, window operation, test rerun or Git mutation occurred in this child package.

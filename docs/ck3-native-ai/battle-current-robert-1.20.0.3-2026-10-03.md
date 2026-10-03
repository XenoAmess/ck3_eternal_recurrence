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

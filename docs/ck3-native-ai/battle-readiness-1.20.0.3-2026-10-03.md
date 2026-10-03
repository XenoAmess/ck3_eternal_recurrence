# Battle observation and readiness for CK3 1.20.0.3

This file-only package prepares Robert `29829` combat work under the root's current authorization. It does not access CK3, advance a date, operate a window, build a DLL, or claim a new live result. Root owns the current campaign, runtime flags, MCP pipe, SDK, and Git. The current campaign's actual CUnit/Combat/Province IDs must be read from its paused frame; none of the episode IDs below is a current argument.

The exact target is CK3 `1.20.0.3 (Crozier)`, Steam build `25652598`, EXE SHA-256 `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. The reviewed `.3` adapter gates this SHA and reuses `.2` layout through `BindCk3_12003AdapterImage`. The existing `.3` `abi-comparison/core-comparison.json` reports unchanged battle, combat, phase, phase definitions, and phase advantage contracts. Reuse is static evidence; it does not move `.2` live results onto `.3`.

The reusable controller is **static-ready for this build**: battle identity, phase/day, stored-order armies, current loss ledger, current rolls/advantage, native strength, manual retreat legality, and terminal journal are implemented. A loaded `.3` descriptor advertises the battle v1 and combat v2 capabilities by inheriting `.2`. The root's first actual `.3` battle read and subsequent hold/retreat/terminal postconditions remain required for `.3` production-live claims.

## Minimal native observation tree

The generated graph and source-pinned edge table are in `battle-readiness-1.20.0.3-2026-10-03.graph.md`. These are the semantic boundaries behind it:

| Domain | Reviewed native source/consumer | What the public query can state |
| --- | --- | --- |
| Identity | CUnit storage → `+0x178` full CArmyID; reciprocal CArmy `+0x124`; CArmy `+0x128` full CombatID; Combat storage `0x5D1DE70` | Actual same-frame battle, with complete IDs and side arrays. Side `0` is battle attacker, `1` defender; do not substitute war attacker/defender. |
| Phase | Combat `+0x6B0/+0x6B4`, winner `+0x6E0`, forced winner `+0x700`, finalized `+0x704`, daily guard `+0x705` | `maneuver/main/pursuit/done`, phase day, current winner/finalizer. `combat_not_found` only proves old generation removal. |
| Advantage/roll | Combat base `int64 +0x6C8`, resolved `int64 +0x710`, current rolls `int32 +0x6D0/+0x6D4`, cadence `+0x6E4`; side selected commander `+0x74` | Current resolved advantage, last rolls, actual selected commander, and roll cadence. These are observations, not next-roll endpoints or a win probability. |
| Damage/width | Combat base/final width `+0x6C0/+0x6C4`; Entry60 effective damage/toughness/pursuit/screen `+0x40/+0x48/+0x50/+0x58`; native strength `0x2651100/0x2657B50` | Current retained entry stats and widths. They are not guaranteed future daily stats or outgoing damage. |
| Casualties | Entry60 starting/current/soft `+0x10/+0x18/+0x20`; main eligibility on MAA type `+0x98A`; side owner-hard ledger `+0x58` | For main-fighting entries, hard = starting − current − soft. Non-main reserve residual stays separate. Stored side totals may lag entry-derived current at tick boundaries; both values and matches-derived flags are retained. |
| Retreat | Native `0x258AA10`, owner-taking rule getter `0x28C2E10`, runtime minimum define `0x5C699B4` | Four gates in native order: disallowed; too early unless override flag; pursuit/done; landless rule. Scope is actual `full_side` or `owner_subset`, with affected and unaffected CUnits. |
| Terminal | Passive native finalizer `0x258CD50`, battle warscore writer `0x249A940` | Normal/no-normal history, result, old-ID removal, subject backlink/routes, residual and successor classification. Normal outcome requires the journal and actual result/war-score rows, not an ACK or missing CombatID. |

All army IDs in public methods are **public CUnit IDs**, including legal ID `0`; internal CArmy IDs must not be passed in their place. Counts and attribute raw values use separate semantics: Q100000 troop/casualty values divide by 100000 for people; damage, toughness, pursuit, and screen raw values are attributes or calculation quantities.

## Executable MCP queries

Use the public revision returned by the current paused root snapshot. Refresh it after operations. `prepare_battle_queries.py` emits JSON MCP calls using supplied observed IDs and never connects to a process.

| Public tool | Exact arguments | Intended use |
| --- | --- | --- |
| `ck3_query_battle_control_snapshot_v1` | `subject_army_id`, `expected_revision` | Current controllable public CUnit's battle frame and retreat gates. |
| `ck3_query_battle_transition_v1` | `combat_id`, `expected_revision` | Requery prior full CombatID even after the player CUnit leaves that battle. |
| `ck3_query_battle_terminal_transition_v1` | `prior_combat_id`, `subject_public_cunit_id`, `expected_revision`, optional `after_terminal_sequence` | Save journal cursor before hold; on later terminal query seek a newer event. Empty cursor `0` is represented by `null`. |
| `ck3_query_battle_reinforcement_assignment_v1` | `selected_public_cunit_id`, `expected_revision` | Actual help flags/target, committed route and native ETA. Present compatible contact is distinct from a future promised join. |
| `ck3_preview_active_combat_retreat_v1` | `selected_public_cunit_id`, `target_province_id`, `expected_revision` | Read actual legality/scope and produce fresh route/token for a separately authorized order. |
| `ck3_query_combat_simulation_inputs` | `target_province_id`, `attacker_entry_province_id`, ordered `attacker_army_ids`, ordered `defender_army_ids`, optional `expected_revision` | Explicit hypothetical precontact v2 inputs: terrain/crossing, stats, counters, candidate commanders/roll endpoints and knights. Do not use a hypothetical new-contact frame as active battle continuation. |
| `ck3_query_actual_contact_scope` | `subject_army_id`, `target_province_id`, optional `expected_revision` | Discover actual contact/ordered side membership; obtain real combat roles instead of assuming them. |

`ck3_query_combat_simulation_inputs_v3` and `ck3_query_combat_phase_event_trace_v1` are Python tool definitions, but the `.3` production descriptor does **not** advertise their complete native capabilities. Availability must come from actual hello/capabilities and typed result. The existing private `query-combat-phase-nonreligious-v1-...` diagnostic can expose implemented fields when its selected worker is loaded; it is not a public completed v3 contract.

The battle-control/transition/terminal/reinforcement v1 and combat v2 readers need no new experimental compile switch. `XAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1` is an OFF-by-default private research trace pair, not a prerequisite for these primitives. Runtime flag/permit ownership and the removed historical warfare stops were sent to the readiness owner; this package does not edit global authorization files.

For a hold, the existing official action is `ck3_execute_step(step_id="life-advance", expected_revision=...)`; only the observed elapsed day plus next paused same-CombatID frame proves a hold. A retreat order must consume the **fresh preview's** revision, CombatID, side index, scope, target and token using `ck3_order_active_combat_retreat_v1`. ACK remains verification-pending; verify retreating/route/target and old-C affected/unaffected membership. Pursuit can retain the old CombatID/backlink until the terminal phase.

## Commander and phase-event inputs

Current v2 reads each CArmy's candidate commander via `0x24E9ED0` / CArmy `+0x120`, generic advantage `0xC6DED0`, and its contextual min/max roll. The contextual endpoints add separately truncated generic modifier IDs `0x115/0x116` and terrain modifier indices from `+0x776/+0x778` to loaded base defines `0x5C699BC/0x5C699B8`. A missing commander is a genuine `0/0` endpoint; a failed read is unavailable. These v2 candidate inputs differ from the active battle's **selected** commander at side `+0x74`.

The phase source proof is native "all commanders, then all knights" stored order. The MAA side array mixes ordinary MAA and knights; only CArmyRegiment `+0x148 != -1` identifies a knight. `CArmyRegiment` type/army fields are `+0x18/+0x140`; the other CRegiment type at `+0x118` must not be substituted. Current phase data include injury/death, prowess, cultures, traditions, perks, accolades, rules, variables and side/army state. This full event layer is distinct from numeric casualty conversion.

Current installed stock `Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/defines/00_defines.txt` lists maneuver 3 days, roll cadence 3 days, event cadence 5 days, pursuit 3 days; damage scale .03, base main hard conversion .3, advantage damage factor 5, roll base 0..10, pursuit conversion 1, pursuit stat scale .5, baseline toughness contribution .05 and minimum pursuit .01. These are **installed stock file inputs**, not a claim that a current playset's runtime values or every exact `.3` transition has been observed. The observed runtime retreat threshold takes precedence over a stock day-15 expectation. The repo game reference differs from the installed defines and both phase-event files; the installed source is pinned here. Neither the reference's event content nor a historical hash is substituted.

## Concrete missing observations and next construction entries

1. **Active selected-commander next-roll bounds.** `.2/.3` `ck3_12002_battle.cpp` publishes current rolls and selected commander but does not fill the existing `selected_commander_next_roll_bounds` DTO. The v2 `ReadCommanderRollContext` already contains the reviewed arithmetic but has candidate identity and hypothetical terrain. Minimal entry: expose/refactor that read-only helper, pass actual side `+0x74` and Combat `+0x6B8 → Province+0x20 → Terrain+B8`, fill both existing DTO members only in an applicable main phase, and recheck identities in the current dual sample. Never call native roll production, which consumes RNG. A focused synthetic fixture should contrast army candidate versus selected commander, terrain modifiers and negative truncation; root then does one actual paused query. This unlocks contextual commander assessment without claiming forecast completion.
2. **Active counter/next-day advantage and casualty operands.** The richer `.1` active-resume sibling is absent from the `.2/.3` battle reader. Entry60 current damage/toughness alone does not expose the next tick's counter context or hard-casualty modifiers. Minimal entry: migrate the already researched operand leaves into the existing battle DTO using the `.3` reuse manifests and current CombatID; independently publish same-sample counter class/stack/context, hard-conversion and pursuit modifier inputs before using them in a continued-battle trial. This is a forecast dependency, not a reason to disable hold/retreat observation.
3. **Complete phase event/advantage model.** Current phase implementation still returns missing religion/rites operands and omits two constructor sources; current authorization removes the historical prohibition, not the missing reads. Entry: implement the 17 frozen AST subtrees' actually required fields and two constructor sources, then prove current loaded-playset/effect evaluator and same-day character feedback in a paused/live bounded trace. Do not reinterpret absent sources as zero or revive old owner-deferred reasons as current prohibitions.
4. **Reinforcement joins.** The existing v1 exposes route/ETA and present compatible CombatID; future actual join still requires actual arrival and subsequent side append/width/current ledger read. Episode02 R0149 closes one `.1` finite arrival; it supplies methodology and field distinctions, not `.3` campaign evidence.

No C++ component was changed in this package: no current root-owned `.3` battle frame was supplied that makes a missing forecast operand an actual prerequisite for the immediate campaign action. Existing basic battle queries remain the first production step. If the root encounters a concrete failed tactical decision requiring one of the listed fields, the native construction entry is explicit and should be implemented rather than cycling on `unknown`.

## Reused evidence and readiness

- `.3` static: `artifacts/migrations/2026-10-02/abi-comparison/core-comparison.json`, permanent `ck3_1_20_0_3_abi_reuse.json`, `.3` adapter and `.2` battle/combat/phase implementations. Their exact copied pins are in this package's `evidence/source-pins.json` and research plan.
- `.2` F21/F22 actual contact/control/one-day hold/normal terminal/full-side/owner-subset retreat are documented in `ck3-1.20.0.2-battle-migration.md`. They establish reusable regression scope; **not new `.3` live**.
- Episode02 R0148/R0149 explicitly use `.1` EXE `2D00FF31...83DB86`. Finite knight death and join findings remain historical `.1` evidence. Episode03 Lewes uses `.3`, but it is a siege/occupation case and does not validate battle rolls/casualties/retreat for Robert.
- This package: file-only research, static source analysis and record checks; no native functions, process reads, game actions, DLL builds or new live samples. `win_probability=null`, `sample_count=0`; no `.1` approximation, manpower ratio or native strength is called a `.3` probability.

Report handoff: root should record completed static readiness/query inventory, missing four forecast observation groups, reused evidence paths, no new live credit, and subsequent actual battle artifact/commit/push in the same day's and week's reports. This child does not edit the reports or perform Git operations.

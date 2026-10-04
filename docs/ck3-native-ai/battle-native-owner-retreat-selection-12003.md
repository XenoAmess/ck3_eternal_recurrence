# Native AI owner retreat selection boundary (1.20.0.3)

Exact build: CK3 1.20.0.3 / Steam25652598 / EXE SHA `94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6`. Readiness: **research**. This source-only increment closes dispatch, legality and actual owner scope boundaries; the native producer that chooses an active owner retreat remains unclosed. It adds no implementation, fixture, SDK, game day or live credit.

The ordinary `.3` AI path at `1A1CB00/1A1CFF0` checks active combat via `24AC3E0`; true takes its early skip. The current precontact classifier `19F5620 → 1A1C810` also returns raw1 before its predictor when attached Combat is true. Stock `.45` belongs to that stand/precontact tree; its current-build runtime lookup is `5C68568`, whose loaded value is not observed in this source packet. These branches establish precontact scope and leave the active owner-retreat threshold unclosed. Native legality `258AA10` consumes flags, elapsed time, phase and actual owner land/rule permission; its predicate does not compare current losses, strength or advantage. True native action selection remains a concrete source gap.

`258B010(Combat*, selected public CUnit full-ID, target Province*)` resolves the selected CUnit's `+178` CArmy and locates its side in the stored Combat rosters. It compares selected CUnit `+174` owner with each stored CArmy → `+124` public CUnit → `+174` owner. All owners equal dispatches full-side `258B830`; mixed owners dispatches owner-subset `264F0F0`. These apply/scope branches do not read Army `+120` commander. Commander identity remains separate from owner/action receiver; the unresolved selection producer may have further inputs.

Existing queries already distinguish main-entry hard residual from non-main residual, owner hard attribution, native Entry/Side strength, and actual advantage identities. That closes the available operands' identity map; it does not prove which of them the natural AI choice reads. The missing producer receipt is a specific observation increment through existing native command history/queue and battle DTOs.

```mermaid
flowchart TD
  D[Ordinary AI1A1CB00 /1A1CFF0] --> C{Active combat24AC3E0?}
  C -->|true| S[Early skip ordinary path]
  C -->|false| P[Ordinary stand / precontact work]
  P --> PC[19F5620 to1A1C810 classifier]
  PC --> AC{Attached Combat true?}
  AC -->|yes| V[Return raw1 before predictor]
  AC -->|no| PR[Precontact predictor and5C68568 lookup]
  U[Active native owner-retreat selection producer] -. unknown choice / receiver .-> R[258B010 actual selected CUnit and target]
  R --> O[Resolve actual CArmy; stored Combat side and owners]
  O --> F{All stored side owners equal selected owner?}
  F -->|yes| W[258B830 full-side apply]
  F -->|no| M[264F0F0 owner-subset apply]
  L[258AA10 flags / elapsed / phase / owner land legality]
  U -. native desirability remains unknown .-> L
  U -. future source-backed selected-action context .-> H[Existing horizon external action adapter gap]
  B[Caller hard-loss budget diagnostic] --> Q[Observed legality and current route preview; existing tool proposal]
```

Existing `run_conditional_horizon` consumes `ConditionalHorizonDay.ai_context` at continuing-main and pursuit stages. `action_selected is False` is an explicit caller timeline declaration; missing context or another value retains the existing selected-action adapter gap. Entry events precede admission, and the main forced/zero exit check precedes the continuing-main context check. A future source-backed owner action context plugs into those existing stages and preserves actual owner-subset identity. Unclosed native selection must not be filled with false.

Existing `assess_current_battle_retreat` is `own_selected_owner_single_frozen_main_tick_budget`, with `budget_source=explicit_caller_own_policy`. It compares the selected owner's modeled hard-loss delta against the caller's Q100000 budget, checks observed eligibility and route preview, then proposes an existing tool. It never executes the tool. This useful diagnostic does not predict native AI intent; win probability and retreat loss remain null. It remains separate from the still-unclosed native owner-retreat selection producer.

The next bounded source entry is the actual active-owner producer calling `1A188B0`, constructing `CMoveUnitCommand` vtables `476B168/476B138`, and reaching the payload/queue/`2969660` execution chain. Its active, target-different branch at `29697D7` reaches `258B010`. The known `1A1CF88 → 1A188B0` kind7 submission is already dominated by the representative `1A1CB59/60` active-combat exit. It does not close the true active producer. The current member/coordinator/owner association, actual combat, dispatch trigger, requested target and producer role must be read at the real selection callsite. Native target enumeration/rank/tie order remains another branch of that producer. A bounded direct-caller count or zero direct AI-region hits does not establish absence.

The narrow observation entry stays in existing native command history/queue and existing battle DTOs: correlate natural `1A188B0` producer caller return RVA and command identity/sequence with actual active apply, retaining full public CUnit/CArmy/owner/Combat IDs, phase, enqueue/apply raw dates, target, route, native mode and applied scope/result. Existing reinforcement-assignment observation supplies coordinator/subunit associations; control and transition observations supply current and prior Combat identity. After a real active receipt identifies its producer, trace that caller's decision operands rather than broadening a caller census. This observer is not implemented by the source packet.

The closed source branches and existing consumer interface are ready as a research handoff. True selection remains a typed native source gap; this packet adds no gameplay restriction and leaves Root's actual campaign independent. No selected-action adapter or stock threshold is inserted, and no complete Monte Carlo, battle win odds or native retreat intent is claimed.

Evidence: [native dispatch and owner application](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v61/native-dispatch/ROOT-DELIVERY.json), [native decision/legality source boundary](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v61/native-criteria/ROOT-DELIVERY.json), and [exclusive g38 consumer boundary](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v61/topic-report/G38-CONSUMER-BOUNDARY-MAP.json). The source-only daily/week fields are [Oct4/W40](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v61/topic-report/OCT4-W40-FIELDS.json). Native instruction/span pins remain owned by the two source lanes; this topic consumes their sealed summaries and does not recapture those caches.

## Increment: exact .3 activity recall selection, 2026-10-04

The v62 increment closes a named stock AI branch that can recall an already fighting army. New bounded1A188B0 caller evidence identifies1A23BD0, whose owner-derived target, mode0, native24AC1B0 permission and path checks can produce a CMoveUnitCommand. It has no ordinary active-combat early exit. The generic1A188B0 helper itself only clones the command through virtual+40 and submits to37EBC40; its use alone does not identify a retreat decision.

WHEN is the accepted daily command post-stage2988FD0→2989031→1A31EE0 actual AI pass, reusing the sealed calendar edge. The manager enumerates actual character contexts from base+90/+9C and+D8/+E4. Synchronous paths and native async callback tables45AC3E8/45AC2F8 reach19E80B0/19E8420 and the two activity wrappers1A7BDF0/1A7E370. The actor integer obtained from a character-keyed hash map is retained raw; it is not a calendar day.

WHO and WHY are source-backed: an admitted outer context calls its first mission planner; on rejection, the wrapper enumerates full public CUnit IDs in the character object's+278 list, resolves each unit's+178 CArmy, and calls1A23BD0 when the relevant CArmy byte+1D4 or+1EC is nonzero. The inner continuations still handle active Combat before their ordinary fallback. A sufficient rejection is independently readable: Character+1C0 object+318 native-list count at+324 being nonzero makes both first planners return false before battle metrics. The two Army bytes and that native list remain raw fields until their business identities/writers are bound. This branch does not compare retained battle loss, strength, advantage or generic casualty cost.

```mermaid
flowchart TD
  D[Accepted daily AI post] --> C[Actual character contexts and raw prefix]
  C --> P[First mission planner]
  N[Native object list count nonzero] -->|sufficient early rejection| F[Planner false]
  P --> F
  F --> U[Character full CUnit list to CArmy]
  U --> B{Relevant raw1D4 or1EC nonzero?}
  B -->|yes| H[Native owner-title target]
  H --> L[mode0 permission and path checks]
  L --> M[Move command submission]
  C -. current context observation not yet live .-> O[Readonly input leaf]
```

TARGET is the actual28B1CD0/28B2220 accessor path: native TitleStorage slot5D1DAF8, TitleID field+10, optional source fallback slot5D1DAE0, and raw-title-type2 first-child chains reach Title+338 Province. This must not be replaced with an arbitrary fixed capital or terrain ranking. Command base+0 is primary vtable476B168 and base+18 is secondary476B138. Submission EDX7, actual mode+2C, route endpoint+28 and desired owner target are separate values; none should be labelled interchangeably.

The E outer-prefix helper1A781A0 is now separately source-bound to actual context flags/level/land, owner rule bit41 and the current player-interface bit8 path. Current observed membership/prefix remains a separate reader dependency. Reading current raw inputs does not establish a submitted natural command or a future `action_selected=false`. The existing `native_command_history` is the local Python driver's primitive transcript, not a natural AI queue census. General battle-metric retreat selection, activity-byte writers and state+C4/C5 writers remain named subsequent source work; they do not erase this closed activity-recall branch.

Minimal readonly publication is now under implementation on the existing MCP surface: actual Unit/Army/owner identities, raw activity bytes, native list count, source-title-derived target and only source-bound current prefix fields. A shared unit-list attachment API supports regular-army strength observations as well as current BattleTransition observations; the transition/control role limits remain explicit. Current-input readiness, natural event capture and full native selection readiness are separate. No planner or submit method is invoked by a readonly query. This source-topic commit claims source closure only; production fixture results and any later live reader validation belong to their independent receipts.

Evidence: [new producer/caller tree](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v62/producer-callers/ROOT-DELIVERY.json), [new predicates and exact input fields](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v62/active-criteria/ROOT-DELIVERY.json), and [Title binding / E prefix addendum](Z:/ck3_mod_rewrite_process_assets/g2-resume-20261004/battle-native-owner-retreat-v62/active-criteria-binding-addendum/ROOT-DELIVERY.json). New targeted slices and cached .3 source reused the existing exact EXE identity; no whole EXE hash, repeated old checks, game, SDK, window or saved-day action was performed. The old v61 packet remains frozen.

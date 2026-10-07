# G2: current contact versus a contact-free first hop on 1.20.0.4

Initial source-only recipe, 2026-10-07 / 2026-W41, followed by the bounded P0 implementation and offline qualification below. Source base is `14f07ade00e9ad359da3aa6af3642592ede3f48d`; Root runtime at assignment is entry19. Exact native build is CK3 `1.20.0.4`, Steam25734779, SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. Root supplied original Robert29829, paused raw date53288448, ordinary save H9638 and saved total6005. This package does not read a fresh gameplay response, choose a numeric opponent/target, execute a query/action, or award sideR68 any G2 credit. Earlier enemy134218098 at2606 is a dated scene, not a current input.

The immediate useful change is to let the existing exact contact-free first-hop branch run before the distant endpoint battle forecast. Genuine endpoint contact continues to use the bounded estimate and its existing risk budget. `monte_carlo_ready` or complete native parity is not an added prerequisite for ordinary contact-free movement or siege travel.

## Native input tree and version boundary

[Army controller](army-controller.md), [combat prediction](combat-prediction.md) and [contact resolution](army-contact-resolution.md) preserve the exact historical1.19 native AI tree: stance/objective selection and deterministic estimated-power-share admission decide a destination; native movement places units; the local contact resolver independently selects an existing Combat or ordered new opponents. The estimated-power share is neither a simulated win probability nor bare soldier ratio. Those pages' historical thresholds, RVAs and stance semantics are not asserted as newly mapped .4 predicates. Reimplementing the full AI predictor is unnecessary for the bounded policy below.

The current .4 source authorities are [Contact migration](existing-contact-phase-migration-12004.md), [H1 restoration](route-contact-horizon-12004-restoration.md), [arrival bindings](battle-reinforcement-arrival-bindings-migration-12004.md), and [projected Contact](projected-contact-scope-v1-12003.md), whose algorithm and existing DTOs are adopted through the separate .4 factory. The [committed-route source chain](route-source-chain-12004-g2-restoration.md) already documents the existing daily consumer; this package does not repeat its qualification.

| Current .4 provider | Closed physical input and semantics |
| --- | --- |
| `BindRouteImage12004` | Actual Core/Army/movement roots; stored progress/path; native speeds and prefix duration `24AAD80`; complete subject/hostile timed routes. `one_day_contact_free` concerns only `[date_raw,date_raw+24]`, including boundary overlaps. |
| `BindContactImage12004` | Qualified Core/Army/H1 roots plus hostility `2C09620`, empty `24E83A0`, in-combat `24E8340`, holder `247D010`, holder classifier `2C097F0`, fallback `2C164C0`. Calls use the already closed null third hostility argument. |
| Existing local contact reader | Current target gate/mode, real unit/army/owner identities, stored target Combat/Unit order; last compatible Combat or first eligible hostile seed, independent reverse hostility and native defender classification. |
| Existing projected query | A real incoming army inserted in a caller-owned ordered list against the **current** target state. It publishes `none`, `create_new` or `join_existing`, native ordered sides and incoming role. It does not move an object or establish future membership. |
| Existing actual query / arrival admission | Actual subject-at-target or current arrival eligibility/side and current roster. It does not replace the timed H1 and does not authorize a future battle from an old observation. |

H1's common reader computes closed-interval conflicts and sets `one_day_contact_free = conflicts.empty()` (`ck3_12002_routes.cpp:816–1022`). The current Contact receiver/layout proof is the already sealed actual4 packet, not the historical19 offsets. Contact-capable, move-valid, favorable battle estimate, actual arrival and actual victory are distinct observations.

The diagram combines closed native input relationships and the construction plan. P0 below is implemented; projected-contact policy integration remains the separately named P1 proposal.

```mermaid
flowchart TD
  H[Historical native AI stance and deterministic power-share tree] -. not a new exact4 ratio implementation .-> P[Minimal counter-policy using current native inputs]
  N[Actual4 current army + full hostile scope + preview] --> T[Existing exact H1: current timed occupancy and edge conflicts]
  T --> C{Next intended segment has contact?}
  C -->|No| F[Exact first-hop preview + H1, existing move available]
  F --> M[Select first hop before endpoint forecast]
  M --> D[Existing committed-route one-day loop]
  C -. P1: final-contact policy integration .-> Q[Existing projected Contact against current target]
  Q --> R{Native transition}
  R -->|complete none| S[Continue existing objective / siege movement with route proof]
  R -->|create_new| O[Native ordered sides and incoming role]
  O --> B[Same-frame V2 or V3 base inputs + existing bounded risk budget]
  R -->|join_existing| A[Existing current Combat / battle-control inputs]
  O -. missing demanded opponent geometry only .-> U[Same-query concrete source leaf, not invented attacker entry]
  A -. missing active-resume model input .-> U
  D -. new paused observation .-> N
  B -. actual placement / future target state .-> X[Actual contact query and Combat readback]
```

## Concrete current consumer seams

The exact source `strategy.py::_general_battle_forecast_ingress` parses only a newly proposed `move-army` step. Its existing committed-route advance therefore bypasses this ingress. Its ordinary endpoint branch currently:

1. collects target `defenders` from snapshot enemy rows and assumes incoming is attacker (`16375–16438`);
2. obtains full-route preview and H1 (`16442–16500`);
3. requires endpoint V2/V3 inputs and evaluates `forecast_fixed_contact` / `contact_admission` (`16501–16575`);
4. only after admission reaches the existing exact contact-free first-hop branch (`16599–16653`).

Thus absent or rejected **endpoint** inputs can prevent an independently useful noncontact waypoint from ever being considered. This is a source-demonstrated functional coupling, not a claim that a newly read H9638 planner has failed at this branch. The current ordinary `_general` source does not consume the already available projected Contact query, so its target enemy-row partition is not the native projected attacker/defender partition.

`forecast_fixed_contact` actually checks `input_observation_ready` and exact scenario/participant identity, then runs the declared approximate model. It does not require `monte_carlo_ready`. Its optional Phase absence permits an explicitly generic estimate. `contact_admission` requires an estimated distribution and the existing loss/wipe/win risk budget, with `native_parity_required=false`. Preserve these meanings; neither completed Phase simulation nor full first-contact Entry is a new ordinary-movement condition.

The existing primary-defender siege ingress already has a first-hop escape for an unresolved future roster (`strategy.py:17050+`). It provides a construction precedent for the ordinary first-hop split. Existing `_native_operational_balance` calls base soldiers/power a routing signal, not battle odds; those values must not be renamed native probability.

## Minimum strategy construction recipe

This source-first recipe was sealed as commit `09737971e219e4c0b9ced832d0711c4ba92f3f97` before the isolated `strategy.py` change or new compound execution. P0 qualification follows below; P1 is not implemented by this package.

**P0: reach the existing first hop without requiring the endpoint model.** After the existing subject/route/full-hostile checks, detect a genuinely intermediate waypoint: the normalized remaining path has more than one Province and its first hop differs from the final contact target. Move the already present exact one-hop preview/H1 selection ahead of endpoint V2/V3 query and forecast admission. Reuse `_fresh_move_route_preview`, `_fresh_route_contact_horizon`, the existing history/frame joins, actual current hostile IDs and existing move-step availability. The selected hop needs its own exact `[first_hop]` path and H1 with no conflicts. It authorizes that waypoint order and the already existing day-by-day continuation, not the final endpoint battle. Do not mark an uncomputed model as used; report `future_contact_authorized=false` and current native route evidence. No new capability, native field, safety gate or model computation is needed for this branch.

If the same-route first day is contact-free but arrival is several days away, the current committed-route consumer already re-reads H1 each day. Starting an observed exact one-hop distant order can also be treated as travel rather than approval of the eventual encounter, while preserving its existing full-hostile/current-war checks. Keep this a separately named bounded travel result, rather than attaching a successful distant forecast that was not computed.

**P1: make actual contact scenarios use the existing native partition.** For the final intended contact, first consume a fresh `ck3_query_projected_contact_scope_v1` using the current target and preview-derived terminal incoming entry. Preserve its `hypothetical_arrival_against_current_target_state` scope. A complete `none` does not need a battle model and returns to the existing movement/siege objective path with route proof. A `create_new` incoming-attacker projection supplies ordered attacker/defender arrays and the same incoming edge for the existing V2/V3 scenario. A `join_existing` uses its actual selected CombatID and ordered sides with the current battle-control path; never feed an ongoing Combat to the new-contact model.

An incoming-defender projection does not make the player's incoming edge the enemy attacker's edge. Preserve the existing lower primitive only with explicitly declared scenario geometry; do not silently relabel that fixed scenario native future geometry. If a demanded native operand is genuinely missing, attach the next source input to the **same existing projected/contact query**, as specified below. This only limits that unresolved contact branch; the already proved first hop, siege travel or unrelated objective remains useful.

The P0 compound invokes the production decision path with an exact safe intermediate hop and absent endpoint model, selecting the existing first-hop query/order without evaluating the endpoint model; missing/stale H1 and first-hop conflict retain the current query/failure. Single-hop contact still demands endpoint combat inputs. A future P1 case must separately cover the native projected incoming-attacker and incoming-defender geometry branches; the current package does not manufacture those inputs or assert that integration.

## Concrete fresh query sequence and source-only missing leaf

Root obtains the next existing formal paused snapshot and derives actual subject, endpoint/objective and complete nonretreating hostile scope. Do not fill these IDs from the old2606 artifact. Current H9638 supplies date/player/save baseline only in this package; its public/native revisions and army roster have not been independently observed here.

| Need | Existing exact call / input |
| --- | --- |
| Current route preview | `ck3_execute_step(step=preview-move-army-<current subject>-to-<chosen target>, expected_revision=<fresh public revision>)` |
| Timed route scope | `ck3_execute_step(step=query-route-contact-horizon-v1-<subject>-to-<target>-h-<count>-<fresh sorted IDs>, expected_revision=<fresh public revision>)`; reuse the existing builder rather than hand-encoding stale IDs. |
| Intermediate hop | Existing preview to `remaining_route[0]`, then same existing H1 for that exact one-hop path. |
| Current-target role and roster | `ck3_query_projected_contact_scope_v1(subject_army_id, target_province_id, incoming_entry_province_id, expected_revision)`; entry from the fresh terminal preview edge, not a campaign constant. |
| Actual membership after arrival | `ck3_query_actual_contact_scope(subject_army_id, target_province_id, expected_revision)` and existing battle-control query if an actual CombatID exists. |
| Comparative endpoint stats | Existing V2/V3 query with the projected native ordered sides and an explicitly valid scenario edge. No Army-strength full payload is required just to choose a contact-free first hop. |

There is **no missing native leaf for P0**. The whole H1 plus current canonical snapshot/preview already publishes the required independent game values. Do not add a metadata-only observer.

For a demanded incoming-defender/new-contact geometry, the shortest potential same-query seam is the native selected opposing public CUnit/CArmy identity plus the **actual receiver's** current raw contact adjacency inputs already read by `ReadContactAdjacencyKind` (`ck3_12002_routes.cpp:1376`): Province pointers at the existing `kArmyCurrentProvinceOffset` and `kArmyTargetProvinceOffset`, validated full Province IDs, adjacency kind/raw match and source receiver. That helper uses existing `.4` Unit/Province mapping; the historical variable name `prior` does not itself prove an attacker's historical entry. Before implementation, reuse the closed constructor/caller source to prove which selected receiver/role demands it. Publish a legal nullable raw source result with that branch identity, rather than manufacturing an attacker-entry Province from a movement target. If the constructor needs a different operand, record that exact named existing caller edge and extend only it. No new EXE capture or such collector is justified merely by this plan.

Existing fixture construction is `projected_contact_scope_v1_production_test.cpp` plus its registered production serializer/normalizer/MCP ten-case receipt recorded in the projected topic. Its current actual4 factory/profile source is in `existing-contact-phase-12004/contact/CONTACT-PROFILE-SOURCE-CLOSED.json`. H1 uses `ck3_12002_routes_test.cpp` and `test_route_contact_horizon_contract.py`; ordinary strategy construction is `test_general_battle_strategy.py`, with `test_general_battle_v2_actual_814_12003.py` retaining the historical V2 approximate-consumer contract. These are references for the next **new affected fixture**, not instructions to rerun old qualified matrices or claim old fixtures as fresh .4 live evidence.

## Readiness and next outcome

The initial sealed source recipe was **research**, with Tests0/Build0/EXE0/Game0/SDK0. P0 is now **static-ready** through the unique offline case below; actual movement and G2 loop qualification remain Root's next work. Root owns the fresh replan, action and independent paused postcondition. P1 can first wire the already existing projected query; demanded defender/join operands remain branch-specific construction entries. Saved6005 and H9638 are Root-provided baselines, not new saved progression. Full Entry/person preparation, calibrated battle forecasting, resolved battle/occupation, war completion and full G2 remain unclaimed.

## P0 implementation and first new consumer qualification

Production commit `d5163ec024710493a54d593ccee94ebfa9248d33` moves the existing intermediate-hop branch ahead of endpoint V2/V3 input demand and `forecast_fixed_contact`, within `_general_battle_forecast_ingress` only. Current subject/contact-state checks, complete hostile roster, full-route preview/H1, exact first-hop preview and fresh first-hop H1 remain the branch's inputs. The result carries the actual first-hop route/H1, `general_battle_forecast_used_for_decision=false` and `future_contact_authorized=false`; no uncomputed forecast/admission is attached. Existing single-hop contact, inbound reinforcement and endpoint risk admission retain their production path. Single-hop distant travel has not been expanded by this change.

One unique compound is `ck3_autonomous_player/tests/unit/test_general_battle_first_hop_before_endpoint_12004.py::FirstHopBeforeEndpoint12004Tests::test_current_normalized_h1_reaches_first_hop_before_endpoint_forecast`. It exercises the production native H1 normalizer and unmocked history/frame joins on a synthetic .4-compatible current frame. Only `forecast_fixed_contact` is replaced by a must-not-call sentinel; this case evaluates no numerical forecast and claims no fresh native wire or game observation.

The first attempt on `d5163ec0` failed at import before any test assertion: the fixture imported the V2 capability/builder from `war_contract` rather than `combat_contract`. The original RED receipt and stderr are preserved under `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/g2-battle-entry-contact-first-hop/FIRST-COMPOUND-RESULT.json`. Fixture-only correction `de9712ec7bfcb8975d20de042109d6c42c287610` imports those symbols from their owning module; production source did not change for the retry.

The corrected unique compound was first assertion-executed at `2026-10-07T07:55:35.408794Z` and completed GREEN at `07:55:37.693888Z`, 2.284359s process wall time, unittest 1/1 with five subcases:

1. Fresh normalized route and H1 select `move-army-11-to-40` with no endpoint cache or combat-query capability, while recording no model use or final-contact authorization.
2. Missing first-hop H1 selects that existing H1 query.
3. Stale native revision also selects the current first-hop H1 query.
4. A genuine normalized first-hop conflict selects no move.
5. A single-hop contact continues to demand the existing endpoint V2 query, with its current participant/edge contract.

Successful receipt, exact tested full source pin and argv: `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/g2-battle-entry-contact-first-hop/attempt02/FIRST-COMPOUND-RESULT.json`, with stdout/stderr beside it. The two earlier first-hop assertions in `test_general_battle_strategy.py` were updated to the new no-forecast semantics; that old file was not executed. Old cases0, native tests/builds0, EXE reads0, game/SDK operations0, days0, saves0 and new live/G2 credit0. Next useful outcome is Root's next fresh paused plan reaching the existing first-hop query/order and verifying actual waypoint progress; do not hot-apply this child to entry19 or replace the current enemy scope with a historical row.

# Finite same-campaign B route after R08

machine_id: desktop-3fevhd2-1c74096080. 2026-10-21 UTC source-only recipe. R226 is closed; its retained geometry/stock observations are historical inputs, not fresh permission for the next game. No SDK/Game command was executed for this document. Reuse a06/a07 for rate/capacity details; do not rerun the spent split pilot.

## Candidate pair and the exact missing read

Use unchanged Army18 as the prospective carrier, rather than the old child16777340. The smallest located candidate pair is **2624 then2623**:

- R226 Army18 was embarked at8645 with an empty complete route, no move target,1194 soldiers and stock/cap300. Its source proves no already queued landing leg.
- At2624 the actual parent/child full observations had positive20 monthly and cap100. This is a location/input clue, not Army18's future rate/cap.
- The retained child preview2624->2623 returned route[2623], available, with target eligible=true, P0, limit5657 and usage0. Its county-entry condition was false because the county object was the same. That is the R04 county-damage predicate, not proof that the Move is illegal. The preview did not submit a Move.
- These files contain **no Army18@8645->2624 preview**, and no proof Army18 can already land there in the new scene. Do not use a child preview to authorize the fleet's Move. Alternate2619 had ongoing combat in the old frame and is not a preaccepted rest site.

After R08's observer is actually detached/restored, fresh paused snapshot F must retain the original game PID/birth/generation/actor and independently rediscover Army18. The next useful public read is:

`CommonRequestRelay.request(unique_id,'ck3_execute_step',{'step':'preview-move-army-18-to-2624','expected_revision':F['revision']})`

Use the actual current full Army ID if it changed. Check accepted/status, route_preview army/origin/target/date, complete route, target province_supply and captured_target_land_supply_inputs_v1. This read unlocks either a real landing candidate/path or an explicit refusal/missing-input result. It does not execute, reserve boarding money, certify safety or prove arrival. If unavailable, stop this route choice and retain its exact diagnosis; do not fan out a map scan or guess another coastal province.

## Bounded execution using existing public primitives

1. Fresh selected full observation rechecks Army18 stock/cap/rate, commander and Fleet date/terrain operands. The old seven-day date threshold and negative scalar are conditional; R08's actual final date replaces any assumed +24. Do not alter that one-day experiment to wait for supply.
2. With an explicitly admitted later B-window budget, retain a fresh empty route/unchanged fleet context and use original CaseClient.advance_day(1,timeout,allow_event_boundary=True). Drain native events/interactions through the existing policy. Count actual updater/stock results, not elapsed days. Stop the wait at the finite cap or any invalidating state; no claim that the due date guarantees a stock update.
3. Only after actual natural stock loss, fresh preview the landing again. Save a unique Move intent before the original `ck3_move_army(army_id=18,target_province_id=2624,expected_revision=fresh_revision)`. Independently read its stored target/route. ACK-unknown means inspect once, never re-Move. Follow that route with the existing finite snapshot/day loop, stopping on arrival or invalidation.
4. At actual stationary2624, take independent full endpoints. Verify the actual commander, stock and cap: landing clamp remains unknown, and sea headroom may not survive. Require0<=S<C and actual final rate>0 before a bounded recovery opportunity. If an update increases S, retain source-bound before/after evidence. Replenished soldiers and cap truncation do not count as stock growth.
5. For point2, require **fresh headroom again**. If point1 returned to cap, use another independently legal/naturally consuming leg before attempting point2. Alternatively, arrive with enough real initial deficit to survive point1. Do not presume one sea debit is enough: fixed C300/rate+20 would turn292.98246 into300 at point1. Three fixed -7.01754 debits would leave enough deficit for two +20 updates, but neither three debits nor their dates are promised or imposed as the plan.
6. Once point2 is feasible, fresh preview the same actual Army from its actual location to2623, then the same unique Move/independent route/finite arrival sequence. At2623 recheck actual stock/cap/rate/cohort/owner and obtain its own positive stock endpoints. Old child eligibility, old usage0 and an ETA never replace these inputs.

Normal-save the continuing campaign through the existing ordinary Save contract; do not overwrite its protected immutable input. A later save/window must retain one coherent campaign lineage and actual Army identity. Do not combine two different cold S0 results as the two sites.

The source implementation patterns already exist: r04_county_entry.py::unique_move lines89-106 and snapshot_only_to_target329-357; the original public advance_day enforces once-only natural requests. The a05 pilot only fixes result checkpoint serial names; it is not this travel runner and must not be restarted. The existing qualify_one_b_site.py consumer can assess retained site input, separately from this recipe.

Formal B0/2 remains unchanged until both distinct-province observations satisfy the real consumer. R05 is an optional later opportunity only if naturally stock<1000000 and the full stationary regular1/siege3 native physical-loss fences hold. Fleet state4, negative rate, a deficit, time passage or soldier replenishment alone supplies no R05 credit. Ordinary war/event handling continues; this finite filming choice does not authorize sacrificing an army or waiting indefinitely.

# H3937 combined paused war observation design

Status: **static design, no launch or date authorization**. This integration
branch stacks the two native read ports on the #595 route-contact and #612
phase-0 Python candidates. It does not enable either existing hard false gate.
The old H3937 DLL `A8EAC0CD5BEEDF90778C76C14679629A96EDD4F7E7B398EB035B865F776786E9`
does not have the province-local query or per-army route status. A combined
attempt needs a Release DLL built from this exact integration checkout, a
fresh ordinary raw-to-prepared rebind and no-launch preflight, and one managed
session; output from distinct DLL sessions cannot be called same-frame.

## One-session sequence for a future separately reviewed collector

1. Require the #612 source identities, new exact DLL and injector hashes,
   fresh prepared-state path and byte-bound rebind receipt, producer checkout
   commit, and fresh Steam-offline/screen ownership evidence. Refuse before
   process creation if any identity or authorization fails. Keep
   `action_authorized=false` and `date_advance_authorized=false` on all paths.
2. Cold load H3937. Take paused snapshot `S0` and apply #612's exact actor,
   War 16777231, Army 83886367 at 2610, date 53219928, episode, modal,
   readiness and generation gates. Project **all native-published** enemy,
   allied and player armies, with unique IDs and the same published rows for
   a player army repeated under allies. Preserve each row's
   `route_read_status` and `route_source_count` beside its current province,
   route and move target. Require every row to have the new fields together:
   paused complete routes use `complete_empty` with count 0 or
   `complete_nonempty` with count equal to the route length. Reject
   `invalid_header`, `unresolved_entry`, `target_only`, `not_attempted`,
   missing fields, contradictory counts, or changing rows. Native roster
   enumeration still lacks a physical-inventory completeness bit; record
   `complete_physical_army_inventory_proven=false` explicitly.
3. If the published roster and route proof pass, issue exactly one
   `query-province-local-siege-v1-2610` read at `S0.revision`. Take `S1`.
   Require `accepted`, exact ProvinceID, date and native revision, valid
   observable occupation and siege fields, the same paused frame and scope,
   and exactly one appended read-only history row with matching result.
   Preserve nulls as unknown; do not infer no siege from a missing siege
   pointer or from an H3928 report. A `partial` response is a bounded RED
   observation, never a substitute for occupation proof.
4. Only when the full **published** roster/route/2610 observation succeeds,
   consider a route-contact query in the same session. The #595 route-contact
   runner is fixed to hostile IDs 50331920 and 83886484, both stationary at
   2629, while H3937 has not observed that state. Its exact subject predicate
   must independently pass on `S1`; otherwise stop after the province query,
   record `route_contact_not_queried`, and request a new reviewed dynamic
   query design for the actual roster. Never issue its fixed query merely
   because an earlier H3928 frame matched. If eligible, issue its canonical
   read-only `QUERY_STEP` at `S1.revision` and take `S2`.
5. Require `S0/S1/S2` to have the same snapshot ID, native/public revision,
   date, episode and connection generation; identical war/army scope; one or
   two exact query-only appended rows; route-contact result bound to the
   complete observed hostile set and same snapshot; unchanged save, child
   sidecar, DLL, injector, rebind receipt and checkout; and proven managed
   cleanup. Save full raw envelopes and a bounded projection. Any failed
   check is RED, with no date or gameplay step. Even a successful read-only
   route-contact result gives no date credit until war risk, cash and formal
   selected-step contracts are evaluated independently.

## Integration and validation boundary

The #612 phase-0 CLI currently requires the old DLL hash and forbids all
queries; the #595 CLI independently pins old assets and assumes historical
stationary enemies. Neither CLI may be reused unchanged for the combined
session. A future collector needs a separate entry and tests for malformed
route status/count, province partial response, changed frame/history, absent
physical-inventory proof, mismatched hostiles, cleanup failure and no-query
fallback. This design does not flip either launch gate or alter an action
selector. The native read ports themselves have offline C++ fixture and
Python contract coverage; live H3937 result is still unobserved.

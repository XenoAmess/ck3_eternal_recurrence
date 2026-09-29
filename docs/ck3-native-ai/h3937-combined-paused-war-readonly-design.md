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
   missing fields, contradictory counts, or changing rows. Require own Army
   83886367 to be currently stationary at 2610 with a complete empty route,
   no combat and no retreat. Native roster
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
4. Only when the full **native-published** roster/route/2610 observation
   succeeds and `route_contact_horizon_supported=true` is advertised on S1,
   consider a route-contact query in the same session. Preserve all
   unique enemy IDs from `S1.active_wars[0].enemy_armies`; derive the sorted
   nonretreating `dynamic_hostile_ids` with the same predicate as
   `_route_contact_hostile_ids(S1)`, and require it to be nonempty. Build
   `query_route_contact_horizon_step(83886367, 2610,
   dynamic_hostile_ids)` from that current row and require the native mailbox
   to re-scan the same current war row before answering. Bind its one-day
   window to raw 53219928 through 53219952. The #595 runner hardcodes two
   historical enemy IDs and positions; leave its existing CLI disabled and
   create a distinct reviewed dynamic read-only collector path. H3928 IDs or
   positions are never fallback inputs. If the roster or query set changes,
   stop after the province query and record `route_contact_not_queried`.
   Otherwise issue the dynamic read-only step at `S1.revision` and take `S2`.
5. Require `S0/S1/S2` to have the same snapshot ID, native/public revision,
   date, episode and connection generation; identical war/army scope; one or
   two exact query-only appended rows; route-contact result bound to the
   complete observed hostile set and same snapshot; unchanged save, child
   sidecar, DLL, injector, rebind receipt and checkout; and proven managed
   cleanup. Match the dynamic result's hostile IDs to the `S1` query set and
   its native source revision to the paused frame. Province and route-contact
   `query_sequence` values are per-query-family counters; the ordered driver
   history rows, not cross-family numeric succession, prove Q1 then Q2.
   Save full raw envelopes
   and a bounded projection. Any failed
   check is RED, with no date or gameplay step. Even a successful read-only
   route-contact result gives no date credit until war risk, cash and formal
   selected-step contracts are evaluated independently.

## Integration and validation boundary

The #612 phase-0 CLI currently requires the old DLL hash and forbids all
queries; the #595 CLI independently pins old assets and assumes historical
stationary enemies. Both existing driver constructors also omit the exact
`succession_lifecycle_binding` required by the current cold restore path;
that live mismatch is RED pending separately reviewed fixes. Neither CLI may
be reused unchanged for the combined session. A future collector needs a
separate entry and tests for malformed
route status/count, province partial response, changed frame/history, absent
physical-inventory proof, mismatched hostiles, cleanup failure and no-query
fallback. This design does not flip either launch gate or alter an action
selector. The native read ports themselves have offline C++ fixture and
Python contract coverage; live H3937 result is still unobserved.

The disabled `h3937_combined_readonly_queries.py` is an inner collector for
the future managed session. It validates complete native-published routes,
issues the province 2610 read, then constructs a dynamic route-contact step
only after the province and roster stay in the same paused frame. It records
exact read-only history rows and raw envelopes with zero gameplay/date
authorization. Its result deliberately keeps
`outer_session_cleanup_verified=false`; the future owner must wrap it with
the corrected lifecycle binding, exact source/rebind checks, persisted driver
history, asset rehash and managed process cleanup before any official result.

## 2026-09-29 master58 integrated candidate

The newer `research/h3937-combined-master58` branch starts at reviewed
`ea5c0000e78028e856be93a8fb2cef866b48049a` (#565/#595/#612 rebased on
master `58d6bf8ec8d8ca8055aed06657fea6275ca8988e`) and carries the two
native read ports plus the disabled inner collector. The lifecycle mismatch
described above is fixed in this newer static stack; the historical live RED
attempt stays RED. Neither older #595 nor #612 CLI is a combined entry.

`h3937_combined_paused_war_scope_run.py` is a disabled **outer** managed-session
candidate. It requires the corrected ordinary `succession_lifecycle_binding`,
fresh byte-bound prepared rebind receipt, exact H3937 checkpoint/sidecar,
the combined Release DLL/injector pins, source checkout and source-module
hashes before session creation. It calls the inner collector once, retains
S0/S1/S2 and both raw query envelopes, then verifies two exact persisted
query-only history rows, one cold restore, same paused frame, unchanged assets
and checkout, and managed cleanup. Its report says
`GREEN_READ_ONLY_COMBINED` only when all those checks pass. This is a
read-only observation label: action and date authorization are always false,
and physical army inventory completeness remains unproven. The outer and
inner hard gates are false, and there is no enabled combined CLI command.

Release build attempt `D:/ck3-research-artifacts/h3937-master58-native-build-attempt07/`
used the exact combined native tree at source commit
`080add7fd06727c318feca9cbfc81734ca5992ca`. DLL SHA-256 is
`310E58F50A9B66360B9FDC761B05AC52F3BD99096E19723A2DAB69F015D5A7A0`
(3,131,392 bytes); injector SHA-256 is
`ED3FBCA683D570BE5B7835894B35CDF4217EC15051FFB2A04F0C53131FE6B99A`
(39,936 bytes). Fixture, synthetic suspended injection and synthetic running
attach CTest cases passed; none launches CK3. The later outer Python-only
commit must preserve the exact native tree, and a reviewer must independently
verify the binary/source binding before any official rebind. A **new**
isolated official raw-to-prepared pair and no-launch preflight are required
for these binary pins. The historical `A8EA` pair and every old live attempt
remain distinct. Any future live attempt additionally requires separate
review, fresh Steam offline and screen ownership evidence, and its own
append-only external output directory.

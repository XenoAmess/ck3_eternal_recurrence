# H3937: one-day recovery after a combined paused read

Status: **design only; date, movement, attack and surrender remain RED**. This
contract starts only if a future, separately authorized H3937 managed run
completes `S0 / Q1 / S1 / Q2 / S2` with exact assets, one paused native frame,
two query-only history rows and proven outer cleanup. The current inner
collector keeps `outer_session_cleanup_verified=false`,
`physical_army_inventory_completeness_proven=false`,
`action_authorized=false` and `date_advance_authorized=false` even when its
read-only checks pass. No H3937 combined live result exists yet.

## Answer to the one-day question

**No independent one-day date credit follows from that read.** A route-contact
result with `one_day_contact_free=true` and `conflicts=[]` covers the dynamic
hostile IDs published in the native war row at the current revision. It does
not certify that every live, physically present hostile CUnit was enumerated.
`ReadArmies` currently returns an empty vector for an absent or malformed
storage header and silently skips slots with an unaccepted ID or failed
canonical-unit check. `ReadWarsAndArmies` then builds the published war roster
from that vector. The route-contact mailbox checks its requested IDs against
the same native-published snapshot, so its agreement is not an independent
inventory-completeness proof. A nonempty war row, exact positions, complete
per-army routes and a Province 2610 `available` result narrow the uncertainty
but do not close it.

The historical [R0271 first-hop contract](r0271-uncertain-siege-first-hop-2026-09-28.md)
did authorize a typed move to 2614 and six separate one-day continuations
under its then-current **bounded, published-roster risk** policy. That is
evidence about those exact formal runs, not authorization to replay them from
H3937 or proof of complete physical inventory. The original [R0271
request](../autonomous-agent-progress/coordination/war-requests/requests/WAR-ROBERT-R0271-SIEGE-PARTITION-20260928.json)
keeps the future 2629 participant partition unknown and forbids using an
aggregate force count, partial V3 forecast or automatic surrender to resolve
it. H3937 is at 2610 on raw 53219928; a hold there is a new decision, not the
old move to 2614.

There is an **existing formal date seam** outside this disabled H3937
collector. `native_driver._fresh_route_contact_advance_proofs` derives its
hostile IDs from the published war row without a physical-inventory
certificate, and `strategy.py`'s stationary branch can select
`native_war_stationary_contact_horizon_progress` when that published-roster
horizon is contact-free. This document and its new bare-boolean test do **not**
close that formal path. A separate formal driver/selector hard gate with
negative tests is required before any H3937 read may be used for a date step;
the current H3937 research result remains date RED.

| Evidence after a hypothetical GREEN read | Established | Still unknown |
| --- | --- | --- |
| S0/S1/S2 war rows and per-army route statuses | Current native-published IDs, positions and complete routes | Whether the physical live-CUnit scan omitted a hostile |
| Q1 Province 2610 `available` | Current occupation, fort, garrison and siege fields for 2610 | Future 2629 encounter membership and siege outcome |
| Q2 current-order 24-hour contact-free horizon | No modeled contact with the requested published hostile IDs in that window | New hostile orders, new units and unenumerated units during the day |
| Current inner collector result | Query-only observations with no gameplay | Formal risk, cash, source lifecycle and executable date permission |

## Smallest missing native authority

Add a versioned, paused-only `physical_army_inventory_v1` observation from
the exact CK3 1.19.0.6 CUnit storage and native war-hostility relation, in the
**same native snapshot and connection generation** as the contact query. It
must expose a typed `complete` / `partial` / `unavailable` status; an unknown
read cannot be serialized as an empty hostile set. The result needs:

1. `snapshot_revision`, `date_raw`, `war_id`, `subject_army_id`, source build
   and connection generation; a query envelope additionally binds public
   `snapshot_id`, public revision and `episode_run_id`. The mailbox must read
   and compare native state before and after the inventory and route query.
2. Validated storage pointer/header/capacity and a bounded count of slots
   scanned, live canonical CUnits, known stale or nonorderable slots, and
   unresolved candidate slots. A valid empty slot is distinct from an
   unreadable or truncated slot. `complete` requires a fully scanned valid
   capacity, no truncation and **zero unresolved potentially live units**.
3. The sorted full-generation IDs of **all** live units classified as hostile
   to Army 83886367 in War 16777231 by an authoritative native relation,
   including retreating units, with their current Province, retreat/combat
   status and route-read status. The
   classification must account for every live CUnit, including a unit absent
   from the existing `enemy_armies` projection; third-party or neutral units
   need explicit nonhostile classification, not silent omission. Any
   ambiguous owner/side/hostility relation makes the result `partial`.
4. A distinct sorted `query_eligible_nonretreating_hostile_ids` set, derived
   from the complete physical set by the exact reviewed engine predicate.
   This second set must equal the published war row's query set and the
   route-contact request/result set. The currently different Python and C++
   retreat predicates must be reconciled or fail closed. Each excluded
   retreating unit needs independent native proof that it cannot contact the
   subject during this day; otherwise date selection remains RED. Every
   included hostile and the subject needs a complete, generation-checked
   route read. Preserve any set disagreement or excluded-unit uncertainty.

A bare `complete_physical_army_inventory_proven=true` flag in a Python
snapshot or a saved report is insufficient. Native source identity, scan
counts, status, IDs and frame binding must be validated as one receipt; the
formal driver must consume that receipt or a same-frame token. The present
`ReadArmies` API and mailbox do not publish this certificate, so this is a
source/ABI task, not a configuration switch.

Even a complete *current* inventory plus a 24-hour route timeline is not a
logical guarantee that AI orders or raised units cannot change during that
day. A future policy may admit **one bounded day of current-order risk** if
its formal war and cash budgets explicitly accept that uncertainty. A strict
no-surprise-contact claim would additionally require a native execution
guard that notices newly hostile units or changed orders and pauses before
contact; no such guard is proven here.

## Proposed date and action gate

For the present H3937 research source, the result is
`RED: inventory_completeness_unproven`; the existing formal date seam above
also remains open until its own hard gate is reviewed.
Do not emit `life-advance`, `advance-route-contact-horizon`, `move-army`, an
attack, a siege assault or a surrender from the read-only collector. Do not
reuse the old H3928 enemy positions, the R0271 move authorization, or a
target-2629 V3 defender list.

After the native certificate exists, a separately reviewed formal consumer
would need **all** of the following for one candidate day:

1. A qualified outer H3937 source/rebind/lifecycle/cleanup receipt and a
   newly paused current snapshot with no forced event, interaction, active
   combat or other blocking modal. War, actor, subject and Province identities
   are checked anew; no prior save's query is imported.
2. A `complete` physical inventory certificate and complete per-army route
   statuses in the same native revision, plus Province 2610 `available` when
   occupation/siege affects the choice. Reconcile all friendly controllable
   armies and all hostiles. The stationary subject must still be at 2610
   without a committed move, combat or retreat. If it is moving, use that
   actual route and the existing moving-route policy instead.
3. A fresh contact query over exactly the certified nonretreating query set,
   with every excluded retreating hostile independently cleared, bound to the
   current frame and raw `[D, D+24]`, with `one_day_contact_free=true` and
   `conflicts=[]`. Its subject route/position must match the snapshot.
   Reject missing, partial, stale, conflicting or target-only evidence.
4. The formal war continuation and joint cash/resource selector must accept
   the one-day cost and risk. Preserve the unresolved future 2629 participant
   set. An actual selected typed one-day step must pass the native driver's
   revision, generation, query-history and one-shot checks immediately before
   execution. A read-only receipt cannot itself become `selected_step`.
5. Submit **at most one** 24-raw-tick day. Require the next independently
   paused snapshot to show the actual date transition and state; if it stops
   early, changes war/army/Province state, loses a proof or hits contact,
   record that outcome and stop. Do not retry an uncertain submission.

At `D+24`, start again with a new native inventory certificate, Province
read where relevant, new complete route/contact query, and new formal risk and
cash comparison. Previous day IDs, timeline, forecast and permission expire.
If Army 83886367 changes position or receives a route, reclassify it before
selecting any step. Future target 2629 contact needs its own contemporaneous
participant/forecast gate; arriving at 2614 or remaining contact-free for a
day never authorizes that battle.

## Static checks and provenance

The inner-collector unit fixture's contact result is explicitly
`one_day_contact_free=true`, while its physical-inventory and date flags
remain false. Its normal and `-O` tests verify that a caller-supplied bare
inventory boolean cannot promote **that inner read**; they do not assert a
formal selector or driver block. The existing formal
`test_committed_route_requires_fresh_daily_horizon_even_when_sentinel_live`
checks that a date change invalidates the preceding day's proof. These are
static invariants; no CK3 date was advanced for this design.

Source references: `ck3_autonomous_player/native_bridge/src/ck3_11906.cpp`
`ReadArmies` / `ReadWarsAndArmies` and
`route_contact_horizon_v1_mailbox.cpp` `RouteContactHostileScopeMatchesSnapshotV1`;
`ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py`
`_fresh_route_contact_advance_proofs`; and
`ck3_autonomous_player/src/xar_autoplayer/strategy.py`
`_primary_defender_siege_forecast_ingress`.

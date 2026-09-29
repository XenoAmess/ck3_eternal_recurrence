# Ordinary feast guest rule provenance: passive exact-build read

Status: **source and focused fixture; paused membership remains RED**. This
private default-OFF path has not produced an observed membership result. It
applies to CK3 1.19.0.6, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
It extends the [ordinary rule binding](activity-feast-guest-rule-toggle-1-19-0-6.md)
and [Stage-5 guest read](activity-stage5-feast-guest-candidate-1.19.0.6.md).

The original `activity_feast` definition lists `activity_invite_rule_vassals`
among its default guest rules (`game/common/activities/activity_types/feast.txt:798-832`).
That rule runs `every_vassal` subject to its authored predicate
(`game/common/activities/guest_invite_rules/activity_invite_rules.txt:194-214`).
Several default rules share priority 1, so an ID in the final priority-1
group does not establish which rule supplied it.

## Native decision tree

```mermaid
flowchart TD
  A[Native Stage-5 planner refresh 0x10B0780] --> B[0x28CF3A0 traverses active rule rows]
  B --> C[Original scripted effect call 0x28CF515]
  C --> D[Temporary per-rule typed CharacterID list]
  D --> E[Merge into priority group]
  E --> F[Original group filter 0x28D06C0]
  F --> G[Intersect captured per-rule IDs with filtered group]
  G --> H[Same-frame authored-key and candidate membership query]
  B -. inactive rule .-> U[unknown: no original effect output]
```

The call at `0x10B0A5C` passes the planner's active-rule vector
`planner+0x1A18` and filtered-group vector `planner+0x1590` to `0x28CF3A0`.
Within its rule loop, `0x28CF4B0` loads the 16-byte active row's definition
pointer and priority. The call at `0x28CF515` invokes the rule's loaded effect
at `definition+0x38` via `0x3380410`. On its natural return, the temporary
output has a `+0x100` row pointer and `+0x10C` row count. The matching list
key is `definition+0x9C`; its 0x48-byte row contains a typed-value pointer at
`+0x10` and count at `+0x1C`. Type 4 values hold full CharacterID at `+8`.
`0x28CF590..0x28CF5B0` merges these IDs into the priority group and loses
their rule origin. The final original filtering later runs per group.

Two exact-prologue observers wrap the original `0x28CF3A0` refresh and
`0x3380410` effect executor. Each trampoline calls the original once. The
effect observer records only calls returning to `0x28CF51A` inside the
current natural refresh; it never invokes a scripted effect for inspection.
After the original refresh returns, the observer intersects each rule's
temporary IDs with the final group of the same priority. It stores a bounded
capture with the current feast planner, paused date/actor/thread, native
definition hash, active-rule contents and final group contents. Any changed
frame/vector, incomplete read or overflow returns a typed unavailable result.

The new private step is `query-activity-feast-guest-rule-provenance-v1`.
It takes the existing exact paused Stage-5 context fields, authored rule key,
and `candidate_character_id`. It first uses the existing key-to-unique-row
and window-binding read, then matches the native hash to exactly one captured
active rule. An observed response contains raw rule ID count, filtered rule
ID count/list, natural refresh sequence and the candidate's membership in
that filtered list. On an inactive rule or a frame without a matching natural
refresh, membership remains `null`; a priority group is never substituted.
The stock feast `max_guests=40` is an authored capacity input, not a measured
native invitation or acceptance outcome.

This read supplies a decision input only. It does not send an invitation,
prove acceptance or attendance, start the feast, advance a turn, or close a
cold-recovery contract. Its focused MSVC fixture checks exact instruction
anchors, rule-specific ID capture, post-filter intersection, negative
candidate membership and stale-group rejection. R0386 supplied a separately
frozen DLL, official pair/no-launch check and paused live read, but the
membership result was unavailable as described below.

The bounded Python runner and operator now expose this read only when a named
rule and the same run's filtered candidate read are requested. The transport
checks the exact envelope, candidate identity and unchanged paused frame;
observed membership still yields `hold` with invitation and Start disabled.
No live membership result exists yet. In H3928,
R0378 separately found Stage-5 `final_can_start=false`: actor 29829 failed
`is_available_adult` because `in_army=no`. A future action trial therefore
needs a fresh legal paused frame with `final_can_start=true`, a matching
candidate/rule membership read, native invitation legality, and the action's
independent postcondition before any Start or invitation claim.

## Ordinary invitation decision seam (2026-09-29 source trace)

The frozen executable still hashes to the EXE SHA above. The original
`window_activity_guest_list.gui` hashes to
`FD293E8FA1D73AFB15D5B1DF2EE1075E7184185E871E8B359F5C1BEC9FADFA97`;
`feast.txt` hashes to
`CE9B72F84B534CE5B8E0764FBFE0552CDBE889ABDEC370747643014B2668FB7C`.
The ordinary GUI offers `ToggleInviteFromRules` for each category
(`window_activity_guest_list.gui:100-115`). Its per-character Select button
is visible only for a special guest (`:547-552`). The normal feast definition
uses category rules and `can_be_activity_guest` (`feast.txt:798-839`).

The exact executable's `0x10B0780` consumes active rules at planner `+0x1A18`
and refreshes filtered groups at `+0x1590`. For each group CharacterID,
`0x28D07A1` calls `0x28CEC60`; that routine checks `0x28AF3B0` and evaluates
the activity type's guest predicate at `+0xD58` before retaining the ID.
Thus the existing candidate reader samples a **post-filter** group and then
checks original join chance and arrival. The provenance read identifies which
named active rule supplied an ID before groups lose that origin. Neither read
is a command validator or evidence that an invitation was sent.

Stage-5 `0x10B0DA0:0x10B1018-0x10B1092` copies the planner payload into a
temporary `CStartActivityCommand` and invokes its validator. After approval,
`0x10B13F0:0x10B1400-0x10B14A9` refreshes the planner, copies the payload and
queues the command. This is an **activity-level** final gate. The source trace
does not establish a separate ordinary per-character invitation action or an
independent pre-Start `final_invite_legal` boolean, nor when the game records
each guest's invitation. No new aggregate read or typed guest action is
justified by the current frame.

```mermaid
flowchart TD
  A[Paused Stage-5 feast] --> B[Active named rule and natural refresh]
  B --> C[Per-rule CharacterIDs]
  C --> D[0x28CEC60 guest predicate and filtered group]
  D --> E[Same-frame candidate join and arrival]
  E --> F[Same-frame named-rule provenance and target value]
  F --> G{0x10B0DA0 final activity CanStart?}
  G -- false --> H[Hold and preserve exact native reason]
  G -- true --> I[Policy approves one typed Start]
  I --> J[0x10B13F0 command queue]
  J -. requires independent readback .-> K[Created activity, cost and guest state]
```

R0373's candidate 38293 and R0377's opinion +62 came from separate paused
runs. R0378's `activity_invite_rule_vassals` was active with 22 filtered
characters, but that aggregate count does not establish 38293's membership;
the #675 provenance bridge has source/fixture coverage only. R0378 also had
`final_can_start=false` from the host's `is_available_adult` army condition.
The next useful trial therefore needs a **new legally Startable paused frame**
with candidate, named-rule membership, join/arrival, target value, current
cost and final CanStart read on that frame. Only then can a formal Start
consumer submit once and verify created activity, debit, guest state, next
turn and required restore. Until then `final_invite_legal` remains unknown;
candidate filtering and a positive join estimate do not turn it true.

## R0386 paused read RED and diagnostic boundary

R0386 used source `d7cbfb4`, Release DLL SHA-256
`5EE67F398863B1EE63A0E8F4BD2E95B5F5F486C2B614CECF071A34BFC27C02CF`,
and the officially paired H3928 paused Robert frame (actor 29829,
raw date 53219928). The Stage-5 candidate and combined route proof both read
the same native refresh sequence and fingerprint, but the named
`activity_invite_rule_vassals` provenance query for CharacterID 38293 returned
`no_normal_refresh`. The runner correctly retained RED; it did not infer a
membership boolean, toggle a category, invite, Start, or advance the game date.

The rule query first returned an observed rule state; its native transport
assigns the same `no_normal_refresh` status when either the second passive
slot-12 read fails or the provenance observer's `latest.sequence` is zero.
The R0386 result does not distinguish those two branches. The earlier
candidate and route proof had observed the passive capture, but that does not
prove its status at the later named-rule query. The exact executable's call at
`0x10B0A5C` supplies `planner+0x1A18` as the fourth argument and
`planner+0x1590` as the sixth, matching the hook's binding. The artifact does
not distinguish an absent matching callback from a callback rejected by its
paused frame, thread, planner, feast-type, or Stage-5 gate.

The next default-OFF diagnostic build reports the second passive read's exact
status or counts each rejection at the natural provenance refresh hook,
whichever branch fails. It includes those details only in the existing
`no_normal_refresh` RED message. It never synthesizes a rule membership,
invokes a refresh or scripted effect, or enables invitation/Start. One newly
paired bounded read can identify the actual failed gate before changing the
capture rules. This diagnostic is source and fixture coverage until that read.

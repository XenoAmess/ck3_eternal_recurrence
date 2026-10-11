# M4 Council through the ordinary planner on 1.20.0.4

2026-10-08 / 2026-W41. Candidate parent is SDK087,
`08709ee77115ac602d8185bc982abef8768e4c04`. The engine input remains CK3
1.20.0.4 / Steam25734779, EXE SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The work reuses the existing qualified Council primitive. It reads no EXE,
introduces no native body, flag, schema, MCP tool or planning framework, and
has **authored source / FIRST NOTRUN** status. Root owns the one new compound
and the future actual paused query/action/receipt.

## Native inputs before the wiring change

[Council composition](council-composition-ai.md) records the native candidate
collection, position main skill, valid-character and fire/reassign rules.
[The actual4 adopted port](council-government-12004-adopted-mcp-port.md) binds
these inputs to the current executable; the historical namespace and old
DTOs are not a new .4 live claim. The
[existing formal consumer](ck3-1.20.0.2-council-private-formal-consumer.md)
uses the current exact native final gates, ranks only legal higher-skill
Steward choices or a legal vacancy, and retains its typed submit, independent
receipt and fresh campaign-root incumbent observation. Chancellor vacancy
fallback and its existing explicit-role handling are unchanged. Native AI's
full utility weights remain unknown; this candidate reuses the already
implemented skill policy and does not guess a replacement score.

The actual4 campaign projection binds Position lookup
`0x2684EE0`. In `ck3_12004_campaign.cpp` lines1423-1448, validated task owner
and scopes distinguish raw incumbent `-1` (known vacancy, serialized `null`)
from a resolved full CharacterID; missing or unresolved tasks are unavailable.
`campaign_root_context_contract.py` lines848-933 preserves the typed nullable
incumbent and all five core seats. `_root` and
`_same_frame_campaign_root_result` retain the existing actor/date/native and
public snapshot binding. A missing position row is not an observed vacancy.

The source087 registered `ck3_plan_turn` and `ck3_auto_turn` choose
`GameplayBridgeService.plan_turn` / `auto_turn` when `nonwar_only=false`.
Previously `plan_council_private` was called only by `plan_nonwar_turn`.
Consequently a successful independent Council final-gates query did not make
the normal planner select its typed Council action or pending receipt.

```mermaid
flowchart TD
  A[Normal registered plan or auto; nonwar_only false] --> B[Existing normal lifecycle, war and domain priorities]
  B --> C{Otherwise selected life-advance?}
  C -->|No| U[Preserve selected action/query or blocked state]
  C -->|Yes, existing Council action opt-in| D[Existing plan_council_private]
  D --> P{Existing pending assignment?}
  P -->|Later native frame| R[Select existing typed independent receipt]
  P -->|Not yet later| W[Keep pending-later-frame; no duplicate or date step]
  P -->|No| G[Read current native final gates and existing skill policy]
  G -->|Useful legal choice| S[Select existing typed Council submit]
  G -->|NO_CHANGE or rejected gate| L[Keep baseline advance]
  R --> I[Applied receipt plus independent matching incumbent]
  I --> F[Existing following-turn holder observation and consumption]
  F --> K{Current old-role seat explicitly changed?}
  K -->|Known vacancy or different holder; same-role reads agree| V[Preserve applied receipt; next_turn_consumed false]
  V --> J[Continue existing ASSIGN_REQUIRED or REPLACE_REQUIRED dispatch]
  J -->|Legal choice| S
  J -->|NO_CHANGE or rejected gate| L
  K -->|Same holder| O[Keep existing persistence flow]
  K -->|Missing, unknown or observer conflict| H[Keep existing mismatch handling]
  S --> P
  G -. Native full AI utility remains unknown .-> X[Recorded quality boundary]
```

## Minimum source change and remaining scope

The normal planning view retains its already collected snapshot/history for
the Council consumer. After the existing domain and prisoner/release
priorities, the consumer runs only when `life-advance` is still selected.
The existing wartime-return path uses the same final dispatch rule. A selected
war action/query, opening focus, lifecycle/modal or other domain action keeps
its priority; the change neither sets `nonwar_only` nor requests another
nonwar service. The normal dispatcher already handles the private Council
submit and receipt tokens, so its existing implementation is reused.

An assignment ACK remains pending. An unchanged native revision retains the
existing `council_pending_later_frame` state; Root obtains the actual later
frame before material verification. No predicted date or synthetic receipt
is used. This original wiring keeps the holder/following flow; the B11-18 increment
below releases only an explicitly changed current seat. Neither change
promises a useful current candidate: Root's
fresh gates may lawfully produce `NO_CHANGE`.

## B11-18 changed-holder continuation: source authored, not run

Before this increment, `private_council_formal_consumer_v1.py` lines291-295
already computed the current legal choice. Lines304-326 nevertheless returned before its existing
ASSIGN_REQUIRED/REPLACE_REQUIRED dispatch whenever the applied assignment
no longer matched. Thus an old receipt for A blocked a seat now known vacant
or occupied by B.

Keep the original persistence write when A still holds the seat. Otherwise,
release this old following block only when the old-role root row explicitly
contains `incumbent_character_id`, the applied candidate field exists, and the
current holder differs from A. The observer must also explicitly contain the
same incumbent: for the selected role it is the fresh query's position; for
another role it is the independent root holder. Two explicit nulls agree on
vacancy. Missing rows/fields, unavailable observations or disagreement retain
the existing mismatch handling.

The existing `_write` retains the historical applied receipt and current
consumption with `next_turn_consumed=False`, then planning continues through
the already computed selector. It neither replays A's receipt as a submission
nor excludes A from ranking, and infers no death or removal cause. Current
native legality, skill policy, pending/urgent handling and query path stay
unchanged. This increment is SOURCE_AUTHORED_NOT_RUN; the historical compound
below supplies no new qualification, appointment or M4 material credit.

The sole new registered compound is
`test_g2_normal_council_service_compound_v1.py::test_registered_normal_council_submit_receipt_following_failgate_and_war_priority`.
It uses real registered MCP callbacks, the real normal Service and existing
Council consumer with the preserved historical DTO Driver seam. Only the
baseline chooser is a fixture seam. It covers typed submit once, pending
frame, independent applied receipt, following holder consumption, a native
fireability rejection and a selected war-query priority. All these are
offline fixture facts; no new .4 Native or Game execution is claimed. The
compound is authored but has not been run by this worker.

M4 itself remains false. Historical Robert construction
53178312–53181984, Council53220000 and first useful Sway material53249664
cannot join one interval of at most17520 raw hours. The
[explicit window reporter](m4-explicit-material-window-12004.md) retains
their actual dates. Root needs useful current construction, Council and
vassal/faction material in a newly selected actual window. Gift and
construction formal opt-ins are not set by the current SDK CLI; those are
separate source/configuration gaps, not completed actions. Current war scope
for new construction and the existing normal gift arbitration remain
separate inputs. No timestamp relabeling, forced appointment, manual Sway
consume or M4 counter update is introduced.

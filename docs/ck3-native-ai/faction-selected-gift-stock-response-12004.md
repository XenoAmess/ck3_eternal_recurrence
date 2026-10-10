# CK3 1.20.0.4: selected faction gift consumes the native dangerous rule

2026-10-10 source increment: the selected-recipient boundary has a concrete
continuation gap when the first direct landed leader/member is already gifted
or natively denied. The [same-frame continuation candidate](faction-gift-candidate-continuation-12004.md)
preserves the existing native/ordinary decision tree and prepares only new
continuation worlds; its compile/FIRST/live status is separate from the
qualified stock-danger comparison below.

Completed background package, 2026-10-07 / 2026-W41. Research first read immutable
source `05e7ef5b08be07afd9cd747d5d60965c3c2aee5b`. The minimum Python consumer now
joins the chosen gift to its current native stock-danger row and gives that
response precedence in the existing peaceful building/gift comparison. No new
native capability, MCP tool, gameplay action, flag or production gate is added.
The new sole Service compound is **GREEN / offline fixture** at source
`79b9225a011a9131b76737759520dc151d25e806`, 2026-10-07 19:40:12 Asia/Shanghai.
The current local CK3 prohibition remains effective: no executable read, fresh
hash, SDK call, process query, window operation, game date, saved day, G2
milestone or production-live qualification is claimed.

## Native input evidence before policy

The exact current engine is **CK3 1.20.0.4 / Steam build 25734779**, EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
`docs/ck3-native-ai/ck3-1.20.0.4-faction-adopted-native.md:23` records that
identity; its lines68-78 record the individually migrated faction/native inputs.
The actual .4 binder is
`ck3_autonomous_player/native_bridge/src/ck3_12004_faction_alerts.cpp:5`.
The existing .4 adapter passes these current addresses to the address-free
typed reader; it does not invoke the old .2 image binder with a substituted hash.

| Native input | Actual .4 source / operand | Existing publication |
|---|---|---|
| Full-generation faction and current target | `CFaction+10`, target `+40`, type `+20`; faction storage `5D1DE90/5D1DE10` | `faction_id`, `target_character_id`, opaque `faction_type_key` |
| Canonical nullable leader and character members | `+44`; member vector `+48/+54`, original full Character IDs | `leader_character_id`, `leader_is_human`, `character_member_ids` |
| Final power and dynamic threshold | `2601ED0`, `2602180` | `power`, `power_threshold`, percentage points Q100000 |
| Current discontent and final monthly growth | `+28`, `2601B30` | `discontent`, `discontent_per_month`, points / points per month Q100000 |
| Native months estimate | `2601C40` | `months_until_max_discontent`; not an exact deadline |
| Native stock dangerous final | `1D65BD0`, `bool(ignored RCX, CFaction* RDX)` | `dangerous_by_stock_rule`, explanation `danger_reason` |
| Actual existing faction war | `2603A90` and full WarID `+8C` | `faction_at_war`, nullable `faction_war_id` |
| Gift legality and concrete effect | prepared actor/recipient context; final `307C020`; named `gift_value` and recipient-root `send_gift_opinion` | existing private preview, native CanSend/cost/opinion delta |
| Already applied gift modifier / current total opinion | current .4 `28BC470/25A2EE0/2949A80/2596290`, native gift definition | distinct presence / signed modifier value and recipient opinion |

The shared reader
`ck3_autonomous_player/native_bridge/src/ck3_12002_faction_alerts.cpp:354`
invokes power, threshold, growth, months and at-war, keeps actual signed values,
then derives the reviewed explanation at line285 and compares it to the
independently called native dangerous final at lines374-377. A mismatch is
unavailable. The .2 namespace is an implementation namespace here, not the
current engine identity.

Current authored scripts reuse the sealed .3-to-.4 GameContent proof:
`docs/ck3-native-ai/vanilla-event-source-migration-12004.md:7` records
`InstalledDepots/1158311` manifest **5078208590259867811**, declared size
**19091661807** bytes in both installed builds. Its source proof is
`Z:/ck3_mod_rewrite_process_assets/g2-migration-20261007/vanilla-events/data-proof/SOURCE-PROOF.json`.
The faction migration explicitly applies this reuse in
`docs/ck3-native-ai/ck3-1.20.0.4-faction-adopted-native.md:76`.
This supports reuse of the authored rule reviews; it neither transfers old
live observations nor substitutes for the separate exact .4 native mapping.
The source-only worker has not reread or rehashed those cached receipts.

Reviewed stock tree anchors are
`common/scripted_rules/00_rules.txt:354`,
`common/scripted_triggers/00_scripted_triggers.txt:206`, and
`common/important_actions/00_realm_actions.txt:351`, as recorded in
`docs/ck3-native-ai/ck3-1.20.0.2-faction-metrics.md:42` and retained by the
current final-result / explanation comparison.

```mermaid
flowchart TD
  A[Exact .4 paused player frame] --> B[Full-generation current targeting faction]
  B --> C[Native final danger at 1D65BD0]
  B --> D[Canonical leader / type / native growth / native months]
  D --> E{Leader is human?}
  E -->|yes| H[Reviewed dangerous explanation: true]
  E -->|no| F{Type is peasant_faction?}
  F -->|yes| P{Native months <= 12?}
  F -->|no| G{Native monthly growth > 0?}
  P -->|yes| H
  G -->|yes| H
  P -->|no| W[Reviewed watch explanation: false]
  G -->|no| W
  C --> I[Require native final equals reviewed explanation]
  H --> I
  W --> I
  I --> J{Faction already at war?}
  J -->|yes| K[Existing war handoff]
  J -->|no| L[Existing dangerous or watch row]
  B --> M[Existing native-selected direct landed leader/member]
  M --> N[Native gift final legality / cost / opinion preview]
  N --> O[Existing budget-approved selected gift]
  O --> Q[Same-frame join to its original faction alert row]
  L --> Q
  Q --> R[Only this chosen row's stock danger enters shared spending priority]
  R -. Actual .4 gift material / next turn NOTRUN in this package .-> S[Independent applied receipt and source-faction requery]
  Q -. Native selector does not enumerate all preview alternatives .-> U[Other factions / members remain outside this bounded choice]
```

## Concrete missing formal consumption

The fixed production source already generates a selected gift only after native
legal, auto-accepted, positive opinion and reserve-budget checks. Its existing
Python chooser is
`ck3_autonomous_player/src/xar_autoplayer/faction_gift_policy_v1.py:45`:
power/discontent are required as observed material, but the ranking at lines183-200
only uses cost/opinion delta, leader role, current opinion and full IDs. It does
not consume the native dangerous rule, growth, dynamic threshold or months.

The current native selector
`ck3_autonomous_player/native_bridge/src/ck3_12004_faction_gift_router.cpp:286`
selects the first non-war targeting row with a direct landed canonical leader,
then a character member, at lines301-309. It returns before any all-candidate
gift ranking. The Python wrapper
`ck3_autonomous_player/src/xar_autoplayer/faction_gift_formal_candidate_v1.py:117`
therefore consumes one observed candidate, even though its helper supports a
sequence. This package may honestly prioritize **that selected candidate's**
native stock danger; it cannot claim a globally optimal faction/member choice.

The real shared budget selector
`ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py:668`
sets `prefer_income` in peaceful building/diplomacy comparison. Its first key at
line801 prefers an eligible positive authored-income building without consuming
any faction danger. `faction_gift_proposal` at line321 carries only source
faction/opinion evidence. This is the concrete functional input gap for the
minimum Python change below.

The existing public normalizer
`ck3_autonomous_player/src/xar_autoplayer/bridge/player_faction_alerts_contract.py:796`
already separates dangerous, watch and war-handoff IDs from the current rows.
Its `planner_projection.dangerous` can also be true solely because of county
exposure; it must not be used as if it describes an unrelated selected gift.

## Minimum deterministic response

Join the already budget-approved selected gift to an existing normalized public
alert on the bound native snapshot revision, date, played Character ID and
exact current build. Use the candidate's full `source_faction_id` and actual
recipient membership in that specific current row. If that row is a non-war
`dangerous_by_stock_rule=true` targeting faction, carry the observed stock
danger as the selected gift's spending-priority evidence. Keep native legality,
quote, existing shared resource claims and reserve tests unchanged. Its urgent
response may precede the positive-income preference; a watch candidate keeps
the existing peaceful comparison.

Existing source production can reuse an already recorded same-frame alert or
obtain the existing `ck3_query_player_faction_alerts_v1` / native step
`query-player-faction-alerts-v1`; no new MCP, native ABI, CMake flag or gameplay
action is needed. This is an observed policy improvement, not a new universal
prerequisite for unrelated independent construction. Missing/mismatched alert
material earns no urgent-response label, and does not invent a political score
or create a synthetic member.

| Input branch | Bounded formal meaning |
|---|---|
| Native-selected gift source is same-frame dangerous, non-war and actually contains recipient | The existing legal, positive, funded gift is a stock-danger response candidate |
| Same selected source is watch | Continue the existing ordinary gift/building comparison |
| Another unrelated faction is dangerous | Do not relabel the selected watch gift; alternate native selection remains an explicit functional gap |
| Row is at war | Existing war handoff; do not create a new peaceful gift candidate for that row |
| Leader/member vectors empty but county vector nonempty | Gift has no recipient; threat is still real and needs county-governance inputs |
| `months_until_max_discontent=0` | Preserve the actual value; it can mean full discontent or nonpositive growth, so no immediate ultimatum inference |
| `power_threshold=0`, growth=0/negative, signed opinion=0, gift modifier present-zero | Preserve observed zeros; never replace them with default80 or missing values |
| Targeting vector no longer contains source faction | Current targeting membership changed; only the existing independent faction-storage receipt can establish known absence |

No gifted-opinion delta predicts member departure. `gift_interaction` has no
direct faction leave/remove effect. A material gift receipt proves mitigation
applied; a later member/power/discontent query establishes the observed faction
state separately. Neither command ACK nor this read-only priority earns M4 or
whole OODA credit.

## Retained readiness and next native inputs

The adopted .4 faction package already records native twelve-whole and actual
registered/Service synthetic fixture qualification at
`docs/ck3-native-ai/ck3-1.20.0.4-faction-adopted-native.md:3`:
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/faction-consumer-only-fix11/registered-root-consumer-only-logs/RESULT.json`.
Reuse it without replay. The new formal priority is qualified by only the new
compound below; this does not rerun that twelve-scene producer or old consumer.

## Actual new formal qualification

`faction_threat_response_inputs_v1.py` reuses a same-frame history alert when
present, otherwise calls the existing read-only step once for a selected gift.
It binds the chosen full FactionID/recipient to the current player/frame and
copies the complete native row, including dynamic threshold, signed growth,
months and member identity. Only that row's stock-danger boolean and absence of
war control priority. The source hook is in
`m5_peacetime_proposal_sources_v1.py`; `faction_gift_proposal` retains the row in
evidence and the existing observed selector consumes it. Missing observations
leave the independent legal opportunities intact. Gift routing still recaptures
the existing quote and uses its ordinary submit/pending/receipt path.

One new method,
`FactionStockResponseFormalFirst12004.test_existing_native_stock_threat_changes_real_formal_faction_response`,
passed four legs in **2.2968583 s** external elapsed / **2.028 s** unittest elapsed
(the log is authoritative for the internal duration):

| Leg | Data qualification | Actual real-production selection |
|---|---|---|
| Original positive gift | Exact original `.4` alert and gift-preview whole bodies, no replacement native field; synthetic paused/root/checkpoint and no-building fixture | Existing typed gift submit selected, stock row retained; no submit sent |
| Dangerous gift versus income | Original native alert whole unchanged; gift treasury changed to 40,000,000 as explicitly controlled input and a synthetic positive-income building quote | Legal funded dangerous gift precedes income building |
| Watch gift versus income | Explicitly controlled consistent watch row, including growth/months zero; controlled treasury/building | Existing positive-income building preference retained |
| Unavailable alert versus income | Original unavailable alert whole unchanged; controlled treasury/building | Existing income building proceeds without a new threat gate |

The real `NativeHeadlessGameplayDriver` public observer and private gift query,
real peacetime source, proposal collector, dispatcher and
`GameplayBridgeService.plan_turn` execute. Only the ordinary baseline selection
and building quote are synthetic callbacks. No planned typed submit is sent.
Native original bodies are copied unchanged into the receipt directory; changed
funding/watch packets are separately labelled controlled inputs. Native fixture
values are not actual game facts or a production construction quote.

Canonical receipt:
`Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261007/faction-response/formal-first-attempt04/compound/FIRST-COMPOUND-RECEIPT.json`;
launch/logs: `formal-first-attempt04/LAUNCH-RESULT.json`, `stdout.log`, `stderr.log`.
The three earlier harness RED attempts remain intact: attempt01 had the wrong
fixture round-ID format; attempt02 omitted the ordinary life-advance capability;
attempt03 had a synthetic snapshot ID outside the existing `native:<revision>`
format. The fixes only correct those fixture inputs and retain failed-plan
diagnostics. Production predicates and original native bodies were unchanged.

Native producer runs, old tests, game/process/SDK operations and game-day advances
are all **0**. G2 remains **5/8**, NW **2/4**, M4 false, natural succession 0.
This is a qualified formal response selector; applied mitigation, faction member
departure, threat resolution and the common two-year M4 outcome remain live work
after the user reauthorizes CK3.

The next useful follow-on, if the current natural frame shows the bounded
selector picking a watch row while an actionable dangerous character faction
exists, is candidate-target selection / multiple concrete native previews in
the same existing gift capability. That input gap is acknowledged without
expanding the present one-selected-candidate delivery.

County-only response remains separate: the observed .3 Robert populist row
33554465/count2111 at raw53286000 had no character members, opinion-22,
native join score31, CanAdd=true and removal_queue=false. See
`docs/ck3-native-ai/faction-county-culture-input-12003.md:3`. Current .4 query
already publishes final opinion/join-score/CanAdd/queue/leave-threshold and
county/target culture relations; culture mismatch alone does not establish the
entire faith/rite/holder/top-liege/capital/holding predicate, nor future county
departure. Those actions require their own native source and independent
outcome. Exact ultimatum date is still unavailable by design; stock danger
alone supplies enough current value for this minimum selected-gift response.

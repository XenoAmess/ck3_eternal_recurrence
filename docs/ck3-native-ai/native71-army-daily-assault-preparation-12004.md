# Native71 actual4 daily assault preparation inputs

This package closes the actual4 pre-date producer/caller source boundary and binds already copied readonly inputs to that boundary. Exact CK3 1.20.0.4 / Steam25734779 EXE SHA-256 is `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`. Z source remains read-only; the candidate is external. No EXE/PE read, broad executable scan, native mutator, Game, SDK, old FIRST or already qualified casualty/supply/scalar test is performed.

The .3 [prepared-stage topic](army-monthly-manager-prepared-stage-inputs-12003.md) supplies the old direct producer locator `2A99B40`. The actual4 mapping comes from retained complete instruction records, including actual direct call operands and preserved member operands, rather than a global address shift.

## Actual source tree and timing

| Source boundary | Actual4 instructions / operands | Input meaning |
| --- | --- | --- |
| Pre-date callback receiver | `2A99DA0..2A9A33E`; incoming secondary receiver retained in R13; `lea rcx,[r13-8]` at `2A99E6D` | The producer receives the primary manager, not its secondary interface |
| Prefix before roster capture | `2A99E71 -> 2A9A340(primary,tomorrow CDate)`; the complete CDate is at caller stack `rbp+140..147` | Current GameState date and this tomorrow CDate are distinct. Prefix source effects belong to continuation44 |
| Original Army roster capture | `2A99E76` reads secondary+48; `2A99E7A` signed count secondary+54; end is captured once | Primary+50/+5C raw DWORD FullID occurrences, native order and repeats; this is captured after the prefix |
| Per-Army prefix and skip | Generation/fallback selects RSI. The `2A92300` true branch queues selected Army+10 and jumps directly to `2A9A08E` | An entire current roster evaluation cannot stand in for the actual subset reaching preparation |
| Preparation call | `2A9A07A mov rdx,rsi`; `2A9A07D lea rcx,[r13-8]`; `2A9A081 -> 2A99B20` | One actual roster occurrence and the same selected CArmy pointer reach one producer call |
| After each preparation call | `2A9A089 -> 24DF3A0(Army)`, then `2A9A08E` advances original DWORD iterator | A capture from another occurrence cannot be relabeled the same entry input |
| After original roster | `2A9A09B` begins the stored-D%30 selected bucket work | Daily assault preparation has ended, but persistent preparation has not started yet |
| Persistent preparation gate | `2A9A2C1` tests GameState+C0 bit2; `2A9A31C -> 262C680` on ordered persistent roster | Assault admission is before this gate and is daily. The intervening bucket work prevents an assumed identical stage frame |
| Later consumer | Actual4 `2A97EB0`, already held; owner37 consumes after optional regular refill | Prepared group inputs do not prove its later current strength/scalar or physical writes |

Actual source-use attachment is also retained in post-date callback mapping: `2A9A984` loads GameState through RIP slot `5C68C50`; `2A9A98B` reads +A0 GameData; `2A9A992` adds primary manager +2A540; `2A9A99C` calls manager method `2A97880`. This is an actual4 member-use witness. It does not claim to close an unrelated outer callback/vtable attachment.

## Producer admission and ordered append inputs

Complete actual4 producer `2A99B20..2A99D9D` is 637 bytes, held as a194-byte prefix and443-byte continuation. Its original direct control tree is:

1. `2A99B30 -> 24E8540(Army)` must return true. The existing current readonly admission observer retains the source-closed gate and its conditional unavailable branches.
2. Resolve Army+124 Unit by full-generation or native fallback. Unit+20 Province uses its native fallback when null. Resolve Province+788 Siege by full-generation or fallback. Siege+44C must be nonzero.
3. Search primary+68/+74 removal queue for **selected Army+10**, not merely the original requested roster token. A match skips this call's append work.
4. FNV1a hashes the selected Siege+8 full DWORD, low byte first. `2A99C7A -> 2AA2010` receives RCX=primary+170, RDX=out(entry pointer, inserted byte), R8D=hash, R9=&raw selected SiegeFullID. Owner36 closes physical placement/growth; an ordered logical append input does not substitute for that native order.
5. `2A99C94 -> B02D10` appends selected Army+10 to returned group+10/+1C DWORD list, without deduplication.
6. Probe pending table primary+130 (entries+138, mask+144, tail+148), stride28. Lookup is for selected Army+10. Selected controlFF skips the entire ArRg append loop, while keeping the prior Army append.
7. Otherwise traverse original Army+38/+44 ArRg raw ID occurrences. Pending record+10/+1C membership excludes matching raw IDs. Every other occurrence appends through `2A99D79 -> B02D10` to group+28/+34; order and repeated occurrences remain intact.

The existing `CurrentDailyAssaultRosterAdmissionBindings12003` DTO/reader is version-independent after binding; its actual4 addresses are supplied by `PopulateClosedCurrentInputs` in `ck3_12004_army.cpp`. In particular the actual4 classifier is `2C099D0`. This package never calls the old `.3` image binder. Reuse its original roster, removal queue, resolutions, gate, Siege44C, pending probes/suppression references and per-ArRg occurrence outputs. The existing `CurrentDailyAssaultTable` collector remains the sole supplier of current physical controls and group-record lists.

## Minimal stage binding and readiness

The independent leaf consumes copied existing observer values and a separately supplied frame boundary. It makes no memory write and installs no native hook. It retains the full original roster, removal queue and full current-table value when supplied; a missing table remains unavailable. It emits append operations in original roster occurrence order and keeps raw Siege/Army/ArRg full IDs and repeated entries. It never assembles or sorts a fake group dictionary, calls a placement/append helper, or treats input group rows as prepared output.

Default boundary is `current_query`: a standalone paused observer can supply conditional append inputs, with no natural-callback claim. For `pre_date_assault_call`, Root must supply the actual original-roster capture, native occurrence index, source PC `2A9A081`, exact selected RSI identity and primary manager identity from that same source entry, plus the current frame identity/date/rawD/rawC0. The copied observer occurrence must match the supplied raw roster occurrence and selected identity. This binds provided input to the known source interface; synthetic fixture labels and source-PC equality are not live observations.

`boundary_binding_ready`, `ordered_append_inputs_ready` and `current_group_records_ready` are independent. A valid controlFF selection has an Army append and an exact empty ArRg append list; it is not an empty group table. Current table absence, physical placement, future prefix changes and later regular refill are separate dependencies. All actual callback execution, full future table placement, full daily assault and full monthly execution flags remain false in this leaf.

Root owns shared collector/binder/serializer/CMake/provider/driver wiring, any actual capture invocation and its live evidence. Continuation36 owns placement and current-table evolution,37 loss/release,38 eligible assault strength,33 persistent preparation,44 earlier prefix effects,41 late daily suffix. Do not reinstall producer `2A99B20` as a readonly callback. Do not replay an old qualification merely to attach this leaf.

## Frozen retained evidence

Under `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/army-world-family/native-main/`:

| Evidence | Actual4 coverage | Retained metadata SHA-256 |
| --- | --- | --- |
| `map01/pre_date_roster_source-DETAIL.json` |1438B, actual call081/prefix/roster and month-first boundary | `b5b83af9f477c57ee15d677487def10633f5df932f6524250c1328b174a56b7e` |
| `map01/daily_assault_admission_source-DETAIL.json` |194B prefix | `521768ed64a4c931072b2d51527eb652b2614409294dd5d76e7646fc60c39967` |
| `map02/daily_assault_admission_remaining_fragments-DETAIL.json` |443B continuation | `98020bf996516268271e120ac58dfa4840da95fd60755f55168886c898d1b7e8` |
| `map03/table_placement_source-DETAIL.json` |actual2AA2010 complete653B | owner36 reuse |
| `map07/daily_assault_table_consumer_source-DETAIL.json` |actual2A97EB0 complete801B | owner37 reuse |

No newly captured native source byte is added. This package's `HELD-SOURCE-SUMMARY.json` and three short actual4 instruction views are derived from retained metadata. The native tree and evidence freeze precede the leaf implementation. One new focused fixture covers stage binding, order/repetition, source-PC/selected-identity matching and missing group input; it does not requalify inherited gate, scalar, casualty or supply arithmetic. Root's exact fresh compile/run argv is delivered separately; until executed its result is NOTRUN. An offline GREEN still grants no natural callback or live readiness.

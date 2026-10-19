# M1 full-realm future Native ABI closure

Source-only audit of HEAD `096f1554798d473d034aa8e443ac5deace225478`.
machine_id: `xenoamess-full-tower-eb9d2c1186`; observed_at_utc: `2026-10-19T10:25:15.490784+00:00`.
Identity source: fresh `tools/ck3_live_run_id.py machine`.
Paths below are relative to `ck3_autonomous_player/native_bridge/`.
Root reports CI node 527 PASS. This audit adds no execution or loaded-Native qualification.

**Future adoption requires a fresh complete DLL target build, including its static runtime dependency. Never link the new reader/projector/serializer with the old 355-object package.** That package's exact affected dependency/flag closure was not established here. Its object count is not a future build contract. Current Native29 and old M1 artifacts remain frozen.

## Definition / sizeof boundary

All changed definitions are in `include/xar_bridge/player_faction_alerts_v1.hpp`:

| Type | Change | Consequence |
| --- | --- | --- |
| game::PlayerSubrealmGeographicCountiesV1, L192 | New bool/u64/i32/i32/vector<i32>/optional<string> | Nontrivial owned STL value |
| game::PlayerFactionAlertsV1, L203/L218 | Appended optional<new component> | Layout/size, generated copy/move/destruction/default equality change |
| ck3_11906::PlayerFactionAlertsSourceSampleV1, L296/L304 | Appended optional<vector<i32>> | Layout/size, special members and double-sample equality change |

Numeric `sizeof`/`alignof` for old/new types are **not observed**. Prior compile/fixture outputs did not emit sizes. Do not guess from x64 or assumed STL 24/32-byte layouts. Appending fields does not prove binary prefix compatibility; disengaged optional still occupies storage. No M1 field was added to `game::Snapshot`; “NativeFactions/SourceSnapshot” are not literal names of these changed types.

In the future build, emit `sizeof`/`alignof` for these three types and the three mailbox contexts below using the exact compiler/STL, CRT, configuration, packing and `_ITERATOR_DEBUG_LEVEL`. Pin those inputs. Do not create a memcpy/fixed-size/offset bridge between versions.

## Producer / consumer allocations

- `src/ck3_12002_faction_alerts.cpp::ReadSample/ReadCountyExposures` produces expanded SourceSample; two samples use its expanded default `operator==`. `src/player_faction_alerts_v1.cpp::MaterializeFull/ProjectPlayerFactionAlertsSourceSampleV1` constructs/assigns expanded public values.
- `src/player_faction_alerts_v1_serializer.cpp` consumes the expanded value. `ck3_12004_faction_alerts.cpp` delegates to the .2 producer/shared serializer. Rebuild both sides.
- `PlayerFactionAlertsMailboxContextV1` (generic mailbox header L30/L44), `PlayerFactionAlertsMailboxContext12002` (.2 mailbox header L8/L11), and `PlayerFactionAlertsMailboxContext12004` (.4 mailbox header L7/L10) embed `result` **by value**. Generic execution-stamp fields and .2/.4 completion fields follow it. Allocators, accessors and destructors must agree.
- .2/.4 `faction_gift_router.cpp` private `Query` embeds `alerts`, followed by observation/request/ack/receipt and other members (.4 L22-L41). A new reader with an old caller can overrun the old allocation or corrupt those following fields.
- Signatures still name the same V1 types. Symbol mangling does not encode object size/layout. Link success and unchanged callback calling convention cannot detect mismatch; mixing inline special members/COMDAT definitions violates the common type definition too.
- JSON is a serialization boundary. Python accepting old wire without the optional field does **not** make old/new in-process C++ objects ABI compatible. Python requires no object-file reuse.

## Literal include closure

Reverse literal `#include` closure in `include/` and `src/`: **40 non-test/non-fixture source TUs; 62 total src TUs**. Conditional includes are conservatively included. This is a source closure, not Native29's actual object manifest; future flags/generated dependencies must be resolved for the frozen target. Rebuild every selected target occurrence, including tests:

```text
bridge.cpp
camera_presentation_v1.cpp
ck3_11906_adapter.cpp
ck3_12002_event_window_context.cpp
ck3_12002_faction_alerts.cpp
ck3_12002_faction_gift.cpp
ck3_12002_faction_gift_router.cpp
ck3_12002_faction_mailbox.cpp
ck3_12002_nonwar_router.cpp
ck3_12002_prisoner.cpp
ck3_12002_prisoner_collection.cpp
ck3_12002_prisoner_mailbox.cpp
ck3_12002_prisoner_wire.cpp
ck3_12003_prisoner_release_preview.cpp
ck3_12003_prisoner_release_preview_serializer.cpp
ck3_12004_event_window_context.cpp
ck3_12004_faction_alerts.cpp
ck3_12004_faction_gift.cpp
ck3_12004_faction_gift_router.cpp
ck3_12004_faction_mailbox.cpp
ck3_12004_interaction_context.cpp
ck3_12004_pending_context.cpp
ck3_12004_prisoner_collection.cpp
ck3_12004_prisoner_collection_result.cpp
ck3_12004_prisoner_mailbox.cpp
ck3_12004_prisoner_negotiated_preview.cpp
ck3_12004_prisoner_ransom.cpp
ck3_12004_prisoner_ransom_action.cpp
ck3_12004_prisoner_release_action.cpp
ck3_12004_prisoner_release_preview.cpp
ck3_12004_prisoner_wire.cpp
ck3_12004_sway_stop_first.cpp
county_faction_final_12003.cpp
game_adapter.cpp
ordinary_character_interaction_v1.cpp
pending_alliance_counterfactual_score_12004.cpp
player_faction_alerts_v1.cpp
player_faction_alerts_v1_mailbox.cpp
player_faction_alerts_v1_serializer.cpp
prisoner_selected_quote_query_capture_12004.cpp
```

Camera consumes the shared subrealm reader; interaction/prisoner routes inherit faction headers transitively. Thus a three-object replacement omits dependencies even outside explicitly named faction TUs.

## Minimum safe future build

1. Freeze one reviewed tree containing the intended Native29 source baseline plus approved M1 changes, exact CMake flags and linked dependencies. No unrelated master candidates; no imported old .obj/.lib/PCH/incremental-link artifacts.
2. Configure a separately admitted **new** directory and build existing `xar_ck3_bridge` from source. CMakeLists L1267 creates `xar_ck3_12002_runtime STATIC`; L1570 creates the SHARED bridge; L1910 links runtime/protocol. `cmake/faction_adopted_12004.cmake` adds the .4 reader to runtime, and mailbox/gift router to bridge under existing flags. Both sides must come from this same freeze/toolchain.
3. Retain source/dependency/command pins plus layout diagnostics. Run existing M1 `xar_ck3_realm_camera_subrealm_v1` CTest against that freeze. When .4 query/gift flags are enabled, existing `xar_ck3_12004_faction_adopted_whole_test` exercises actual mailbox/router with synthetic transport; inspect the new optional wire there. These are future scoped checks, not an extra business matrix now.
4. After software/EXE requirements pass, schedule separate normal maintenance adoption and actual DLL/source/frame/owner readback. CI/fixture PASS alone establishes neither loaded identity nor complete realm observation.

Selective rebuilding can be safe only with verified old provenance, dependencies and flags proving **every** affected occurrence was rebuilt. This audit does not certify that closure for the old 355 objects. With current evidence, the minimum defensible plan is the **full clean target/dependency build**.

M3 owner confirms its future getter is separate header/cpp + independent Observation DTO, without changing Snapshot or these types; default gate off. It is not incorporated here. Later combined adoption still needs one production closure.

## Source pins / closure

These audited working files matched HEAD bytes: the changed header; generic/.2/.4 faction mailbox headers; .4 faction gift router; root CMakeLists.

- Changed header: 14,279 B, SHA256 `9fa5509813ea5276490ec4ec2fe4bc76db9eb8aa38e0fab9d23a4f03c5ddb5d4`.
- CMakeLists: 453,329 B, SHA256 `b2e0d46fd5554c6887f94c9a55b3cb6d35d3d58b7a7852a13f5c27e0ed428323`.

Repo-only new MD <=8192 B. This audit performed no build, GUI/business matrix, Game/Driver/SAVE read or external write.
producer_closed: true; future_write_bytes: 0; allocated_bytes: null; physical_release_credit_bytes: 0.

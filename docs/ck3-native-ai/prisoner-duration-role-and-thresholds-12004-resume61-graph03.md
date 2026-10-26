# Research plan: prisoner-duration-threshold-source12004-resume61

GENERATED from the supplied research plan; no native semantics are inferred.

Question: Which final prisoner owns the duration threshold, and what do stock prison callbacks/maintenance prove without a raw getter?

```mermaid
flowchart TD
    n0["Stock candidate source and role redirect"]
    n1["Final prisoner scope; 12 sender duration uses"]
    n2["Native time_in_prison trigger/getter UNKNOWN"]
    n3["Final CanSend and recipient answer separate"]
    n4["Existing collection/retained custody identity"]
    n5["Duration observation NOT PROVIDED"]
    n6["CourtWindow.GetPrisoners / CharacterListItem"]
    n7["GetText imprisoned_time presentation key"]
    n8["on_imprison / on_release_from_prison callbacks"]
    n9["Historical imprisonment / conditional release memories"]
    n10["prison_maintenance_pulse engine entry UNKNOWN"]
    n11["45/135/225/315 delays then current prisoner enumeration"]
    n12["Type-specific +1day pool; current imprisoner existence guard"]
    n0 -->|"roles [static-confirmed] Duration belongs to captive regardless of initiator/payer/jailer"| n1
    n1 -. "dispatch [unknown] Exact compiled trigger dispatcher and producer field" .-> n2
    n1 -->|"score_not_gate [static-confirmed] ai_will_do score is separate from legality and recipient answer"| n3
    n4 -->|"reader_gap [static-confirmed] Existing readers do not publish prison start/duration"| n5
    n2 -. "native_duration [unknown] Future same-frame duration or exact compiled threshold reads" .-> n5
    n6 -->|"gui_named_key [static-confirmed] Both prison list layouts use the same named text key"| n7
    n7 -. "formatted_raw_gap [unknown] Registered key/context/raw-duration branch not yet located" .-> n2
    n8 -->|"callback_memory [static-confirmed] Prisoner root; imprisoner scope; old child memory retained; release death/escape exclusions"| n9
    n9 -. "historical_memory_gap [unknown] No source-proved unique current-custody start from historical memory" .-> n5
    n10 -. "maintenance_entry_gap [unknown] Code entry and runtime cadence not located" .-> n11
    n10 -->|"maintenance_delays [static-confirmed] Authored any_prisoner guard and45/135/225/315 day delays"| n11
    n11 -->|"maintenance_recheck [static-confirmed] Current house_arrest/dungeon enumeration; queue+1day; recheck current imprisoner existence"| n12
    n12 -. "pool_duration_gap [unknown] Queued guard checks existence, not original jailer or raw time" .-> n5
```

| Edge | Declared status | Evidence IDs | Open question |
|---|---|---|---|
| roles | static-confirmed | stock |  |
| dispatch | unknown |  | Locate held current-build registration/getter and actual engine caller |
| score_not_gate | static-confirmed | stock |  |
| reader_gap | static-confirmed | collection, retained |  |
| native_duration | unknown |  | Units/calendar boundaries, jailer transfer and reimprisonment reset/cache lifecycle unknown |
| gui_named_key | static-confirmed | court_gui |  |
| formatted_raw_gap | unknown |  | No held metadata locator from NativeProtocolIdentity; no formatted-text parsing or neighboring timestamp inference. |
| callback_memory | static-confirmed | prison_hooks, prison_release |  |
| historical_memory_gap | unknown |  | Native origin/current spell association and reset remain unlocated |
| maintenance_entry_gap | unknown |  | Do not infer runtime cadence from filename or authored pool count |
| maintenance_delays | static-confirmed | prison_maintenance |  |
| maintenance_recheck | static-confirmed | prison_hooks |  |
| pool_duration_gap | unknown |  | Event arrival/maintenance count do not prove transfer/reimprisonment reset |

| Observation design | Value |
|---|---|
| mode | offline-only |
| actor_kind | ai |
| owner_scope | Stock sender scoring for finalized full prisoner identity; player legality/answer/poststate separate |
| identity_kind | generation-id |
| identity_lifetime | Full prisoner ID; custody duration lifetime/reset unknown |
| producer_trigger | unknown |
| producer | Native raw duration/getter unknown. CharacterListItem.GetText imprisoned_time is presentation only. |
| caller | Four stock sender trees after role redirect; prison lifecycle/delayed maintenance separate; engine entry/raw dispatcher unknown |
| consumer | Sender modifiers for ransom, pay_ransom, ransom_me and release_from_prison |
| cache_lifetime | Custody relation observed; time origin/reset/cache lifetime unknown |
| expected_signal | Held current-build registered time_in_prison name entry and exact native caller/getter; no live sample requested |
| zero_sample_meaning | No catalog match is a missing locator, not zero duration/no prisoner/no modifier |
| stop_condition | Exact interactions, two bridge files, court GUI, three prison callback/maintenance scripts and held metadata only. No EXE scan/Game/provider/formatted text parsing. |
| runtime_window_ref | None |

| Evidence ID | Declared layer | File | SHA-256 | Supports |
|---|---|---|---|---|
| stock | source-contract | Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/character_interactions/00_prison_interactions.txt | 1bb43b3c2061212af8d41b11314ff4e569af2a3506319f820d05877a7762abc5 | Twelve duration sites/four sender trees, final role scopes, independent modifiers and duration-free child branch |
| collection | source-contract | Z:/ck3_mod_rewrite/ck3_autonomous_player/native_bridge/src/ck3_12004_prisoner_collection.cpp | 90545bf882d658a061ba25b881d4d79eaf9c590582b27cd90f715915674ded4a | Existing full captive/jailer collection without duration output |
| retained | source-contract | Z:/ck3_mod_rewrite/ck3_autonomous_player/native_bridge/src/ck3_12004_prisoner_retained_target_state.cpp | c235cc583cfc904f1d026638d52de846ba037d5182165252ec3b65382bfeb5d4 | Retained alive/free/player-held/other-held state has jailer identity without prison start date |
| installation | exact-build | D:/codex-ck3-background/ck3-java-g2-resume-r4-20261025/resume61/formal_release/INSTALLATION-WITNESS02.json | 49f08808eb15dd2eb2d24d05f400c7dd68cf1d4d7de14741e2efbbd7417c339c | Current metadata witness reuses historical full EXE SHA by exact file identity; no new hash/loaded Game proof |
| court_gui | source-contract | Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/gui/window_court.gui | e730078c5f671e7e564c6e7799215d9fabda0546d38ba615f26302b122ad5135 | CourtWindow.GetPrisoners row source, both &gt;4 and &lt;=4 layouts bind CharacterListItem.GetText imprisoned_time at405/574. Formatted presentation, not raw duration/getter/unit. |
| prison_hooks | source-contract | Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/on_action/prison_on_actions.txt | e46f66ed9ab72f7c210842a2fac7cf432f60a8fa11e1ff0ae26f41d4eed5dbf5 | Code-hook declared roles; childhood memory retention; death/escape release-memory exclusions; delayed current-custody rechecks |
| prison_release | source-contract | Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/events/prison_events/prison_events.txt | 4a9311641df34eedf885c3c0af093e1d2c14d1a01c7e64d7389dd9dded23bac6 | prison.0001 living-imprisoner trigger; escape opinion differs from release consume-imprisonment-reasons |
| prison_maintenance | source-contract | Z:/SteamLibrary/steamapps/common/Crusader Kings III/game/common/on_action/yearly_on_actions.txt | 14c97f3845138d74a2c2552c5dd3c95de1da035014a5cdf31c92540aae3390fe | Authored45/135/225/315 delays; code-entry cadence not located |

Check result (file integrity and declarations only):

```json
{
  "schema": "xar.native-research-plan-check.v1",
  "result": "plan-consistent",
  "proof_layer": "record-structure-and-file-integrity",
  "semantic_correctness_verified": false,
  "live_execution_performed": false,
  "observation_plan_issues": [
    "offline-only plan does not define a live observation window",
    "the real producer trigger must be located before live sampling"
  ],
  "declared_edges_by_status": {
    "counter-policy": 0,
    "inference": 0,
    "live-confirmed": 0,
    "static-confirmed": 7,
    "unknown": 6
  },
  "enumerated_native_edges": 13,
  "declared_cases_by_status": {
    "pending": 3,
    "observed": 0,
    "not-applicable": 0
  },
  "checked_evidence_files": 8,
  "limitations": [
    "Evidence layers and conclusions are author declarations; hashes bind bytes, not their truth.",
    "Counts cover this enumerated graph only, not all CK3 branches.",
    "A consistent observation plan is not authorization to run or manipulate CK3."
  ],
  "plan_sha256": "14225fd79c840db8fb15b655c106a1eb6c81830756c93239d18de85fdf84d073"
}
```

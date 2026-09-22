# Research plan: war-film-relationship-gate-20260923

GENERATED from the supplied research plan; no native semantics are inferred.

Question: Does the native loader bind can_potentially_call_ally to scripted-rules singleton+0xF08-&gt;+0x1960 used by 0x1B35DF0, and what is the exact scope direction?

```mermaid
flowchart TD
    n0["Rule name and token"]
    n1["Native index registration"]
    n2["Loaded rule array"]
    n3["root / scope:ally"]
    n4["Common eligibility result"]
    n5["Unobserved runtime behavior"]
    n0 -->|"rule-name-registration [static-confirmed] 0x1B34610 registers index 29 with token 0x3529 and scope kind 4. The token catalog row at 0x42C7830 is {token, string-pointer}; 0x3B580E2/0x3B580E9 and 0x3B58279..0x3B58294 prove this layout. Its string is can_potentially_call_ally. The following 0x352A belongs to the next row."| n1
    n1 -->|"registration-transfer [static-confirmed] 0x203D340 builds the table, 0x203D34D moves it to setup+0xD0, and 0x203D51D calls 0x332C380. That function copies setup+0xD0 into global 0x576AF88 owner+0xD0 and then owner+0xF0. 0x33ED7E0 copies owner+0xF0 into rules singleton+0x2B30 before reading rule files."| n2
    n2 -->|"loaded-rule-to-array [static-confirmed] 0x33ED7E0 reads common/scripted_rules through 0x33EF390 and 0x33EE960, then 0x33EDB00 resolves each registered token to its name, hashes it and looks up the parsed entry using 0x33EEF90. A valid entry with nonnegative +0x78 copies its trigger data from entry+0x38 into singleton+0xF08 array[index*0xE0]. Thus index 29 reaches offset 0x1960. Missing definitions have a distinct logged/default-construction path; no runtime success is inferred."| n4
    n3 -->|"exact-scope-direction [static-confirmed] 0xC060 registers the literal ally at slot 0x57EB86C. 0x1B35DF0 constructs root from its first character argument, binds the second character full ID (kind 4) using that slot via 0x3358160, and evaluates rules[index 29] via 0x334C510. The authored rule passes WARRIOR=root and JOINER=scope:ally."| n4
    n0 -->|"authored-gate-boundary [static-confirmed] The hash-bound vanilla trigger rejects ordinary vassal-to-root and root-to-liege calls subject to its explicit diarch, same-confederation and vassal_contract_liege_forced_war_override exceptions. Its body contains no CombatID, war-side, accepted-call or joining observation. Comments about defensive wars cannot add an absent war-side test to this predicate."| n4
    n4 -. "runtime-rule-and-outcome [unknown] No live rules object, actual predicate result, override set, contributor sum, call acceptance or joined war was observed. This is a static default-source binding for the pinned executable and files." .-> n5
    n4 -. "nested-trigger-implementation [unknown] The loaded script text is preserved; the native implementations and complete semantics of every nested relationship/contract trigger are outside this bounded loader audit." .-> n5
```

| Edge | Declared status | Evidence IDs | Open question |
|---|---|---|---|
| rule-name-registration | static-confirmed | static-contract |  |
| registration-transfer | static-confirmed | static-contract |  |
| loaded-rule-to-array | static-confirmed | static-contract |  |
| exact-scope-direction | static-confirmed | static-contract |  |
| authored-gate-boundary | static-confirmed | static-contract |  |
| runtime-rule-and-outcome | unknown |  | No live rules object, actual predicate result, override set, contributor sum, call acceptance or joined war was observed. This is a static default-source binding for the pinned executable and files. |
| nested-trigger-implementation | unknown |  | The loaded script text is preserved; the native implementations and complete semantics of every nested relationship/contract trigger are outside this bounded loader audit. |

| Observation design | Value |
|---|---|
| mode | offline-only |
| actor_kind | ai |
| owner_scope | One declaration assessment actor and effective target; not all diplomacy or wars |
| identity_kind | generation-id |
| identity_lifetime | Synchronous collector locals and full CharacterID only; no pointer reuse |
| producer_trigger | not-applicable |
| producer | Unknown native rule registration/loader into the +0x1960 trigger subobject |
| caller | 0x1879850 and 0x18758C0 -&gt; 0x1B35DF0 |
| consumer | Boolean eligibility gate for one actor or target network contribution |
| cache_lifetime | Military+0x308 freshness remains separate; no runtime age observed |
| expected_signal | Exact symbol/string/registration or loader-index proof reaching the same consumed object and scope binding |
| zero_sample_meaning | No live samples are taken; an excluded branch is not proof that the relationship cannot join a war |
| stop_condition | No live access. One bounded pass over literal/registration and singleton-owner loading plus its trigger-array addressing. If no exact binding closes, freeze ruled-out matches and precise remaining edge; do not repeat broad scans. |
| runtime_window_ref | None |

| Evidence ID | Declared layer | File | SHA-256 | Supports |
|---|---|---|---|---|
| static-contract | source-contract | static.json | 63c2b31b6088c7289cc914e977b54fb40ed1d5b741ceeba50497cff6e7a99fcf | Exact registration operands, catalog layout and loading instructions, scope binding, and pinned authored text. Static interpretation only; no live success. |

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
    "static-confirmed": 5,
    "unknown": 2
  },
  "enumerated_native_edges": 7,
  "declared_cases_by_status": {
    "pending": 1,
    "observed": 0,
    "not-applicable": 0
  },
  "checked_evidence_files": 1,
  "limitations": [
    "Evidence layers and conclusions are author declarations; hashes bind bytes, not their truth.",
    "Counts cover this enumerated graph only, not all CK3 branches.",
    "A consistent observation plan is not authorization to run or manipulate CK3."
  ],
  "plan_sha256": "aa1e4f018f591eccdfe0e5f50e4131a5f9fb997e022d11c5a5309acc55459120"
}
```

# Research plan: war-film-relationship-network-20260923

GENERATED from the supplied research plan; no native semantics are inferred.

Question: Which relationship sources and filters enter declaration network power at 0x1879850?

```mermaid
flowchart TD
    n0["Actor/effective target"]
    n1["Spouses, betrothed, active alliance relations, subject contracts, suzerain and confederation"]
    n2["Common predicate then actor-only extra filters"]
    n3["Ordered network +308 sum"]
    n4["Unobserved runtime behavior"]
    n0 -->|"family-and-alliance-sources [static-confirmed] 0x1879850 first visits the complete FamilyData spouse vector (+0x20), then its betrothed ID (+0x10), then relation-map rows (Character+0x1A8-&gt;+0x20, stride0x10). The latter excludes spouse/betrothed duplicates, requires relation+0x94 != 0 and +0x1A9 == 0, matching the established native IsAlliedTo predicate 0x2661E00."| n1
    n0 -->|"contract-sources [static-confirmed] The fourth source is military+0x248 CSubjectContract IDs: subject+0x20 qualifies only with an explicitly present tributary_war_participation_obligation whose level is not its native default. The fifth source is the root own contract+0x28 suzerain when explicitly present suzerain_war_participation_guarantee is non-default. These names are independently bound by 0x2D59578/0x2D595B1 to database+0xF18/+0xF28."| n1
    n0 -->|"confederation-source [static-confirmed] The final source resolves Character+0x1C0-&gt;+0x80 as ConfederationID and enumerates that Confederation+0x18 full CharacterID vector (count+0x24), skipping the root itself and IDs already seen. GetConfederation registration/callback/getter independently names that exact ID field."| n1
    n1 -->|"actor-at-war-filter [static-confirmed] Actor configuration enables filter_a: candidates whose military+0x318 vector count+0x0C is nonzero are excluded. IsAtWar registration 0x50CF7D -&gt; callback 0x2622F10 -&gt; getter 0x2610510 independently names this condition. Target configuration disables this extra filter."| n2
    n1 -->|"actor-human-filter [static-confirmed] Actor filter_b excludes candidates recognized by 0x28BCEB0 in the human-player CharacterID set; target configuration disables this extra filter. This affects estimated actor network contribution, not the legality of sending an actual call to war."| n2
    n1 -->|"actor-confederation-suzerain-filter [static-confirmed] Actor filter_c first excludes candidates with the same valid non--1 ConfederationID. It then excludes the root native GetSuzerain result when the root own subject contract has an explicitly non-default suzerain_war_participation_guarantee. The older same-realm/government labels are not supported names for these instructions. Target configuration disables both extra exclusions."| n2
    n2 -->|"accumulation-and-seen-order [static-confirmed] Every admitted contributor adds military+0x308 without a percentage discount in this collector. The first sources populate a local seen vector even after common-filter rejection; later contract/confederation sources check it. This is ordered duplicate suppression across sources, not a claim that the first spouse vector is generically deduplicated by this function."| n3
    n1 -->|"common-predicate-boundary [static-confirmed] The shared filter calls 0x1B35DF0(root,candidate) and requires true before accumulation. That function constructs root scope, binds the candidate CharacterID into a named scope slot, and evaluates the singleton+0xF08 object subobject+0x1960. Its exact authored rule-name binding remains unresolved in this package."| n2
    n3 -. "common-rule-name [unknown] The current vanilla can_potentially_call_ally rule and its WARRIOR/JOINER trigger are a strong source candidate, but a string/token match did not close its loader binding to the +0x1960 object. Do not present its full script exclusions as instruction-confirmed here." .-> n4
    n3 -. "relationship-lifecycle [unknown] Creation/removal and suspended-state lifecycle of relation+0x94/+0x1A9, malformed source duplicates, and every wider relationship producer remain outside this bounded reader audit." .-> n4
    n3 -. "live-outcome [unknown] No live contributor list, cache freshness, refreshed assessment ratio, call acceptance, actual declaration, or same-war joining was observed. These static exclusions do not mean a candidate can never join an actual war." .-> n4
```

| Edge | Declared status | Evidence IDs | Open question |
|---|---|---|---|
| family-and-alliance-sources | static-confirmed | static-contract |  |
| contract-sources | static-confirmed | static-contract |  |
| confederation-source | static-confirmed | static-contract |  |
| actor-at-war-filter | static-confirmed | static-contract |  |
| actor-human-filter | static-confirmed | static-contract |  |
| actor-confederation-suzerain-filter | static-confirmed | static-contract |  |
| accumulation-and-seen-order | static-confirmed | static-contract |  |
| common-predicate-boundary | static-confirmed | static-contract |  |
| common-rule-name | unknown |  | The current vanilla can_potentially_call_ally rule and its WARRIOR/JOINER trigger are a strong source candidate, but a string/token match did not close its loader binding to the +0x1960 object. Do not present its full script exclusions as instruction-confirmed here. |
| relationship-lifecycle | unknown |  | Creation/removal and suspended-state lifecycle of relation+0x94/+0x1A9, malformed source duplicates, and every wider relationship producer remain outside this bounded reader audit. |
| live-outcome | unknown |  | No live contributor list, cache freshness, refreshed assessment ratio, call acceptance, actual declaration, or same-war joining was observed. These static exclusions do not mean a candidate can never join an actual war. |

| Observation design | Value |
|---|---|
| mode | offline-only |
| actor_kind | ai |
| owner_scope | One declaration assessment actor and effective target; not all diplomacy or wars |
| identity_kind | generation-id |
| identity_lifetime | Synchronous collector locals and full CharacterID only; no pointer reuse |
| producer_trigger | not-applicable |
| producer | Native collector 0x1879850 |
| caller | Declaration assessment 0x1878A00 |
| consumer | Actor/target strategic power before final ratio |
| cache_lifetime | Military+0x308 freshness remains separate; no runtime age observed |
| expected_signal | Instruction-backed source container naming and exact filtering differences |
| zero_sample_meaning | No live samples are taken; an excluded branch is not proof that the relationship cannot join a war |
| stop_condition | Freeze bounded native membership and filtering contract, preserve unsupported names unknown; no live execution |
| runtime_window_ref | None |

| Evidence ID | Declared layer | File | SHA-256 | Supports |
|---|---|---|---|---|
| static-contract | source-contract | static.json | 78b0cddf5dedd081972379470b9b992088761ec1f5d6a6949eea724380bc5de7 | Pinned instructions, independent named getter/term bindings and prior contract provenance; analyst-interpreted static semantics only. |

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
    "static-confirmed": 8,
    "unknown": 3
  },
  "enumerated_native_edges": 11,
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
  "plan_sha256": "e8c864b011aee27b401ce4d2b620a94d4786017c5d8c456a0046d30ab69a5eee"
}
```

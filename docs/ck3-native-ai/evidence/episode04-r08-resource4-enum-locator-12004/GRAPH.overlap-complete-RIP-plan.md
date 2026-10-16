# Research plan: e04-GetCurrency-only-overlap-complete-RIP-locator

GENERATED from the supplied research plan; no native semantics are inferred.

Question: Which independent raw 8B/8D opcode starts in .text target exactly GetCurrency44DB128?

```mermaid
flowchart TD
    n0["GetCurrency44DB128"]
    n1["Raw RIP LEA/MOV candidate"]
    n2["Instruction/function boundary UNKNOWN"]
    n1 -. "xref [unknown] Exact target from every independent opcode start, boundary unknown" .-> n0
    n1 -. "boundary [unknown] No source boundary proof yet" .-> n2
```

| Edge | Declared status | Evidence IDs | Open question |
|---|---|---|---|
| xref | unknown | literal, data, coverage-correction | Any matching target-only LEA/MOV pattern? |
| boundary | unknown | literal | Use genuine site to locate containing.pdata and decode from function entry later |

| Observation design | Value |
|---|---|
| mode | offline-only |
| actor_kind | engine |
| owner_scope | Proposed corrected locator only; requires Root approval of additional71141888B before execution. This preparation does not access EXE. |
| identity_kind | definition-key |
| identity_lifetime | Exact image and same native file identity; preferred offsets not runtime frame |
| producer_trigger | not-applicable |
| producer | Every8B/8D opcode independently tested for RIPrelative mod00/rm101 and exact target; prior optionalREX byte is context. No function/instruction boundary proof. |
| caller | Unknown named registration wrapper; previous .rdata GetCurrencyQWORD refs0 |
| consumer | Potential named GetCurrency registration/handler route, not actual selector mapping |
| cache_lifetime | Static locator bytes only |
| expected_signal | At most16rawsites/96B each; duplicate prefixed/unprefixed starts not created; no overlapping opcode skipped. |
| zero_sample_meaning | Zero can cover the specified independent8B/8D raw pattern family only, not other instructions/tables/absence of registration. |
| stop_condition | Proposed single71141888B .text read; cumulative176532480B sections,608B metadata,8reads; output&lt;=131072B; no callee or new name; not executed by this preparation. |
| runtime_window_ref | None |

| Evidence ID | Declared layer | File | SHA-256 | Supports |
|---|---|---|---|---|
| literal | locator | LITERALS.actual.json | af76ea5a7e69ea52048dc6ed80e6c78de7244e19ed02346a8f095cf378e47121 | Unique exact GetCurrency literal44DB128 |
| data | locator | QWORD-REFS.actual.json | b2903c63f08fcc6d5a3e59e7beae4214c54f54bc3ec273974a058fed3716da79 | No same.rdata QWORD data reference for GetCurrency; need explicit named RIP locator |
| coverage-correction | locator | NAMED-RIP-COVERAGE-CORRECTION.actual.json | 965c0ac7ab1d455828fc8dd7761ed4ae1ec676b8b1d63709bd364690b8d81b2b | Prior matcher cannot prove full negative; synthetic overlapping counterexample without EXE read. |

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
    "static-confirmed": 0,
    "unknown": 2
  },
  "enumerated_native_edges": 2,
  "declared_cases_by_status": {
    "pending": 1,
    "observed": 0,
    "not-applicable": 1
  },
  "checked_evidence_files": 3,
  "limitations": [
    "Evidence layers and conclusions are author declarations; hashes bind bytes, not their truth.",
    "Counts cover this enumerated graph only, not all CK3 branches.",
    "A consistent observation plan is not authorization to run or manipulate CK3."
  ],
  "plan_sha256": "b478da86964a698b2924a2c41dd43510eb739a13140f69c3cf950523365d99f4"
}
```

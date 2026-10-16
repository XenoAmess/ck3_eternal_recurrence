# Research plan: e04-resource4-two-literal-data-qword-refs

GENERATED from the supplied research plan; no native semantics are inferred.

Question: Does actual .rdata hold preferred-VA QWORD data references to the two established exact literals, allowing a concrete registration row candidate?

```mermaid
flowchart TD
    n0["Two exact literal preferredVAs"]
    n1["Named QWORD data references"]
    n2["Registration/handler/enum UNKNOWN"]
    n0 -. "refs [unknown] Exact8B data reference locator" .-> n1
    n1 -. "meaning [unknown] Raw row is not a verified handler" .-> n2
```

| Edge | Declared status | Evidence IDs | Open question |
|---|---|---|---|
| refs | unknown | literal | Any actual data references to the two literalVAs? |
| meaning | unknown | literal | What actual schema/registration/handler does the row encode? |

| Observation design | Value |
|---|---|
| mode | offline-only |
| actor_kind | engine |
| owner_scope | Second Root-approved target-only data scan; exactly one same.rdata read, no.text/newstrings/callee |
| identity_kind | definition-key |
| identity_lifetime | Same exact image/file identity as first literal packet; preferredVA neverruntimeVA |
| producer_trigger | not-applicable |
| producer | Only two known QWORD literal references; registration schema unknown |
| caller | GetCurrency44DB128 and barter_goods450BB80 exact literal locations from prior scope |
| consumer | Potential native named registration/enum rows, not yet source-confirmed handlers |
| cache_lifetime | Static bytes only |
| expected_signal | &lt;=32 raw QWORD-reference rows with&lt;=128Bcontext each; any0/truncation remains explicit |
| zero_sample_meaning | Zero data references only excludes retained QWORD matches in this one section; codeRIP-relative registrations and other sections/encodings uninspected |
| stop_condition | Single17124352B.rdata read,1read;2exactQWORDtargets;&lt;=32rows/128Bcontext; body0,no.text/newstrings/callee/hash; totaloutput&lt;=131072B |
| runtime_window_ref | None |

| Evidence ID | Declared layer | File | SHA-256 | Supports |
|---|---|---|---|---|
| literal | locator | LITERALS.actual.json | af76ea5a7e69ea52048dc6ed80e6c78de7244e19ed02346a8f095cf378e47121 | Actual two name literal RVAs and static preferredVAs; no handler mapping |

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
  "checked_evidence_files": 1,
  "limitations": [
    "Evidence layers and conclusions are author declarations; hashes bind bytes, not their truth.",
    "Counts cover this enumerated graph only, not all CK3 branches.",
    "A consistent observation plan is not authorization to run or manipulate CK3."
  ],
  "plan_sha256": "ec160339d1645a0c2e86c72a27192e35f9c56f182c966085d851ea4f75f28f6b"
}
```

# Current post-admission numeric refresh inputs, 1.20.0.3

The optional `current_post_admission_refresh_inputs_v1` family supplies the original Army/ArRg occurrence stream needed to model the two numeric writes in `24DF3C0`. It closes the missing QWORD `ArRg+40` operand for every admitted occurrence, including occurrences whose `ArRg+38` is positive. The pure result reaches `post24df4c3_pre24df4c7` when both sums are complete; it does not invoke the native callback or describe a subsequent roster occurrence.

The source prerequisite is [the exact callback ledger](army-pre-date-character-prefix-and-post-admission-callback-12003.md). The game pin remains 1.20.0.3 / Steam build 25652598 / EXE SHA-256 `94b55397…02a6`. The source packet at `Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/pre-date-character-prefix-post-admission-source/phase-two-24df3c0-body/` contains the complete 669-byte `[0x24DF3C0,0x24DF65D)` body, raw SHA-256 `942f9e6dea3a26a7015d75bc8b350b3aa85e0905cc278424a4915a1102766c3a`. Its preceding exception-bound lookup read 160 metadata bytes separately. This implementation reuses that evidence and reads zero additional EXE bytes.

```mermaid
flowchart TD
    R[Same-query original primary50/5C raw roster] --> A[Original Army occurrence and actual resolution]
    A --> V[Original Army38/44 raw references in order]
    V --> E{Actual selected ArRg14 magic and own10 ID}
    E -->|bad magic or ID FFFFFFFF| Z[Keep occurrence; zero contribution; numeric operands unused]
    E -->|admitted| X[Read raw DWORD38 and QWORD40 independently]
    X --> S24[wrap i32 sum; modeled Army24 store at24DF452]
    X --> S28[wrap i64 sum; modeled Army28 store at24DF4C3]
    Z --> S24
    Z --> S28
    S24 --> F{Both sums complete?}
    S28 --> F
    F -->|yes| P[post24df4c3_pre24df4c7 conditional numeric frontier]
    F -->|only24| Q[post24df452_pre24df455; independent28 facts retained]
    F -. missing demanded numeric or diagnostic count .-> U[Branch-local partial with verified prefixes]
    P -. outside this package .-> C[Army20/30 getters; Army21/31 predicates; actual callback execution]
    C -. unknown association .-> N[Next repeated occurrence / full pre-date dispatch]
```

## Reader and transport

`ReadCurrentPostAdmissionRefreshInputs12003(bindings, same_query_roster, same_query_pending, same_query_table)` copies the already captured complete original roster. It reuses original Army references and raw `ArRg+38` observations only when their requested ID and actual selected identity match. An internal query-local resolver cache materializes the selected objects with the established generation/fallback resolver; output occurrences are never deduplicated. The new reader always demands `ArRg+40` for admitted occurrences. Existing daily-loss fields that intentionally omit `+40` for positive `+38` retain their meaning.

The ArRg registry is `5D1F340`, with fallback `5D1F338`; selection uses the complete requested DWORD ID. Rejected selected magic does not demand the fallback object's own full ID or numeric fields. A valid magic requires the actual own full ID before admission. A complete count zero skips unused data and resolves no elements. A negative count remains a diagnostic partial rather than an empty list.

The native DTO preserves raw Army/ArRg references, selected identities and fallback facts, raw numeric values and independent `numeric_24_inputs_ready` / `numeric_28_inputs_ready`. It also retains observed Army `24/28/20/21/30/31` caches separately. Those caches neither substitute for missing operands nor gate a legal zero-vector projection. The new binding belongs at the end of `ArmyBindings`, preserving existing aggregate initializer positions.

## Pure consumer and service seam

`normalize_current_post_admission_refresh_inputs_v1` validates the native shape, original occurrence correspondence and source-demand readiness. `project_current_post_admission_refresh_12003` derives wraparound sums, independent per-occurrence contributions and known prefixes. Missing `+40` preserves a complete `Army+24` projection; missing `+38` preserves independently complete `Army+28` facts without advancing the continuous frontier past the first write.

The proposed complete service result contains `current_post_admission_refresh_inputs_v1: [{army_id, projection}]`, alongside the unchanged raw leaf within each ArmyStrength row. The supplied entrance is observed current input for a conditional callback model. `actual_refresh_execution_ready`, `actual_next_occurrence_ready`, `full_callback_ready`, `full_daily_assault_ready`, `full_monthly_ready` and future-tick claims remain false. No native merger, callback, effect or refresh store executes.

## Qualification and next inputs

Eight exclusive implementation/fixture files are prepared, plus this topic. Root owns the minimal shared query, serializer, normalizer and service hooks. The new native target is `xar_bridge_ck3_12003_current_post_admission_refresh_test`, linked to the actual `xar_ck3_12002_runtime`; its only source is `src/ck3_12003_post_admission_refresh_test.cpp`. Nine new whole-Strength frames cover ordered repeats and signed wrap operands, wrong-generation fallback, rejected magic/sentinel, legal zero values, a zero Army vector, missing positive-row `+40`, independently ready `+28`, negative count and a zero original roster. Additional assertions verify matching captured-reference reuse and rejected-magic demand without producing extra frames.

One new complete-service compound case is prepared to consume the genuine optional normalizer and result hook. At this source milestone it has not run; native build, CTest, compiled-wire consumer and local game operations are also zero. The implementation packet is `Z:/ck3_mod_rewrite_process_assets/g2-background-20261006/current-post-admission-refresh-inputs/`. Source-shaped service qualification and later compiled-wire qualification must be recorded separately.

The shortest remaining callback inputs begin at the actual `2C4B840` and `2C4AB70` flag getters after this numeric frontier, followed by `24E3FE0` and the actual selector-24 rule verdict. Those source lanes are independent of these numeric operands. Full callback execution, earlier Character/Unit preparation, outer dispatch association and next-repeat state require their own closed transitions; this package does not generalize a direct numeric store into those effects.

# Current request guardian skill inputs in 1.20.0.4

The existing education interaction query can copy four current skill values from its final secondary actor. This is the guardian bound to that interaction request. Stock education effects choose their `scope:educator` separately; this profile does not observe that choice.

The source identity is CK3 1.20.0.4 / Steam 25734779, inherited executable SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. The retained actual function is `0x28B1690`, with the valid enum arm at `0x28B16D8`: `MOV EAX,DWORD[RCX+RBX*4+0xD8]`, followed by register restoration and `RET 0x28B16E9`. The unsigned enum check admits 0 through 5. This arm has no child call. The reader copies the corresponding member values and never invokes the getter or its invalid-enum assertion path.

The actual source receipt is [council effective skill DETAIL](Z:/ck3_mod_rewrite_process_assets/g2-migration-20261007/council-government/native-candidates/capture01/council_effective_skill-DETAIL.json), with the retained field mapping in [SOURCE-PROOF](Z:/ck3_mod_rewrite_process_assets/g2-migration-20261007/council-government/native-candidates/SOURCE-PROOF.json). The current production [council profiles](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_council_candidates.hpp) and [reader](../../ck3_autonomous_player/native_bridge/src/ck3_12004_council_candidates.cpp) use that same mapping after full-generation identity resolution. The 94-byte retained instruction packet includes the complete function and four trailing INT3 bytes. No new native bytes were captured.

| Component | Qualified enum | Character member | Result |
| --- | ---: | --- | --- |
| diplomacy | 0 | signed DWORD +D8 | independently copied |
| martial | unavailable named mapping | unavailable | null with `actual4_martial_name_enum_unqualified` |
| stewardship | 2 | signed DWORD +E0 | independently copied |
| intrigue | 3 | signed DWORD +E4 | independently copied |
| learning | 4 | signed DWORD +E8 | independently copied |

The leaf is [ck3_12004_request_guardian_skill_inputs.hpp](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_request_guardian_skill_inputs.hpp). `ReadRequestGuardianSkillInputs12004(access, final_child_full_id, final_secondary_actor_full_id, owning_native_revision)` accepts the existing guarded full-generation resolver and DWORD reader. The actual ordinary caller owns exact-build admission, final-role observation and the enclosing query frame checks. It supplies final `roles[3]` and `roles[2]` after native role and option materialization, while its local context remains alive.

The reader checks each full32 identity at Character +18, copies each qualified skill twice, then resolves and checks both receivers again. A skill read failure or value change affects only that component. Receiver identity drift invalidates all four copied values. Zero and negative observed DWORD values keep their signed source representation; this leaf performs no arithmetic or normalization.

A null guardian ID is accepted only from a successfully copied final-role DWORD of -1 and produces `binding_status=known_null`. An unavailable role read produces no profile. A resolver failure retains the observed role ID with `binding_status=unavailable`; it does not infer absence or use a fallback character.

`WriteRequestGuardianSkillInputs12004(std::ostream&, profile)` writes the object for optional key `request_guardian_skill_inputs_v1`. Its exact keys are `schema`, `role_source`, `child_character_id`, `character_id`, `owning_native_revision`, `binding_status`, `unavailable_reason` and `skills`. IDs are unsigned full32 integers or null; skill values are signed int32 integers or null. Each of the five named skill objects has `available`, `value` and `unavailable_reason`. The source role literal is `request_guardian_secondary_actor`.

The existing query publishes the optional profile only for actual4 education when its ordinary query and frame checks succeed. Raw skill failure changes no existing context support, CanSend, native-ready or queue decision. The consumer can select the raw component matching the child's independently observed current education focus and retain learning independently. A learning focus reuses the same copied learning value for both source terms if a separately qualified conditional calculation needs them.

```mermaid
flowchart TD
    A[Actual4 education query] --> B[Final secondary child and guardian full32 roles]
    B --> C[Existing guarded full-generation resolver]
    C --> D[Four independent signed DWORD skill copies]
    D --> E[Receiver identity and existing outer-frame bookends]
    E --> F[Optional request_guardian_skill_inputs_v1]
    F --> G[Actual current focus selects corresponding raw component]
    F --> H[Independent learning component]
    S[Stock random scope educator selection] --> U[Actual selected effect identity unavailable]
```

The profile may support facts about the requested guardian or a conditional statement about this person serving as educator. It does not populate actual effect `educator_present`, `educator_id`, `educator_values` or `educator_selection_observed`. Traits, culture, house modifiers, probability and education outcome remain outside this leaf.

Readiness is `SOURCE_AUTHORED_NOT_RUN`. The API, native caller and consumer are source work only. No tests, imports, build, game query or native getter invocation ran for this change.

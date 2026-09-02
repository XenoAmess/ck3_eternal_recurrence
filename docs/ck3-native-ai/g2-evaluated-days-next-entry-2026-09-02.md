# G2 `evaluated_days` next-entry sheet (2026-09-02)

This is a bounded static handoff for the remaining Raiktor truce leaf.  It
does not change the public v1 wire, ABI, readiness, offsets, or policy, and it
does not start CK3 or issue a termination command.

## Evidence to carry forward

- Frozen build is CK3 `1.19.0.6`, executable SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- The latest semantic-ready attempt is
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-fresh-semantic-ready-20260902T100431236\report.json`
  (SHA-256
  `4A7C66D34C851698572F4BBA2970ECAA00C005C2DC338ABCD75A7FD304F0B991`).
  It reached WarID `50331699`/CharacterID `29829`, performed two equal
  read-only terms queries on one paused frame, and observed gold, prestige,
  prisoner-release, and favor-hook rows.  The truce row still reported
  `evaluated_days_observable=false`, `evaluated_days=null`,
  `expiry_date_raw=null`; no write was sent.  Therefore `truce_ready=false`,
  `decision_ready=false`, and `GEN-034` remains unresolved.
- Its offline accelerator preflight is
  `open-kaishek-preflight-mod-20260902.json` in the same directory (SHA-256
  `5F7F67C439D8721E56C735E2DFA49E07A32630DD7019EB221C1C1215DD68AC90`).
  This is parser/profile evidence only (`ck3_started=false`), not a paused
  artifact.  Before a future native attempt, bind the current
  `open_kaishek` checkout/JAR and archive the new preflight alongside the
  runner report.
- The exact-build static evaluator review remains closed at evaluator RVA
  `0x3373000`; both known `CAddTruce` call sites use `truce_effect+0x108` and
  `context+0x28`.  No evidence supports an alternate offset.  Do not infer
  expiry by adding a guessed duration to the date.

## Baseline RED accounting

The fresh MSVC/Ninja run used for this handoff passed the focused G2 fixture
(`xar_ck3_game_access_test`).  The repository-wide CTest result retained 15
pre-existing path/source-contract/harness REDs; they are recorded in
`Z:\ck3_mod_rewrite_process_assets\zg361\g2-private-truce-build-20260902T122700\Testing\Temporary\LastTestsFailed.log`
(SHA-256
`D6C53B75D0B676B04E9BAB82006AE517C6E25255EB66A4B5EC2F66A35EF6F924`) and
are not G2 capability failures:

```text
xar_ck3_native_bridge_combat_v3_source_contract
xar_ck3_native_bridge_campaign_root_context_v1_source_contract
xar_ck3_native_bridge_zhongguo_ai_owned_case_snapshot_v1_source_contract
xar_ck3_native_bridge_zhongguo_case_snapshot_v1_source_contract
xar_ck3_native_bridge_zhongguo_b2_pip_snapshot_v1_source_contract
xar_ck3_native_bridge_zhongguo_incident_snapshot_v1_source_contract
xar_ck3_native_bridge_zhongguo_result_case_snapshot_v1_source_contract
xar_ck3_native_bridge_loaded_feature_manifest_v1_source_contract
xar_ck3_native_bridge_main_thread_query_mailbox_v1
xar_ck3_native_bridge_war_entry_assessments_v1_source_contract
xar_ck3_native_bridge_startup_particle2_stage_recorder_v1
xar_ck3_native_bridge_startup_particle2_null_guard_v1
xar_ck3_native_bridge_startup_particle2_consumer_null_guard_v1
xar_ck3_native_bridge_startup_dx11_render_context_draw_guard_v1
xar_ck3_native_bridge_startup_localize_current_root_guard_v1
```

The 15 entries must remain visible in reports; do not rerun or relabel them to
make the aggregate count appear green.

## Smallest next exact-build entry

1. Run the existing `run_war_termination_terms_live_acceptance.py` once after
   binding the frozen checkpoint, driver provenance, current bridge, and one
   `open_kaishek` offline preflight.  Stop before CK3 if any identity or
   semantic-ready proof differs.
2. If the concrete
   `query-war-termination-terms-v1-50331699` step and paused semantic snapshot
   are present, perform only the existing read-only sequence and retain the
   two terms payloads plus their SHA-256.  The required new observation is two
   equal, non-negative `evaluated_days` values on the same frame, with the
   pointer-only `CAddTruce` shape and exact role identity.
3. If that leaf fails, use the already merged test-only thread-local typed
   `RaiktorSurrenderTruceFailureV1` seam to classify the private reader failure
   in the offline fixture.  It is not a public field and must not be copied to
   JSON/MCP or used to change readiness.
4. Preserve `expiry_observable=false`, keep surrender/white-peace/enforce
   writes frozen, and leave `GEN-034` unresolved until a real paused artifact
   proves the truce leaf and the remaining six-domain/policy inputs.

No additional offset hunt, public schema field, timeout increase, or identical
checkpoint replay is justified by the current evidence.

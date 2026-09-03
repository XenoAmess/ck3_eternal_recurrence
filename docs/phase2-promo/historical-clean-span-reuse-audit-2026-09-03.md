# Phase 2 historical clean-span reuse audit (2026-09-03)

This is a read-only provenance audit for the two Phase 2 promo cuts. It did
not start CK3, call TTS or FFmpeg, write media, or promote an old artifact into
the current intake. The decision below is deliberately conservative and is
based on the current Phase 2 source/claim/seed contract.

## Decision

**Legally reusable current-Phase-2 clean spans: `0/8`.** Both target cuts
remain `RED / footage_pending`; no placeholder footage or MP4 was created.

The eight required IDs are:

1. `phase2_fact_quota_calibration`
2. `phase2_receipt_appeal_pip`
3. `phase2_manager_governance`
4. `phase2_promotion_compensation`
5. `phase2_hc_workforce`
6. `phase2_projects_metrics`
7. `phase2_incidents_operations`
8. `phase2_cross_cycle_endgame`

A reusable span must bind the same canonical seed/save lineage, exact Phase 2
source commit/tree, game version and EXE, and product-only mod mount. Each span
also needs a continuous session identity, pre/action/post revisions,
checkpoint, provider-observed postcondition, and cleanup receipt. Legacy
一期/old-version captures and fixture mounts are explicitly out of scope.

## Current intake evidence

The latest delivery queue is
`_runtime/promo-inventory-20260903/delivery-queue-20260903-1236.json`
(SHA-256 `4C7369DFBA31BF407EB42C8B3D46963E42153691D1BBCC4615F17B60FC129723`).
It records `RED / BLOCKED`, `spans_green=0`, `spans_total=8`, and all eight IDs
as missing. Its capture root is the imported fixture directory
`mod_zhongguo_style/promo/imported/fixture-live-zga-20260829-061314-ea5f04ad`.
The corresponding intake report
`_runtime/promo-audit-footage-20260903.json` (SHA-256
`D34CF4070C0D474A06F29BA2C3A0707E4BA391D42D5C700992A6BE826D67A2A2`) is
`RED / footage_pending`: the root exists, but `capture-timeline.json` and
`cell/04_phase2_seed_loaded.json` are absent. The available report and
evidence-index hashes are `3E3268419D52D8406E5657B61906E15F61E9E07F02318E4B5D96572A143A9C1F`
and `4E365432264D4075E4082563362B6DC920102B4051EFBE7829D341AE0A2173C9`.

The fixture's `import-index.json` labels it “fixture-live acceptance stills;
not a clean promotional recording”, records `source_result=GREEN`, and sets
`loading_excluded=true`. It contains stills and diagnostics, not the required
Phase 2 span timeline/seed envelope.

## Historical artifact scan

The external asset root `Z:\ck3_mod_rewrite_process_assets\zg361` was scanned
recursively for `capture-timeline.json` and the canonical Phase 2 IDs:

- 40 timeline files were found.
- **Zero** timelines contain any of the eight current Phase 2 IDs. The
  historical run/evidence envelope identifies only one completed clean promo
  take among these timelines; `clean=true` is not a literal top-level field in
  that older timeline schema.
- That historical clean take is
  `promo\captures\zga_20260830_0930_clean_2fa2ac8_mcp\cell\promo\capture-timeline.json`
  (schema 2, SHA-256
  `02F39DC0CEF2F62E558592F96E49CF38CC07B4E1487054364AC6854655497F3B`).
  Its marks are the older product-card route (`calibration`,
  `managed_scoreboard`, `policy_cockpit`, `jingcha_mandate`,
  `free_jingcha_planner`, `superior_assigned_325`,
  `received_scoreboard_with_325`, and `policy_card_001/007/020/022/026/361`),
  not the Phase 2 IDs.
- That capture also mounts both `mod/zg361_acceptance.mod` and
  `mod/zga_acceptance_fixture.mod`, and its evidence binds old source head
  `2fa2ac86d6e114a009d6b5c5bd8f79b33baed3ed` and the old development projection.
  It therefore fails the current product-only mount and source-lineage gate.
  The associated raw MKV is 762,266,772 bytes (SHA-256
  `4D85D5D38A9D89C230153EFC66146A0C25AFD23F0E50120795D7C82CF016CA67`);
  those bytes are retained as historical evidence, not as Phase 2 input.
- The external `promo` area contains old release/smoke names
  (`zg361-promo-release.mp4` and `zg361-promo-pipeline-smoke.mp4`) but no
  current Phase 2 target names or Phase 2 span IDs. Names alone never satisfy
  the lineage contract.

The two Phase 2 capture plans
`promo\phase2-capture-plan-20260902T111751Z\capture-plan.json` and
`promo\phase2-capture-plan-20260902T111859Z\capture-plan.json` are both
`RED / waiting-for-bound-inputs`; they list
`completion_observer_artifact_pending` and `legacy_seed_forbidden`. Their
no-launch attestations and seed readiness fields are false. They are plans,
not footage.

## Authoring/tool readiness that can proceed independently

- Character treatment and institution treatment remain separate, distinct
  10-chapter authoring plans. Their SHA-256 values are respectively
  `B573A1A0A09FC532D9190ED765222943E95948D833666B898A5AD32F5BE9A44B` and
  `D9EA9CB3804C11FA4877B7444BB66D1CD3F3A9C047AE0E340F4E76C957AD97B8`.
- Both cut-specific claim ledgers validate `GREEN` (10 chapter drafts and
  8/8 gameplay cues still marked for future real clean spans; media generated:
  no).
- The fresh promo-tool checkout
  `Z:\ck3_mod_rewrite\_runtime\promo-tool-fresh-20260903` is clean and
  currently `HEAD == origin/main ==
  57c42fca13ea459432c1caf76e069a1fbccf602c`. Its full suite passes
  `263 tests`, with `2 skipped`. A live `git ls-remote` check matched the same
  main commit. This freshness check must be repeated immediately before real
  TTS/render because the remote may advance.

## Next executable sequence and ETA

1. After the exclusive CK3/seed gate is green, capture the eight shared
   same-lineage spans and run the existing read-only intake (`20–40 minutes`
   once a stable desktop session is available).
2. With intake green, run the two independent source-review, TTS, bilingual
   subtitle, and candidate pipelines in parallel (`45–90 minutes` per cut).
3. Perform the cut-specific claims audit, two named 1× human reviews, export,
   and hash receipts. A fixed wall-clock delivery time cannot be promised
   while the shared capture remains `0/8`.

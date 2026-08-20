# Release QA v1.0.0

## Automated Evidence

- Static generated parity, BOM/localization structure, player-only guards, assets and release allowlist: required GREEN.
- Python scoring reference vectors: required GREEN.
- Deterministic double release build: required GREEN.
- GitHub official `windows-latest` runs the L0 checks above and builds uploadable ZIP/manifest artifacts for manual runs or `v*` tags; it does not contain CK3.
- Local CK3 selftest, production smokes, persistence, death edges, with-heir death, bargain timing, progression UI, scoring matrix and paid-courtier scenarios: required GREEN with zero `xar` error lines.
- Landless courtier delivery, process-restart retention and multilingual layout are explicitly uncovered compatibility/presentation cases; they do not downgrade the landed-player functional scenario from GREEN.

Historical local evidence (2026-08-19):

The runs below predate production-code candidate `a19808d`. They remain evidence for the named paths only; they do not validate the paid courtier or the current complete tree.

| Scenario | Run ID | Result |
|---|---|---|
| 57-assertion selftest + expanded shop + scaled Gaze rewards + transaction UI + ledger/contract decisions + AI guard + observer HUD | `xar_accept_t_4fu4zt` | GREEN, 0 `xar` errors |
| Two-process persistence / A writes 405 / B imports 405 without pre-seeding | `xar_accept_ie68yqxu` | GREEN, 0 `xar` errors |
| Actual AI death guard + no-heir native-window settlement + main-menu exit | `xar_accept_fmq_wxxc` | GREEN, eight values visible, 0 `xar` errors |
| Three cumulative production bargains / three exact day-1094 and day-1095 reopen boundaries | `xar_accept_ue4ye_un` | GREEN, nine game years, three ordered production resets, 0 `xar` errors |
| Wise Ruler 3/6/10 milestones / PB lessons / collection / Gaze 10 / ledger pixels | `xar_accept_gqppgi_f` | GREEN, PB 10, collection mask 16, `R 1` / `S 0`, 0 `xar` errors |
| Controlled descendant depth/dedup/dead-intermediate scoring + all 200 production pool dispatchers | `xar_accept_h0lgmvyf` | GREEN, 7 living descendants, depth 6 excluded, 200/200 wire markers, 0 `xar` errors |
| Release projection / first life / zero record | `xar_accept_v6wtivlm` | GREEN, autosaves isolated/restored, 0 `xar` errors |
| Release projection / recorded life / 100 tier, default Growth + 100% | `xar_accept_2sv8bfoi` | GREEN, 0 `xar` errors |
| Release projection / 2000 tier / page-4 Dread + Legitimacy / 1133 reformation | `xar_accept_pq2qn3e6` | GREEN, 0 `xar` errors |
| Release projection / rule disabled | `xar_accept_n_sya3ke` | GREEN, 0 `xar` errors |
| Optimized full selftest regression | `xar_selftest_fast_v4_20260819` | GREEN, 159.411 seconds total; inheritance recovery 2.882 seconds |
| Optimized passive balance smoke / synthetic / two pairs | `xar_balance_synthetic_fast2_20260819` | GREEN, two pairs only; not a 30–40 year balance result |

Release-candidate baseline plus post-review targeted evidence (2026-08-20):

Rows for the full suite retain their original tree fingerprints. Subsequent production changes were confined to the death gates and paid-courtier transaction/GUI paths; those paths were rerun below after review. The current 78-file production projection has deterministic L0 evidence, but was not itself put through another complete CK3 suite after every post-review edit.

| Scenario | Run ID | Result |
|---|---|---|
| L0 static + scoring vectors + deterministic release projection | current working tree | GREEN, 78 release files |
| Full selftest / 57 assertions / production UI / pool sweep | `xar_selftest_release_candidate_20260820` | GREEN, 57/57, 200-entry sweep, persistence, observer transition, 0 `xar` errors |
| Four production-only smokes | `xar_on_first_life_release_candidate_20260820`; `xar_on_recorded_release_candidate_20260820`; `xar_on_high_budget_release_candidate_20260820`; `xar_off_release_candidate_20260820` | GREEN, stripped staging first/recorded/high-budget/off paths, 0 `xar` errors |
| Two-process persistence restart | `xar_persistence_release_candidate_20260820` | GREEN, process B imported process A tier 445 without pre-seeding, 0 `xar` errors |
| Death edges / AI and no playable heir | `xar_death_edges_postreview_20260820` | GREEN after the shared AI-gate review, AI blocked, eight-value native settlement, main-menu return, 0 `xar` errors |
| Ordinary death with playable heir | `xar_death_with_heir_postreview_20260820` | GREEN after the shared AI-gate review, heir carrier, control transfer, one production score and visible settlement, 0 `xar` errors |
| Three production bargain reopens | `xar_bargain_release_candidate_20260820` | GREEN, each day 1094 blocked/day 1095 opened, cumulative pairs 1/2/3, 0 `xar` errors |
| Contract/Gaze progression UI | `xar_progression_release_candidate_20260820` | GREEN, 3/6/10 PB, collection mask 16, Gaze 10, `R 1` / `S 0`, 0 `xar` errors |
| Controlled scoring and 200 dispatchers | `xar_scoring_matrix_release_candidate_20260820` | GREEN, seven descendants, depth/dedup/dead-intermediate parity, 200/200 branches, 0 `xar` errors |
| Paid custom courtier real UI | `xar_courtier_creator_postreview22_20260820` | GREEN after delivery rollback review, cancel/119-gold/default 120/custom 348/seven tabs/numeric controls/non-default culture and faith/same house/reopen/two delivered courtiers/AI guard, 0 `xar` errors |

Current candidate gates:

| Gate | Status | Required evidence |
|---|---|---|
| Current-tree L0 and deterministic release projection | GREEN | `validate_static.py`, reference vectors and 78-file `build_release.py --check` all pass; this is not a CK3 runtime claim |
| Full baseline plus post-review targeted CK3 regression | GREEN | the full release-candidate suite passed; changed death paths and paid courtier were then rerun on the reviewed tree with zero `xar` errors |
| Ordinary death with a playable heir | GREEN | `xar_death_with_heir_postreview_20260820`; one compute, dispatch and visible settlement |
| Paid custom courtier | GREEN | `xar_courtier_creator_postreview22_20260820`; both selected origins differ from the player, successful delivery precedes configuration and charge, and remaining landless/process-restart cases are declared coverage gaps |

## Manual Language Sign-off

The structural validator covers all nine languages. Human terminology/persona review remains an external release task and must not be represented as automated approval.

Commit `6e186bb` replaced the then-current seven-language English placeholders. The v2 courtier pass translated 22 active v2 values in each of French, German, Japanese, Korean, Polish, Russian and Spanish with MiniMax-M3 assistance (154 values total), then manually verified exact keys, protected tokens, numeric literals and CK3 1.19.0.6 native terminology; obsolete v1 option labels were removed from all nine languages. Structural and source-term review is not mother-tongue approval. Simplified Chinese seven-tab rendering is GREEN; the other languages still require in-game clipping review.

| Language | Structural | Human reviewer | Persona/terms | In-game truncation | Status |
|---|---|---|---|---|---|
| Simplified Chinese | GREEN | pending | pending | seven-tab courtier modal GREEN; full pass pending | partial |
| English | GREEN | pending | source reviewed | pending | partial |
| French | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| German | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Japanese | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Korean | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Polish | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Russian | GREEN | pending | source/CK3 terms reviewed | pending | partial |
| Spanish | GREEN | pending | source/CK3 terms reviewed | pending | partial |

## Manual Presentation Sign-off

- Clean non-debug Simplified Chinese screenshot set: pending.
- Matching clean English screenshot set: pending.
- Thumbnail legibility at Workshop card size: pending.
- No-heir settlement presentation: automated Simplified Chinese proof GREEN; clean non-debug release screenshot remains pending.
- Paid custom-courtier window: all seven tabs, price/available-gold row and longest nine-language strings must be checked for clipping at supported UI scales: pending.
- Steam item `3784706360` upload and downloaded-cache manifest verification: pending.

## Passive Soak / Matrix Telemetry

`balance-long` and the four-fixture passive matrix are non-gating soak, stability and telemetry. GREEN validates fixture setup, cadence, terminal wiring, recovery, sampling and stated error criteria only; it neither certifies numerical balance nor blocks merge or release. Numerical balance requires an explicit strategy, controls and skilled-player evidence.

Known death-carrier edge: normal succession follows the vanilla-style single delayed `player_heir` carrier. If that carrier itself dies before `xar.1003` dispatches, the queued event can be lost; no player-only fallback is currently proven. Initial no-heir deaths and the ordinary living-heir path remain independently GREEN.

## External Delivery

- `v1.0.0` tag, GitHub Release, deterministic release artifact publication and Steam upload: pending.
- Downloaded Workshop cache verification against the release manifest: pending.
- Clean screenshots and thumbnail aesthetic approval: pending.
- Author/source and redistribution permission for all four release assets: recorded from the author in `docs/asset-provenance.md`; no separate public asset license is asserted.

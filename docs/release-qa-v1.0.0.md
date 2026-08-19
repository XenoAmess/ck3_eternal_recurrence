# Release QA v1.0.0

## Automated Evidence

- Static generated parity, BOM/localization structure, player-only guards, assets and release allowlist: required GREEN.
- Python scoring reference vectors: required GREEN.
- Deterministic double release build: required GREEN.
- GitHub official `windows-latest` runs the L0 checks above and builds uploadable ZIP/manifest artifacts for manual runs or `v*` tags; it does not contain CK3.
- Local CK3 selftest, production smokes, persistence, death edges, with-heir death, bargain timing, progression UI and scoring matrix scenarios: required GREEN with zero `xar` error lines.
- The paid custom-courtier flow has no automated CK3 scenario yet. Its L0 invariants and the manual matrix in `docs/courtier-creator.md` are both required before release approval.

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

Current candidate gates:

| Gate | Status | Required evidence |
|---|---|---|
| Current-tree L0 and deterministic release projection | pending | `validate_static.py`, reference vectors, `build_release.py --check` on the candidate tree |
| Current-tree CK3 regression | pending | selftest, production smokes and affected L2/L3 scenarios with zero `xar` errors |
| Ordinary death with a playable heir | pending | first GREEN `death-with-heir` run ID; one compute, dispatch and visible settlement |
| Paid custom courtier | pending | cancellation, insufficient gold, default/max configurations, limits, both sexes, all ages, landed/landless delivery, exactly-once charge, save/reopen and language layout |
| Passive balance matrix | pending | current fail-fast natural-death terminal plus complete `count|king|emperor|synthetic` reports; 40 years/14 pairs/pair 10 when the fixture survives |

## Manual Language Sign-off

The structural validator covers all nine languages. Human terminology/persona review remains an external release task and must not be represented as automated approval.

Commit `6e186bb` replaced the seven target-language English placeholders with MiniMax-M3-assisted source translations and completed the then-current key/token audit. Candidate `a19808d` added 45 paid-courtier keys in all nine languages, including translated core UI text and native trait-name wrappers. No current-tree L0 or in-game language pass has run after that addition. Translation presence is not mother-tongue approval.

| Language | Structural | Human reviewer | Persona/terms | In-game truncation | Status |
|---|---|---|---|---|---|
| Simplified Chinese | source present; current L0 pending | pending | pending | pending | pending |
| English | source present; current L0 pending | pending | pending | pending | pending |
| French | translated source; current L0 pending | pending | pending | pending | pending |
| German | translated source; current L0 pending | pending | pending | pending | pending |
| Japanese | translated source; current L0 pending | pending | pending | pending | pending |
| Korean | translated source; current L0 pending | pending | pending | pending | pending |
| Polish | translated source; current L0 pending | pending | pending | pending | pending |
| Russian | translated source; current L0 pending | pending | pending | pending | pending |
| Spanish | translated source; current L0 pending | pending | pending | pending | pending |

## Manual Presentation Sign-off

- Clean non-debug Simplified Chinese screenshot set: pending.
- Matching clean English screenshot set: pending.
- Thumbnail legibility at Workshop card size: pending.
- No-heir settlement presentation: automated Simplified Chinese proof GREEN; clean non-debug release screenshot remains pending.
- Paid custom-courtier window: all four tabs, price/available-gold row and longest nine-language strings must be checked for clipping at supported UI scales: pending.
- Steam item `3784706360` upload and downloaded-cache manifest verification: pending.

## Balance Gate

The four-fixture matrix is required engineering evidence before the final 1.0 release decision because its terminal wire, 1095-day cadence and 40-year censoring paths have not completed end to end. Its numerical outcome is not an L0 structural-correctness assertion: once the matrix is GREEN mechanically, any tuning changes remain a separate product decision and require a fresh matrix.

## External Delivery

- `v1.0.0` tag, GitHub Release, deterministic release artifact publication and Steam upload: pending.
- Downloaded Workshop cache verification against the release manifest: pending.
- Clean screenshots and thumbnail aesthetic approval: pending.
- Author/source and redistribution permission for all four release assets in `docs/asset-provenance.md`: pending; file presence does not establish rights.

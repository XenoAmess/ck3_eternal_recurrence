# Release QA v1.0.0

## Automated Evidence

- Static generated parity, BOM/localization structure, player-only guards, assets and release allowlist: required GREEN.
- Python scoring reference vectors: required GREEN.
- Deterministic double release build: required GREEN.
- GitHub official `windows-latest` runs the L0 checks above and builds uploadable ZIP/manifest artifacts for manual runs or `v*` tags; it does not contain CK3.
- Local CK3 selftest, production smokes, persistence, death edges, bargain timing and progression UI scenarios: required GREEN with zero `xar` error lines.

Latest local candidate evidence (2026-08-19):

| Scenario | Run ID | Result |
|---|---|---|
| 57-assertion selftest + expanded shop + scaled Gaze rewards + transaction UI + ledger/contract decisions + AI guard + observer HUD | `xar_accept_wy1o9wkg` | GREEN, 0 `xar` errors |
| Two-process persistence / A writes 405 / B imports 405 without pre-seeding | `xar_accept_ie68yqxu` | GREEN, 0 `xar` errors |
| Actual AI death guard + no-heir native-window settlement + main-menu exit | `xar_accept_fmq_wxxc` | GREEN, eight values visible, 0 `xar` errors |
| Three cumulative production bargains / three exact day-1094 and day-1095 reopen boundaries | `xar_accept_ue4ye_un` | GREEN, nine game years, three ordered production resets, 0 `xar` errors |
| Wise Ruler 3/6/10 milestones / PB lessons / collection / Gaze 10 / ledger pixels | `xar_accept_gqppgi_f` | GREEN, PB 10, collection mask 16, `R 1` / `S 0`, 0 `xar` errors |
| Release projection / first life / zero record | `xar_accept__1403689` | GREEN, 0 `xar` errors |
| Release projection / recorded life / 100 tier, default Growth + 100% | `xar_accept_2sv8bfoi` | GREEN, 0 `xar` errors |
| Release projection / 2000 tier / page-4 Dread + Legitimacy / 1133 reformation | `xar_accept_pq2qn3e6` | GREEN, 0 `xar` errors |
| Release projection / rule disabled | `xar_accept_n_sya3ke` | GREEN, 0 `xar` errors |

## Manual Language Sign-off

The structural validator covers all nine languages. Human terminology/persona review remains an external release task and must not be represented as automated approval.
Routine development authors and reviews only Simplified Chinese and English. The other seven generated languages may intentionally retain English structural placeholders until the user explicitly requests a release; only then are MiniMax-assisted translation and the full audit in `docs/localization-workflow.md` performed.

| Language | Structural | Human reviewer | Persona/terms | In-game truncation | Status |
|---|---|---|---|---|---|
| Simplified Chinese | automated | pending | pending | pending | pending |
| English | automated | pending | pending | pending | pending |
| French | automated | deferred until release | deferred until release | deferred until release | deferred |
| German | automated | deferred until release | deferred until release | deferred until release | deferred |
| Japanese | automated | deferred until release | deferred until release | deferred until release | deferred |
| Korean | automated | deferred until release | deferred until release | deferred until release | deferred |
| Polish | automated | deferred until release | deferred until release | deferred until release | deferred |
| Russian | automated | deferred until release | deferred until release | deferred until release | deferred |
| Spanish | automated | deferred until release | deferred until release | deferred until release | deferred |

## Manual Presentation Sign-off

- Clean non-debug Simplified Chinese screenshot set: pending.
- Matching clean English screenshot set: pending.
- Thumbnail legibility at Workshop card size: pending.
- No-heir settlement presentation: automated Simplified Chinese proof GREEN; clean non-debug release screenshot remains pending.
- Steam item `3784706360` upload and downloaded-cache manifest verification: pending.

# Release QA v1.0.0

## Automated Evidence

- Static generated parity, BOM/localization structure, player-only guards, assets and release allowlist: required GREEN.
- Python scoring reference vectors: required GREEN.
- Deterministic double release build: required GREEN.
- CK3 selftest, first-life, recorded-life, high-budget, disabled-rule and two-process persistence scenarios: required GREEN with zero `xar` error lines.

Latest local candidate evidence (2026-08-18):

| Scenario | Run ID | Result |
|---|---|---|
| 54-assertion selftest + transaction UI + ledger/contract decisions + AI guard + observer HUD | `xar_accept_mbnpw868` | GREEN, 0 `xar` errors |
| Two-process persistence / A writes 405 / B imports 405 without pre-seeding | `xar_accept_ie68yqxu` | GREEN, 0 `xar` errors |
| First life / zero record | `xar_accept_tw20hu2u` | GREEN, 0 `xar` errors |
| Recorded life / 100 tier, default Growth + 100% | `xar_accept_5j1hqj8z` | GREEN, 0 `xar` errors |
| High budget / 1200 tier / 1133 reformation purchase | `xar_accept_iqz9ocec` | GREEN, 0 `xar` errors |
| Rule disabled | `xar_accept_qlbea8ug` | GREEN, 0 `xar` errors |

## Manual Language Sign-off

The structural validator covers all nine languages. Human terminology/persona review remains an external release task and must not be represented as automated approval.
The 1.0 contract narrative is authored in Simplified Chinese and English; the other seven generated contract files intentionally use English pending human translation.

| Language | Structural | Human reviewer | Persona/terms | In-game truncation | Status |
|---|---|---|---|---|---|
| Simplified Chinese | automated | pending | pending | pending | pending |
| English | automated | pending | pending | pending | pending |
| French | automated | pending | pending | pending | pending |
| German | automated | pending | pending | pending | pending |
| Japanese | automated | pending | pending | pending | pending |
| Korean | automated | pending | pending | pending | pending |
| Polish | automated | pending | pending | pending | pending |
| Russian | automated | pending | pending | pending | pending |
| Spanish | automated | pending | pending | pending | pending |

## Manual Presentation Sign-off

- Clean non-debug Simplified Chinese screenshot set: pending.
- Matching clean English screenshot set: pending.
- Thumbnail legibility at Workshop card size: pending.
- No-heir native Game Over overlap: pending.
- Steam item `3784706360` upload and downloaded-cache manifest verification: pending.

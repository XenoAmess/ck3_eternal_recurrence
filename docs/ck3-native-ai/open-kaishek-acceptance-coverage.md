# open_kaishek acceptance coverage

This matrix records the one-time source audit performed on 2026-09-02.  The
offline gate is an accelerator only; it never upgrades a run to CK3 live,
paused-snapshot, MCP, or production readiness.

| Entry point | CK3/desktop boundary | Offline decision | Hook and evidence |
| --- | --- | --- | --- |
| `tools/run_acceptance.py` | Base XAR debug/live runner | Parser + validator over `XenoAmess_s_Eternal_Recurrence`, fixture `none` | Direct call at the start of `preflight()`; result is retained in `report.json` |
| `tools/run_terminal_acceptance.py` | Non-debug observer/Ironman wrapper | Reuses the base XAR gate; no second invocation | Delegates to `run_acceptance.main()`; the base call runs before launch |
| `tools/run_vivhite_acceptance.py` | Vivhite standalone/dual matrix | Parser + validator over the checked-in `vivhite_acceptance` fixture, fixture `none` | Direct call at the start of `preflight()`; result is included in cell and matrix reports |
| `tools/run_ox_here_acceptance.py` | Ox Here non-debug cell | Parser + validator over the checked-in `ox_here_acceptance` fixture, fixture `none` | Direct call at the start of `preflight()`; result is included in the cell report |
| `tools/run_zhongguo_acceptance.py` | ZhongGuo 361 native/MCP and promo modes | `ck3-1.19.0.6-zg361` profile with the configured runtime root and `synthetic-361-014` | Existing direct adapter call at the start of `preflight()`; result is copied to `open_kaishek-preflight.json` |
| `tools/run_zg361_phase2_seed_capture.py` | Direct phase-two native-session/CK3 seed capture | `ck3-1.19.0.6-zg361` over the frozen product root plus `synthetic-361-014` | Direct adapter call in both no-launch `run_preflight()` and capture `run_capture()`; the latter runs before supervisor startup and writes `open_kaishek-preflight.json` |
| `tools/run_ox_here_loc_smoke.py` | Fresh-process CK3 localization matrix (desktop + launch per language) | Parser + validator over the checked-in `ox_here_loc_smoke` fixture, fixture `none` | Direct call at the start of `preflight()`; result is included in the matrix report |
| `ck3_autonomous_player/native_bridge/research/run_*_live_acceptance.py` | Native bridge/save/checkpoint live probes | Not applicable for the current profile: these steps exercise native save/bridge semantics, for which the current offline profile has no deterministic source/fixture subset | Keep the live boundary and evidence requirements unchanged; do not add no-op CLI calls |

The terminal wrapper does not call the adapter itself because doing so would
run the same immutable XAR corpus twice.  The wrapper's only CK3 delegation is
`run_acceptance.main()`, whose `preflight()` owns the single call.  The static
contract test `tools/test_acceptance_open_kaishek_coverage.py` checks this
ordering and the no-duplicate terminal path without starting CK3 or touching
the desktop.

For all rows, an absent checkout/JAR is recorded as
`NOT_APPLICABLE`; `FAILED`/`UNSUPPORTED` from the accelerator remains separate
from the runner's own CK3 result.  The exact command and provenance are
provided by `tools/kaishek_preflight.py` and the external
`open_kaishek.preflight.v1` contract.

The parent adapter's default contract/provenance pin is `open_kaishek`
`aecb14f` (or a compatible descendant). The resolved checkout commit and JAR
SHA-256 are archived independently, and an intentionally different
checkout/JAR can be bound with `XAR_OPEN_KAISHEK_ROOT`,
`XAR_OPEN_KAISHEK_JAR`, and `XAR_OPEN_KAISHEK_COMMIT`. A legacy JAR that
answers `preflight` with the generic `UNSUPPORTED` envelope remains
`UNSUPPORTED`; a missing checkout or JAR remains `NOT_APPLICABLE`.

The default subprocess timeout is 180 seconds. This replaces the former
120-second bound after a real 76-file full-corpus preflight exhausted that
window. The effective value is included in adapter provenance and can be
overridden with `XAR_KAISHEK_PREFLIGHT_TIMEOUT_SECONDS` for a specifically
bounded corpus; changing it does not alter any CK3 live timeout or evidence
level.

## Progress-report fields

Use the following compact fields in the daily and weekly reports:

| Field | Value for this audit |
| --- | --- |
| `acceptance_preflight_coverage` | `7/7 CK3/desktop entrypoints covered` (five new direct hooks, one existing ZhongGuo hook, and one terminal wrapper that inherits the base hook) |
| `acceptance_preflight_entrypoints` | `run_acceptance`, `run_terminal_acceptance`, `run_vivhite_acceptance`, `run_ox_here_acceptance`, `run_ox_here_loc_smoke`, `run_zhongguo_acceptance`, `run_zg361_phase2_seed_capture` |
| `acceptance_preflight_na` | No N/A coverage gap among the seven; native-bridge research `run_*_live_acceptance.py` remains N/A/excluded because the current profile has no deterministic source/fixture subset for its save/bridge semantics |
| `acceptance_preflight_semantics` | Offline parser/validator accelerator only; an adapter `NOT_APPLICABLE`, `UNSUPPORTED`, or `FAILED` result never becomes CK3 live/readiness evidence |
| `acceptance_preflight_evidence` | Commits `9764ad6`, `6c2117a`, `9cf958a`; coverage 4/4 and adapter 7/7; no CK3 or desktop run performed |

Copy-ready daily wording:

> `open_kaishek` source coverage is 7/7 for the CK3/desktop acceptance
> entrypoints (terminal reuses the base gate; ZhongGuo already had its gate).
> The gate is advisory and offline, so readiness/live status is unchanged;
> native-bridge research runners remain N/A for the current profile/fixture.

For the weekly report, retain the same count and boundary, then link this
matrix and the evidence commit.  Do not describe the count as CK3 gameplay
coverage, a paused snapshot, or a production-live result.

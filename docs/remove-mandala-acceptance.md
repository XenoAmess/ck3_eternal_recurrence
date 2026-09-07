# Mandala Purge v1.0.0 Acceptance Report

Status: **GREEN for source release candidate and real CK3 runtime**

Date: 2026-09-08 (Asia/Shanghai)

Test plan: [`remove-mandala-test-plan.md`](remove-mandala-test-plan.md)

## Accepted product

- Product: `mod_remove_mandala`, version `1.0.0`
- Engine: CK3 `1.19.0.6`, non-debug, isolated userdir
- CK3 EXE SHA-256 before/after: `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`
- Exact runtime projection: 15 files
- Runtime product tree SHA-256 before/after: `cac4f5033cec8e96d5f268eff097850f6844e1441fea121bc607f2aed737dad8`
- External fixture tree SHA-256 before/after: `d876f09b4cd6218d396cf4e8ad70d827a0757bbfaf3b3ac02619a2e72be25fc7`
- Final artifact: `C:\Users\1\AppData\Local\Temp\mrma_20260908_044123_6e4451cd`
- Final `report.json` SHA-256: `6ebd3d055f3ca1816512ebac925999695f80de8f73e3d09151fd050130ad6547`
- Duration: 523.032 seconds
- Protected real player storage: unchanged; postflight quiet window: 5 seconds

## Functional result

All required marker assertions passed and no `MRMA: TEST FAIL` appeared:

| Assertion | Result |
|---|---|
| game-start global Mandala ruler count is zero | GREEN |
| game-start global Temple Citadel count is zero | GREEN |
| day-one seeded ruler changed to Wanua | GREEN |
| day-two seeded holding changed to Castle | GREEN |
| legal independent-feudal AI Mandala transition redirected to Wanua | GREEN |
| accelerated exact monthly dispatcher restores global zero Mandala rulers | GREEN |
| accelerated exact yearly dispatcher restores global zero Temple Citadels | GREEN |
| localized final acceptance event displayed and closed through visible UI | GREEN |
| source and both mounted runtime trees remained byte-identical | GREEN |

`project_diagnostics` is empty. The fixture was mounted after the exact product projection and is not present in the release allowlist.

## Static and build result

| Command | Result |
|---|---|
| `tools/validate_remove_mandala_static.py` | GREEN: 15 runtime files, 9 languages, 6 hidden sweep events |
| `tools/test_build_remove_mandala_release.py` | GREEN: 8/8 tests |
| `tools/compose_remove_mandala_key_art.py --check` | GREEN: tracked 640×640 thumbnail byte-identical, 770,575 bytes |
| `tools/build_remove_mandala_release.py --check` | GREEN: deterministic two-build manifest and ZIP |
| Python compile, `git diff --check`, repository credential-pattern scan | GREEN |

The provisional reproducibility hashes before the release commit/tag were manifest `81b1e81f7e2ea8f113e94b35cca9a0d39c52de1a6df3b66c7e0e466df074bfcd` and ZIP `04cda5dc095cc329edbd21a71eda533bd3005fddf979721af63d7b4c8f5b90d9`. The formal tag-bound hashes are recorded in the release changelog only after the Workshop upload succeeds.

## Offline preflight boundary

The runner first called local `open_kaishek` commit `33d690234d8217422978ee642055ab1b13e44c76`, profile `ck3-1.19.0.6`, CLI JAR SHA-256 `cc42a0bbd4991095deb4c8af4142a4657d46d07d616b89643a9f2d7a1e4a3cd7`, and source corpus SHA-256 `a942cb1ae74b015dd91d7ca40e6f45211cc6a190bc1536c05c9ce73e37820478`.

The general root parser was GREEN for all four script files with zero diagnostics. The named fixture/profile validator, IR and finite runtime returned RED because this new fixture ID, directory and opcodes are not supported by the current schema. The report classifies that result as `not-applicable`, preserves the exact CLI output, and does not treat it as CK3 evidence. The later real CK3 run is the evidence for runtime behavior.

## Preserved RED iterations

Earlier attempts are retained under their original temporary artifact roots. They exposed harness problems and were not rewritten as product evidence:

- `mrma_20260908_031615_7c356e9c`: boot timeout before the main menu.
- `mrma_20260908_032506_9e896d2e`: a `|` in the product display name collided with the launcher's inventory delimiter.
- `mrma_20260908_033344_38108852`: unrelated external diagnostics were over-attributed by context.
- `mrma_20260908_034604_9ffe8408`: same-date queue ordering and an illegal random AI government seed invalidated two assertions.
- `mrma_20260908_040024_f086aa57`: nine markers appeared, but the illegal AI seed still allowed a false positive and the visible event OCR timed out; not accepted.
- `mrma_20260908_042032_c479e847`: stricter checking correctly rejected another illegal special-government AI sample.

The final run instead selects an ordinary independent feudal AI. Its transition is legal, produces no relevant runtime diagnostic, and is then redirected by the product's common `on_government_change` path.

## Visual evidence

- Full acceptance event PNG: `cell/08_acceptance_summary_event_full.png`, 2560×1440, 4,948,867 bytes, SHA-256 `8eb4519fb1fd182f17d6a2f352806dbcd9c316d8fa71c958f7e7f4f341abc114`
- Final paused map PNG: `cell/09_final_map_paused.png`, 2560×1440, 5,284,680 bytes, SHA-256 `911df2b0aaed412eec7f1e9645d2138f7d0fb23b6eeb5ca5cb464ef767805f31`
- Tracked Workshop projections and intended upload order: [`../workshop/remove_mandala_screenshots.md`](../workshop/remove_mandala_screenshots.md)

## Honest boundary

The static contract binds the recurring dispatchers to `months = 1` and `yearly_global_pulse`; the live fixture invokes those exact dispatchers on accelerated dates instead of waiting a wall-clock in-game year. The run proves global-zero postconditions for its loaded 1066 world and a successful AI transition, not compatibility with every third-party mod that replaces the same keys. Seven non-English/non-Chinese language files are model-generated candidates reviewed for semantics and CK3 formatting, not native-speaker certification.

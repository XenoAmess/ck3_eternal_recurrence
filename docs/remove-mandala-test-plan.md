# Mandala Purge v1.0.0 Test Plan

## Acceptance target

Release a standalone CK3 `1.19.0.6` mod whose only game rule is enabled by default and whose enabled state guarantees:

1. every Mandala ruler is changed to Wanua at game start, after one day, and on a self-renewing monthly event loop;
2. every Temple Citadel holding is changed to a Castle at game start, after two days, and on the yearly global pulse;
3. every successful AI transition into Mandala is intercepted through `on_government_change` and redirected to Wanua;
4. disabling the rule prevents every product dispatcher and redirect;
5. the formal release is the exact 15-file allowlisted staging, never the development source tree.

## Test layers

| Layer | Check | Pass condition |
|---|---|---|
| L0 source | `py tools/validate_remove_mandala_static.py` | exact descriptor/rule text, one default-enabled rule, six hidden event bindings, global sweeps, AI transition hook, nine complete localization files, generated 640×640 thumbnail, UTF-8/BOM contracts |
| L0 builder unit | `py tools/test_build_remove_mandala_release.py` | eight release allowlist, manifest, ZIP, item-ID isolation, and cache-verifier tests pass |
| L0 reproducibility | `py tools/build_remove_mandala_release.py --check` | two independent builds have byte-identical manifest and ZIP |
| Offline preflight | `open_kaishek preflight` recorded by the live runner | record exact tool/game/corpus hashes; unsupported fixture/schema coverage is classified separately and does not masquerade as CK3 runtime evidence |
| L1 live | `tools/.venv/Scripts/python.exe tools/run_remove_mandala_acceptance.py` | isolated non-debug CK3 emits all nine required PASS/BEGIN/DONE markers, no FAIL marker, no product/fixture diagnostic, runtime/source trees unchanged, protected player storage unchanged |
| Visual | final acceptance event and Workshop projections | event title, summary, option and live CK3 map are legible; JPEGs are deterministic projections below 2 MB |
| Release | `py tools/build_remove_mandala_release.py --release` | clean exact `remove-mandala-v1.0.0` tag produces versioned 15-file staging/manifest/ZIP |
| Workshop | launcher upload plus subscribed-cache verification | a new item ID is used, live JPEGs are uploaded, public page is readable, and the fresh subscribed cache verifies 15/15 against the release manifest (allowing only launcher's terminal `remote_file_id`) |

## Live fixture sequence

The acceptance fixture is external to the product and never enters Workshop staging.

1. On `on_game_start_after_lobby`, assert the product's immediate sweeps leave zero Mandala rulers and zero Temple Citadels.
2. Seed the player as Mandala and seed a Castle as Temple Citadel.
3. After one day, assert the player is Wanua.
4. After the product's day-two queue drains, assert the holding is Castle.
5. Select an ordinary independent feudal AI ruler, perform a legal Mandala transition, then assert the product transition hook redirects that ruler to Wanua.
6. Reseed player/holding, invoke the exact monthly and yearly product dispatchers on accelerated fixture dates, and assert global zero counts after each.
7. Display a localized acceptance event and preserve full-screen PNG evidence.

## Failure policy

- Any `MRMA: TEST FAIL`, missing marker, relevant `error.log` diagnostic, changed runtime/source tree, or changed protected user data is RED.
- Harness and offline-tool limitations are preserved as separate RED evidence; they do not cancel a later distinct GREEN run and cannot be reported as product failures.
- Failed attempts and their artifacts are retained. A retry uses a new isolated userdir and artifact directory.

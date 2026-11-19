# Superman Qiang 1.2.1 Florin software candidate

machine_id: `desktop-3fevhd2-1c74096080`
Observed at UTC: `2026-11-19T07:05:20.567179+00:00`
Installed source: `C:/SteamLibrary/steamapps/common/Crusader Kings III/game`
CK3 1.21.0 / Steam build 26622941 / EXE SHA256 `2f2b236a16223891c2da8b167f5f3738d2ae3e6d69de1b4fbe190a5402998acc`.

This is an unpublished candidate for canonical Workshop item 3812991990.
No Game, Steam, native injection, tag creation, commit or push was performed.
Version 1.2.0 remains the historical public release.

The pinned `mpo_temujin_flavor.0030` definition preserves Florin's
`set_relation_rival_effect` and `set_relation_nemesis_effect` wrappers with
`TARGET` / `REASON`. The other ten selected definitions, ten inline helper
bodies and eight complete inline-name inventories remain unchanged.
All current full-source references and game identity bindings were refreshed.
The historical October source audit remains unchanged; current renderer tests
use the separate [Florin source audit](2026-11-19-florin-source-audit.json).
The health fixture's visible `sxat.2` now specifies `theme = realm`;
the existing monthly fixture's `sxanf.10` already had a theme.

| Actual check | Exit | Elapsed seconds |
| --- | ---: | ---: |
| Existing generator against installed source | 0 | 1.183 |
| Generated parity against installed source | 0 | 1.671 |
| Static validator against installed EXE/source | 0 | 3.426 |
| Runtime regression: 62 tests | 0 | 39.298 |
| Release/publication regression: 16 tests | 0 | 16.665 |
| Existing two-file mypy scope | 0 | 6.203 |
| Canonical-ID double build reproducibility | 0 | 3.487 |
| Generic Clausewitz parser: 23 product + 8 fixture scripts, concurrency 2 | 0 | 4.065 |

Static results: 35 runtime files, 33 generated outputs, nine languages with
25 keys each, zero validator errors. Mypy covered the complete
`test_runtime.py` and `prepare_live_fixture.py` using
`--follow-imports=silent --ignore-missing-imports --cache-dir nul`;
this is not whole-product strict typing.
Parser JAR SHA256:
`6ac143ebf03f3e1a041dff01b2d808e60de8e289d18cebf9855682f0a80b6d82`.
Generic parsing does not establish CK3 symbol, scope, eligibility or business
qualification.

Reproducible candidate manifest SHA256:
`abaab724f58b523d11969c3b6f456097c07d97e9600f2671fc4180cfaa054d3a`
Reproducible candidate ZIP SHA256:
`b9bc3dab623083262348e9c5dfdf9c1060e40f82de25c00aee834e5dc57be56b`

Actual command arrays, timings, stdout/stderr and source identities are retained
under `D:/ck3-state/upgrade-20261118/superman-florin-software-a01` in
`generation-results.json`, `software-results.json`, `static-validation.json`
and `parse-results.json`. These are machine-local software evidence, not a
tag-bound formal publication package.

Test TEMP/TMP/TMPDIR and Java temporary output used the task's D-drive root.
The admitted temporary increment was 16 MiB; the sampled output logical-byte
peak was 7720411 bytes. No foreign assets were
deleted. Test-created temporary directories were closed by their own fixtures.

Florin live acceptance is **NOT_RUN**. Clinical, forced-pregnancy, twin,
pilgrimage and Mongol narrative branch gaps remain, as does the unresolved
repeated-notification issue. Earlier CK3 1.20 live results are historical.
The legacy six-skill random matrix and 1.20 Native launcher are not qualified.
Real paired/anonymous entry, seven-attribute behavior, monthly callback,
ordinary UI and independent cold-save checks remain for the current engine.

At 2026-11-19T08:20:30Z on the same machine, the existing health fixture's
`sxat.4` gained a visible realm completion window and an empty close option.
The complete 52362-byte verify body remains byte-identical, as do the other
three events, 20-case contract and schedule. An actual CLI producer regression
reproduced the old hidden completion failure and passed after the change;
generation, changed-test-file mypy, all 33 production output parity checks
and one changed-event generic parse exited 0. Only fixture presentation changed.
The actual completion pause and physical before/after SAVE checks remain NOT_RUN.
See the [source-pinned follow-up evidence](../../docs/maintenance/evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/superman-florin-health-done-software.json).

The log verifier truncated the two existing floor case IDs containing underscores.
It now preserves those complete IDs and returns a typed log report. An actual
producer-manifest-to-verifier CLI regression reproduced the failure before the
fix, then passed together with the existing health producer regression; duplicate
PASS, FAIL, missing and unexpected markers remain rejected. The two modified
files passed their existing mypy scope. Producer and all 20 case-data bytes stayed
unchanged. These synthetic-log software checks grant no Game or SAVE credit.
See the [regression receipt](../../docs/maintenance/evidence/2026-11-18-ck3-1210-desktop-3fevhd2-1c74096080/superman-florin-health-log-parser-regression.json).

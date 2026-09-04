# Promotion source production capture: latest-native no-launch refreeze (`a01f8cb`)

## Result

The B7 promotion-source production capture candidate is refrozen against
canonical `a01f8cb684d39e2ea8e95fbf0f20f170b6f1a396` and is
`READY_TO_SERIAL_LIVE`. This work did not start CK3, create a checkpoint,
advertise a production provider, or treat an ACK as a business result.

The repository manifest is a compact schema-2 overlay:

`ck3_autonomous_player/native_bridge/research/fixtures/zhongguo_promotion_source_capture_no_launch_candidate_a01f8cb_20260904.json`

It extends the immutable `366f30f` manifest only after checking that file's
exact SHA-256. The verifier then hydrates the old full contract, replaces the
five drifted per-file fingerprints, and checks the complete native aggregate
fingerprint and count. This preserves the old freeze's strictness; no source
fingerprint or readiness gate was weakened.

## Why the old candidate is superseded

The original manifest has SHA-256
`4268B6D147D234536A03A98EC1F7A5E08DAAA7246DFF340B51FD42E2E94A8F98`.
On `a01f8cb`, its verifier returns RED with exactly two failed checks:

- `frozen_source_files_match`;
- `native_source_fingerprint_matches`.

The five explicitly frozen files that drifted are `CMakeLists.txt`,
`bridge.cpp`, `ck3_11906_adapter.cpp`, `game_adapter.cpp`, and managed
`native_driver.py`. The native aggregate also grew from 295 to 298 files due
to the default-off actual-truce-expiry implementation. The old candidate,
binary pair, live-attempt path and command are revoked but retained as
append-only evidence.

## Fresh default build

The replacement was built from the exact `a01f8cb` source with MSVC and Ninja
in a fresh Release directory. A repeat build reported `ninja: no work to do`,
and Visual Studio CTest passed **94/94**. The cache independently records these
private candidates as OFF, including:

- `XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1=OFF`;
- `XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=OFF`;
- `XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1=OFF`.

The complete native source inventory is 298 files with aggregate SHA-256
`F37A113C77B7293857D813222B19E6FF3EA4DE8E61A097FFEA753C70F2651433`.

## Frozen external evidence

External root:

`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-a01f8cb-20260904T085119Z`

| File | Bytes | SHA-256 |
|---|---:|---|
| `xar_ck3_bridge.dll` | 2,425,856 | `CD152F935228F53CA9A51A5DB952D3DBF81A24C7ECFB6E6E14644931CDB4D138` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `372EDF62B8537F7B4C0E4C21603F707389974A431B70DB08B8CE9F93E5C7D296` |
| `CMakeCache.txt` | 19,888 | `1AC17D725987CB8802CC78BB369686656A242686D6088D78CBB6394DF2BD183B` |
| `frozen-candidate-manifest.json` | 5,807 | `CE33DAB589FF02EBABCE7928233935B41E6D0EEE8C68E27BF4F6AC8697DA6A30` |
| `no-launch-preflight.json` | 7,849 | `405E5950D18D4AF0C39E6B7BC1E246DE6468C46D3A49A3A38FF153965FB0043F` |
| `no-launch-preflight-red-existing-ck3-pid21388.json` | 7,857 | `30DC2C2F87471F1D27211E442782F1BAEC5EDA7B20E3D707043157E6C3B2E0F9` |

The first formal no-launch verifier call correctly returned RED while another
serial work package owned CK3 PID 21388; that report was retained and the
process was not touched. After the owner released the gate, the same immutable
candidate returned `READY_TO_SERIAL_LIVE` with every check GREEN, no `ck3.exe`
or injector process, and the reserved live-attempt path absent. The production
query/action remain unadvertised transport-only fail-closed seams. The
player-only gates, real paused `zg361pp.146` option 1 to D+1 `zg361pp.147`
choreography, schema-2 capture, and ACK-not-result boundary remain byte-pinned.

The refresh verifier tests pass 7/7 and the historical verifier tests pass 5/5.
The five choreography tests, five checkpoint-capture tests, four runner tests
and four managed contract tests also pass. Two stale choreography assertions
left behind when `d53befa` added the real production entry were updated to
assert the already-integrated default-off runner path; no product code changed.

## Effect boundary

No effect content changed. The preflight re-counted all relevant shards:

| Purpose family | Files | Effects | Per-file range | Aggregate SHA-256 |
|---|---:|---:|---:|---|
| feedback / promotion / PIP | 39 | 275 | 1-10 | `94042BE37F3950D21F8B6AB39F9E1206B431A90CB9ACB51A6D9E814693B8CB4A` |
| compensation / LTI | 25 | 148 | 3-9 | `9F7041818149A0F532CE1A6C217C77240F2C17019D63B3D0FD087619CBC29B5C` |

Both families meet the requested 1-10 target and the 20-effect hard principle;
there is no exception requiring live evidence.

## Single authorized future command

Only the following runner-owned command is frozen for the future CK3 serial
gate. It has not been executed:

```powershell
& "Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\run_zhongguo_acceptance.py" "--artifacts-dir" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-live-attempt-a01f8cb-20260904T085119Z" "--phase2-promotion-source-checkpoint-live" "--phase2-promotion-source-checkpoint-timeout-seconds" "600" "--bridge-dll" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-a01f8cb-20260904T085119Z\xar_ck3_bridge.dll" "--bridge-injector" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-a01f8cb-20260904T085119Z\xar_ck3_bridge_injector.exe" "--bridge-pipe" "\\.\pipe\xar_ck3_bridge_zg361_38d097690e12445f810d29a20e8dcf81" "--phase2-seed-contract" "Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\zg361_phase2_seed_contract.json"
```

The candidate remains `static-ready-live-pending`; only a real paused
production snapshot, saved game and reviewed schema-2 artifact may change that
status.

# Promotion source capture: final cleanup-dispatch-aware no-launch freeze (`7d50c2d`)

> Superseded on 2026-09-04 by the product/native dual-build freeze at
> `1c69658`. This historical candidate is now honestly RED: canonical product
> source, native descriptor source, and the formal runner advanced. Its own
> source fingerprints were not refreshed or weakened; use
> `zhongguo-promotion-source-product-native-freeze-1c69658-2026-09-04.md`.

## Result and boundary

The B7 promotion-source candidate is refrozen on
`7d50c2d3b739221e216c5158a04b6d18bf6b3587`, directly above canonical private
G2 cleanup dispatch commit `ff89dcdbefb9d8fc86ce4722df847946e96d0e81`.
The formal no-launch result is `READY_TO_SERIAL_LIVE`. This package did not
start CK3, create a checkpoint, advertise the production provider, or accept an
ACK as promotion/compensation evidence.

The schema-3 manifest extends the immutable `a01f8cb` manifest only after
checking its exact SHA-256
`CE33DAB589FF02EBABCE7928233935B41E6D0EEE8C68E27BF4F6AC8697DA6A30`.
The previous candidate now returns RED on exactly
`frozen_source_files_match` and `native_source_fingerprint_matches`. Its five
explicit drifts are `CMakeLists.txt`, `bridge.cpp`, `ck3_11906_adapter.cpp`,
`game_adapter.cpp`, and managed `native_driver.py`. The final verifier hydrates
the complete prior contract, replaces those exact fingerprints, and checks the
full 298-file aggregate fingerprint
`EF9FF55AC41E231EAD78049E412A66A0AACAC85A9814BE16B25DFB23A052CCF1`.
No fingerprint check was removed or weakened.

## Fresh build and CTest

The first configuration attempt selected Cygwin Ninja from ambient PATH and
failed before compiling source. The replacement fresh directory explicitly
used Visual Studio's Ninja with MSVC Release defaults. Its first CTest pass
also correctly exposed that the new worktree lacked the gitignored, read-only
CK3 reference directory: 86/94 tests passed. Adding a directory junction to the
canonical reference tree reduced this to one real source-contract failure.

The cleanup query branch had been inserted between the original war-termination
options and actual-expiry branches, so the old test's substring included two
extra `PublishSnapshot` calls. Commit `7d50c2d` minimally teaches the test to
stop at whichever adjacent branch begins first; all original ordering and
exact-count assertions remain. The final fresh CTest result is **94/94 GREEN**.

The Release cache independently records all adjacent private candidates OFF:

- `XAR_CK3_ENABLE_G2_ACTUAL_TRUCE_EXPIRY_CANDIDATE_V1=OFF`;
- `XAR_CK3_ENABLE_G2_WAR_BOUND_LOSS_CANDIDATE_V1=OFF`;
- `XAR_CK3_ENABLE_ZHONGGUO_PROJECTS_METRICS_CANDIDATE_V1=OFF`;
- `XAR_CK3_ENABLE_ZHONGGUO_CAREER_HC_WORKFORCE_CANDIDATE_V1=OFF`.

## Frozen external evidence

Root:

`Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-ff89dcd-20260904T095918Z`

| File | Bytes | SHA-256 |
|---|---:|---|
| `xar_ck3_bridge.dll` | 2,425,856 | `BC7E4CDAB5F8ED8ACF1C6D8C3E64C28DEC6355C4CC039609A254F847B5A67B7B` |
| `xar_ck3_bridge_injector.exe` | 39,936 | `D4C3E0315F256AE91AA215EC2285845D23E465D17D06AAF9D768C62E9FF92429` |
| `CMakeCache.txt` | 19,916 | `3FCA92EA6F70086808D7C3F01329480BA158602A95AE50297A57A7D504DD7A52` |
| `native-ctest.txt` | 18,765 | `B3F5BF2E26882534BF65000E00146D849254B43C0F1ED29816AD390318485963` |
| `frozen-candidate-manifest.json` | 6,953 | `E778470FF5733E0E5A737F192B82B1B29F52DF2CBBAB5BA7D0BE46C40B13AE5A` |
| `no-launch-preflight.json` | 8,291 | `B3EB71FED20C38847EB17EA76326C181B65E7E44E5B5170F836907ED23E41803` |

The preflight checks the exact binary pair, cache, CTest log, old-manifest
supersession, complete native aggregate, player-only gates, product
choreography, command vector, seed, and absent live-attempt path. It observed
zero `ck3.exe` and injector processes.

## Effect-file boundary

No effect content changed. Formal preflight re-counted 39
feedback/promotion/PIP shards containing 275 effects at 1-10 per file, and 25
compensation/LTI shards containing 148 effects at 3-9 per file. Both remain
inside the requested 1-10 target and the 20-effect principle; there is no
exception.

## Single authorized future command

This runner-owned command is the only command frozen for a future CK3 serial
gate. It has not been executed:

```powershell
& "Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\.venv\Scripts\python.exe" "Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\run_zhongguo_acceptance.py" "--artifacts-dir" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-live-attempt-7d50c2d-20260904T095918Z" "--phase2-promotion-source-checkpoint-live" "--phase2-promotion-source-checkpoint-timeout-seconds" "600" "--bridge-dll" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-ff89dcd-20260904T095918Z\xar_ck3_bridge.dll" "--bridge-injector" "Z:\ck3_mod_rewrite_process_assets\zg361\promotion-source-production-capture-candidate-ff89dcd-20260904T095918Z\xar_ck3_bridge_injector.exe" "--bridge-pipe" "\\.\pipe\xar_ck3_bridge_zg361_d1c5a4e578b043a88a0d9e2b6cf77134" "--phase2-seed-contract" "Z:\ck3_mod_rewrite\_root-promo-split-20260902\tools\zg361_phase2_seed_contract.json"
```

The honest status remains `static-ready-live-pending` until a real paused
`zg361pp.147` snapshot, saved game and reviewed schema-2 artifact exist.

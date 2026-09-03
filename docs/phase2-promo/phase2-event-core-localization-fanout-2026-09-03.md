# Phase 2 event-core localization fan-out audit (2026-09-03)

## Scope and verdict

This note records the offline, hash-bound fan-out prepared for the next
event-core startup round.  It covers the B1, B2, incident-platform, manager,
and workforce owners, and records the central localization/ABI boundary.  No
canonical source tree or freeze was edited by this audit, and the generator
does not start CK3.  The formal reports cited below are retained evidence from
separate startup attempts; they are not a release or Workshop manifest.

“Complete” below means that the selected projection has a complete localization
matrix.  It does not mean that the full Phase 2 feature set is production-live
or that CK3 reached Frontend.

The machine-readable artifact is
[`phase2-localization-fanout-manifest-2026-09-03.json`](phase2-localization-fanout-manifest-2026-09-03.json).
Its `authority.rows` and `comparison.rows` arrays are the authoritative full
file lists: every row contains the relative path, byte count, and SHA-256 of
the raw file.  The artifact also retains the 51/66/81/162-file inputs, all
added/removed/changed paths, owner and language totals, and report hashes.

## Hash and runner authority

The 51-file control remains byte-authoritative at the formal current-bridge
overlay, not at a reconstructed Git checkout:

```text
overlay:
Z:\ck3_mod_rewrite\_runtime\formal-phase2-legacy51-currentbridge-20260903\profile\mod-content\zhongguo_361
files / bytes: 51 / 7,137,587
product_tree.tree_sha256: 84e36658728e57b43005300c6e51e398edb6420e3c43dd2f42762c491bc9e36a
bootstrap.tree_sha256.product: ddac4703d99b7e498e276c37c685af28b2006ad73f4124f9cd77e745aa14a693
```

The historical commit is lineage only.  The overlay contains byte differences
from that checkout, so it must not be substituted when reproducing a run.

The projection utility uses three independent digests:

* `source_tree_sha256`: the sorted `path -> {size, sha256}` map used before
  materialization;
* `formal_overlay_tree_sha256`: the sorted list of `{path, bytes, sha256}`
  rows recorded in a formal product tree;
* `file_list_sha256`: the sorted relative-path list.

Generate the tracked audit artifact (read-only with respect to product trees):

```powershell
py tools/generate_phase2_localization_fanout_manifest.py
```

For a fresh serial CK3 attempt, pass a matching source and manifest pair to the
existing runner.  The command below shows the exact Phase 2 options; retain the
other pinned bridge/fixture arguments from the normal runbook and use a fresh
attempt directory:

```powershell
py tools/run_zg361_phase2_seed_capture.py `
  ...pinned runner arguments... `
  --product-source "Z:\ck3_mod_rewrite\_runtime\phase2-bisect-source-direct-union-v2-20260903\mod_zhongguo_style" `
  --product-projection event-core-locfanout `
  --product-projection-manifest "Z:\ck3_mod_rewrite\_runtime\phase2-event-loc-manifests-20260903\projection-event-core-locfanout-201.json"
```

The all-language comparison can be replayed only with its own pair:

```powershell
--product-source "Z:\ck3_mod_rewrite\_runtime\phase2-event-locfull-clean-20260903\mod_zhongguo_style" `
--product-projection event-core-locfull `
--product-projection-manifest "Z:\ck3_mod_rewrite\_runtime\phase2-event-loc-manifests-20260903\projection-event-core-locfull-261.json"
```

Never mix a manifest with another source root.  The runner and projection
utility reject the resulting byte/tree mismatch before the CK3 launch gate.
Only one CK3 launch may run at a time; manifest generation and report review
remain safe to do offline.

## Candidate inventory and exact tree identities

| candidate | source root | rows / bytes | localization rows / bytes | source-tree SHA | product-tree SHA | file-list SHA | observed runtime boundary |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| event-core baseline (81) | `Z:\ck3_mod_rewrite\_runtime\phase2-event-clean-20260903\mod_zhongguo_style` | 81 / 14,802,010 | 18 / 2,793,969 | `f25fe00faccc891f9a8a802ba39c14d29a92babf6283d6eb9decffa5268853db` | `2ed2f8fbde21c55e5bdef1dd54e7e21debcba934e231678c44b31952a527ec74` | `d17eed4595f692fe2fe01659b4e0231ecc939364bccac4dbc216cf1937c4e1c6` | `formal-phase2-event-core-20260903`: 323 unrecognized-loc lines, `Total of : 881`, timeout, Frontend not observed |
| event-locaug intermediate (162) | `Z:\ck3_mod_rewrite\_runtime\phase2-event-locaug-clean-20260903\mod_zhongguo_style` | 162 / 15,060,079 | 99 / 3,052,038 | `285ae4f6f13f9972f692cea5ae23607560b4324d8ac08a4283ba6d2b9af214cd` | `d6229717cec58c6244bd1e838a3d9c4536bdbe72bd7b6faffcb74e0377841383` | `1cdcb0149ee9449c67a1ada44aca68e54a197aee129743f5d8c71a686357f294` | `formal-phase2-event-locaug-20260903`: 68 unrecognized-loc lines, `Total of : 881`, timeout, Frontend not observed |
| **direct-union-v2 fan-out (201)** | `Z:\ck3_mod_rewrite\_runtime\phase2-bisect-source-direct-union-v2-20260903\mod_zhongguo_style` | **201 / 15,245,061** | **135 / 3,224,382** | `97f9c0f82ce7f5e8712ac21db8879b521c6828bd6c95cd5bb37fa80c4e7c5602` | `4913ebb63e073ad5df114e94e92c8bd19dec409eb740d544bc4158765732dfbe` | `821bb490ed6cbc2449f05cb82d58cabbd20d26d67ec17e7df8f8b0a08e750103` | static authority; its current formal report stopped at the launch boundary and has no Frontend claim |
| **all-language locfull (261)** | `Z:\ck3_mod_rewrite\_runtime\phase2-event-locfull-clean-20260903\mod_zhongguo_style` | **261 / 15,924,897** | **198 / 3,916,856** | `0a5a6c423309ddd5b87f1fec287f87a544f24af53725f66143b03f8ea5e27ac9` | `242246e79a56c9da7a43d224c9c65d8472c41b4d922388c632b689aca6284a00` | `33cc2896263c3683a92fb80f4a0d49045fce157b178957572164c9f80d230f1f` | `formal-phase2-event-locfull-20260903`: error.log 0 lines, `Total of : 881`, timeout, Frontend/history not observed |

The external projection-manifest file hashes are also recorded in the tracked
JSON (`manifest_identities`):

```text
projection-event-core-locfanout-201.json  c60f2c9373cdd2e6a2133980b9c878d81223902e4d848b0c3c6142acc4c52d38
projection-event-core-locfull-261.json    55f6b8611f881d9c407c9e60663a1dbdc01da71f11f106bed0219038ee8603f6
```

## The 201-file fan-out

The 201 rows are exactly 2 root files, 40 `common` files, 16 event files, 4
gfx files, 4 GUI files, and 135 localization files.  The category totals are:

| category | files | bytes |
| --- | ---: | ---: |
| `common` (effects, triggers, values, decisions, workforce positions, etc.) | 40 | 9,076,083 |
| `events` | 16 | 723,366 |
| `gfx` | 4 | 814,936 |
| `gui` | 4 | 706,441 |
| `localization` | 135 | 3,224,382 |
| root (`descriptor.mod`, `thumbnail.png`) | 2 | 699,853 |
| **total** | **201** | **15,245,061** |

The localization matrix is 15 owner families × 9 languages.  Owner totals
(the full per-language path/byte/SHA rows are in the JSON) are:

| owner family | files | bytes |
| --- | ---: | ---: |
| `zg361` (base) | 9 | 208,174 |
| `zg361_mechanisms` | 9 | 2,585,795 |
| `zg361_b1` | 9 | 66,461 |
| `zg361_b2` | 9 | 29,553 |
| `zg361_incident_platform` | 9 | 69,333 |
| `zg361_manager_governance` | 9 | 14,156 |
| nine `zg361_workforce_*_fact/endgame` families | 81 | 250,910 |
| **total** | **135** | **3,224,382** |

The requested B1+B2+incident+manager+workforce localization subset is 117
files / 430,413 bytes.  Its 9-language deterministic digest is
`eafd73c8630ae169f78ad190245109d92371d6b8f233ac2c432379fb8f4a4dc4`.

The central shared callable files that are actually present in this projection
include these exact rows:

```text
common/scripted_effects/zg361_case_kernel_effects.txt       172748  8453d36be33c4c17447a13b0312251ef276f0918fe0153dbede1509a5d7a9b20
common/scripted_triggers/zg361_case_kernel_triggers.txt       2939  95ad268dedd7045ab45645c54272c96b62eeff17ffdb82a461622d8dd3e47a6a
common/scripted_effects/zg361_effects.txt                    50219  5cb03f9c75d9a31c889d246516a21e20b89cbd33fe8666fdea7ff634d7092342
common/scripted_effects/zg361_generated_mechanism_effects.txt 1019397 9e0479b33b322c3d51921180b5a4c34adc13bb9cea9f0f7a70d577a945edd052
common/scripted_triggers/zg361_manager_governance_runtime_triggers.txt 55260 eb2a522d12e72fc83a4a1566ee35a74153cf6a8238e001ba7a94aab78d56520c
```

The 201 projection does **not** contain the phase-2-central executable owners:

```text
common/scripted_effects/zg361_phase2_central_runtime_effects.txt   126811  94d893631fcf1c6fdf25f19d536c99664112e6c16ac39bfc2d4edc36c13b3ceb
common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt  16712  ee8d962f5a9aa95ae68098b96ffe26e1b2da2435821617bd51e75fe0fec377d7
events/zg361_phase2_central_runtime_events.txt                      12440  bfdc761091da43d1950ffdd29ee727b3f049cd0a0a1f7dbcfda5be7511cd1859
```

It does contain the central localization family only indirectly: the nine
`zg361_phase2_central_l_<language>.yml` files are absent from 201 and present
in 261 (9 files / 6,588 bytes).  Therefore “201 complete fan-out” must not be
read as “phase2-central code closure”.  If a later A/B names one of the three
central code owners, add it to a new disposable projection and generate a new
manifest; do not mutate this authority or the canonical source.

## 201 versus 261: exact localization delta

The 261 candidate has all 22 owner families × 9 languages and its 198
localization rows are byte-for-byte equal to the current canonical localization
tree (3,916,856 bytes).  Relative to 201 it adds 63 files / 685,315 bytes:

| added owner family (each is 9 language files) | files | bytes |
| --- | ---: | ---: |
| `zg361_career_hc` | 9 | 154,120 |
| `zg361_career_learning` | 9 | 52,215 |
| `zg361_compensation_runtime` | 9 | 52,172 |
| `zg361_credit_project` | 9 | 87,048 |
| `zg361_feedback_promotion_pip` | 9 | 220,770 |
| `zg361_phase2_central` | 9 | 6,588 |
| `zg361_phase3_metrics_delivery` | 9 | 112,402 |
| **total added** | **63** | **685,315** |

Nine shared base files also differ: every `localization/<language>/zg361_l_*`
row in 201 is an older/stale byte set.  The all-language candidate is larger
by 7,159 bytes across those nine rows.  The complete old→new path/size/SHA
pairs are in `fanout_delta.authority_to_full_localization.changed` and the
row arrays; the aggregate is:

```text
shared base localization delta (261 - 201): +7,159 bytes, 9/9 SHA changes
```

Conversely, 261 is not a strict superset of the 201 runtime code.  It omits
these three 201-only rows (12,638 bytes):

```text
common/court_positions/types/zg361_workforce_appointment_fact_court_positions.txt  3213  b7e5d455da319c9f1587fd6928c69fbe51cc22916fbe40c241851d715d9261bd
common/court_positions/types/zg361_workforce_exit_fact_court_positions.txt         2998  ae7ddf10df3cc36a4f8ef531f26703c9025d956007be94f844d895ec80e8606c
common/script_values/zg361_incident_platform_runtime_values.txt                    6427  692d8693477669266f49a9cac0f0705e2a94577647c2c97cacea6fe4f3c4184d
```

Consequently, the total 261−201 payload difference is **+679,836 bytes**:
`+685,315` added localization, `+7,159` shared-base refresh, and `−12,638`
201-only code.  A hypothetical 264-file union would be a new, untested
projection and is not silently implied by this note.

## Intermediate fan-out accounting

For context, the 81-file event-core baseline has only base and mechanisms
localization (18 files).  The 162-file locaug adds the nine workforce owner
families (99 localization rows total), but still lacks B1, B2, incident, and
manager localization.  Relative to the 261 all-language rows:

```text
81  -> missing 180 localization files / 1,115,728 bytes
162 -> missing  99 localization files /   864,818 bytes
201 -> missing  63 localization files /   692,474 bytes
```

The 201 missing-byte figure is relative to the current canonical/full rows and
therefore includes the 7,159-byte stale-base difference.  Relative to the 261
candidate alone, the missing localization files are 63 / 685,315 bytes.

## What the runtime evidence does and does not prove

The progression is useful but not a green startup result:

* 81 files: 323 unrecognized dynamic-description localization lines, then
  `Total of : 881`; timeout before Frontend.
* 162 files: 68 such lines, then `Total of : 881`; timeout before Frontend.
* 261 files: error.log is empty and the same `Total of : 881` marker is
  reached, but the run still timed out before Frontend/history completion.
* The current 201 v2 report is incomplete at the launch-call boundary, so its
  manifest is a static byte authority, not a claim of zero runtime errors or
  Frontend.

Thus the localization fan-out fixed the observed missing-loc error class in the
261 attempt, but it did **not** fix the load bottleneck.  `Total of : 881` is a
diagnostic marker, not a readiness signal.  Until a fresh run observes the
Frontend/history completion contract and exits cleanly, this line remains RED
and no production-live or gameplay conclusion may be drawn.  No gameplay,
save, store, purchase, or payment action is part of this audit.

## Reproduction and review checklist

1. Verify the tracked JSON's SHA and the two external manifest SHA values above.
2. Materialize a fresh disposable root with the exact source/manifest pair; do
   not copy from the canonical tree by hand.
3. Run one CK3 attempt at a time, preserving timeout and error artifacts even
   when the result is RED.
4. Compare the resulting product-tree hash against the manifest before reading
   runtime conclusions.
5. If central code is added, record it as a new named projection and rerun the
   static row/hash audit; leave this 201/261 comparison immutable.


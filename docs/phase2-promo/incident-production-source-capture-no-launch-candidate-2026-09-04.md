# Incident production source capture: no-launch candidate (2026-09-04)

This package freezes the current Incident source-capture seam from canonical
`5c54014c7317bd2446bd342d7205cf00fe024dc9`.  The production choreography
(`baaf048`) and formal read-only capture entry (`55c23da`) are both ancestors.
The machine-readable artifact index is
`incident-production-source-capture-no-launch-candidate-5c54014-2026-09-04.json`.

## Outcome and honest boundary

The no-launch preflight is GREEN, but the live gate is **not ready**.  The
freshest hash-compatible real seed is the r20 checkpoint, 57,377,533 bytes,
SHA-256
`96D1919D569E6F3EA115BF21882B0F4372246812B1E1F630F3AED44968D49335`,
at exact `date_raw=53147016`, paused and map-ready as player `29037`.  Its
provider evidence observes owner `32904`, subject `29037`,
`result_grade=1`, and `absolute_grade=1`.  Product event/localization
semantics map grade value `1` to the 3.25 band.  This is a real inherited
product result; this candidate writes no grade and does not manufacture 3.25.

That same seed is nevertheless **after delivery**, not the required
pre-option source frame.  The bootstrap waits for
`zg361_result_case_state=3` and the matching settlement receipt before it
offers its final seed card.  In contrast, `zg361.50` requires case state `1`
and an unselected player-facing option.  Reopening that historical event or
rewriting the grade would fabricate the source and is forbidden.

The capture entry adds no hidden choreography: it polls snapshots for at most
300 seconds, captures only an already-visible exact `zg361.50`, and otherwise
ends with typed RED `real_zg361_50_wait_timeout`; it never resumes the map or
selects an option.  Therefore the exact live command below is frozen for
handoff but marked `blocked_do_not_execute`.  It becomes eligible only after a
real product-only save is frozen while the target event is still visible and
unselected.

## Exact no-launch verification

The following command was run from the isolated candidate worktree.  Its only
temporary accommodation was a read-only directory junction to the ignored
CK3 installation; that junction was removed immediately after the command.
It returned `ZHONGGUO 361 ACCEPTANCE PREFLIGHT: GREEN`, exit code 0, with zero
`ck3.exe` processes before and after.

```powershell
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'tools\run_zhongguo_acceptance.py' --preflight --phase2-incident-source-checkpoint-capture --phase2-frontend-first-load-save-name autosave --phase2-frontend-first-timeout-seconds 180 --bridge-dll 'Z:\ck3_mod_rewrite\_runtime\bridge-rbx-rel-0903\xar_ck3_bridge.dll' --bridge-injector 'Z:\ck3_mod_rewrite\_runtime\bridge-rbx-rel-0903\xar_ck3_bridge_injector.exe' --bridge-pipe '\\.\pipe\xar_ck3_bridge_zg361_d7d331c972c44e0697968583385f0ed1' --phase2-seed-contract 'Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r20-20260904-121400\artifacts-live\candidate\zg361_phase2_seed_contract.candidate.json' --phase2-product-source 'Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-entry-production-closure-20260904-r10-final\product' --phase2-product-projection 'phase2-seed-entry-production-closure-20260904-r10' --phase2-product-projection-manifest 'Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-entry-production-closure-20260904-r10-final\projection.json'
```

The matched r10 projection has source-tree SHA-256
`FC4218469CE72EA1BCA4E5BC0E5FA668E644EC05DEA537E38EBDA607AE72DC8F`,
252 files, and no runtime fixture mount.  The exact CK3 1.19.0.6 executable,
bridge, injector, seed contract, checkpoint, source report, evidence index,
provider probes, and projection manifest are byte/hash pinned in the artifact
index.

## Exact CK3 command (frozen, do not execute yet)

```powershell
& 'Z:\ck3_mod_rewrite\tools\.venv\Scripts\python.exe' 'Z:\ck3_mod_rewrite\tools\run_zhongguo_acceptance.py' --artifacts-dir 'Z:\ck3_mod_rewrite_process_assets\zg361\incident-production-source-capture-5c54014-20260904T081913Z' --phase2-incident-source-checkpoint-capture --phase2-frontend-first-load-save-name autosave --phase2-frontend-first-timeout-seconds 180 --bridge-dll 'Z:\ck3_mod_rewrite\_runtime\bridge-rbx-rel-0903\xar_ck3_bridge.dll' --bridge-injector 'Z:\ck3_mod_rewrite\_runtime\bridge-rbx-rel-0903\xar_ck3_bridge_injector.exe' --bridge-pipe '\\.\pipe\xar_ck3_bridge_zg361_d7d331c972c44e0697968583385f0ed1' --phase2-seed-contract 'Z:\ck3_mod_rewrite_process_assets\zg361\phase2-b2-r20-20260904-121400\artifacts-live\candidate\zg361_phase2_seed_contract.candidate.json' --phase2-product-source 'Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-entry-production-closure-20260904-r10-final\product' --phase2-product-projection 'phase2-seed-entry-production-closure-20260904-r10' --phase2-product-projection-manifest 'Z:\ck3_mod_rewrite_process_assets\zg361\phase2-seed-entry-production-closure-20260904-r10-final\projection.json'
```

The reserved attempt directory is absent.  A successful eligible run must
produce the capture report, frozen `.ck3` bytes, strict receipt, schema-2
registry entry, report, and evidence index.  Neither transport ACK nor static
preflight is result evidence.

## Effect-file boundary audit

This candidate changes zero production effect files.  In its selected
seed-compatible product projection, all 11
`zg361_incident_platform_*_effects.txt` purpose shards contain 1–10 top-level
effects; the maximum is 10 and there is no over-20 exception.  At canonical
`5c54014`, the expanded Incident family has 27 purpose shards: 25 are within
the 1–10 target, while the two Z apply shards contain 11 and 12 effects.
Both remain below the hard principle maximum of 20; no Incident file exceeds
20 and no exception is claimed.

This is deliberately an Incident-family statement.  The historical product
projection still contains inherited non-Incident/pre-B2 monoliths; this
no-production-change capture package neither reclassifies those files nor
claims them as compliant.

## Required next checkpoint

The missing input is one real, product-only save paused on exact `zg361.50`
before selection, with player = root = subject `29037`, distinct saved notice
owner `32904`, option 1 shown/enabled, and provider/UI identity on the same
frame.  Its bytes, SHA-256, date, seed lineage, and capture lineage must all be
recorded.  Until that input exists, readiness remains
`static-ready-live-pending`; there is no source checkpoint or schema-2 entry
to merge.

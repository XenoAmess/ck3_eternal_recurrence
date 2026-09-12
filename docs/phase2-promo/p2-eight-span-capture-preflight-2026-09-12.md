# T0 P2 eight-span capture preflight

Status time: 2026-09-12 14:30 Asia/Shanghai.

## Admission result

T0 P1 remains `GREEN / 9 of 9`. The canonical Phase2 source registry is
`GREEN / 4 of 4`; its SHA-256 is
`4C6A9346F32194E7EF26BFCD79289D207E1C6DE7356ED4E7C61930E1FE75AAB3`.
Raw footage is still `0/8`, shared media intake is pending, and neither final
cut has entered source review.

The fresh media-environment receipt is:

- path: `Z:\ck3_mod_rewrite_process_assets\zg361\promo\media-preflight-20260912T062032Z.json`;
- SHA-256: `59847507FE4B4C8CDB17B4BF5DD8DEFA6977100F8D9EB758649D35A71E62BC5C`;
- result: `GREEN`;
- expiry: `2026-09-13T06:20:36+00:00`;
- promo tool: clean `origin/main` at
  `adb52f4404d21072f13762dc4e674e75e2c63a9b`;
- verified media programs: FFmpeg/ffprobe 8.1.1, byte-bound by the receipt.

Its `final_promo_readiness` remains typed `RED` only for
`footage_pending,publish_target_pending`. This is the expected stage boundary:
the receipt proves the environment and does not claim footage, a candidate,
review, export, or publication.

The latest no-launch capture plan is:

- path: `Z:\ck3_mod_rewrite\_runtime\p2-capture-plan-20260912T062945Z\capture-plan.json`;
- SHA-256: `825875058C5805A2C76165D3B9224317AAFEDF85F0DABF74F161216A03E84824`;
- source commit: `502020bfbb1309a5bbfe6359365c4df91e3caf7a`;
- result: `GREEN`, blockers `[]`;
- execution attestation: CK3, FFmpeg, capture directory and media were not
  started or created.

The plan binds the exact seed contract, completion-observer receipt, schema-3
four-source registry, current product projection, bridge DLL/injector and all
eight canonical handlers. A fresh execution plan must be generated after this
documentation transaction so its source commit equals the final synchronized
root HEAD.

## CK3 round allocation

Current round R508 is terminated. Old round R507 is terminated, and the R506
harness RED remains preserved and closed by the later same-process R508 result.
There is no live CK3 instance and no unexplained RED.

The capture lifecycle can start one initial process and perform six managed
checkpoint restores. Round labels are allocated in launch order:

| Launch | Round | Reason |
|---:|---|---|
| 1 | R509 | initial managed seed and loader session |
| 2 | R510 | restore Promotion/Compensation registered source |
| 3 | R511 | restore Projects/Metrics registered source |
| 4 | R512 | restore Incidents/Operations registered source |
| 5 | R513 | restore Cross-cycle/Endgame registered source |
| 6 | R514 | Cross-cycle/Endgame exact-result transition restore 1 |
| 7 | R515 | Cross-cycle/Endgame exact-result transition restore 2 |

Every restore must terminate the old PID before the new PID becomes the sole
CK3 instance. The runner's PID lineage, connection-generation lineage and
restart-shutdown receipts are the actual launch authority. If the run stops
early, only rounds whose PIDs actually started are consumed; later rows remain
unused. The final capture report must map each observed PID/generation to the
corresponding round and record its cleanup.

All planned rounds use CK3 `1.19.0.6`, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
bridge DLL SHA-256
`65C14FE284EA99036DBFBA950B3BE38C3656FA2D064017FD8A38FF21B32B61EF`,
and the single capture command emitted by the fresh plan. There is no DLL,
game-file, load-order or launch-configuration change in this package.

## Next action

After root commit/push synchronization, create one new no-launch plan bound to
that HEAD, reconfirm CK3 count `0`, then invoke its single capture command once.
Stop on the first real RED, the first harness RED, or complete eight-span
GREEN; do not turn a single failure into a long-running acceptance loop.

## First execution admission RED

The first post-sync invocation stopped before CK3 launch. The wrapper generated
`\\.\pipe\xar_ck3_bridge_zg361_phase2_capture_<uuid>`, while the acceptance
runner accepts only `\\.\pipe\xar_ck3_bridge_zg361_<32 lowercase hex>`. The
failure is a `HARNESS_RED`; business was not evaluated, lifecycle remained
GREEN, and planned round R509 was not consumed.

The immutable detail is
`Z:\ck3_mod_rewrite\_runtime\p2-capture-r509-r515-6213626-20260912\execution-red.json`,
SHA-256 `5E25089F59AB6AAA9C80314516C7B8430FBFE23612CFED79283236E977596E0A`.
The minimal fix removes the descriptive infix and adds a focused assertion that
the emitted pipe matches the runner's public namespace. The plan tests pass
`2/2` in normal and optimized Python. No CK3 instance, recorder, capture
directory, media file, or game input was created.

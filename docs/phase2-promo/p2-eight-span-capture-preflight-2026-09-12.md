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

## R509 direct-continue loader RED

The corrected wrapper launched current round R509/PID `184256` as the only CK3
instance, using CK3 `1.19.0.6`, the frozen EXE and bridge bytes, and
`-continuelastsave`. The bridge connected, the loader completed all `303`
database callbacks through `CJominiInGameMusicDatabase`, and no loader fatal
signature was classified. It then remained without Frontend, Load Save, In
Game or native readiness for `105.019` seconds and stopped at the fixed
`299.762`-second loader bound. No recorder, gameplay input or raw span started;
raw footage remains `0/8`.

This is a harness/configuration RED rather than a product verdict. The plan
accepted omission of `--phase2-frontend-first-load-save-name` even though the
same-day R507/R508 source run had already proved the required working sequence:
reach an authenticated Frontend, terminate that warm-up process, then launch
the product save with `-loadsave=autosave`. The capture wrapper already
supported that argument; the missing admission check allowed the unproven
direct-continue path to consume R509.

The minimal correction makes a frontend-first save name mandatory before a
capture plan can become GREEN. A fresh plan must bind `autosave`. Its first
actual process will be new round R510 for Frontend warm-up; after R510 is
terminated, the product-save process will be new round R511. Any later
checkpoint restores continue incrementing from the PIDs actually launched.
There is no DLL, game-file, load-order or product change.

The retained RED report is
`Z:\ck3_mod_rewrite\_runtime\p2-capture-r509-r515-b8f44fb-20260912\capture\report.json`,
SHA-256 `9BF4EBE74FFF076A40F1D1E5A67121A39EE72D147181034C157DB62538567845`.
Managed cleanup is GREEN at SHA-256
`1566C40EA86A2782808C7AB2919E23919602E9A40571723D42409C241493E23F`;
current round R509 and old round R508 are terminated, with CK3 count `0`.

## R510/R511 frontend-first capture RED

The corrected plan bound `Frontend -> -loadsave=autosave`. New round R510/PID
`59056` reached authenticated Frontend and terminated before new round R511/PID
`8872` became the only live CK3 process. R511 completed all 303 loader callbacks,
passed loader gate `EEA51CA5...87EDE`, paused-seed gate `F170E385...6FB2`, and
paused readiness `F5F09FF2...F6745`. The recorder then started after the gameplay
HUD appeared.

The first read-only `query-zhongguo-scoreboard-state-v1` failed before any
gameplay input. Python sent the bridge's common `type="execute_step"` envelope,
while this one native parser still required `type="command"`; the adjacent
scoreboard action parser already required `execute_step`. This is preserved as
`HARNESS_RED / business NOT_EVALUATED / lifecycle GREEN`. Report
`DCC2F209...A0F26` and cleanup `DAABE7C6...76C55` bind the failure and prove both
R510 and R511 terminated with CK3 count `0`.

The retained 2.03-second MKV `B326E844...C9B82` contains no completed evidence
gate and contributes **0** raw spans. The source fix changes only the state
request discriminator and adds one parser regression executable; that focused
test is GREEN. Because native DLL bytes change, same-frame retry is forbidden.
P2 raw footage remains `0/8` and the next capture requires a newly built DLL and
a new CK3 round.

## Corrected bridge candidate

Root `5c206794e8eb73756b1dfc4eb833dc62521e9d3d` and open_kaishek
`1ac7082ff606389b9da648b356c8f6963e83dedb` are pushed and synchronized.
The Windows MSVC 19.51 Release build produced bridge DLL
`16CBA80C...0451D` and injector `E626D1F5...0D8E7`; all candidate options remain
OFF. The dedicated mailbox parser test is GREEN. Build receipt
`76C91D40...C8082` records the exact inputs, artifacts, and two resolved
toolchain-selection failures.

No CK3 process was launched and R512 was not consumed. This build is
static-ready only. The next bounded capture must use new round R512 for Frontend
warm-up and new round R513 for `-loadsave=autosave`, with this exact bridge pair.

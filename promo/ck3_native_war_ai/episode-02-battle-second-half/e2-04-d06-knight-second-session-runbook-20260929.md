# E2-04 d06 second session: current Character 34333 / Regiment 61

Status: **operator candidate only**. No screen lease, Steam picture, CK3 launch, current native number, or raw recording is claimed here. The d06 a01 no-launch attempt is RED. Historical a02 was READY on `5629d147f`, with preflight SHA-256 `EACE028F6AD8ACBEF29004FFF833722F82DF3E383C9814BFB6C1467C49C76488`; it is excluded from admission on the integrated #451 HEAD. The a03 takeover and a04 final preflights belong to earlier checkouts and are also excluded. A fresh a05 no-launch must be run from this exact checkout and sealed by the operator before any live attempt.

## Frozen inputs and run code

| Input | SHA-256 / identity |
| --- | --- |
| a08 immutable d06 save | `F05A48A0839E76DD05D053FACBA524405FD547DD0A6CA07396ADB8ABE42A0B5A` |
| a08 native save sidecar | `85C226E247AF4D32E246DCCF9F4C7323106D3A6BD0F12FCB883ABE843D3B785B` |
| CK3 1.19.0.6 exe | `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` |
| a03 Release DLL / injector | `9B6EB4E8E77AB5EF8DFE211F5A2FAF20DC42A912887874E5D836C659DD75F1FE` / `90078D708C74F05FEDB29D6AA232902E3230282F48D32D6361742A797EF81735` |
| UI saved full settings / 54-byte GUI block / receipt | `E6AD4D44435F17B77C6A5BD6554AB812FBF396D9A27370DB7CF9B56D658FDF7D` / `F5172E8A9DC92E8998957B5F443575608D04AC44342CE085DF23370CDA26F593` / `69F4535E4FDA428E910CBE6F3B44C70E352853535A2D546CB71AA09CEA941779` |
| historical a02 capture code (excluded) | `D:/w/e204_d06_admission/promo/ck3_native_war_ai/integration/capture_session.py`, SHA `752F8E2096CA363857B806DE605B7DC90E679C55F79FD9747827D405E4B7110A`, commit `5629d147fa94ab68ad5ccda484fe1eb32d4cb59e` |

The a03 DLL lacks private phase-trace BEGIN/FINISH strings. This second session only reads current knight and battle control. **Do not pass `--enable-private-phase-trace`; do not use `remaining_live_step.py`**, which is for a separate trace-enabled d11 capture.

## Screen GO before starting

1. Root/live owner receives exclusive `ck3-screen:acquired`, checks no other CK3/recorder/screen owner, and captures a **new current desktop frame**. Check actual pixel freshness using the documented window movement method when necessary; directly review Steam's “离线模式” on the new image. Save a new `steam-offline-reviewed.json` under an `episode02-e2-04-d06-knight-offline-20260929-*` attempt, with the screenshot and screen lease sequence. The a02 no-launch had no live Steam evidence.
2. Re-query latest formal `xar-promo` GitHub Release before the live run; verify the exact wheel SHA, interpreter version, top-level/relevant help. The historical a02 baseline was `xar-promo 0.2.1`, wheel `F8DE0711415E7FCE2BF07A34D3DB4EDC0593F32BA1CB61034946665E27014621`; a changed formal release requires an updated requirements pin and new preflight.
3. Rehash the exact DLL/injector, immutable save/sidecar, UI source/receipt, and `capture_session.py`. Confirm the **new** no-launch `run-result.json` exit 0, `ck3_started_by_command=false`, and `admission-lock.json` matches the current checkout HEAD, script bytes, full argv and original preflight/result files. Preserve a01 RED and a02 history. Choose a fresh live root, state dir, output dir and pipe. Never copy the a08 profile or old recorder workdir.

The example below uses live attempt `a01`; change **all** four `a01` locations and the pipe together if that name exists. Execute from the final integrated #451 checkout with the verified main venv; preserve command argv/stdout/stderr/exit in the fresh attempt. The offline receipt placeholder must be replaced by this screen lease's reviewed receipt.

The CAS screen gate in [screen-bus-cas-admission-20260930.md](screen-bus-cas-admission-20260930.md) supersedes this old example's screen arguments. A future live argv must also supply `--screen-task-id`, `--screen-expected-sequence`, and `--screen-cli-sha256` from a new reviewed registration; the old installed CLI and unresolved XQOL screen record currently make live admission STOP. `capture_session.py` renews its own task; do not start a second renewer. This code change invalidates any earlier no-launch seal, so regenerate the exact-HEAD attempt before live use.

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe D:/w/video_e2_final_20260929/promo/ck3_native_war_ai/integration/capture_session.py
  --game-dir C:/SteamLibrary/steamapps/common/CRUSAD~1
  --bridge-dll D:/ck3-research-artifacts/e2-04-d06-current-knight-release-20260929-a03/build/xar_ck3_bridge.dll
  --bridge-injector D:/ck3-research-artifacts/e2-04-d06-current-knight-release-20260929-a03/build/xar_ck3_bridge_injector.exe
  --state-dir D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-live-20260929-a01/ck3-state
  --output-dir D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-live-20260929-a01/ck3-output
  --pipe-name \\.\pipe\xar_ck3_e204_d06_knight_live_20260929_a01
  --checkpoint-save D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-live-20260929-a08/e2-04-d06-postframe-preservation-a01/d06-immutable.ck3
  --checkpoint-receipt D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-live-20260929-a08/ck3-output/interactive-requests-responses/e2-04-d05-postframe-save.json
  --frontend-timeout 900 --gui-scale 1.0 --import-a04-ui-gui-100
  --a04-ui-settings-snapshot D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.pdx.txt
  --a04-ui-preservation-receipt D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d05-screen-lease-20260928-a04/native-ui-saved-settings-a01.json
  --recovery-seconds 1800 --interactive-seconds 3600 --hold-seconds 60
  --steam-offline-receipt <fresh-d06-knight-offline-attempt>/steam-offline-reviewed.json --capture
```

Those are **argv items**, not a multiline shell command. First run a new no-launch preflight with the same source pair and exact code HEAD, saving the original argv/stdout/stderr/result and `ck3-output/preflight.json`/`command.json` under `episode02-e2-04-d06-knight-preflight-20260929-a05-admission`. Then execute the operator's `seal --no-launch-attempt <new-root>` once; it create-exclusively freezes the verified files into `admission-lock.json`. The live owner may use the same Python argument-array style as historical a02 `run_no_launch.py`, changing only the new live dirs/pipe plus fresh `--steam-offline-receipt` and `--capture`. Do not insert a trace flag.

## Paused same-frame observation and media

Wait for new live `ck3-output/preflight.json` READY, `native-start-readback.json` `postcondition_verified=true`, and three GUI disk receipts (`before-native-session`, `postmap`, `posthold`) that retain serialized `"1"` and the frozen 54-byte block SHA. Directly review a new full-resolution desktop image: CK3 has actually loaded the map/HUD, no modal/launcher, UI fits the full recorded geometry, and the game is paused at d06. `map_ready` or a scale disk receipt alone does not prove a usable shot.

Run the new read-only helper from the same integrated checkout, with the **new sealed a05** as `--no-launch-attempt`:

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe D:/w/video_e2_final_20260929/promo/ck3_native_war_ai/episode-02-battle-second-half/e2_04_d06_knight_live.py observe --session-output <new-live-root>/ck3-output --no-launch-attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-preflight-20260929-a05-admission
```

The helper creates exclusive intent and result files, then reads a new paused snapshot, same-revision battle control, current CharacterID `34333`/RegimentID `61`, and a final unchanged snapshot. It requires actor `29829`, War `4`, CUnit/native CArmy `18`, Combat `16777218`, Province `2633`, date raw `53146368`, unique defender regiment `61`, paired generation checks and new frame revisions. `current_effective_prowess` and `province_evaluated_*_raw` are current native values at scale 100000; `stored_combat_entry_*_raw` are old battle-entry fields. **No 7/11 or 612.5/122.5 is assumed in advance.** On a timeout or unavailable result, preserve the request/response and RED receipt; do not retry that request in the same attempt.

If observation and visual geometry are good, start `record_bounded_gameplay.py record` in a **new sibling recorder workdir** with `--track e2-04-d06-current-knight --seconds 180 --session-output <new-live-root>/ck3-output --source-save <F05 save path> --source-receipt <85C sidecar path> --steam-offline-receipt <same fresh receipt>`. Start it while CK3 is paused. During the bounded recording, show (a) war/battle d06 context, (b) knight roster with two Geoffroy rows (12 and 7), (c) character identity/direct view of `34333` and wounded/one-legged state if UI supports it, and (d) regiment `61` details with native numbers. UI clicks require original screenshot geometry, coordinate map receipt, and target focus checks per AGENTS. Do not advance a game day or issue a save.

While FFmpeg is still recording, append a `mark` for the independent d06 shot with `--date-raw 53146368 --combat-id 16777218 --war-id 4 --control <new-live-output>/interactive-requests-responses/e204-d06-knight-control.json --report <new-live-output>/interactive-requests-responses/e204-d06-current-knight-34333-61.json --capture-screenshot`. Use a second mark/screenshot after the direct character or regiment panel if the first image does not show all. Preserve raw MKV, geometry admission, frames/probe, journal, screenshots, and any RED artifacts. Wait for `recorder-end.json` and `recorder-final.json`; visually review the raw and identify a clean span before any edit claims.

After the recorder has sealed, request managed cleanup exactly once:

```text
D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe D:/w/video_e2_final_20260929/promo/ck3_native_war_ai/episode-02-battle-second-half/e2_04_d06_knight_live.py finish --session-output <new-live-root>/ck3-output --no-launch-attempt D:/workspace/ck3_native_war_ai_promo_work/episode02-e2-04-d06-knight-preflight-20260929-a05-admission
```

Wait for `capture_session.py` exit, then verify `session-result.json`, `capture-report.json`, CK3/FFmpeg process inventory and screen lease release. `finish` only requests cleanup; its receipt alone does not prove cleanup or footage quality. All new outputs remain in the new attempt; the a08 save/sidecar and every old attempt stay immutable.

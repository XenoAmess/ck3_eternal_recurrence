# H3937 combined read-only one-shot admission

This isolated candidate runs one managed H3937 observation on the paused save. It requests the province-2610 siege partition once and the target-2610 route-contact horizon once in the same native session. It never advances the date, moves an army, attacks, spends cash, or authorizes those actions. A read-only result cannot by itself qualify the full physical enemy inventory or the war forecast.

## Exact entry and assets

The direct entry is `ck3_autonomous_player/h3937_combined_once.py`, with **no arguments**. The selected interpreter is `D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe` (Python 3.14.7). The script fixes round `R3940`, the H3937 persisted pipe `\\.\pipe\xar-g2-robert-1066-seed-66f926d`, game directory `C:/SteamLibrary/steamapps/common/Crusader Kings III`, and these exclusive paths:

- New official no-launch pair: `D:/ck3-research-artifacts/war-h3937-combined-no-launch-20260929/attempt-02/`.
- New screen evidence: `D:/ck3-research-artifacts/war-h3937-combined-live-20260929/screen-attempt-02/`.
- External GO receipt: `D:/ck3-research-artifacts/war-h3937-combined-live-20260929/go-attempt-02.json`.
- New live output: `D:/ck3-research-artifacts/war-h3937-combined-live-20260929/attempt-02/`. It must not exist before invocation.

The source save is SHA-256 `92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6`, raw driver `2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722`, and child sidecar `798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7`. The combined master58 Release DLL is `310E58F50A9B66360B9FDC761B05AC52F3BD99096E19723A2DAB69F015D5A7A0`; injector is `ED3FBCA683D570BE5B7835894B35CDF4217EC15051FFB2A04F0C53131FE6B99A`. The new prepared driver, environment, rebind, and preflight hashes must come from attempt-02, not historical attempt-01.

## Conditions before invocation

1. Freeze this enablement checkout at an exact clean commit, then create attempt-02 from the exact raw H3937 source and new Release binaries. Run official `prepare-profile`, `rebind-ordinary-seed-v1`, and `native-one-generation-preflight` with `ordinary_campaign_succession`, `xar_off`, no pact, actor 29829, episode `native-29829-2bc2d599f7f9`, date raw 53219928, and history index 3937. Archive their original stdout/stderr, receipts, hashes, and a clean Git blob check. Any changed checkout needs another new attempt.
2. Obtain the exclusive `ck3-screen` task lease. Capture a new original desktop screenshot after verifiable window movement and have root directly review the visible Steam “离线模式”. Check that the Steam account has no conflicting session, CK3 and recorder inventories are empty, and no other screen task owns the display. Do not infer offline status from receipt metadata.
3. Root writes a fresh external GO receipt only after those checks. It binds the exact checkout HEAD, round, state/output/pipe, SHA-256 of admission, operator manifest, official rebind and preflight, and the original Steam image and screen-lease receipt paths and hashes. It must carry `decision=GO_READ_ONLY_H3937_COMBINED`, `authorized_scope=two_paused_readonly_queries`, and true direct visual, exclusive lease, account, and zero-process attestations. Both proof files must reside under the exact screen-attempt-02 directory. No receipt means no invocation.

## Execution and failure boundary

The no-argument supervisor starts one worker with a 540-second limit. The worker consumes the exact empty output directory, rechecks source bytes, ordinary lifecycle, official prepared pair and GO receipt, and requires fresh zero CK3/recorder inventory. It opens the outer and inner live booleans **only in that process for the single call**, restores them in `finally`, and writes the original outer report or traceback plus a completion receipt. The supervisor stores worker stdout/stderr, checks the child completion and zero-process cleanup, and records a separate result. On timeout it invokes `taskkill` on the worker PID and descendants, then records both the result and a fresh process inventory; any unproven cleanup remains RED and the screen lease stays held for controlled clearing. A second invocation cannot overwrite the consumed output directory.

`GREEN_READ_ONLY` requires exactly two native read-only queries, same-frame and history proof in the outer report, unchanged date and assets, both action/date authorization fields false, managed cleanup, restored in-memory gates, and an empty final process inventory. A missing, changed, or false field is RED. The outer candidate and all action/date gates remain false in the checked-in modules. Historical H3937 phase-0 live attempt-01 remains RED with no native snapshot or unchanged-date proof; its prepared pair is never reused.

This document and the static tests do not grant screen access or a live GO. The final enablement diff and new attempt-02 no-launch packet require independent review before root can approve the one read-only invocation.

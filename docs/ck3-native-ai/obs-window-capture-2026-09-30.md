# OBS window capture provider v1

Ownership: `tools/ck3_obs_capture.py` in this repository is the reusable provider. The Damengsan suite imports this file and supplies its own attested CK3 PID/HWND, allowlisted engine installation and isolated recording root. No mod identity, suite path, temporary run label, arbitrary OBS request or keyboard/mouse operation is in the generic contract.

Install `tools/requirements-obs-capture.txt` into the caller's verified Python environment. Deploy the official portable OBS 30.1.2 archive from [the OBS release](https://github.com/obsproject/obs-studio/releases/tag/30.1.2). `prepare_profile` creates a fresh portable configuration and refuses to replace an existing user configuration. Keep the generated engine profile/password outside Git and outside video evidence exports.

The v1 capture profile is 1920×1080, 60/1 fps, NVENC H.264 HQ, MKV, no cursor and no microphone/desktop audio. Window binding checks CK3 title, native HWND visibility and PID. Each bounded job (15/30/45/60/90/120 seconds) mints a UUID, retains start/completion/failure receipts and records source settings, source PNG, native OBS statistics and completed output bytes/SHA-256. Start/stop commands are asynchronous: the worker polls actual output state before advancing. A periodic status request keeps the synchronous WebSocket client responsive to server keepalive.

`stop_session_recording` stops only a matching opaque filename/session and validates the output scope. `request_engine_close` applies only to the engine PID recorded by the provider and recognized OBS main/duplicate-instance dialog windows, after the recording worker has finished. Read the next status/window inventory to confirm closure. Failed attempts remain intact. `recovered-stop.json` does not turn an earlier failure into an approved take.

## Delayed startup and owned close (2026-10-16)

Machine `xenoamess-full-tower-eb9d2c1186`. In the Native20 cold attempt, the
dedicated OBS PID206588 reached its listener after approximately 41.5 seconds
as reported by the on-site investigation. `OwnedEngine.start` previously
waited only 40 one-second polls and reported a timeout just before readiness.
The original failed attempt remains failed; it is not a successful take.

The permanent v2 provider now allows 120 startup polls and returns immediately
when the existing connection/profile checks succeed. Occupied ports, changed
executables and changed process generations still reject. This changes the
startup wait only: it adds no game-session, video-duration or video-capacity
limit, and does not relaunch or attach to an unrelated OBS instance.

Normal close now selects the unique owned-PID `OBS ` / Qt window with
`GetParent(hwnd)==0`, then rechecks that parent and PID before `WM_CLOSE`.
Owned hidden Qt child dialogs cannot make the root main window ambiguous;
multiple root candidates still reject. No foreground switch or forced-process
fallback is introduced, and an exit timeout remains unverified.

Root independently closed the late-started PID206588 normally with kernel exit
code0, no forced calls and foreground HWND1121666 unchanged. The close intent
records the method as excluding hidden children by parent; it does not contain
a separately recorded `GetParent` value or the exact selector source. The
parent-zero condition is Root's on-site execution account plus the permanent
implementation and offline regression checks, not a field invented in the
old receipt. External evidence root:
`continuation42-cold-prep/native20-cold-generation02/`.

- Original attempt: `recordings/e1a5e0fb-cfc1-4610-8ba4-5d0fb0385914/`.
- `ROOT-LATE-OBS-206588-NORMAL-CLOSE-INTENT.json`, SHA-256
  `dd00325053c61b1a9aa9256bd26c53cf3e1521d7f2ee41786c8a16ea5f2e9c55`.
- `ROOT-LATE-OBS-206588-NORMAL-CLOSED.json`, SHA-256
  `17691e57563fae631ed4e0e6a1d659fd79b6a445e26693a8eda4b26c62900a67`.
- `ROOT-RECORDING-STARTUP120-RECOVERY-PREPARED.json`, SHA-256
  `4501c0faf635504fff867c6b94b804eef587a1814bdf7e4def910d5a24e52df26`.

The production startup method with a fake clock reproduces the old 40-second
timeout and succeeds at the first 42-second poll for a 41.5-second listener.
Six startup checks plus the existing provider/close suite pass **48 tests and
21 subtests**, including never-ready timeout, fast startup, custody rejection,
same-title Qt children, duplicate roots and a parent change before close.
Tests create no processes or sockets. This public integration does not modify
the current recording provider, certify the new take, or replace Root's actual
recording/overlay readback. Earlier v1 evidence below retains its original
scope and limits.

## Native evidence

On 2026-09-30, caller run `promo-jichou-20260930-r5` used CK3 1.19.0.6 / Steam build 23530548 / EXE SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`, RTX 3060 Laptop GPU, driver 31.0.15.4665. OBS's log confirmed D3D11 shared-texture game capture and NVENC H.264. The separate FFmpeg 9.0.2 NVENC encoder requires a newer driver API on this machine; that failure does not mean OBS NVENC is unavailable.

Completed session `cc933682-0a47-401a-a40f-b9f3fc9f4348`: 62,822,499 bytes; SHA-256 `a6dc7f29dd607f03a17b9b3f7d70465a2d3951b0edab99c1c53f2014ce58ce7c`; native output skipped 15/3657 frames, render skipped delta 7/3681. The selected 00:12–00:24 has 720 decoded presentation frames, maximum spacing 17 ms, zero gaps >50 ms. Pixel-region analysis still detects naturally small/still changes and cannot prove the CK3 engine renders every frame at 60 fps. Source screenshots show actual date, army-position and strength progression; timestamps alone do not establish visual smoothness.

Evidence is preserved by the suite's `xar-promo 0.2.1` run `motion-revision-20260930-r5`. Generic provider tests cover request bounds, local authenticated/non-overwriting profile creation, SDK response serialization and refusal to stop another session.

## Startup findings

- WebSocket v5.4.2 settings belong to `global.ini` section `OBSWebSocket`, as defined by the [official source](https://github.com/obsproject/obs-websocket/blob/5.4.2/src/Config.cpp).
- Use `key=value` when generating OBS INI files; OBS rewrites them with a BOM. Python readers use `utf-8-sig`.
- A hidden duplicate-instance dialog can retain the single-instance lock after another engine window closes. Preserve that failed session and close its owned dialog before starting a new attempt.
- Source creation and NVENC startup exceeded a two-second control timeout here. The bounded provider uses ten seconds and output-state readback.
- `obsws-python` INFO logging includes the connection password. The provider suppresses that namespace below WARNING and never includes credentials in receipts.

The provider is a capture capability, not a gameplay verifier or publication signoff.

Longer control check: a status request alone did not prevent a later 90-second attempt's connection reset. The final worker renews its local control connection every 20 seconds, rechecking the UUID filename binding before continuing. A new 90-second session `fb18242d-1800-409c-99df-592bf5a32dab` completed and stopped automatically: 55,271,544 bytes, SHA-256 `a60d90805321b0ccb2cfbc17012ed0fd2c50459c25c9dc96d70f25d9a859358c`, zero encoding skips in 5,435 output frames. This take was a paused UI stability check; it is not an additional live battle-motion proof. Five focused provider tests now include ownership rejection on control reconnection.

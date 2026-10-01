# Steam UI host compatibility and fresh offline evidence

Correction on 2026-10-01: the initial narrative attributed the external
Damengsan diagnostic's Steam window to native `steam.exe`/`SDL_app`. Later
read-only process metadata proved that the successful R1 receipt's PID 14140
was `bin/cef/cef.win64/steamwebhelper.exe`, created at `1790591117.8362925`.
The separate native client was PID 5808, `<steam-root>/steam.exe`, created at
`1790591116.7471032`. The actual recovery therefore proves the CEF path; it
does not prove a native SDL host. The native-host branch added to the generic
helper has mocked coverage only in this work package. The setup RED in the
first recovery attempt came from the task-bus directory argument.

The authoritative fix remains in this repository's
[`steam_offline_fresh_frame.py`](../../tools/steam_offline_fresh_frame.py).
`_steam_windows()` now accepts the native `steam.exe` host and the existing CEF
`steamwebhelper.exe` host. Both require exact window title `Steam`, visibility,
and a live matching process owner. It returns all matching candidates;
`capture()` and recovery preflight still reject zero or multiple windows.
No HWND, account, machine, mod item, or run identity was added to the generic
implementation.

## Verification

The focused suite
[`test_desktop_steam_offline_recovery.py`](../../tools/test_desktop_steam_offline_recovery.py)
passed **17/17 tests**. The four added tests cover the native host, the old CEF
host, rejection of non-Steam owners/incorrect titles/invisible windows, and
ambiguous hosts causing refusal before any movement or screenshot. All tests
mock window/process enumeration and desktop operations.

```text
<python-3.13-with-existing-desktop-dependencies> tools/test_desktop_steam_offline_recovery.py
```

The tested source base was `9ee1cc1bc7b9e66c7d3043e06ab492c227e9069b` plus
this patch. The patched freshness helper SHA-256 used by the actual frozen
operator job was
`9A34FE59DE520EA4B7A09A1B1F8C8B2C112E9E37901E1621B317AAD81274EA8D`.

## Actual recovery evidence

The external suite operator ran the existing
[`desktop_steam_offline_recovery.py`](../../tools/desktop_steam_offline_recovery.py)
through a profile-frozen operator MCP job while holding the task-bus screen
lease. Its second preflight attempt used the actual task-bus Python entrypoint;
the earlier attempt had passed the bus directory and remains a setup RED.
The successful evidence is retained outside this repository at:

```text
<suite-root>/_runtime/acceptance/C-damengsan-core-R1/offline-preflight-02/recovery.json
<suite-root>/_runtime/acceptance/C-damengsan-core-R1/offline-preflight-02/probe-1/steam-frame-freshness.json
<suite-root>/_runtime/acceptance/C-damengsan-core-R1/offline-preflight-02/probe-1/steam-moved.png
```

Readback SHA-256 is `eb6668bab8da93f7c206fbf0554dfdfcebfab2efefb21fe85afd40c40a5a8101`
for `recovery.json` and
`76e99f2372718aa5f39b251c1ce87466088a02720e1eabeefebefc8152f0fa40`
for `steam-frame-freshness.json`.

At `2026-10-01T08:01:23.933827+00:00`, the receipt recorded a unique Steam
window, desktop `1920 × 1080`, a 20-pixel horizontal movement, changed moving
edge pixels, and exact restoration of the original window rectangle. The
moved image is 1,734,729 bytes, SHA-256
`A557A6726F7AA079CE4FB44CB8AEA26B03828096BCD43E78442BC87D6C16CAA5`.
The recovery outcome was `fresh_frame_needs_offline_visual_review`;
`steam_mode_mutation_attempted=false` and `ck3_launch_attempted=false`.

The coordinating operator visually reviewed that new image and confirmed
Steam offline before starting CK3. The receipts deliberately keep
`offline_status_observed=null`: fresh pixels prove capture responsiveness,
while the visual review proves the displayed mode. The later read-only
process metadata identifies the receipt's UI process as CEF; the recovery
receipt itself records HWND/PID but does not contain a class or executable.
No screenshot, account data, or external mod source is copied into this repo.

The screen remains owned by the suite's game diagnostic. This patch's author
only edited the generic helper/test and read existing evidence; no extra
desktop operation or CK3 launch was performed for the code package. The
general recovery boundary remains
[desktop Steam offline recovery](desktop-steam-offline-recovery-2026-09-27.md).

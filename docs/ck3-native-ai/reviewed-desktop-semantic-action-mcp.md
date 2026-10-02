# Reviewed desktop semantic actions MCP

This source-local MCP provides one reviewed left click when the active CK3
build has no usable native GUI action. Ownership belongs to this repository:
the operation is reusable across mods and operator machines. External suites
only provide target-side deployment data and consume the generic tool.

The immediate blocker was a real 1.20.0.2 total-conversion bookmark page.
The existing native frontend contract still binds 1.19.0.6, and its 1066 ruler
selection binds vanilla bookmark identities. See
[native frontend route](frontend-gui-route-v1.md). The new desktop fallback
does not relabel these capabilities, inject a DLL, use OCR, type text, send
keys, or accept caller-selected coordinates or control names.

## Tools and bootstrap

[`desktop_semantic_action_mcp.py`](../../tools/desktop_semantic_action_mcp.py)
exposes two closed-input MCP tools:

```text
desktop_query_action_profile_v1()
desktop_execute_action_v1(action_name)
```

`action_name` must be a configured semantic name such as
`select_bookmark_ruler` or `confirm_save`. The client cannot provide a path,
point, key, mouse button, HWND, PID, session ID, or run ID. The target-side
server generates its session UUID and binds all receipts to its frozen
profile SHA-256. One action is attempted once per server session; repeated
calls return the same receipt, including a RED receipt. A new reviewed screen
requires a new target-side profile and server session.

Start on the local interactive desktop using an existing compatible Python
environment with MCP 2.0.0, Pillow, psutil, PyAutoGUI, and pywin32:

```text
<python> <main-repo>/tools/desktop_semantic_action_mcp.py --profile <target-side-profile.json>
```

Alternatively, the official in-memory `mcp.Client` can consume
`create_server(SemanticActionService(load_profile(profile_path)))` in a local
client process on that same desktop. Native identity is read from the actual
process/window; another machine's profile is not a substitute.

## Frozen profile schema

All listed fields are required, and extra fields are rejected. SHA placeholders
below stand for complete 64-character SHA-256 digests. Paths must be absolute
local deployment paths; the generic code contains none of these example
identities or points.

```json
{
  "schema_version": 1,
  "target": {
    "pid": 123,
    "hwnd": 456,
    "process_create_time": 1234567890.0,
    "executable": "<absolute ck3.exe>",
    "executable_sha256": "<SHA-256>",
    "app_manifest": "<absolute Steam appmanifest ACF>",
    "build_id": "<exact installed Steam build>",
    "window_title": "<observed exact title>",
    "window_class": "<observed exact class>",
    "window_rect": [0, 0, 1920, 1080]
  },
  "steam": {
    "root": "<absolute Steam root>",
    "pid": 789,
    "process_create_time": 1234567880.0,
    "client_pid": 987,
    "client_process_create_time": 1234567870.0,
    "offline_evidence": "<absolute steam-frame-freshness.json>",
    "offline_evidence_sha256": "<SHA-256>",
    "offline_visual_reviewed": true
  },
  "task_bus_script": "<absolute standard codex_task_bus.py entrypoint>",
  "task_bus_sha256": "<SHA-256>",
  "screen_task_id": "<current exclusive screen lease owner>",
  "evidence_directory": "<absolute external run evidence directory>",
  "actions": {
    "select_bookmark_ruler": {
      "source_image": "<absolute reviewed full desktop screenshot>",
      "source_sha256": "<SHA-256>",
      "preview_bounds": [0, 0, 1920, 1080],
      "observed_point": [960, 540],
      "reviewed_bounds": [940, 520, 40, 40]
    }
  }
}
```

The operator must replace the example geometry with the actual reviewed image
content bounds and button region. Axis conversion and region checks reuse
[`desktop_coordinate_map.py`](../../tools/desktop_coordinate_map.py). The
source image dimensions must match the live desktop; the mapped point must
fall inside the unchanged target window rectangle. This entrypoint accepts
full desktop screenshots, not cropped window images.

## Guard and readback boundary

Before dispatch, the server verifies the reviewed screenshot bytes, actual
PID and process creation time, executable path/SHA-256, installed build,
visible HWND and owner, exact title/class/window rectangle, foreground HWND
and PID, desktop size, no held mouse button, and the task bus's unique screen
owner with a heartbeat no older than ten minutes. It freezes the standard bus
CLI's SHA-256 and calls that entrypoint's read-only `list`, never arbitrary
client commands.

Steam checks combine a SHA-bound freshness receipt already visually reviewed
as offline, its UI host PID, the same live UI host/process creation time, an
independently bound native Steam client PID/process creation time, and current
`WantsOfflineMode=1` file readback. The UI host executable must be exactly
`<steam-root>/steam.exe` or
`<steam-root>/bin/cef/cef.win64/steamwebhelper.exe`. The native client must be
exactly `<steam-root>/steam.exe`; it can share the host PID in native mode but
is distinct for a CEF-hosted window. A living helper does not substitute for
the client after that client's death or restart. This is a configuration
and session-continuity guard; it does not claim a new visual reading of Steam
or infer mode from screenshot pixels. Source/reviewed and live whole-frame
hash equality is deliberately unnecessary because CK3 portraits and scene
backgrounds animate. Geometry, source artifact identity, native process
identity, and the locally reviewed button region remain binding.

The server saves `before.png`, reads all guards again immediately before the
click, dispatches one left click, then saves `after.png` and rereads native
identity, foreground, Steam, lease, and dimensions. Its external evidence
path is `<evidence_directory>/<server-session-UUID>/<action_name>/receipt.json`.
Receipts preserve source/profile hashes, mapping, before/after image bytes
and SHA-256, and before/dispatch/after observations. Failures after evidence
creation retain a RED receipt and never trigger an automatic second input.
`click_attempted` distinguishes a dispatch attempt from a completed input API
ACK if the input provider itself fails.

Successful status is `dispatched_requires_business_readback` and
`business_postcondition_verified=false`. A changed screenshot or successful
input API ACK does not prove selected character, event outcome, save creation,
or playable campaign. The consumer must use independent native/log/save
readback for these results and visual review for the relevant GUI state.

## Native timeline refusal and reviewed modal recovery

An operator-owned exact 1.20.0.3/build25652598 regression on 2026-10-02 exercised this boundary with the already qualified n2 bridge. A normal resume after a checkpoint returned `CK3 map state is unavailable`, while a fresh native snapshot was paused/map-ready with no active event or pending mail. Direct review of a frozen screenshot identified a war-result modal. Map-ready state and empty event/mail fields do not establish that all blocking GUI has closed.

The frozen adapter's `TimelineReady` checks commands, pause vtables, map readiness and player ID; `QueueTimeline` folds both native queue rejection and unavailable submission into the same bridge error. That text cannot independently identify a modal, pending interaction, allocation problem or other exact failing condition. The existing `current_timeline_blocker_context` is not a general war-result query: its identities/routes cover legacy death, game-over and destiny windows, bind 1.19.0.6, and its private death-modal dispatch flag is OFF in n2. Python thin exposure cannot make that frozen artifact observe or acknowledge a patch3 war-result window.

The operator preserved the rejected attempt and used one existing artifact-reviewed, profile-bound semantic action to close the observed ordinary modal. The action receipt remained `dispatched_requires_business_readback` with `business_postcondition_verified=false`. A fresh native snapshot and independent native clock then agreed on the unchanged paused date; only after that evidence did a new policy attempt submit normal resume and observe `paused=false` with actual date advancement. The same CK3 PID, loaded DLL, bridge session and generation 2 remained in use. No rejected command was blindly replayed, and no game restart, reinjection or accumulated-year reset occurred.

| Frozen independent-project evidence | SHA-256 | Boundary |
| --- | --- | --- |
| `dismiss-war-result-001-desktop_execute_action_v1.json` | `f27af2e8467a760c2283911630f6cfa354a148635b3868a362cbd54922ceb3a0` | One input ACK; business result still false |
| `0163-snapshot.json` | `65a0bdccbb39a472d3a65eee6415e168be5d377253b97be7d0ec7af2900f7814` | Paused, map-ready, raw date 77675448 after dismissal |
| `war-result-dismiss-clock-001.json` | `a80894b71de0a20011d87ae888390b69c5054b1f7da87848e02481ac1a628863` | Independent same paused raw date with offline guard |
| `000018-action-confirmed.json` | `1701f1d7fbe0036af69314e3be8c2f92734dcc39fb1f33900c24be7573b668bc` | New resume reported `native_gameplay_postcondition_verified` |
| `0169-snapshot.json` | `bf841e1c9a5f9dde707a2a919d56bb984eeaedb10bf4e9493491c3942e2d4469` | Map-ready, running, raw date 77676120, same generation |

This is an observed use of the existing recovery contract, not new modal-detection or automatic button-selection capability. The consumer still needs reviewed source geometry and independent state readback for each configured action. Generic method and capability limits belong here; project war settlement, source-specific decisions, screenshots, logs, saves and the original RED remain in the independent project. The running Python consumer remains `0700e17546d27d76fa1e37085d3d69db642c4988`; this docs-only update changes no tools/native artifacts and introduces no new test result or century-completion claim. See also [profile transport continuity](native-profile-transport-resume.md).

## Verification

The focused test command is:

```text
<python> tools/test_desktop_semantic_action_mcp.py
```

Eleven tests passed, including official MCP closed schemas and rejection of
extra coordinates/spoofed session IDs, allowlist names, independent-axis
mapping, source/region bindings, fifteen pre-dispatch guard changes, a focus
change after before-capture, preservation of after-input RED evidence, and
native-backend mocked reads of the pinned bus/build/offline session/lease.
Native and CEF hosts are both covered, with separate client continuity,
unknown host/executable/PID rejection and a dead-client native-provider test
that refuses input even while the configured CEF helper remains available.
All desktop APIs and input are mocked. No live action was performed by this
implementation package; the consuming suite owns its next controlled attempt.

Correction on 2026-10-01: the first provider assumed the freshness receipt's
UI host PID was the native client. Actual local metadata showed the receipt
was emitted by CEF, so that assumption rejected a legitimate existing host.
The two new required profile fields `client_pid` and
`client_process_create_time` repair this real compatibility failure. Existing
target-side profiles must be regenerated with both host and client identities.

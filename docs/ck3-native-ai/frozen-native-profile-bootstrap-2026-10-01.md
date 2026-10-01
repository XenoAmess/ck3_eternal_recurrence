# Frozen profile consumption of the existing native bridge

The shared CK3 bridge and MCP provider belong to `ck3_eternal_recurrence`.
`tools/ck3_native_profile_mcp.py` is a thin consumer of that provider for an
already launched, isolated run. A calling project supplies target-side profile
data; the tool contains no mod identity, project run name, screenshot point or
project absolute path.

The bootstrap exposes eight closed MCP tools. The first three and current-frame
pause take no arguments. Other ordinary-player tools accept only typed native
revision/event identities and a fixed semantic simulation enum:

| Tool | Result |
| --- | --- |
| `ck3_query_native_profile_v1` | Rechecks the frozen process, build, desktop, Steam and lease bindings. |
| `ck3_attach_profile_bridge_v1` | Starts the native named-pipe endpoint, invokes the existing injector once, then requires a real exact-build native snapshot. |
| `ck3_take_profile_native_snapshot_v1` | Reads the existing native provider and saves a receipt. |
| `ck3_query_profile_event_window_v1` | Queries the current event's existing native context from a paused, bound revision. |
| `ck3_set_profile_simulation_v1` | Performs only `pause`, `resume`, `speed_1`, `speed_3` or `speed_5` and verifies the native result. |
| `ck3_pause_profile_simulation_v1` | Pauses the current running campaign using the provider's own submission frame, with native postcondition and full guard readback. |
| `ck3_select_profile_event_option_v1` | Selects one enabled authored option through the existing event service and verifies the selected event is no longer active. |
| `ck3_save_profile_checkpoint_v1` | Uses the existing fixed native save command and verifies actual save bytes, path, SHA-256 and raw date. |

The server generates its session UUID and pipe. A caller cannot supply a PID,
command, artifact path, coordinates, keys or session/run identity in a tool
call. The profile binds a previously reviewed semantic desktop profile by
SHA-256, and reuses its native HWND/PID/create-time/EXE SHA/build/foreground
guards, legitimate Steam UI-host and client continuity, current offline flag,
reviewed fresh offline receipt, pinned task-bus CLI and exclusive lease of at
most ten minutes. It also verifies that the live command line has exactly one
`-userdir=` identifying the configured isolated userdir.
The isolated userdir's `crashes/` directory must be empty both before and after
observation. An incomplete newly created package already denies the guard.
This rejects reusing a failed run as a healthy run. A live process and a readable
native clock can persist during exception processing; neither alone proves
healthy simulation.

Artifact names are the existing `xar_ck3_bridge.dll` and
`xar_ck3_bridge_injector.exe`, both bound by SHA-256. Before injection the tool
polls the pinned task bus and repeats the guard. The existing Windows contained
injector is only invoked after the independent read-only clock proves an
initialized paused campaign prefix. The first native provider snapshot must
be map-ready, remain paused and match that pre-attach raw date. The before-clock
receipt is retained with the attach evidence. The existing Windows contained
injector Job must prove return code zero and complete process-tree containment.
That ACK alone is insufficient: the tool reads the provider's actual hello PID,
exact game version, EXE SHA and ready adapter, followed by native integer
`date_raw`, boolean `paused` and integer `speed`. It preserves the injector
report and before/after observations. Its per-run `attach-claim.json` is created
exclusively before any injector invocation; a new server cannot replay attach
into that evidence directory. RED attempts remain claimed.

The profile has exactly these fields:

```json
{
  "schema_version": 1,
  "guard_profile": "<absolute reviewed semantic profile JSON>",
  "guard_profile_sha256": "<64 hexadecimal digits>",
  "userdir": "<absolute isolated userdir>",
  "state_directory": "<absolute new native state directory>",
  "evidence_directory": "<absolute new per-run native evidence directory>",
  "game_version": "1.20.0.2",
  "dll": {"path": "<absolute xar_ck3_bridge.dll>", "sha256": "<SHA-256>"},
  "injector": {"path": "<absolute xar_ck3_bridge_injector.exe>", "sha256": "<SHA-256>"}
}
```

Use a persistent official MCP client/server session. An in-memory consumer can
start the narrow server without a shell command or live input wrapper:

```python
import asyncio
from pathlib import Path
from mcp import Client
from ck3_native_profile_mcp import NativeProfileService, load_profile, create_server

async def run(profile_path):
    service = NativeProfileService(load_profile(Path(profile_path)))
    try:
        async with Client(create_server(service), cache=None) as client:
            preflight = await client.call_tool("ck3_query_native_profile_v1", {})
            attached = await client.call_tool("ck3_attach_profile_bridge_v1", {})
            snapshot = await client.call_tool("ck3_take_profile_native_snapshot_v1", {})
            return preflight, attached, snapshot
    finally:
        service.close()
```

Put the authoritative repository's `tools/` directory on the consuming Python
process's import path. On the current Windows machine, the installed Python
3.13 interpreter already has the MCP, OpenCV, Pillow, psutil and pywin32
dependencies. The suite's virtual environment lacks OpenCV for imports used by
the existing full provider. No package installation was needed.

An independent clock-only profile omits `state_directory`, `dll` and `injector`
from the schema above. `load_clock_profile`, `NativeClockProfileService` and
`create_clock_server` expose only the closed, no-argument
`ck3_read_profile_native_clock_v1` tool. The CLI can select this target-side mode
with `--clock-only`. It does not create a named-pipe endpoint or run an injector.
It opens the profile's already guarded process with exactly
`PROCESS_QUERY_INFORMATION | PROCESS_VM_READ` (`0x0410`), verifies the main
module path, and consumes the authoritative 1.20 header/source ABI using
`ReadProcessMemory`. Null state pointers, an uninitialized clock, invalid speed,
missing local player or missing played-character binding are rejected. Two
matching clock samples must fit within three attempts, and state slots/player
identity are reread before return. This is a clock and campaign-player prefix,
not a claim to the full in-process provider's `map_ready` contract.

The clock receipt includes native `date_raw`, `speed`, `paused`, player IDs,
clock-prefix SHA-256, read-only access mask and SHA-256 of the consumed C++
header, C++ source and Python reader. The exact route contract uses 24 raw units
per simulation day. The package does not assume a raw-date epoch or leap-year
calendar: its `calendar_projection` is explicitly
`unbound_requires_independent_save_date`. A calling project must cross-check
its first paused native read with its independently inspected save date before
claiming a calendar date or a century milestone.

The companion suite independently exercised the read-only clock against its
core-only R6 run, with the exclusive desktop owner performing the call. The
`clock-baseline-001.json` receipt records PID 7548, raw date 77535240, speed 5,
paused true, local-player ID 1 and played-character ID 7923; its independent
seed save date is 3851.1.21. The receipt binds C++ header SHA-256
`3a6a701735402a75dd4c99deb6aa1027aff7283d1a636784ebb8efb68d41308c`,
C++ source SHA-256
`a5c1411c5c7db9838477a77209735d3aa47e18a291c9d7ebaf33e14885c23e6e`
and reader SHA-256
`439ad0934a0f0192eb8774f4b59c1379186b37bd9b753107705070357886a59e`.
This single anchor fits `24*((3851+5000)*365+20)` but does not establish the
epoch, month conversion or future leap-day behavior. The bounded offline
exact-EXE calendar locator investigation did not close that semantic contract;
raw dates remain authoritative and future annual save metadata must be checked.
R6 subsequently crashed after approximately 142 days of normal simulation,
without any DLL bridge attachment. A later clock read could overlap its exception
processing window; it is not health or long-duration gameplay proof. The new
crash-artifact guard addresses that observation gap.

Exact-build provider entry points are `native_bridge/include/xar_bridge/ck3_12002.hpp`,
`native_bridge/src/ck3_12002.cpp`, `ck3_12002_adapter.cpp` and
`ck3_12002_commands.cpp`. The 1.20.0.2 adapter expects EXE SHA-256
`AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D`.
The existing `NativeHeadlessGameplayDriver` opens the named-pipe endpoint in its
constructor and accepts separate `state_dir` and `save_dir`. The main
`bridge.mcp_server.create_server(driver, profile_dir=...)` supports consuming
the same provider with the calling run's actual userdir, unlike the native CLI's
implicit `<state-dir>/profile` layout.

The existing driver's default snapshot projection binds a legacy one-life
identity even if its controller is never started. The profile consumer therefore
passes the explicit `episode_projection="native_campaign"` option. This new
authoritative provider option skips that counter-policy projection, follows the
engine's actual played character through ordinary succession and adds no
invented game-rule binding. Supplying an episode lifecycle binding together
with this mode is rejected. The bootstrap requires that mode marker in its
snapshot readback. Default callers retain the previous one-life behavior.

This package does not establish live long-duration gameplay or ordinary succession,
event policy or save/reload acceptance. Existing normal speed, pause/resume,
event and checkpoint commands remain in the authoritative provider. The narrow
ordinary-player tools call those existing service methods, require a map-ready
revision, poll before actions, repeat profile guards and retain a native snapshot
after each action. Saves and event queries/selections require a paused frame.
ACKs with an unchanged event, unmaterialized pause/speed or absent/mismatched
checkpoint bytes produce RED receipts, without replay. These tools do not bind
an episode or require an XAR game rule. The existing one-life controller's current
ordinary-succession environment binder requires an actual frozen `xar_off` rule
and fresh no-pact campaign; a project without that rule must not invent one.
The bootstrap does not start the one-generation controller, observe, reseed,
jump dates, skip simulation ticks or alter AI behavior. It performs no desktop
input or OCR. Live attach and gameplay are left to the exclusive desktop owner.

Validation: 6 read-only clock tests, 18 profile/bootstrap/ordinary-player tests,
7 real-provider endpoint campaign-projection tests and 11 existing semantic-profile tests
plus 4 real-provider delayed postcondition tests
passed, including official in-memory MCP schemas, stale process/Steam/lease
rejection, wrong userdir and artifact rejection, native hello/build rejection,
ACK without containment proof, one-shot attachment across server instances and
native receipt readback, boot/null/incomplete/unstable byte reads and the exact
read-only Windows process-access mask. These are deterministic fixtures, not live CK3 proof.

ACKs now use a bounded read-only semantic postcondition wait; the trigger,
operation-specific checks and preserved R8 RED are documented in
[the wait contract](profile-native-postcondition-wait-2026-10-02.md).
`open_kaishek` is not applicable to Windows process identity, named pipes and
native byte/transport bindings; there is no Clausewitz script semantic change.

DLL build qualification is a separate work package: a successful artifact link
must not be described as a complete fresh-build/test pass. Preserve exact source,
build log and artifact SHA-256 together, including failed fixture qualification.

The exact 1.20.0.3 profile keeps this schema with its actual `.3` version and
current guard/installation identity. Local scoped production DLL/injector
qualification, independent pause-provider adaptation and source/artifact pins
are in [the patch3 consumer handoff](native-campaign-patch3-local-qualification-2026-10-02.md).

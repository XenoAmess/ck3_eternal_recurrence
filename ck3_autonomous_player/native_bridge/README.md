# CK3 native bridge

This directory contains the first native slice of the dual-backend CK3 player.
Its current first gameplay slice is intentionally small:

- `xar_ck3_bridge.dll` connects to the named pipe supplied in
  `XAR_CK3_BRIDGE_PIPE` and emits length-prefixed UTF-8 JSON frames;
- `xar_ck3_bridge_injector.exe <pid> <dll-path>` injects the x64 bridge into
  an existing x64 process with `VirtualAllocEx` + `WriteProcessMemory` +
  `CreateRemoteThread(LoadLibraryW)`; adding `--pipe <pipe-name>` also invokes
  the exported `XarCk3BridgeStartWithPipe` inside a process that did not
  inherit bridge environment variables;
- the first frame is a build identity/capability announcement; gameplay
  capabilities are present only when the process executable exactly matches
  the pinned CK3 1.19.0.6 SHA-256;
- the DLL emits a heartbeat every 250 ms, publishes semantic state snapshots
  on actual date/speed/pause/map-ready/local-player/active-event/pending-
  interaction changes, and answers a framed `ping` with `pong`; if the MCP
  daemon exits or drops its pipe, the same injected DLL reconnects to a new
  server under the same pipe name and republishes its current snapshot;
- for the exact pinned build it accepts `pause-map`, `resume-map`, and fixed
  `set-speed-1`..`set-speed-5` steps plus one-based
  `select-event-option-1..N` and `save-checkpoint` through CK3's native locked
  command queue; it also accepts or rejects the current pending character
  interaction without opening or focusing its notification window, and now
  exposes active wars/player armies plus native `raise-troops-default`,
  `move-army-<army_id>-to-<province_id>`, and
  `disband-army-<army_id>` commands; explicit `query-declarable-wars`
  returns current generation-bound choices, `declare-war-<choice>` submits
  one exact revalidated choice, and `enforce-demands-<war_id>` resolves a
  100% war led by the player; `query-arrange-marriage-choices` returns
  natively valid direct matches for the played character and
  `arrange-marriage-<played_id>-<candidate_id>` submits only a cached exact
  generation-bound pair;
- `xar_ck3_bridge_host.exe` creates a minimal target with
  `CREATE_SUSPENDED`, runs the PID injector, verifies the complete
  hello/heartbeat/ping/pong exchange from inside that target, deliberately
  replaces the pipe server and verifies a second exchange without reinjection,
  and only then resumes its original primary thread.

The bridge protocol is deliberately not MCP. The external Python daemon owns
MCP (stdio first, Streamable HTTP if a persistent service is later useful) and
translates typed CK3 tools into these small local frames. Consequently MCP,
planner and schema changes do not require restarting CK3. Native DLL changes
require a new injection generation; `--pipe` can attach such a build to an
already-running CK3 process, while a clean production launch still injects it
before the first resume.

The DLL hashes the host executable once, selects an exact-build adapter from
the registry, and exposes only that adapter's capability set. Semantic DTOs and
results live in `game_contract.hpp`; pipe dispatch depends on `GameAdapter`
rather than the 1.19.0.6 bindings. `hello` retains the protocol-v1 expected
version/SHA fields and adds `game_adapter_id` plus
`game_adapter_status=ready|unsupported_build`. See
[`docs/ck3-native-version-adapters.md`](../../docs/ck3-native-version-adapters.md)
for the migration contract and per-capability upgrade workflow.

## Build and offline test

Use an x64 Visual Studio developer shell with CMake and Ninja:

```powershell
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
ctest --test-dir build --output-on-failure
```

The offline tests inject only into the purpose-built
`xar_ck3_bridge_target.exe`; they do not start or touch CK3. One test covers
the suspended environment-driven launch. The second starts the target normally,
removes `XAR_CK3_BRIDGE_PIPE` from its child environment, confirms that it is
already running, then attaches and starts the bridge with an explicit pipe. A
successful run includes:

```text
PASS: suspended=1 injected=1 protocol=1 hello=1 heartbeat=1 pong=1 reconnected=1 resumed=1 target_exit=0 ...
PASS: already_running=1 inherited_pipe=0 explicit_pipe=1 injected=1 hello=1 heartbeat=1 pong=1 target_exit=0
```

For direct use against an x64 process that has inherited
`XAR_CK3_BRIDGE_PIPE`:

```powershell
.\xar_ck3_bridge_injector.exe <pid> .\xar_ck3_bridge.dll
```

For a process that is already running and therefore did not inherit the pipe
environment variable, start the pipe server first and use:

```powershell
.\xar_ck3_bridge_injector.exe --pipe \\.\pipe\xar_ck3_native <pid> .\xar_ck3_bridge.dll
```

The reusable implementation is
`xar::bridge::InjectLibrary(HANDLE, std::filesystem::path)` or
`InjectLibraryAndStart(HANDLE, path, pipe_name)`, exposed by the
`xar_bridge_injector` static library. The explicit-start path locates the
loaded remote module, derives the exported start function from its PE-relative
address, copies the pipe name into remote memory, and invokes it with a second
remote thread. The supplied process handle must allow remote allocation,
writes, module queries, and thread creation.

## Frame contract v1

Each frame is:

```text
uint32 little-endian payload_bytes
payload_bytes of compact UTF-8 JSON
```

The current maximum payload is 1 MiB. Frame types are `hello`, `heartbeat`,
`state_snapshot`, `execute_step`, `command_result`, `ping`, and `pong`.
`hello.capabilities` is authoritative. Non-matching executables advertise only
bridge identity, heartbeat, and ping; they never expose game reads/actions.

The snapshot currently contains `date_raw`, `speed`, `paused`, `map_ready`,
`local_player_id`, nullable `played_character`, `active_event` and
`pending_character_interaction` objects, and the last checkpoint queue
submission. It also contains `active_wars` and `player_armies`. Each active
war identifies the player's side, reports war score relative to that player,
and groups currently observable armies into `allied_armies` and
`enemy_armies`. Army records expose `army_id`, owner `CharacterID`, nullable
current province, and whether the played character controls them. Soldier
count and in-flight move target are deliberately absent: two candidate
`+0x38/+0x44` interpretations conflict in the pinned binary, so this slice
does not publish a guessed value. `played_character` exposes the current played `CharacterID` and
the engine's alive/dead projection; the one-generation planner treats dead as
an episode terminal and never continues as the heir. The pending object exposes the engine component instance ID, the
sender's 32-bit `CharacterID` handle, and whether CK3 classifies it as an
acknowledgement-only auto-accept notification. `map_ready` stays false until
CK3 resolves a valid local player, so
the caller can wait through early startup snapshots without retrying actions.
The player field is Jomini's 32-bit local/network player ID used by the pause
command, not CK3's 64-bit played-character ID. Public speed is `1..5`; the
bridge maps it to and from CK3's zero-based native payload `0..4`. Event steps
likewise use public option numbers `1..N` and translate to the command's native
zero-based option index. Checkpoint results expose the fixed requested save
name `xar_checkpoint`, submission sequence, and date; `submitted` describes
the queue operation, while the produced file remains the completion check.

`accept-pending-character-interaction` and
`reject-pending-character-interaction` construct CK3's own 0x28-byte
`CReplyCharacterInteractionCommand` for the currently published pending
instance. They return a distinct error for acknowledgement-only notifications.

`raise-troops-default` resolves CK3's own default rally province, runs the
native 0x50-byte command constructor and validator, queues its clone, and then
destroys the stack command. `move-army-*` resolves both component IDs, derives
CK3's direct-move mode, runs the native can-move helper, initializes the
0x168-byte command's path storage, and queues it. `disband-army-*` uses the
native 0x28-byte command. Move and disband reject armies not owned by the
current played character. Dynamic IDs are parsed as complete positive decimal
strings; trailing bytes, signs, whitespace, missing separators, and overflow
are rejected.

War declaration discovery is an explicit request rather than part of the
250 ms snapshot publisher: it evaluates current CBs across live characters
and returns `declaration_id`, stable `casus_belli_key`, target/claimant IDs,
and target title IDs. The ID's numeric CB/configuration components are runtime
ordinals, not persistent semantic IDs. `declare-war-*` consumes only a choice
from that query and re-enumerates the exact target before constructing CK3's
native character-interaction command. `enforce-demands-*` uses the native war
resolution context builder and accepts only a war for which the played
character is the primary war leader.

Marriage discovery is also an explicit request rather than a heartbeat field.
Its successful `command_result` contains `query_sequence` and an
`arrange_marriage_choices` array. Each item contains
`choice_id="<played>-<candidate>"`, `played_character_id`, and
`candidate_character_id`, all using the complete signed CharacterID handles.
`arrange-marriage-*` resolves only an exact item from the latest cached query,
then repeats native context construction and validation before sending. The
minimal route matches the played character directly with the candidate; CK3
derives marriage versus betrothal from their current state.

## Runtime integration

`xar_autoplayer.runtime` already creates `ck3.exe` with `CREATE_SUSPENDED`,
assigns it to the tracked Job, verifies its identity, and only then resumes its
main thread. The native MCP mode can now reuse the tested injection sequence in
that existing suspended interval:

1. the external daemon creates the pipe and supplies its name in the child
   environment;
2. runtime creates the suspended CK3 process exactly as it does now;
3. runtime calls `InjectLibrary` (or invokes the PID CLI) for this DLL;
4. runtime resumes CK3 and waits for `hello`;
5. pure `native-headless` routes only advertised native capabilities and
   returns unsupported for every other action; separately configured
   `hybrid-fallback` may route those other families to data-Mod or visual
   backends.

The loader, exact-build rejection, snapshot offsets, and command object layouts
are covered by offline fixtures. On 2026-08-23 the bridge was also attached to
the pinned live `ck3.exe` while its window remained minimized. The official MCP
client called `ck3_take_snapshot`, `ck3_execute_step`, and
`ck3_wait_for_change`; the native queue resumed the map, advanced `date_raw`
from `53171400` to `53171424`, then paused it again. No OCR, screenshot, focus,
keyboard, or mouse backend participated in that loop. A later clean minimized
session waited through `map_ready=false`, ran 90 composite `life-advance`
turns for 94 game days, and remained paused and minimized after every turn.
Another continuous run found event instance `14` with five options after 130
game days, submitted option one, and observed the active event change to
instance `15` with three options. Finally, minimized `save-checkpoint`
materialized `save games/xar_checkpoint.ck3` (63,367,813 bytes) and its command
result matched the forced `last_checkpoint_submission` snapshot. These are
live completion checks, not only queue-submission fixtures.
Reverse-engineering evidence, exact RVAs/signatures, and unsupported event
boundaries are recorded under [`research/`](research/README.md).

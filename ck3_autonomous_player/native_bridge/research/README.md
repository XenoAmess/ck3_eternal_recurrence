# CK3 1.19.0.6 native-headless anchors

This directory freezes the first implementation-grade reverse-engineering
result for the local `ck3.exe`. The analysis was offline only: no CK3 launch,
process attachment, DLL injection, or desktop query was used to obtain it.

Pinned executable:

- version: `1.19.0.6`
- size: `95,206,008` bytes
- SHA-256: `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- PE timestamp: `0x6A1EEE6D`
- preferred image base: `0x140000000`

Run the dependency-free offline verifier from the repository root:

```powershell
py ck3_autonomous_player/native_bridge/research/scan_anchors.py
```

The DLL separately hashes its current process executable and advertises game
capabilities only for this exact digest. A different CK3 build retains only
bridge identity/heartbeat/ping.

## Implemented capability matrix

| Capability | Native-headless state | Evidence | Visual fallback |
|---|---|---|---|
| `game.state.snapshot.date_raw` | implemented, live minimized probe passed | high static + offline layout fixture + live exact-build probe | never inside native driver |
| `game.state.snapshot.speed` | implemented, live minimized probe passed | high static + offline layout fixture + live exact-build probe | never inside native driver |
| `game.state.snapshot.paused` | implemented, live minimized probe passed | high static + offline layout fixture + live exact-build probe | never inside native driver |
| `game.state.snapshot.local_player_id` | implemented, live minimized probe passed | high static + offline layout fixture + live exact-build probe | never inside native driver |
| `game.state.snapshot.map_ready` | implemented, live false→true transition passed | resolved local-player getter + early/ready fixture + minimized live probe | never inside native driver |
| `game.command.pause-map` | implemented, live minimized probe passed | high static + offline command/queue fixture + live exact-build probe | explicit upper-layer policy only |
| `game.command.resume-map` | implemented, live minimized probe passed | same native pause command with requested byte `0` | explicit upper-layer policy only |
| `game.command.set-speed-1..5` | implemented, live minimized probe passed | high static + offline command/queue fixture + live exact-build probe | explicit upper-layer policy only |
| `game.state.snapshot.active_event` | implemented, minimized live probe passed | high static current-event getter + offline layout fixture + live instance transition | never inside native driver |
| `game.command.select-event-option-1..N` | implemented, minimized live probe passed | high static command/queue layout + offline fixture + live option submit | explicit upper-layer policy only |
| numeric event option count/indexes | implemented, minimized live probe passed | executor bounds-check and option-array layout at RVA `0x33E68C0` + live 5→3 option snapshots | never inside native driver |
| `game.command.save-checkpoint` | implemented, minimized live file creation passed | high static `CAutoSaveCommand` layout + offline queue fixture + 63,367,813-byte live save | explicit upper-layer policy only |
| event title/option text | unsupported | no repeatable localized text projection yet | unsupported in pure native mode |
| played-character `CharacterID` | unsupported | do not confuse with 32-bit local player ID | unsupported in pure native mode |
| main-thread tick hook | anchor-only/not located | command submission uses a locked queue, so it is not a prerequisite for the first loop | unsupported |

`native-headless` must return unsupported for the rows marked unsupported.
`hybrid-fallback` may explicitly choose data-Mod or visual paths;
the native DLL itself never restores/focuses the window, captures pixels, or
sends keyboard/mouse input. When CK3 is minimized, visual fallback remains
unavailable unless an upper layer explicitly chooses to restore the window.

## State anchors and widths

- `*(base + 0x570E068)` is `CGameState`. The date storage begins at `+0x08`
  and is eight bytes as a `HistoricalDate` object. The initial bytes are
  `F8 77 9C 02 FF FF FF FF`; engine date arithmetic repeatedly consumes the
  **low signed dword**, including `(date_raw - 0x029C55C0) / 24`. The bridge
  therefore publishes that observed 32-bit tick value as `date_raw` and does
  not mislabel the unclassified high dword as a 64-bit calendar scalar.
- current native speed is zero-based `int32` at `CGameState + 0x70`; core RVA
  `0x346AC80` writes the same field. The public bridge contract translates
  native `0..4` to user-facing `1..5` in both directions, matching
  `speed_1 -> SetGameSpeed(0)` through `speed_5 -> SetGameSpeed(4)` in the
  original HUD.
- `*(base + 0x570F7B8)` is the Jomini game state. Paused is `uint8 +0x20`;
  core RVA `0x346B850` writes it and `int32 +0x24` as the player ID.
- its player collection pointer is `+0x18`; collection `+0x1F0` and the
  resolved local player object `+0x70` both hold the same **32-bit local/network
  player ID**. This ID is correct for `CPauseGameCommand`; it is not CK3's
  64-bit `CharacterID`, so the public field is named `local_player_id`.
  `map_ready` is stricter: it becomes true only when RVA `0x346B7C0` resolves
  a local-player object and that object's `int32 +0x70` ID is non-negative.
  Startup snapshots may therefore expose date/speed/pause while keeping
  gameplay commands gated until the map has actually finished initializing.
- `CGameState + 0xA0` points to CK3 game data, whose embedded event manager is
  at `+0x2F4C0`. Engine getter RVA `0x2706AD0` locks that manager, scans its
  active-event pointer array (`+0x1F18`, count at `+0x1F24`) backward, applies
  the local-player/current-event filters, and returns the same actionable
  event consumed by the event UI. The event instance ID is `ActiveEvent
  +0x1BC`; its event-data pointer is `+0x1B0`; option count is `EventData
  +0x1BC`.

## Command queue and object layouts

The common submission wrapper is RVA `0x973E00`; the command manager object is
`base + 0x57621F0`. It calls the command virtual at `+0x40` to clone the stack
object, then calls RVA `0x341D990`. For UI channel flags `7`, that function
takes the queue lock at the manager's internal queue `+0x78`, enqueues, and
unlocks. This is strong static evidence that the bridge worker may submit
without a main-thread callback; the minimized pause/speed probe has already
confirmed that queue path. Event selection still needs its bounded minimized
live probe.

`CPauseGameCommand` is `0x28` bytes: primary vtable at `+0x00`, flags byte `8`
at `+0x08`, secondary vtable at `+0x18`, local player ID at `+0x20`, requested
pause byte at `+0x24`. The native UI constructs exactly this shape at RVA
`0xA067DE` and submits with channel flags `7`.

`CSetGameSpeedCommand` is also `0x28` bytes: primary vtable at `+0x00`, zero
flags byte, secondary vtable at `+0x18`, and `int32 speed` at `+0x20`. The UI
constructs it at RVA `0xA074E0` and submits with channel flags `7`.

`CSelectEventOptionCommand` has `int32 event_instance_id` at `+0x20` and
`int32 option_index` at `+0x24`. Executor RVA `0x26FF190` resolves the active
event and sends the event data plus index to RVA `0x33E68C0`, which reads
`option_count` at `+0x1BC`, rejects negative/out-of-range indexes, then selects
`options[index]` from the pointer array at `+0x1B0`. Public steps are numbered
`select-event-option-1..N`; the bridge subtracts one only when constructing
this native payload.

`CAutoSaveCommand` is `0x40` bytes: primary vtable `0x40AABE8`, flags byte
`0x20` at `+0x08`, secondary vtable `0x40AAC80` at `+0x18`, and a CK3/MSVC
small string at `+0x20` (inline bytes, size at `+0x30`, capacity at `+0x38`).
The native save scheduler constructs and submits this shape with channel flags
`7` at RVA `0x2051031`; executor RVA `0x26D4360` ignores an empty name and
passes a non-empty name to the game save path. `save-checkpoint` requests the
fixed short name `xar_checkpoint`. Its command result and the next forced
snapshot report submission sequence, requested name, and `date_raw`; these
confirm queue submission and deliberately do not claim asynchronous disk
completion.

## Completed and next live acceptance

The exact pinned build completed this bounded gameplay probe on 2026-08-23:

1. obtain the first native snapshot while the CK3 window is minimized;
2. submit `set-speed-3` and `resume-map`, then use the public MCP
   `ck3_wait_for_change` tool to observe speed `3` plus `date_raw` advancing
   from `53171400` to `53171424` without restoring or focusing the window;
3. submit `pause-map`, observe a successful command result and `paused=true`;
4. keep every unadvertised action explicitly unsupported in pure native mode.

The same exact build then completed the next two background slices:

1. a clean session published an early `map_ready=false` snapshot and later
   transitioned to `true` without action retries;
2. while still minimized, a continuous speed-five run advanced 130 game days,
   published active event instance `14` with five numeric options, accepted
   `select-event-option-1`, and next published instance `15` with three options;
3. a separate minimized session accepted `save-checkpoint`, forced a matching
   `last_checkpoint_submission` snapshot, and materialized
   `save games/xar_checkpoint.ck3` at 63,367,813 bytes (SHA-256
   `A50E61B839CD80C08661D402A9BC0D3EA42FDFD418EE21C294A089657D69BFA2`).

No OCR, screenshot, focus, keyboard, or mouse backend participated. The next
native gameplay priorities are checkpoint restore and semantic
marriage/inheritance/war commands; event and save are no longer pending live
acceptance.

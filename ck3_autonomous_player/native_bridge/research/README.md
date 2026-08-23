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
| `game.state.snapshot.played_character` | implemented, live probe pending | player-character manager + Character storage alive projection + offline layout fixture | never inside native driver |
| `game.state.snapshot.pending_character_interaction` | implemented; four live requests advanced before a reproducible global-storage false positive exposed the missing recipient filter; filtered build awaits bounded live replay | exact notification-recipient predicate + native reply validator + offline multi-player fixture | never inside native driver |
| `game.command.accept/reject-pending-character-interaction` | implemented; live accept advanced four locally addressed requests | high static UI enum/command/queue path + native actionability validation + offline command fixture | explicit upper-layer policy only |
| `game.state.snapshot.active_wars` | implemented, live probe pending | exact WarManager/storage/participant/score helpers + offline attacker/defender fixture | never inside native driver |
| `game.state.snapshot.player_armies` | implemented, live probe pending | exact Army storage/ID/owner/current-province fields + offline component fixture | never inside native driver |
| allied/enemy army current province | implemented, live probe pending | war participant helper classifies each observable army owner | never inside native driver |
| army soldier count / move target | unsupported | conflicting `+0x38/+0x44` interpretations at RVAs `0xC73D00` and `0x26B51B0`; no value guessed | unsupported |
| `game.command.raise-troops-default` | implemented, live probe pending | native default-province/construct/validate/clone/destruct lifecycle + offline fixture | explicit upper-layer policy only |
| `game.command.move-army-N-to-N` | implemented, live probe pending | native mode/can-move/path-init/clone/destruct lifecycle + offline fixture | explicit upper-layer policy only |
| `game.command.disband-army-N` | implemented, live probe pending | exact 0x28-byte command/vtables/clone + offline fixture | explicit upper-layer policy only |
| `game.command.query-declarable-wars` | native C++ core implemented, bridge route/live probe pending | exact declare-war UI CB registry/evaluator/item rules + offline SSO/heap-key and configuration fixture | explicit upper-layer policy only |
| `game.command.declare-war-<declaration_id>` | native C++ core implemented, bridge route/live probe pending | generation-bound exact re-enumeration + native context/validation/queue/destruction fixture | explicit upper-layer policy only |
| `game.command.enforce-demands-<war_id>` | native C++ core implemented, bridge route/live probe pending | exact WarOverview victory context builder + common interaction command lifecycle fixture | explicit upper-layer policy only |
| event title/option text | unsupported | no repeatable localized text projection yet | unsupported in pure native mode |
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
- `CK3GameData + 0x1D4F0` is the player-character manager. Its pointer array
  begins at `+0x58` with count at `+0x64`; each record's local-player key at
  `+0xD8` selects the current player and `int32 +0xB0` is the played
  `CharacterID`. `*(base + 0x570C130)` is the Character component storage;
  the resolved Character object's pointer at `+0x1C8` is null while alive and
  non-null on the native death path. The bridge publishes only
  `{character_id, alive}` and does not infer an heir from this manager.
- `CGameState + 0xA0` points to CK3 game data, whose embedded event manager is
  at `+0x2F4C0`. Engine getter RVA `0x2706AD0` locks that manager, scans its
  active-event pointer array (`+0x1F18`, count at `+0x1F24`) backward, applies
  the local-player/current-event filters, and returns the same actionable
  event consumed by the event UI. The event instance ID is `ActiveEvent
  +0x1BC`; its event-data pointer is `+0x1B0`; option count is `EventData
  +0x1BC`.
- `*(base + 0x57BF1C8)` is the component storage used by the original
  character-interaction notification UI to resolve a pending interaction ID.
  Its slot array is `+0x20`, capacity is `int32 +0x2C`, and each 0x10-byte
  slot stores the object pointer at `+0x08`. A valid pending object repeats its
  component ID at `+0x10`; the low 24 bits are its slot index. UI `GetSender`
  resolves the sender from the `int32 CharacterID` at pending object `+0x2F0`.
  The storage is global: slot order does **not** imply that the request belongs
  to the local player. Notification enumeration at RVA `0xD9DAE0` resolves the
  currently played Character and calls exact predicate RVA `0x1266BA0` for
  each candidate. That predicate accepts routing kinds `0` and `2` only when
  CharacterID `+0x2F4` is the played Character, kind `1` only when CharacterID
  `+0x300` is the played Character, rejects other kinds, and checks the pending
  object/context state. The bridge performs the cheap routing comparison
  before calling the same predicate, then constructs an accept reply and calls
  native command validator RVA `0x26B3540`. Only a candidate passing both is
  published. Byte `+0x5C6` is the UI's `IsAutoAcceptNotification` value;
  those require reply enum `4` (acknowledge), so the accept/reject snapshot
  deliberately omits them.
- `CK3GameData + 0x29C20` is `CWarManager`; its `+0x20` pointer is the
  `ComponentStorage<CWar>`. A live `CWar` repeats its component ID at `+0x08`
  and has a null end marker at `+0x358`. Attackers at `+0x20` and defenders at
  `+0x80` are participant containers (pointer array `+0x08`, count `+0x14`,
  member `CharacterID` at element `+0x08`). Helper RVA `0x2224870` performs
  membership tests. RVA `0x222A8A0(war, nullptr)` returns attacker-relative
  `int32` war score, so the bridge negates it for a defending player.
- `base + 0x570CC80` is a pointer slot whose single dereference is
  `ComponentStorage<CArmy>`. RVA `0xA84603` ends at `0xA8460A`; adding its
  signed RIP displacement `0x4C88676` resolves to `0x570CC80`. Do not repeat
  the discarded hand-arithmetic result `0x572CC80`: it points two MiB beyond
  the real slot. On 2026-08-23 the wrong RVA reproducibly caused `C0000005`
  during the first live snapshot at DLL RVA `0x890F` while reading the bogus
  storage object's `+0x20`; the minidump is in local crash bundle
  `ck3_20260823_213129`. `CArmy +0x10` is its
  component ID, `+0x174` is owner `CharacterID`, and `+0x20` is current
  `Province*` (`Province +0x10` repeats its positive ID). The controllable
  projection is owner equals the current played character. Candidate soldier
  and move-target reads are omitted: RVA `0xC73D00` treats `+0x38/+0x44` as a
  four-byte component-ID vector, while RVA `0x26B51B0` treats those offsets as
  an eight-byte pointer vector. Their true relationship is not uniquely
  classified, so the bridge publishes neither field.

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

`CReplyCharacterInteractionCommand` is `0x28` bytes. The original UI action
at RVA `0x1268270` writes primary vtable `0x4082930`, zero flags at `+0x08`,
secondary vtable `0x4082900` at `+0x18`, pending component ID at `+0x20`, and
reply enum at `+0x24`, then submits with channel flags `0x0E`. Reflection
thunks tie UI methods to enum `0=accept`, `1=reject`, `2=block`, and
`4=acknowledge`. Heap clone RVA `0x8038E0` independently confirms the `0x28`
size and both payload offsets. Validator RVA `0x26B3540` resolves the pending
component, verifies its live object and interaction context, and accepts enum
`0` after those common checks. The bridge runs this validator on the exact
command shape before advertising a pending request as accept/reject-actionable.

## Reproduced global-pending blocker

The first live interaction loop advanced four consecutive requests, then the
old component-storage scan parked on instance `1308622950`. Native accept and
reject submissions both left that instance unchanged until the driver's
postcondition timed out. This was an actual-use failure: the scan returned the
first globally live component without checking that its recipient was the
played Character. The corrected offline fixture places another character's
valid component in the lower storage slot, asserts that it is skipped, and
publishes only the later locally routed component after the exact CK3
visibility predicate and accept-command validator both pass.

`CRaiseTroopsCommand` is `0x50` bytes. RVA `0x224CC80(Character*)` resolves
the game's default rally province. Constructor RVA `0x26D6FC0` receives the
played `CharacterID` and one `{province_id, -1}` entry, installs vtables
`0x41226D8`/`0x41226A8`, and produces the same `+0x40=-1`, `+0x44=1`,
`+0x48=false` shape as the original path at RVA `0x27A2198`. The bridge calls
validator `0x26D7150(command, nullptr)`, submits with flags `7`, then calls
destructor `0x10E7950(command, 0)` after the queue synchronously clones it.

`CMoveArmyCommand` is `0x168` bytes with vtables `0x432BF18`/`0x432BFB0`.
The direct-target path at RVA `0x186B232` writes `+0x20=2`, ArmyID at `+0x24`,
destination ProvinceID at `+0x28`, move mode at `+0x2C`, `+0x30=2`, and
`+0x34=1`. The bridge reproduces the original helper order: mode
`0x26B51B0(army, province, 1)`, can-move
`0x26B4610(2, army, mode)`, path initialization
`0xC7BA70(command+0x38)`, submit flags `7`, then destructor
`0x26B46D0(command, 0)`. Heap clone RVA `0x26C1E50` confirms size and payload.

`CDisbandArmyCommand` is `0x28` bytes: vtables
`0x432BFE0`/`0x432C078`, `+0x20=2`, and ArmyID at `+0x24`; it submits with
flags `7`. Clone RVA `0x26C2090` independently confirms the complete layout.

Declare-war discovery is an explicit strategic query, not part of the 250 ms
heartbeat snapshot. The global query scans live Character components and runs
the original UI evaluator for each target/type pair, which is intentionally
too expensive for continuous polling; a target-scoped native overload is also
available when the planner already knows a CharacterID. The query returns a
generation-bound opaque declaration choice:

- `target_character_id`;
- `casus_belli_index`, the current `CCasusBelliTypeDatabase` array ordinal;
- `configuration_index`, or `-1` for CK3's combined/special-CB item;
- `casus_belli_key`, the stable canonical script key;
- exact claimant CharacterID and target TitleID vector used by the command.

The public opaque ID remains `<target>-<cb-index>-<configuration-index>` and
must be resolved against the query generation. The dense CB index is never
presented as a semantic CasusBelli ID. `CCasusBelliType` inherits
`CGameDatabaseObject`: constructor RVA `0x345E620` writes the dense index at
`+0x10`, hashes the key into `uint32 +0x14`, and copies the canonical MSVC
string to `+0x18` (size `+0x28`, capacity `+0x30`). The bridge publishes the
full string rather than treating the non-unique 32-bit hash as identity.

The original declare-war UI at RVA `0x1086440` reads the CB pointer array at
database `+0x68`/count `+0x74`, skips a type when `[[type+0x38]+0x211]` is
nonzero, clears global `CPdxArray<SValidCasusBelliConfiguration>` at
`base+0x4FED598`, then calls evaluator RVA `0x2D95D00(type, actor, target,
scratch, false, false, nullptr)`. Each `0x98`-byte configuration holds claimant
CharacterID at `+0x00` and the declaration's target TitleID array at `+0x08`.
When type flag bit 20 at `+0x1718` is clear, the UI emits one choice for each
configuration whose target array is nonempty. Otherwise it emits one choice
with claimant `-1` and concatenates every configuration's target array. The
native fixture reproduces both branches and both MSVC key-string forms.

`declare-war-<declaration_id>` re-runs that evaluator for the target and CB
ordinal and requires the complete cached choice, including key, claimant and
TitleIDs, to match before submitting. It constructs the 0x338-byte character
interaction context using `CK3GameData +0x1070`, verifies the special data is
a `CWarDeclaration` with vtable `0x411DAA0`, writes CB pointer `+0x08`, native
TitleID array `+0x10`, and claimant `+0x28`, then follows the UI's refresh
`0x2C40950`, finalize `0x2C40B20`, and validation `0x2C43F00` calls.
Constructor RVA `0x26B3220` creates the complete 0x368-byte
`CSendCharacterInteractionCommand` (vtables `0x40829F8`/`0x40829C8`, copied
context at `+0x20`, derived payloads at `+0x358/+0x360`). Submission uses flags
`0x0E`; the copied and original contexts are then destroyed with RVA
`0x2C3F380`, matching UI send RVA `0xFE5190`.

`enforce-demands-<war_id>` resolves the same live `CWar` storage used by the
snapshot and rejects both a non-participant and a participating ally who is
not one of the primary war leaders at `+0x288/+0x28C`. It default-constructs
a 0x338-byte context with RVA `0x2C3F300`, then calls exact
WarOverview builder `0xC569F0(context, war, false)`. That builder compares the
played CharacterID with primary sides at `CWar +0x288/+0x28C`, chooses the
opponent, and uses the enforce-demands interaction at `CK3GameData +0x1018`.
WarOverview send RVA `0xF54FA0` proves the remaining native path is validation,
`CSendCharacterInteractionCommand` construction, submit flags `0x0E`, and
embedded-context destruction. Its visual confirmation window is only a UI
wrapper and is not part of the headless gameplay command.

The canonical marriage script key is `arrange_marriage_interaction` in the
1.19.0.6 base-game `00_marriage_interactions.txt`. Static UI paths show
`CSendCharacterInteractionCommand` is `0x368` bytes (vtables `0x40829F8` and
`0x40829C8`) and owns a copied context at `+0x20` containing four roles and
option data. This slice does not guess those still-unclassified fields. A
reply needs neither the key nor four role IDs: its pending component ID is the
complete engine payload, so incoming marriage/betrothal acceptance ships
independently of send-side construction.

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

No OCR, screenshot, focus, keyboard, or mouse backend participated. Checkpoint
restore, incoming character-interaction reply, played-character terminal
state, and the native war loop now have offline implementations. The bounded
next war acceptance is a minimized exact-build probe of declaration discovery,
declare war, raise, movement, enforce demands, and disband; event and save are
no longer pending live acceptance.

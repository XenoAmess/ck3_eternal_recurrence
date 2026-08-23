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
| `game.state.xar-one-life-settlement` | implemented, third minimized death snapshot passed while CK3 was minimized | exact live 12-global read + correct script-identifier registry + character EventTarget kind/ID ABI + independently proven CFixedPoint scale + dead-source fixture | never inside native driver |
| `game.state.snapshot.pending_character_interaction` | implemented; four live requests advanced before a reproducible global-storage false positive exposed the missing recipient filter; filtered build awaits bounded live replay | exact notification-recipient predicate + native reply validator + offline multi-player fixture | never inside native driver |
| `game.command.accept/reject-pending-character-interaction` | implemented; live accept advanced four locally addressed requests | high static UI enum/command/queue path + native actionability validation + offline command fixture | explicit upper-layer policy only |
| `game.state.snapshot.active_wars` | implemented, minimized live declaration projected a new war | exact WarManager/storage/participant/score helpers + offline attacker/defender fixture | never inside native driver |
| `game.state.war-primary-opponent` | implemented, live probe pending | exact primary-side fields + generation-safe opponent resolution + reused default-raise resolver + offline attacker/defender/non-primary fixture | never inside native driver |
| `game.state.snapshot.player_armies` | implemented, live probe pending | exact Army storage/ID/owner/current-province fields + offline component fixture | never inside native driver |
| allied/enemy army current province | implemented, live probe pending | war participant helper classifies each observable army owner | never inside native driver |
| army soldier count / move target | unsupported | conflicting `+0x38/+0x44` interpretations at RVAs `0xC73D00` and `0x26B51B0`; no value guessed | unsupported |
| `game.command.raise-troops-default` | implemented, live probe pending | native default-province/construct/validate/clone/destruct lifecycle + offline fixture | explicit upper-layer policy only |
| `game.command.move-army-N-to-N` | implemented and minimized-live accepted: player command submitted and army province changed | exact player-UI kind/channel plus native mode/state/can-move/path-init/clone/destruct lifecycle, offline fixture, and live movement | explicit upper-layer policy only |
| `game.command.disband-army-N` | implemented; live exposed the distinct command-target ID and corrected build awaits replay | exact 0x28-byte command/vtables/payload source/clone + offline fixture | explicit upper-layer policy only |
| `game.command.query-declarable-wars` | native C++ core implemented, bridge route/live probe pending | exact declare-war UI CB registry/evaluator/item rules + offline SSO/heap-key and configuration fixture | explicit upper-layer policy only |
| `game.command.declare-war-<declaration_id>` | native C++ core implemented, bridge route/live probe pending | generation-bound exact re-enumeration + native context/validation/queue/destruction fixture | explicit upper-layer policy only |
| `game.command.enforce-demands-<war_id>` | native C++ core implemented, bridge route/live probe pending | exact WarOverview victory context builder + common interaction command lifecycle fixture | explicit upper-layer policy only |
| `game.command.query-arrange-marriage-choices` | implemented; minimized-live empty result was correctly explained by the played character's existing spouse | exact interaction registry, bounded enumeration diagnostics, generation-validated relationship snapshot, native validation fixture | explicit upper-layer policy only |
| `game.command.arrange-marriage-<choice_id>` | native direct-player path implemented, minimized-live submit pending | generation-bound CharacterIDs + redirect/all-role/refresh/finalize/validate/common-send fixture; spouse/betrothal outcome is snapshot-observable | explicit upper-layer policy only |
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
- Jomini's global-variable accessor is the function-pointer slot at
  `base + 0x570F750`. `CJominiGlobalVariableLink` RVA `0x3410F80` calls it,
  then scans the container's `+0x10` entries with `int32 +0x1C` count and
  0x20-byte stride. Each entry has its script-identifier ID at `+0x08` and a
  complete 0x10-byte `CJominiEventTarget` at `+0x10`. These IDs do **not**
  belong to the generic PdxString table returned by RVA `0x3B58870`: live
  inspection showed that API maps `xa_settlement_ready` to ID `25393`, which
  the script-identifier table reverse-maps to `student_flirt`, while the actual
  global entry key is `44011`. The bridge instead gets the script-identifier
  table with RVA `0x3B971A0` and calls the locking lookup-only wrapper RVA
  `0x3B97020` with ABI `(table, int32* out, NativeStringView*) -> out`. That
  wrapper locks `table+0x48`, calls raw lookup RVA `0x3B96D40`, and unlocks; it
  never inserts a missing name. RVA `0x3B96E50` is lookup-or-insert and is not
  used by the reader. Live reverse lookup confirmed IDs `44011` for
  `xa_settlement_ready`, `44012` for `xa_settlement_source_character`, and
  `44023` for `xa_settlement_commit_serial`.
- The global-variable mutation path at RVA `0x338F221` independently proves
  numeric EventTarget kind `uint16 1` and signed `int64` CFixedPoint raw at
  payload `+0x08`. CFixedPoint conversion RVA `0x3A41DA0` divides that raw by
  the `100000.0f` constant at RVA `0x4594E08`; the signed magic-division
  sequence at RVA `0x3A48E16` independently gives the same scale. Score
  fields therefore cross the version-neutral boundary losslessly as
  `{raw, scale:100000}`. Integer/boolean globals are published only when raw
  is exactly divisible by 100000 (and booleans are exactly 0 or 1).
- `xa_settlement_source_character` is character EventTarget kind `4`, with the
  complete signed `int32` CharacterID at payload `+0x08`. Character resolver
  RVA `0x201AD30` proves this variant before doing the same generation-safe
  component-storage lookup as the bridge. The engine resolver then performs
  additional gameplay-liveness checks and returns null when
  `CCharacter+0x1A8` is null. On the second minimized production death on
  2026-08-24, read-only PID 60728 inspection found all twelve globals complete,
  source kind `4` / ID `29829`, the exact dead object still present in Character
  storage, and `CCharacter+0x1A8 == null`; native revision 24 consequently still
  returned `one_life_settlement=null`. The reader now decodes only proven kind
  `4` directly and requires that full-generation ID to resolve through Character
  storage to an object whose `+0x18` repeats the exact ID. It does not invoke the
  liveness-gated gameplay resolver. The offline fixture models both validity and
  resolver returning false/null while the dead object remains generation-valid
  in storage. A unique sidecar build using the corrected identifier registry
  then re-read the still-persisted third-death globals from minimized PID 119628
  without another game action. Snapshot `native:1` published source CharacterID
  `29829`, scores `{raw:680000, scale:100000}`, candidate/old/delta `6/0/6`,
  blessing/refusal/contract `1/0/0`, `record_written=true`, and serial `1`.
  All twelve lookups matched the live container entries, closing both the
  dead-source and ID-domain failure gates. The public settlement stays null
  unless `ready==1`, every payload field decodes, and a final reread still sees
  `ready==1`; no partial settlement is synthesized.
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
  `int32` war score, so the bridge negates it for a defending player. The
  primary attacker and defender CharacterIDs are at `+0x288/+0x28C` (also
  consumed by WarOverview context builder RVA `0xC569F0`). The snapshot picks
  the opposite primary by the player's participant side and re-resolves the
  complete generation-bearing CharacterID. It compares the own-side primary
  with the played CharacterID for `player_is_primary_war_leader`. For the
  resolved opponent, the already verified RVA `0x224CC80(Character*)`
  supplies `enemy_primary_default_raise_province_id`; that value is explicitly
  a fallback location for the opponent, not a decoded war goal or army target.
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
The actual player map UI path at RVA `0xA8464A` obtains mode with
`0x26B51B0(army, province, direct_target)`, checks
`0x2248860(army, mode)`, then constructs the command at RVA `0xA84722` with
`+0x20=1`, ArmyID at `+0x24`, destination ProvinceID at `+0x28`, move mode at
`+0x2C`, `+0x30=2`, and the direct-target flag at `+0x34`. It initializes
the path via `0xC7BA70(command+0x38)` and submits with player channel flags
`0x0E`. The command validator at RVA `0x26B4A3C` subsequently passes the
stored `+0x20` kind to complete can-move wrapper `0x26B4610`; the bridge
preflights the same wrapper with kind `1`, queues, then calls destructor
`0x26B46D0(command, 0)`. Heap clone RVA `0x26C1E50` confirms size and payload.
The superficially similar direct-target construction at RVA `0x186B232`
uses kind `2` and submit flags `7`: it is an AI/controller path, not the
player UI path. On the live player army, that wrong kind made the complete
wrapper fail after move-mode and army-state gates had both passed.
Move-mode RVA `0x26B51B0` can return sentinel `2`, which the complete wrapper
rejects before a command is constructed. The bridge reports that separately
from the `0x26B26A0(owner, 1)` character-state gate, the `0x2248860`
army-state gate,
and the remaining checks inside `0x26B4610`; do not infer the rejecting stage from a generic
`cannot_move` result.

A 2026-08-24 minimized live run raised army `83886341` at province `2619` and
still received the old generic rejection after about 49 days of actual time
advance, for both a neighboring province and changing enemy locations. Direct
memory reads showed route count `CUnit+0x44=0`, state `CUnit+0x170=0`, linked
`CArmy+0x5C=0`, and date field `CUnit+0x180` equal to the original raise date.
The `+0x5C=0` value also makes CK3's stop-gathering validator at RVA
`0x26B6230` return false, so this run is **not** blocked by ongoing gathering.
The linked army's `+0x128=-1` causes the optional association check inside
`0x2248860` to be skipped; it is not itself a rejection. The staged live probe
then passed both move-mode and `0x2248860`, but failed the complete wrapper
while the bridge supplied kind `2`; this reproduced the player-versus-AI
command-path mismatch above. Adding more time delay or a stop-gathering
command cannot address that failure. After changing the bridge to the player
path (`kind=1`, submit flags `0x0E`), the minimized live call returned
`move_submitted`; twelve seconds at speed 5 advanced roughly 35 in-game days
and the same army's province changed from `2619` to `2606`. This is the direct
gameplay acceptance for the move-command fix, not merely queue acceptance.

`CDisbandArmyCommand` is `0x28` bytes: vtables
`0x432BFE0`/`0x432C078`, and the command-target ID read from `CArmy+0x178` at
`+0x24`. The public step still uses the component ArmyID from `CArmy+0x10` to
resolve the army. The original player UI path at RVA `0xBC8EE0` calls validator
`0x26B5710(1, command_target_id, nullptr)`, writes player command kind `1` at
`+0x20`, and submits with flags `0x0E`. Kind `2` plus flags `7` at RVA
`0x187954F` is an AI-controller path; its control check at RVA `0x26B26A0`
rejects a player-owned army, so queueing that otherwise well-formed command is
a silent no-op. Clone RVA `0x26C2090` independently confirms the complete
command layout. The fixture gives the public and target IDs deliberately
different values, requires the `+0x178` value, and separately pins player kind,
validation, and channel flags.

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
TitleIDs, to match before submitting. It calls singleton getter RVA
`0x831890` and constructs the 0x338-byte character interaction context using
`CCharacterInteractionDatabase +0xF78`. It then verifies the special data is
a `CWarDeclaration` with vtable `0x411DAA0`, writes CB pointer `+0x08`, native
TitleID array `+0x10`, and claimant `+0x28`, then follows the UI's refresh
`0x2C40950`, finalize `0x2C40B20`, and validation `0x2C43F00` calls.
Constructor RVA `0x26B3220` creates the complete 0x368-byte
`CSendCharacterInteractionCommand` (vtables `0x40829F8`/`0x40829C8`, copied
context at `+0x20`, derived payloads at `+0x358/+0x360`). Submission uses flags
`0x0E`; the copied and original contexts are then destroyed with RVA
`0x2C3F380`, matching UI send RVA `0xFE5190`.

The `+0xF78` slot is pinned by the canonical `declare_war_interaction`
registration at RVA `0x2C3EB3B`. An earlier live build incorrectly used
`+0x1070`; the first minimized declaration then crashed inside the generic
context constructor because that slot contains unrelated `piety_level_%i`
data. The 2026-08-23 minidump recorded execute AV RVA `0x431F5B0` through the
wrong interaction's redirect evaluator before refresh, validation, queueing,
or destruction.

Changing only the slot to `+0xF78` exposed a second live failure. The minimized
sequence reached `map_ready`, successfully returned declarable-war choices,
then submitted `declare-war-29097-11-0`; CK3 exited with `0xC0000409`, WER
fast-fail code 7, and dump `ck3.exe.104500.dmp` contained an original C++
`std::bad_alloc`. Unwinding again stopped in the generic interaction-context
constructor, where the context's first qword was an allocator object rather
than an interaction definition. The remaining error was the base: `+0xF78`
had been added to `[game_state+0xA0]`, but all interaction slots belong to the
independent `CCharacterInteractionDatabase` returned by RVA `0x831890`.
Direct call sites in declare-war AI/UI (`0x187B4C9`, `0x18BE80E`,
`0x2E9E55D`), marriage UI (`0x126F609`, `0x126F6E9`, `0x126FF52`), and the
generic interaction machinery (`0x2C3FF5B`, `0x2C45BA8`, `0x2C46E6D`)
independently establish that base. The native fixture keeps non-null trap
objects at the obsolete `CK3GameData +0xF48/+0xF78` locations, so either
marriage or declare-war fails deterministically if the wrong-base regression
returns.

`enforce-demands-<war_id>` resolves the same live `CWar` storage used by the
snapshot and rejects both a non-participant and a participating ally who is
not one of the primary war leaders at `+0x288/+0x28C`. It default-constructs
a 0x338-byte context with RVA `0x2C3F300`, then calls exact
WarOverview builder `0xC569F0(context, war, false)`. That builder compares the
played CharacterID with primary sides at `CWar +0x288/+0x28C`, chooses the
opponent, and uses the enforce-demands interaction at
`CCharacterInteractionDatabase +0x1018`.
WarOverview send RVA `0xF54FA0` proves the remaining native path is validation,
`CSendCharacterInteractionCommand` construction, submit flags `0x0E`, and
embedded-context destruction. Its visual confirmation window is only a UI
wrapper and is not part of the headless gameplay command.

The canonical marriage script key is `arrange_marriage_interaction` in the
1.19.0.6 base-game `00_marriage_interactions.txt`. Registration xref
`0x2C3EA90` stores its interaction pointer at
`CCharacterInteractionDatabase +0xF48`, reached through getter RVA
`0x831890`.
All-role context constructor `0x2C3F000` proves the exact role layout:
actor `+0x2D8`, recipient `+0x2DC`, secondary actor `+0x2E0`, secondary
recipient `+0x2E4`, and the intermediary CharacterID at `+0x2E8`. The
marriage UI and AI direct paths leave `+0x2E8` at `-1`. Redirect helper
`0x2C3C4C0(interaction, &actor, &recipient, &secondary_actor,
&secondary_recipient, &intermediary)` mutates all five IDs in place. The original
direct path at `0x18FA80E` initializes all roles before redirect and then calls
`0x2C3F000(context, interaction, actor, recipient, secondary_actor,
secondary_recipient, intermediary, nullptr)` at `0x18FA8A1`; Win64 stack slots
`+0x20/+0x28/+0x30/+0x38` carry its last four arguments. Complete context
validation `0x2C43F00` remains the authoritative eligibility check. Marriage
versus betrothal is derived from the selected characters' age/state and is not
a separate payload bool.

The original UI also has a valid generic-constructor route: callbacks at
`0x126F923` and `0x126FAF3` update `+0x2E0/+0x2E4` on an existing context,
then refresh and finalize it. Therefore two-role construction followed by
those role updates is not, by itself, evidence of a bug. The bridge currently
uses the separately anchored all-role direct route: initialize
`(played, candidate, played, candidate, -1)`, redirect all five IDs, construct,
refresh, finalize, and validate. This is a pinned implementation route, not a
claim that the original UI route is invalid or that constructor selection
alone determines whether choices exist.

The minimized query remained `available` with no choices after that route was
installed. Bounded diagnostics showed contexts were constructed and rejected
by CK3's native validator. Live memory then established the actual state for
played CharacterID `29829`: no betrothed, primary spouse `34730`, and native
spouse list `[34730]`. The empty result was therefore valid for the tested
monogamous state, not a query-construction failure. Snapshot relationship
projection reads `CCharacter +0x1A0` FamilyData, `FamilyData +0x10`
betrothed, `+0x14` primary spouse, and the native CharacterID array at `+0x20`;
every emitted ID is re-resolved with its full generation. The internal absent
value is `-1`; bridge JSON emits null for the two scalar links and an empty
array for no spouses. `FamilyData +0x18` is not exposed.

The first headless query deliberately exposes only the immediately useful
direct path: played Character as both actor and secondary actor, candidate as
both recipient and secondary recipient. It scans live Character components,
constructs and natively validates each exact pair, and returns the two full
CharacterID handles. Those handles include the component generation and form
the opaque query choice; submission rebuilds and revalidates the exact pair.
No dense slot index is published as identity. The default marriage option is
left untouched; matrilineal configuration is a named interaction scope, not a
proven standalone byte offset. Generic UI send `0xFE5190` proves the remaining
path: validate, construct the `0x368`-byte `CSendCharacterInteractionCommand`,
submit flags `0x0E`, then destroy its owned context at `+0x20`. Incoming
marriage/betrothal acceptance remains the independent pending-interaction
reply path. A submitted adult marriage is complete only when the candidate's
full CharacterID appears in `played_character.spouse_ids`; a betrothal is
complete only when `played_character.betrothed_id` equals that candidate.

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

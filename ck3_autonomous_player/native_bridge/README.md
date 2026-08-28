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
  `disband-army-<army_id>` commands; it also exposes the exact player command
  `split-army-half-<army_id>` for one public CUnit ID and strict pair command
  `merge-armies-<destination_army_id>-with-<source_army_id>`; explicit
  `query-declarable-wars`
  returns current generation-bound choices, `declare-war-<choice>` submits
  one exact revalidated choice, and `enforce-demands-<war_id>` resolves a
  100% war led by the player; paused
  `query-war-termination-options-<war_id>` now returns read-only native
  surrender/white-peace/victory contexts and exact war-score evidence;
  `query-war-termination-terms-v1-<war_id>` separately returns the narrow
  claim-CB claimant/targets/claim-disposition slice. Native typed
  `surrender-war-<war_id>` and `offer-white-peace-<war_id>` both rebuild and
  revalidate their original contexts, but the Python action surface keeps both
  frozen until structured exit-terms v2 and campaign-decision readiness;
  paused read-only
  `query-army-strengths-v1` atomically publishes generation-checked soldier
  and AI base-power aggregates for the snapshot's player/allied/enemy armies;
  `query-combat-simulation-inputs-v2-<target>-<entry>-a-<Acount>-<A...>-d-<Dcount>-<D...>`
  publishes one exact paused hypothetical-contact composition/context
  observation without depending on current routes or consuming RNG;
  `query-arrange-marriage-choices` returns
  natively valid direct matches for the played character and
  `arrange-marriage-<played_id>-<candidate_id>` submits only a cached exact
  generation-bound pair; exact-build snapshots additionally expose the Mod's
  completed Rogue one-life death settlement without depending on the current
  played character or a visible game window;
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

Use an x64 Visual Studio developer shell and the fresh-build helper for every
DLL that will be injected into CK3:

```powershell
.\tools\build_fresh.ps1
```

The helper always allocates a new `build-fresh-*` directory and refuses an
existing path. It requests English MSVC `/showIncludes` output and, on the
Chinese MSVC 19.51 distribution that ships only `2052/clui.dll`, repairs
CMake's incorrectly decoded UTF-8 dependency prefix in the generated Ninja
rules before compiling. It then verifies that Ninja recorded `ck3_11906.hpp`
for both sides of the `Bindings` ABI, runs the offline CTest suite, and rejects
the artifacts if native sources changed while the build was running. This gate
exists because a localized Ninja dependency database with zero header
dependencies once linked a new `Bindings` producer to an old adapter object
and made CK3 crash during pre-resume injection. The locale repair does not
bypass that gate: `ninja -t deps` must still contain the header for both
objects.

To choose the fresh path explicitly, or only inspect the intended build without
creating it:

```powershell
.\tools\build_fresh.ps1 -BuildDir ..\build-fresh-production
.\tools\build_fresh.ps1 -BuildDir ..\build-fresh-production -PlanOnly
```

`-BuildDir` must not already exist. `-SkipTests` is available for a diagnostic
compile, but such an artifact is not a production-tested bridge.

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
submission. It also contains `active_wars`, `player_armies`, and nullable
`one_life_settlement`. The exact-build capability
`game.state.xar-one-life-settlement` is authoritative for that field. It is
null until `xa_settlement_ready` is exactly one and every required global can
be decoded. A published object contains `ready`, `commit_serial`,
`source_character_id`, `record_candidate`, `old_record`, `record_delta`,
`blessing_count`, `refusal_count`, `contract_progress`, and `record_written`.
`final_score` and `score_before_reject` are lossless CK3 fixed-point objects:
`{"raw":<signed int64>,"scale":100000}`. Each active
war identifies the player's side, the generation-validated primary opponent,
whether the player is their side's primary war leader, and war score relative
to that player. Exact-build capability `game.state.war-objectives` publishes
each war's exact `targeted_title_ids` and the deduplicated
`war_objective_province_ids`. A barony target contributes its own province, a
county contributes its capital barony province, and a duchy/kingdom target
walks its complete de jure title tree and contributes every county capital.
The generation-safe walk is bounded to 4096 resolved titles and depth 8;
an invalid branch suppresses that target's entire partial projection.
Four independent exact-build capabilities add `objective_province_states` in
the same order: `game.state.war-objective-occupation`,
`game.state.war-objective-fort-level`,
`game.state.war-objective-garrison`, and
`game.state.war-objective-siege-progress`. Occupation and fort level are direct
Province scalar reads. Garrison, eligible besieging strength, and active-siege
details are observable only in paused snapshots; running snapshots leave those
fields null and `siege_observable=false` rather than traversing mutable native
containers without an engine read lock. In a paused row,
`siege_observable=true` with `active_siege=null` means the Province really has
no active siege. A non-null siege contains its generation-validated ID,
nullable uniquely joined public army ID, player involvement, native fixed-point
progress/current-work/total-work objects, and nullable days left. Stalled siege
`INT_MAX` maps to null, not a large day count. The total rich-state budget is
256 objective Provinces per snapshot because paused heartbeats still run every
250 ms; a war is published atomically or its state array remains empty/unknown.
Exact-build capability `game.state.war-primary-opponent` also
publishes nullable `enemy_primary_default_raise_province_id`: the opponent's
native default rally province, explicitly only a fallback when no enemy army
province is observable, not a decoded war goal. Wars group currently
observable armies into `allied_armies` and `enemy_armies`. Army records expose
`army_id`, owner `CharacterID`, nullable current province, exact native
`army_state_code`/`army_state`, `in_combat`, `retreating`, and whether the
played character controls them. Exact-build capability
`game.state.army-routes` adds `route_province_ids`: the complete native
remaining-route array in engine order, without inserting the current province
or deduplicating entries. Every item must resolve through the current province
table and the route is bounded to 4096 entries; an empty, invalid, or oversized
route publishes `[]` atomically. Full arrays are read only while the snapshot
is paused because the engine route container has no read lock. A running
snapshot deliberately leaves `route_province_ids=[]`; this means "not fully
read", not necessarily "no route". It retains the pre-existing single-tail
read as `move_target_province_id`/`move_target_observable`, so progress tracking
does not lose its old signal. In a paused snapshot, a valid nonempty full route
has `route_province_ids.back() == move_target_province_id`.
  Soldier count remains intentionally absent from the 250 ms heartbeat; its
  heavier exact aggregate is available through the explicit paused query below.
  `played_character` exposes the current played `CharacterID` and
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

Exact capability `game.command.split-army-half-N` accepts only
`split-army-half-<army_id>`, where the ID is the public generation-bearing
CUnit ID already exposed in `player_armies`. The 1.19.0.6 adapter resolves the
distinct internal CArmyID from that CUnit, passes it together with the current
played CharacterID through CK3's complete Split Half validator, constructs the
original 0x30-byte player command, and queues its synchronous heap clone with
flags `0x0E` before destroying the stack object. Success status
`split_submitted` means only that validation and queue submission completed;
it does not claim that a sibling CUnit is already present. A later paused
snapshot must establish the actual postcondition. Validator rejection is
reported directly, including native combat/raid/barter/retreat/movement-lock
or insufficient-live-regiment gates; the adapter does not reproduce those
rules with guessed bridge-side predicates.

Exact capability `game.command.merge-armies-N-with-N` accepts only
`merge-armies-<destination_public_CUnitID>-with-<source_public_CUnitID>`.
Both complete generation-bearing IDs must be distinct and present as
player-controllable armies in the current snapshot. The underlying
`CMergeUnitsCommand` is a batch command, but the bridge always constructs a
single-element source array so native validation cannot degrade into partial
success. The exact adapter uses CK3's heap factory, canonical int32 range-copy
helper, complete object validator, synchronous deep-clone submit with player
flags `0x0E`, and paired deleting destructor; no array ever borrows a stack
ID. Success is only `merge_submitted`. A later paused snapshot must prove the
destination ID remains and the source ID disappears. Province, combat,
retreat, movement-lock, raid and land/naval compatibility stay under CK3's
complete validator. See
[`docs/ck3-native-merge-contract.md`](../../docs/ck3-native-merge-contract.md)
for the exact-build ABI, ownership and postcondition contract.

Exact capability `game.command.preview-move-army-N-to-N` accepts only
`preview-move-army-<army_id>-to-<province_id>` while the map is paused. It
runs the same mode/character/army gates, resolves CK3's move origin, and calls
the native A* route builder into caller-owned scratch. It copies and validates
the complete route before destroying the temporary path. It neither binds nor
calls the apply routine and never submits a command. Success returns
`result.status="available"` and
`route_preview={status:"available",army_id,origin_province_id,target_province_id,route_province_ids}`.
`origin_province_id` is the selected army's current Province from the same
paused snapshot. While an army is already between Provinces, CK3's native
origin resolver may instead return the first entry of that snapshot's
remaining route. The exact adapter accepts only those two possibilities and,
when they differ, prepends the effective origin to the untouched native A*
output. Loops and duplicate Province IDs are deliberately preserved. A target
equal to the observed current Province returns an empty route only when it is
also the effective origin; in flight, CK3 must finish the current edge and A*
  may route back. A target equal to a differing effective origin returns the
  one-entry route containing that effective origin and skips A*.

Exact capability `game.command.query-army-strengths-v1` accepts only the fixed
no-argument step `query-army-strengths-v1` while paused. It takes one semantic
snapshot, then returns the stable first-seen union of top-level
`player_armies` followed by each active war's `allied_armies` and
`enemy_armies`. Public full-generation CUnit IDs are deduplicated; scope role
priority is `player > active_war_ally > active_war_enemy`, and `war_ids` are
unioned in snapshot order. The external MCP tool requires explicit caller
`army_ids` and filters this atomic native result at the same revision; native
scope itself never depends on an untrusted list encoded into a step string.

Each `army_strengths` row generation-resolves `CUnit -> CArmy -> every
CRegiment` through the exact storages and rejects CK3's fallback regiment
object. It validates the bounded native ID array and each regiment's original
public-ID identity predicate, then checked-sums current soldiers, maximum
soldiers, and `CRegiment+0x40` AI base-power raw from every identity-valid
regiment. The predicate proves only `CRegiment+0x10 != -1`; it is not a combat
activity or participation test.
The current/max mirrors must equal CK3's original helpers before publication.
`ai_base_power_scale` is the proven CFixedPoint scale `100000`; this base metric
is neither terrain-adjusted combat strength nor a battle probability. A broken
generation, array, identity, sum, or helper match makes the complete row
`status="unavailable"` with all numeric aggregates null. Other rows remain
typed and the top status becomes `partial`; no bad regiment is silently skipped.
The query constructs no command, advances no date/RNG, and never queues.

Exact capability `game.command.query-combat-simulation-inputs-v2-N` accepts
only the canonical paused literal
`query-combat-simulation-inputs-v2-<target>-<attacker_entry>-a-<Acount>-<A...>-d-<Dcount>-<D...>`.
The former v1 literal is superseded and is not advertised or dispatched. Its
offline admission required an already observable move/current-position contact
shape; the paused `83886341@2596` versus `357/33554657@2581` production scenario
could not construct one target accepted for all three armies before ordering a
move, so that contract was a live blocker rather than an observation result. Every
numeric token is a positive canonical ASCII decimal; each count is exact and in
1..63, the combined count is at most 64, the target differs from the entry, and
all public full-generation ArmyIDs are distinct across both partitions. In one
paused snapshot the adapter revalidates every ID against player/active-war
scope, requires a common active WarID, and proves the two requested partitions
are opposite coalitions. Player and active-war allies may share one partition.

The participant policy is
`explicit_hypothetical_fixed_at_contact_no_reinforcements`. The caller fixes
all attackers at the explicit final-edge entry Province and all defenders at
the target for this conditional scenario. Current Province remains an optional
observation, but current position, native move target, and route are not
admission inputs. Crossing is derived only from the unique generation-valid
entry-to-target edge; edge kinds 0..3 map to none/strait/river/large-river,
while 4..6 reject the scenario. Attackers and defenders retain request order;
that order is the hypothetical CCombat insertion order, so each side's first
army supplies its native primary-participant owner for holding and side-wide
counter context. This is explicit conditional ordering, not a claim about
actual arrival order.

The successful `combat_simulation_inputs` observation carries a typed `scenario`
block and lists armies as attackers then defenders, with an `encounter_role` on
every row. It publishes each selected army's nullable current Province, exact
CArmy ID, owner/counter modifiers, commander and
target-specific inclusive roll bounds, generation-checked regiments, nullable
MAA keys, exact levy/men-at-arms classification, main-phase eligibility,
target-evaluated max/siege/damage/toughness/pursuit/screen values, counter
operands, and generation-checked knights with direct effectiveness plus native
damage/toughness contributions. The target row includes terrain, signed Q100000
width multiplier, crossing, attacker/defender holding context, and mirrored
initial contact width. Two directional native counter resolutions and any
generation-validated already-associated CCombat rows are included in the same
result. No nullable MAA type is inferred to mean levy; combat kind comes from
CK3's original side-population classifier.

`completeness.observation_slice` is `precontact-composition-context-v2`, and
`completeness.input_observation_ready=true` only when every advertised input
subdomain above is available. A failed input read returns typed `partial`, names
the concrete input domain, and never substitutes zero. An available observation
still has `monte_carlo_ready=false`; its fixed `missing_required_domains` are
the simulator transitions `damage_to_casualty_allocation`,
`pursuit_transition`, `battle_end_and_retreat_transition`, and
`phase_event_rng_and_effects`, not missing MCP observations. The query only
reads the paused exact-build graph and invokes synchronous read/evaluation
helpers: it submits no command, advances no date, and never calls CK3's random
commander-roll helper.

Production capability `game.command.query-combat-simulation-inputs-v3-N`
uses the same canonical explicit target/entry/A/D literal as v2 with the
version token changed to `v3`.  A successful paused same-frame result atomically
combines the v2 `base_inputs` object with 81 exact native phase-event leaves,
51 exact offline derivations, and a temporary unregistered `0x718` CCombat
shell whose stock advantage helpers must agree with the serialized source
ledger and resolved total.  The raw named objects are fixed and complete; no
missing field may be represented as a permanently nullable observation.

Each raw side also carries `candidate_source_proof`.  The native reader directly
re-reads the stock `0x23C9100` local CCombatSide commander-then-knight source
vector, requires every `role/source_army_id/source_regiment_id/character_id`
row to equal the expected raw roster, publishes an uppercase SHA-256 digest of
that exact ordered preimage, and repeats the native read after all advantage
helpers.  Python independently checks the rows, roster binding and digest; it
does not trust the digest alone.  Available and unavailable command-result
goldens pass the same strict production normalizer.  This closes current-frame
132/132 observation only: phase-effect feedback/original-trace and the combat
transition simulator remain separate false gates, so v3 does not itself publish
a win probability or authorize an attack.

`game.command.query-combat-phase-event-trace-v1-N` remains a reserved,
unadvertised research capability.  Its probe and fixed-width seven-boundary
capture ring have source/ABI fixtures, but no exact-build detour is installed
and no bridge dispatch exists.  The ring is fail-closed on sequence, identity,
capacity or memory faults and never allocates, pauses, resolves a component
store, draws RNG or re-enters the bridge on CK3's native call stack.  Production
advertisement remains forbidden until a managed live same-Combat drain and the
full mutable feedback bundle both pass.

Research-only capabilities
`game.command.research-arm-tactical-daily-sentinel-v1-N` and
`game.command.research-query-tactical-daily-sentinel-v1` expose the exact-build
daily tactical sentinel.  While paused, arm it with
`research-arm-tactical-daily-sentinel-v1-<start>-to-<target>-speed-<1..5>-mode-<decision|terminal>-a-<count>-<ArmyID...>`,
after setting the matching speed, then resume exactly once.  A later paused
frame is accepted as the native stop even when no intermediate running frame
was published; the harness must never re-resume an already-triggered arm.  A
new paused arm may replace a stale armed experiment after RED recovery.  The
post-day hook calls CK3's original
final-stage function exactly once before checking the absolute date and bounded
route/combat fingerprints.  `decision` stops on ordinary tactical decision
epochs; `terminal` deliberately crosses phase and winner-only transitions so
an admitted overwhelming battle can run without intermediate external pauses.
The status result records the armed/stop dates and speed, trigger reasons,
overshoot, intermediate pauses, terminal observation and abnormal state.  The
same exact-build primitive is production-live through narrowly admitted upper
layer composites: ordinary active battle at speed 3, committed route at speed
3, and a full-watch terminal speed-5 primitive.  This does not admit speed 4 or
double-4x crush selection.  In terminal mode, a crush candidate additionally
requires a cursor-bound passive terminal-journal event on the same day and
equal core terminal outcomes across the restored speed arms; a date fallback
is not terminal admission.

`main_thread_query_mailbox_v1` now exposes one deliberately typed execution
boundary for `query-war-entry-assessments-v1`; it is not a generic native-call,
effect, phase-query or simulation-main executor.  The exact SDL Windows pump
returns from `USER32!PeekMessageW` on the application/startup-main
HandlePdxEvents TLS path.  Admission requires the initialized TLS global,
stable TLS context with marker `+0x20 == 1`, current thread, paused/date and
Jomini/game identities across two consecutive epochs and pre/post samples.
The global RNG owner's scoped TID is heartbeat provenance only and never a
readiness gate.  At most one typed request is drained per pump.

The `.rdata` IAT install and uninstall use `VirtualQuery`, a temporary
single-page `PAGE_READWRITE`, atomic CAS, protection rollback, and a
counted-call stop/reinstall drain.  V1 is process-lifetime pinned: restoring
the IAT cannot prove that no thread fetched the old target before incrementing
the counter, so the static mailbox and original function pointer remain valid
until process exit and remote `FreeLibrary` is forbidden.  The production
war-entry literal accepts exactly one target.  The worker freezes one
declarable-war target set after a fresh same-paused-snapshot read; the reader's
before/middle/after callbacks each perform a fresh full `ReadSnapshot`, then
the native resolver, network collector and assessment rows are sampled twice.
Typed-executor live result acceptance remains pending.  The exact ABI and
diagram are documented in
[`main-thread-query-mailbox.md`](../../docs/ck3-native-ai/main-thread-query-mailbox.md).

War declaration discovery is an explicit request rather than part of the
250 ms snapshot publisher: it evaluates current CBs across live characters
and returns `declaration_id`, stable `casus_belli_key`, target/claimant IDs,
and target title IDs. The ID's numeric CB/configuration components are runtime
ordinals, not persistent semantic IDs. `declare-war-*` consumes only a choice
from that query and re-enumerates the exact target before constructing CK3's
native character-interaction command. `enforce-demands-*` uses the native war
resolution context builder and accepts only a war for which the played
character is the primary war leader.

Exact capability `game.command.query-war-termination-options-N` accepts only
`query-war-termination-options-<positive full-generation WarID>` while paused.
It re-resolves the active war, cross-checks the participant side and the total
score already published in the same semantic snapshot, then returns a typed
`war_termination_options` object. The object includes player side/primary
status, player-relative and absolute attacker/defender totals, nullable
attacker-relative `{imprisonment,battles,occupation,ticking}` breakdown,
nullable duration in days, active-CB ordinal/key, and the CB's native
white-peace permission. Its `surrender`, `white_peace`, and `victory` options
each report the absolute outcome, context/validator result, native AI answer
score as `{"raw":<signed int64>,"scale":100000}`, and exact `auto_accept`.
The query only constructs, validates, reads, and destroys temporary contexts;
it never builds a send command or queues anything. Every unavailable subfield
is emitted as null/false observability rather than a guessed zero.

Each result option deliberately fixes `hostage_variant="none"` and
`terms={status:"unavailable",reason:"cb_specific_terms_not_observable"}`.
Absolute outcome is not a proof of CB-specific title, gold, prestige, piety,
legitimacy, truce or prisoner effects.

Exact read-only capability
`game.command.query-war-termination-terms-v1-N` accepts only
`query-war-termination-terms-v1-<positive full-generation WarID>` while
paused. It reads ordered target TitleIDs from `CWar+0x270`, claimant
CharacterID from `+0x290`, generation-resolves both domains, and calls
`0x28B1AA0` once per title. A present temporary must repeat the requested
TitleID and is destroyed through its vtable slot 0 with delete flags 0; an
absent result publishes only `{title_id,present:false,state:"absent"}` and
does not inspect or destroy uninitialized fields. The strict available union
is limited to `claim_cb_claim_disposition`; other CBs return typed
`unsupported`. Python binds the cache to the same paused native revision,
snapshot, connection generation and episode. Public MCP is
`ck3_query_war_termination_terms`.

Native capabilities `game.command.surrender-war-N` and
`game.command.offer-white-peace-N` accept only their canonical WarID literals.
Surrender rebuilds the
absolute defeat context (`0xC569F0` takes `true` for attacker victory and
`false` for attacker defeat), runs CK3's validator, constructs the common
interaction command and honors the queue's bool result. Thus an attacking
player's surrender passes `false`, while a defending player's surrender
passes `true`. White peace independently requires the active-CB permission
bit, resolves the opposite primary leader, constructs special interaction
index 3, validates it, and submits the same command family with flags `0x0E`.
Both destroy the temporary and command-owned context on all constructed paths.
`submitted` is only a queue ACK; disappearance of that WarID from a later
snapshot proves that the war actually ended. These are mechanical native
capabilities, not current planner authorization: Python advertises neither
literal and rejects direct MCP execution until `claim_cb_exit_terms_v2` plus
campaign-decision readiness are complete.

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

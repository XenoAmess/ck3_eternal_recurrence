# CK3 1.19.0.6 native-headless anchors

This directory freezes the first implementation-grade reverse-engineering
result for the local `ck3.exe`. The original anchors were obtained offline;
the army runtime additions below also use a read-only minimized-process probe
and record its PID/IDs explicitly. No reverse-engineering probe issued a game
command or restored/focused the window.

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

## Startup particle2 null-slot containment

Three no-DLL controls—including a no-save main-menu launch—reproduced CK3
`C0000005` at RVA `0x1DABD89` when the synchronously-built particle2 resource
slots were null. The exact-build startup guard is installed only by the bare
cold-start injector while the new process primary thread is still suspended.
It patches 13 bytes at RVA `0x1DABD6D`, after the complete `0x1D`-byte
UNWIND_INFO prologue. Null root/slot or an out-of-range index follows the
native normal epilogue; a non-null slot resumes at RVA `0x1DABD82`. It never
fabricates a graphics resource and is not used by running `--pipe` attach.

Fresh merged candidate
`ck3_autonomous_player/.build-startup-guard-production8e-msvc/xar_ck3_bridge.dll`
has SHA-256
`4614CF951F28FB063BB72ADBE521E6BD7E20FC71305B29819B1944A5BD378CC6`;
its injector has SHA-256
`26F09E40F032B1C4B161E5886F3908FB6DBCA4385FE38E3978C698855D02E2FC`.
Native CTest was 18/18 and the offline scanner was 138 signatures / 23 vtable
prefixes. The one managed production8e cold start then live-confirmed the guard:
all eight calls were suppressed (`count=8`, mask `0xFF`, last index `7`) and the
old `0x1DABD89` fault disappeared. Startup continued to the immediately later
consumer at RVA `0x1FCC100`, which read the same null slot family and faulted at
RVA `0x1FCC14C`. No MCP query, input, or gameplay action was issued.

The follow-up exact-build consumer guard is intentionally narrower than
skipping its caller. It patches the 15-byte entry at `0x1FCC100` while the new
primary thread is suspended, before the native `0x2A`-byte unwind prologue has
changed the stack. It preflights the root and all eight slots at `+0xA8..+0xE0`.
If all are present it replays the three overwritten instructions and resumes at
`0x1FCC10F`; if any is null it atomically records the missing mask and returns
before the function creates scratch objects. Both exact callers ignore the
void-style result, while the surrounding GUI factory registration remains
untouched. The generated stub is leaf-only and performs no calls, allocation,
logging, or world-state write.

This second guard is offline-verified by an executable synthetic function,
exact PE/PData/unwind and two-xref checks, per-slot and root-null vectors, and
transactional rollback fault injection. A fresh merged MSVC build and all 19
native CTest cases pass; the scanner remains 138 signatures / 23 vtable
prefixes. It is still crash containment, not proof that particle rendering is
healthy.

The subsequent single managed cold start live-confirmed both guards. The first
reported `count=8`, mask `0xFF`, last index `7`; the later consumer reported
`count=1`, missing mask `0xFF`; both were installed with `failure=0`. Startup
therefore passed both known null dereferences, but failed later at new RVA
`0x3B0AE5F` (read address `0x90C`) before the map/mailbox boundary. No snapshot,
MCP query, input, or gameplay action occurred, and managed cleanup was proven.
The bundle is `ck3_20260825_171910`; its minidump SHA-256 is
`A0430F36B9C291792EF04F831C60EE43FF6E2CBCF1DE441798DA5F054C84D329`
and its exception report SHA-256 is
`F81C1BB8D916A255E5F8811D9C7BB6AE05B9B87B62EA82CEB8C19BA9A01061BD`.
The new fault must be closed independently before another startup attempt.

Static exact-build unwind and RTTI identify that third fault as a
`CGfxDX11RenderContext` pre-draw binding flush on the Clausewitz graphics worker
thread. Its constructor legally creates a transition state with dirty mask
`+0x1938 = 0xFFFFFFFF` and current shader-state pointer `+0x1940 = null`; the
setter later writes only the pointer, leaving dirty set for the first real
flush. The live load-screen draw reached the flush during that transition.

The implemented exact-build guard covers only the live-confirmed first draw
wrapper at RVA `0x3B0B0F0`, not the shared flush helper or its other three draw
frontends. Before its complete 15-byte prologue, a 62-byte leaf stub tests
`dirty.bit0 && state == null`. That exact condition records a diagnostic and
returns from this draw while preserving dirty; every other state replays the
prologue and resumes at `0x3B0B0FF`. Clearing dirty in the helper would be
incorrect because it would both continue an unbound backend draw and prevent a
later valid state from receiving its first flush.

The executable fixture covers the bad transition plus both healthy null/state
combinations, exact dirty preservation, W^X, and transactional rollback faults.
The source contract binds the exact EXE SHA, PDATA/unwind row, helper predicate,
RTTI/COL, and the observed vtable `+0x130` callsite. Startup preparation installs
the producer, particle2 consumer, then this draw guard while the primary thread
is suspended and unwinds in reverse order on failure. Independent review found
no BLOCKER/HIGH. Fresh Release CTest is 20/20 and the scanner remains 138 exact
signatures / 23 vtable prefixes. The production9 DLL SHA-256 is
`7F3052C9B37F77AFB90BAA7F9A8D748531BDDF8C7641E8B156E7318EB9CA6DAF`.

The single managed production9 cold start live-confirmed this guard too. Dump
state showed all three installed with `failure=0`: the first retained
count/mask `8/0xFF`, the particle2 consumer `1/0xFF`, and this DX11 draw guard
`suppressed_count=1`. The process then failed at new RVA `0x3A70610` (read
address `0x40`) before the mailbox was installed; mailbox pump and executed
request counts were both zero. No MCP query, input, or gameplay action occurred,
and no restart was attempted. Bundle `ck3_20260825_181347` has minidump SHA-256
`0408F46AEEDCEA33A3930067254B485FA64A7EE4FBA4D340FDE9976D116DA7E1`.

Exact unwind and producer analysis identifies this fourth fault as a legal
localization publication window on the application startup thread.
`LocalizeInit` publishes a zeroed 0x40-byte state at global RVA `0x57DFA28`
before a later language-select producer writes its active root at `state+0`.
The `TPdxNullObject<CSiege>` callback consumed that null root while resolving
`ACCLAIMED_KNIGHTS_IN_ARMY`.

The owner lookup already contains a correct miss/raw-key fallback at
`0x3A6A51A` / `0x3A6A67F`. The implemented minimum guard is therefore a 13-byte body
guard at `0x3A6A4D6`: healthy lookup resumes at `0x3A6A4E3`, while a null
current root jumps to that existing miss path without writing localization
state. The shared hash leaf at `0x3A70610` has 128 direct callers and remains
untouched.

The fourth guard is now compiled into suspended startup after the particle2
producer/consumer guards and the live-directed DX11 draw guard. Its 64-byte
leaf stub preserves the lookup seed and input view, and only records the
observed current-root-null window before taking the native raw-key fallback.
Failure rolls the preceding three guards back in reverse order. A fresh Release
production10 build passes 21/21 CTest cases; the exact-build scanner remains
138 signatures / 23 vtable prefixes. Artifacts are DLL
`EB10D9D9A6C89B5DFB3680179A5B5C9D2CCFF210F1D5C62BCA4F5B4E45B4CE2F`,
injector `F928C93654085E7C2FC94CBDFAF9E1222A3A6A6C3E2E20CD2BCA51DB9BBA602E`,
and host `8CE6BCA7214F7C6F0025511C8A7F36D84AFA7DC0A9E36047FA983E609D723450`.
The single managed production10 cold start then live-confirmed all four guards
with `failure=0`: suppression counts were `8`, `1`, `1`, and `5` respectively.
It crossed the localization publication window, then failed later on the
application main thread at new RVA `0x369CB58` (`RSI=null`, read `+0xD0`). The
mailbox remained detached with zero pump/executed counts, so declarable and
war-entry queries, inputs, and actions all remained zero. No restart occurred;
checkpoint, history, and driver-state bytes were unchanged and managed cleanup
proved the process tree empty. Bundle `ck3_20260825_190705` has minidump SHA-256
`26BBE695A818794D221F7B5B4D47B79C2AB30CA937C4D17C093768C8C98A36`.
This is a live containment advance, not a successful startup/query claim; the
new main-thread fault is the next exact-build gate.

The operator subsequently identified Kaspersky as a component that had killed
or interfered with a test artifact. Read-only local state confirmed that `avp`
was active and the quarantine directory acquired an object belonging to an
older combat-detour test, while the project CK3 and all three bridge artifacts
still matched their frozen hashes. This made an antivirus-cleared,
original-byte control mandatory; it did not prove that the antivirus caused
each CK3 null-state failure. No fifth guard was developed.

The four guard implementations and executable fixtures remain available for
forensics, but production defaults to
`kStartupFailureContainmentEnabledV1=false`. The suspended Prepare export now
admits the exact adapter and returns without patching CK3; heartbeat exposes
`startup_failure_containment_enabled=false`. Source-contract tests and Release
disassembly freeze that behavior. The ensuing managed control waited for a
verified Kaspersky restore/exclusion and used the original executable bytes.

The fresh production11 no-patch candidate passes 21/21 Release CTest cases and
the scanner remains 138 signatures / 23 vtable prefixes. Direct export
disassembly confirms no startup-guard installer call. Artifact SHA-256 values:
DLL `F3A6634E2C8808462E9A75066E9FE2D1C391F49D6D653DE9AB1941CB6FE36A8C`,
injector `3CE544C424CCF778853D987B069C5D837A159ECF7C6A433CC466DA6E75677088`,
host `9B29AEB618795BF9D00E8B1DEC8D5AFED1F441E471F9C09AFD5D2EB129487F8A`.
After the operator restored/allowed the relevant paths, one managed cold start
used this production11 build with no containment guard and no gameplay query or
input. CK3 still failed after 17.633 seconds at exact RVA `0x1DABD89`; there was
no retry, and managed cleanup proved the process tree empty. Dump
`ck3_20260825_200506` has SHA-256
`DE594C85F7E9BDE1463F618156BF6CD21773072B27642D43AC4E91F6FBFADC35`.
Its application-main exception context reads address `0x244` with `RBP=0`,
`R14=0x1F8`, and particle2 root `RAX=0x18DD5E37B60`; all root slots
`+0x68..+0xE0` are null. The dump-retained heartbeat says containment false and
mailbox uninstalled/zero-pump. Direct reads of all four guard states show
installed/failure/counters zero and patch/stub pointers null; the captured
producer patch window remains original.

This closes only causality: Kaspersky was not necessary for this rerun's native
particle2 fault, though its earlier quarantine event was real. The post-crash
dump cannot identify whether factory `0x3A866D0` returned null at source/VFS
`0x3A86772`, variant lookup `0x3A867B0`, or backend creation `0x3A867EC`.
The next diagnostic is an opt-in recorder at those exits which only increments
atomics and replays the original instructions; it must not suppress a fault or
fabricate a resource.

That diagnostic is now implemented as
`XAR_CK3_ENABLE_STARTUP_PARTICLE2_STAGE_RECORDER_V1`, default `OFF`. On the
exact executable it installs three absolute-jump patches at RVAs `0x3A86769`,
`0x3A867B0`, and `0x3A867EC` while the new primary thread is still suspended.
The generated leaf stubs only increment preallocated atomics, replay the
overwritten instructions, and return to the original healthy/null targets;
they contain no call, allocation, log, resource fabrication, or outcome
suppression. The recorder and the four containment guards are compile-time
mutually exclusive. Its executable fixture covers all six healthy/null
branches, W^X finalization, exact target identity, reverse-order uninstall, and
recoverable plus an unproven installation-time rollback. For that covered
retained-install state, a quiescent retry must re-flush the byte-identical
original code and restore the captured executable protection before retained
ownership or RX stub storage can be released.

Fresh Release evidence is 22/22 CTest cases plus the unchanged 138-signature /
23-vtable-prefix exact-build scan. The enabled production12 DLL is 586,240
bytes, SHA-256
`DD0833B66F8EADE4564BA83C23A26752D55A1FCF3D2D52BCE56E9A1CC127CB36`;
injector SHA-256 is
`17CD90A44BE641AC538F6431AD6FC258376349A06F41EB36974643632E89F824`
and host SHA-256 is
`ED68911826C76ECB7055AC71522994B93C45414B323FA463E901CB735F877F77`.
The separately rebuilt default-OFF DLL is 578,048 bytes, SHA-256
`D48A45CA043F91A2E0927BC620694EF854B946A8D6A267B68E580F9696C48702`;
direct Prepare-export disassembly contains no recorder installer call.

[live-confirmed diagnostic only, 2026-08-25] Three managed exact-build launches
used the same immutable 66,594,755-byte checkpoint (SHA-256
`5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F`)
without an MCP query, gameplay command, or input. The first and second launches
remained alive until their 91.685-second and 62.287-second timeouts. During the
third launch, a read-only `ReadProcessMemory` sample of PID 62888 proved
`installed=1`, patch mask `7`, `failure=0`, the frozen module/target address
relationships, and all three installed absolute-jump byte sequences. Across a
13-second sample interval, source-null stayed `0`, variant-null increased
exactly from `20874` to `21071` (delta `197`), and backend-null stayed `0`; the
process remained alive and was then stopped through the managed session after
72.668 seconds. These are branch executions, not unique variants, resources,
or errors. The two zero counters mean only that their respective null outcomes
were not observed while this recorder was active, not that those stages were
never called. All three
attempts ended without a new Paradox crash bundle. After the attempts,
checkpoint, `last_save`, and driver-state bytes were unchanged, cleanup had
converged to an empty process/control inventory, and no unsafe-cleanup marker
existed.

This proves that the recorder was active and that the factory's frozen
variant-null branch was taken repeatedly during this bounded startup interval.
The original predicate makes that branch mean that source resolution succeeded
but exact requested-name lookup in that source's variant table returned null;
whether any particular miss is expected or benign remains unproven. The three
patches also do not cover the earlier null graphics-global exit. It does not
associate an aggregate counter increment with the earlier
`ParticleColor` / `particle2.shader` request, prove that the old fault was
resolved, or establish map/mailbox/gameplay readiness. The first new launch
also populated the isolated profile's shader cache, so the later samples are
not pristine-cache reruns. Each recorded null also performs one locked atomic
RMW, so control-flow equivalence is not a claim of zero scheduling/cache-line
perturbation. No production guard or resource substitute follows from this
result: containment remains disabled and the recorder remains opt-in. Only if
the original fault recurs, the next bounded diagnostic is a one-shot tuple-
specific observation for `gfx/FX/cw/particle2.shader` plus `ParticleColor`, not
another global total.

[live-confirmed production value path, 2026-08-26] The default-OFF production12
DLL `D48A45CA043F91A2E0927BC620694EF854B946A8D6A267B68E580F9696C48702`,
same-tree injector
`7D4F39C650F14A2B0B16DCCD02DA2406205A3CA972BC971C670545F52A7ECB14`,
and host
`4CFF5AC0A58C83C9EDC9077163FC982DCB081DBABD4E7FC4401B5AD4988AF54F`
subsequently crossed map and mailbox readiness with containment and recorder
both false. A first planner loop queried WarID `16777290` termination options
and completed one paused-to-paused native day (`53175816 -> 53175840`). A
second cold start completed 12 more one-day native actions, interleaved with 12
same-frame termination queries, moving ArmyID `83886341` from Province `2596`
to `2603` and advancing to `53176104`. Native save then replaced the isolated
checkpoint with a 66,426,917-byte file, SHA-256
`6F4970AEACBEEEA18E7F2502D63A4E31D1163A2F0F211AD9C7137A090EC1DD16`.
A third independent CK3 PID cold-restored those exact bytes and reproduced the
date, alive CharacterID `29829`, Province `2603`, and remaining route `[2604]`
on one ready paused frame. All managed cleanups passed; no crash bundle or
unsafe marker was added. The isolated shader cache was already warm, and no
typed war-entry mailbox request was made, so neither pristine-cache causality
nor first-live war-entry acceptance follows from this value result.

[live-confirmed managed auto-run, 2026-08-26] The production owner then cold-
restored the same `53176104` anchor in PID `81684`, performed three same-frame
WarID `16777290` termination queries interleaved with three semantic one-day
advances, and reached `53176176`. Exactly after the third eligible advance it
materialized a 66,420,106-byte checkpoint, SHA-256
`E8041581C789C21792280A893325082452F8A9717C8CDD421358FF9739189F07`, whose
date and history index `166` matched the current snapshot and history tail.
Managed shutdown removed CK3, injector, and host with no unsafe marker or new
crash bundle. Independent PID `34084` then cold-restored those new bytes and
reproduced the date and episode binding, so this is both write and restore
evidence rather than a save-command ACK. That replay did not qualify as a
continued autonomous run: four fresh objective-route previews all crossed
hostile ArmyID `357`'s target/remaining route, and the planner stopped with
`native_war_no_safe_exact_route`. Cleanup still passed. That run established
exact contact/ETA observation as the next dependency. The acceptance below now
closes native arrival and one-day avoidance; the current dependency is the
same-day candidate/stored-order actual-contact scope, followed, where contact
cannot be avoided, by an exact combat forecast. Base-power diagnostics must
not be promoted to either result.

[live-confirmed route-contact horizon, 2026-08-26] The first diagnostic replay
at paused date `53176176` submitted the typed route query but cancelled its
still-queued ticket after the generic two-second wait; the application-main
pump had not executed it. Exact EXE SHA, adapter binding, and native timing
bindings had all passed, so this was a mailbox scheduling failure, not an ABI
or reader failure. The route worker now retains the same queued ticket for a
bounded 8,000 ms and, once execution begins, waits in 2,000 ms slices until the
terminal result. A deterministic fixture delays the pump by 2,200 ms and proves
that the original ticket executes exactly once and is reclaimed.

The rebuilt production DLL SHA-256
`7AF3472A67218BDC407693D93A51826E2D99E29DB101EF724DC0B10FA60DC524`
then qualified on the same checkpoint. The query became `available` in 2.466 s
and mailbox `executed_requests` advanced `0 -> 1`. Its complete hostile scope
(`357`, `33554657`) and native per-route arrival timelines proved the interval
`53176176..53176200` contact-free, authorizing exactly one speed-1
paused-to-paused advance to `53176200`. The war snapshot changed, a
66,415,726-byte checkpoint was materialized with SHA-256
`51A3C202D6785988F3E3E7F028B64C4F0949DD83A4E32F3222E286B110224BE8`,
and managed cleanup was proven. This accepts production native arrival and the
bounded one-day route-contact horizon only; it does not infer actual contact
sides/order, so the same-day stored-order gate remains closed.

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
| `game.state.snapshot.pending_character_interaction` | implemented; recipient-filtered ordinary request discovery is live-confirmed, while auto-accept notifications remain deliberately filtered | exact notification-recipient predicate + native reply validator + offline multi-player fixture + ordinary white-peace cold replay | never inside native driver |
| `game.command.accept/reject-pending-character-interaction` | implemented; live accept advanced four locally addressed requests | high static UI enum/command/queue path + native actionability validation + offline command fixture | explicit upper-layer policy only |
| `game.command.query-pending-character-interaction-context-v1` | implemented; ordinary recipient white-peace pending completed production-only cold-reload same-revision double query | exact stable definition/roles/target/options/routing/deadline/legality ABI + application-main mailbox + live artifact `D20E339D...B8BC89` | explicit typed service/MCP query; semantic reply policy remains blocked by structured terms |
| `game.state.snapshot.active_wars` | implemented, minimized live declaration projected a new war | exact WarManager/storage/participant/score helpers + offline attacker/defender fixture | never inside native driver |
| `game.state.war-primary-opponent` | implemented, live probe pending | exact primary-side fields + generation-safe opponent resolution + reused default-raise resolver + offline attacker/defender/non-primary fixture | never inside native driver |
| `game.state.war-objectives` | implemented; live war 16777290 exposed target title 2388 and province 2585; multi-county hierarchy projection passed offline fixture | exact CB targeted-title serializer, generation-safe title storage, engine recursive de-jure walker + `title_province` capital-barony path + hierarchy/generation/bound fixtures | never inside native driver |
| `game.state.war-objective-occupation` | implemented; exact-build live projection pending | Province occupied getter + full-generation occupying CharacterID roundtrip + offline occupied/unoccupied/stale-generation fixture | never inside native driver |
| `game.state.war-objective-fort-level` | implemented; minimized exact-build live projection passed | plain int32 Province getter + running/paused offline fixture + live objective value | never inside native driver |
| `game.state.war-objective-garrison` | implemented for paused snapshots; minimized exact-build live projection passed | canonical Province garrison wrapper and eligible-besieger getter + zero/nonzero fixture + live siege values | never inside native driver |
| `game.state.war-objective-siege-progress` | implemented for paused snapshots; minimized exact-build live progression passed | exact Siege storage/generation/alive/Province-backlink chain + native CFixedPoint progress/work and days-left getters + transition fixture + same-SiegeID live progression | never inside native driver |
| `game.state.snapshot.player_armies` | implemented, minimized read-only live probe passed | exact CUnit storage/ID/owner/current-province fields + offline component fixture + PID 144324 probe | never inside native driver |
| allied/enemy army current province | implemented, minimized read-only live probe passed | war participant helper classifies each observable CUnit owner | never inside native driver |
| army state / combat / retreating | implemented, minimized read-only live probe passed | exact RVA `0xC7AAB0` state ABI, CUnit→CArmy→CCombat association and `CUnit+0x170` + nine-state fixture | never inside native driver |
| `game.state.army-routes` / army move target | implemented from minimized-live-validated route ABI; paused full-array/running-tail fixture passed | paused snapshots validate the full `CUnit+0x38/+0x40/+0x44` remaining-route array; running snapshots retain only the legacy last-entry target read | never inside native driver |
| `game.command.query-route-contact-horizon-v1-N` | implemented and exact-build live accepted for one-day paused progress | typed application-main mailbox, complete active-war hostile scope, exact per-route native arrival dates, one-day closed-boundary vertex/opposing-edge conflicts, delayed-pump fixture, and production replay | never use as actual-contact side/order proof; same-day stored order remains unknown |
| `game.command.query-army-strengths-v1` | implemented; paused revision 4 exact-build live probe passed for three public ArmyIDs | exact CUnit/CArmy/CRegiment storages, original current/max helpers, AI collector power loop, full-generation/fallback/predicate/empty/partial-row offline fixtures + live `83886341`/`33554657`/`357` rows | never inside native driver |
| `game.command.query-combat-simulation-inputs-v2-N` | explicit hypothetical-contact paused read-only query implemented; exact-build live probe pending | partitioned participants/final-edge entry, exact effective-stat/counter/knight/commander/terrain/crossing/role/holding/width ABIs, strict available/partial fixtures | never inside native driver |
| `game.command.query-combat-simulation-inputs-v3-N` | production exact-build capability advertised; paused live acceptance pending | v2 base object + 81 exact native leaves + 51 offline derivations = 132/132, original temporary-shell advantage helpers, strict same-frame candidate-source row equality/digest, available/unavailable production goldens and Python normalizer | never inside native driver |
| `game.command.query-combat-phase-event-trace-v1-N` | production DLL source present but explicitly not advertised or dispatched | real kind-11 scope evaluator probe, fixed-width seven-boundary ring, exact-build transactional detour installer, full-generation capture-plan builder, typed paused begin/finish executors and bounded checkpoint/drain serializer are compiled; shared mailbox union dispatch, recoverable external one-day driver, live sequence and full mutable feedback bundle remain closed | never inside native driver until the managed lifecycle is wired and accepted live |
| `game.command.query-battle-terminal-transition-v1` | implemented and normal-terminal exact-build live accepted | passive `0x230A590` terminal and `0x222A69B` post-warscore journals, bounded gap-aware rings, old full-CombatID/Province/Result removal, typed AI-membership subdomain, exact subject-bound successor, strict Python/service/MCP normalization; managed v6 reached normal terminal after 33 one-day commands, artifact SHA `61D0D912206A90D9B34DDE3555AEC941EC3538C253DBC4DCEB9D177D7456FDB1` | read only; no-normal, residual-new-combat and assignment-reopened live branches remain pending |
| `game.command.research-arm/query-tactical-daily-sentinel-v1` | exact-build static-ready; live arm pending | final daily-stage detour at `0x26D3E80` calls the original once, then checks an absolute deadline and bounded route/combat fingerprints before pausing through `0x346B910`; decision/terminal modes and speeds 1--5 pass deterministic fixtures, the serial harness submits resume once, and terminal admission requires a same-day cursor-bound passive journal result | research-only; production selector remains off, and date fallback cannot admit crush mode |
| `main_thread_query_mailbox_v1` infrastructure | application-main TLS boundary live-confirmed; multiple individually bound typed readers now live, including route-contact and battle-terminal | paused SDL pump, TLS global/context/+0x20 marker, stable date/game identities, delayed 2.2 s pump fixture, and live executed-request proofs; the earlier `failure=32` remains raw RNG provenance, not admission | never call it simulation-main and never admit a generic effect/evaluator; every reader requires its own exact contract and live boundary |
| `game.command.raise-troops-default` | implemented, live probe pending | native default-province/construct/validate/clone/destruct lifecycle + offline fixture | explicit upper-layer policy only |
| `game.command.preview-move-army-N-to-N` | implemented; paused minimized live probe exposed and closed the mid-edge effective-origin case | canonical plan/apply split + exact origin/PathCtx/MovePath/A* ABIs + current/route-front normalization + success/failure/cleanup/bound/paused fixture; no apply binding or queue call | explicit upper-layer policy only; paused map required |
| `game.command.move-army-N-to-N` | implemented and minimized-live accepted: player command submitted and army province changed | exact player-UI kind/channel plus native mode/state/can-move/path-init/clone/destruct lifecycle, offline fixture, and live movement | explicit upper-layer policy only |
| `game.command.disband-army-N` | implemented; live exposed the distinct command-target ID and corrected build awaits replay | exact 0x28-byte command/vtables/payload source/clone + offline fixture | explicit upper-layer policy only |
| `game.command.split-army-half-N` | implemented; minimized live split and independent-control postcondition passed | exact player GUI/validator/0x30-byte command/vtables/clone/destruct/executor path + offline public/internal-ID fixture + live sibling CUnit | explicit upper-layer policy only |
| `game.command.merge-armies-N-with-N` | implemented; minimized live strict-pair source-removal postcondition passed | exact batch GUI/public-CUnit payload/0x40-byte command + canonical factory/range-copy/deep-clone/destruct, offline owned-array fixture and live merge | explicit upper-layer policy only |
| `game.command.query-declarable-wars` | native C++ core implemented, bridge route/live probe pending | exact declare-war UI CB registry/evaluator/item rules + offline SSO/heap-key and configuration fixture | explicit upper-layer policy only |
| `game.command.declare-war-<declaration_id>` | native C++ core implemented, bridge route/live probe pending | generation-bound exact re-enumeration + native context/validation/queue/destruction fixture | explicit upper-layer policy only |
| `game.command.enforce-demands-<war_id>` | native C++ core implemented, bridge route/live probe pending | exact WarOverview victory context builder + common interaction command lifecycle fixture | explicit upper-layer policy only |
| `game.command.query-war-termination-options-N` | implemented paused read-only query; default-OFF exact-build live probe passed repeatedly | exact WarOverview three-context construction/validation, score/duration/CB/acceptance ABIs + no-submit offline fixture + live WarID `16777290` same-frame results | never inside native driver |
| `game.command.query-war-termination-terms-v1-N` | implemented narrow paused read-only claim-CB union; exact getter/destructor live probe pending | `CWar+0x270/+0x290`, full-generation Title/Character resolution, `0x28B1AA0`, present-only vtable-slot-0 destruction, strict available/unsupported fixtures | never inside native driver |
| `game.command.surrender-war-N` | native typed primary-leader command implemented; Python/MCP action frozen pending structured exit terms v2 | exact absolute-outcome WarOverview builder (`true` attacker victory / `false` attacker defeat) + validator/common-send/bool-queue/destruction fixture | unadvertised by upper-layer policy |
| `game.command.offer-white-peace-N` | native typed primary-leader command implemented; Python/MCP action frozen pending structured exit terms v2 | active-CB permission + full-generation opponent + special index 3 + validator/common-send/bool-queue/two-context destruction fixture | unadvertised by upper-layer policy |
| `game.command.query-arrange-marriage-choices` | implemented; minimized-live empty result was correctly explained by the played character's existing spouse | exact interaction registry, bounded enumeration diagnostics, generation-validated relationship snapshot, native validation fixture | explicit upper-layer policy only |
| `game.command.arrange-marriage-<choice_id>` | native direct-player path implemented, minimized-live submit pending | generation-bound CharacterIDs + redirect/all-role/refresh/finalize/validate/common-send fixture; spouse/betrothal outcome is snapshot-observable | explicit upper-layer policy only |
| event title/option text | unsupported | no repeatable localized text projection yet | unsupported in pure native mode |
| daily final-stage tactical sentinel hook | exact-build static-ready; live pending | exact 15-byte anchor at `0x26D3E80`, original-once trampoline, bounded post-day evaluator and native pause wrapper at `0x346B910` | research-only until the same-seed 1--5 live matrix passes |

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
- The paused termination query keeps all score values attacker-relative until
  JSON projection. Total is `0x222A8A0(war, nullptr)`. Its atomic nullable
  breakdown follows WarOverview exactly: imprisonment is
  `0x29030B0(war, nullptr)`; battles are `0x2903150(war, nullptr) +
  0x2903DA0(war, false, nullptr) - 0x2903DA0(war, true, nullptr)`; ticking is
  `0x2905BC0(war, false, nullptr, true) - 0x2905BC0(war, true, nullptr,
  false)`. Occupation helper `0x2904B00(war, side, nullptr)` returns a packed
  `uint64`: low signed dword is score and `(value >> 32) & 0xff` marks a
  single-side authoritative result. Read side false first; if not authoritative
  read true and select `-second` when that result is authoritative, otherwise
  use `first-second`. Checked overflow suppresses the entire breakdown rather
  than publishing partial zeroes.
- `CWar +0xE0` is the signed low dword of its start `HistoricalDate`.
  `CWarDaysTrigger` evaluator RVA `0x2848230` subtracts it from the current
  `CGameState +0x08` date and divides by 24; negative or overflowing duration is
  unavailable. `CWar +0x100` is the active `CCasusBelliType*`. Its dense
  database ordinal is `int32 +0x10`, canonical MSVC string is `+0x18` (size
  `+0x28`, capacity `+0x30`), and `uint32 +0x1718` bit 7 (`0x80`) is the same
  `IsWhitePeacePossible` gate consumed by WarOverview. `+0x14` is only the key
  hash and is never published as identity.
- `CWar +0xF8` embeds its `CCasusBelli`; the `targeted_titles` native int32
  array is CB `+0x178`, therefore war `+0x270` (data `+0x270`, capacity
  `+0x278`, count `+0x27C`). Serializer RVA `0x23E6B00` pairs that field with
  script identifier `0x2B3C`, whose live reverse lookup is `targeted_titles`.
  War `16777290` exposed the exact array `[2388]`. Title resolution starts at
  embedded `CLandedTitleManager = CK3GameData +0x2FC8`, whose storage pointer
  is `+0x20`; slots use the normal 0x10 stride/object `+0x08`, and full
  generation-bearing `TitleID` repeats at `CLandedTitle +0x10`. The target's
  capital `TitleID` is `+0x214` (serializer RVA `0x20B0DA0`). Engine
  `title_province` evaluator RVA `0x19D5AB0` proves the remaining projection:
  for county tier 2 it takes the first ID from the title's `+0x240` de-jure
  vassal array as the capital barony, resolves that complete ID, then reads
  ProvinceID from its template pointer `+0x160`, field `+0x80`. The checkpoint
  path is `2388 d_spoleto -> 2389 c_spoleto -> 2390 b_spoleto -> province
  2585`. Province `2543` is enemy-held `b_firenze` and can be sieged, but it is
  only the opponent's default-raise fallback and is not this war objective.
  The original adapter stopped at that single capital county. Static RE now
  closes the full child-container ABI: landed-title field dispatcher RVA
  `0x20B2C80` selects the native int32 array at `+0x240`, and engine recursive
  province walker RVA `0x20B4D50` reads count `+0x24C`, indexes 4-byte TitleIDs,
  resolves each child through title storage, compares the complete generation
  ID at child `+0x10`, and recurses. At barony tier 1 it reads template
  ProvinceID `+0x80`. The adapter therefore projects a barony target directly,
  a county through its first de-jure capital barony, and a duchy/kingdom through
  every de-jure county capital in stable depth-first child order. It uses one
  4096-title budget per war, depth limit 8, and stable ProvinceID de-duplication.
  If any target hierarchy is stale, malformed, or over bound, that target's
  partial result is discarded while its original `targeted_title_ids` entry
  remains visible.
- Each resolved objective Province has an additive `objective_province_states`
  row in the same stable order. Direct getters expose `Province+0x744` occupied
  state (a non--1 full CharacterID must round-trip through Character storage)
  and plain `int32 Province+0x858` fort level even in a running snapshot.
  Rich Holding/Siege reads are paused-only: current garrison wrapper RVA
  `0x220E710`, eligible besieging strength RVA `0x220E580`, and every CSiege
  pointer/getter remain uncalled while the map is running because no read lock
  for their mutable subgraphs has been identified. `Province+0x790 == -1`
  means a paused row has observably no active siege. Otherwise the adapter
  resolves the full SiegeID through `*(base+0x57BF1B8)`, checks `CSiege+0x08`,
  calls component-alive RVA `0x10495A0`, and requires `CSiege+0x200` to point
  back to that exact Province. Any failed gate leaves the siege domain
  unavailable rather than publishing a partial object.
- A valid active siege publishes progress fraction from RVA `0x229B960` as
  `{raw,scale:100000}` in the native 0..1 range, plus current work from
  `CSiege+0x3D0` and total work from RVA `0x229CCA0` in the same lossless
  CFixedPoint representation. Fractions outside raw `0..100000`, or negative
  work values, suppress the entire siege object. RVA `0x229BAA0` returns game
  days left; `INT_MAX` is the engine's invalid/dead/stalled/no-progress result
  and maps to JSON null, whereas zero remains a valid value. `CSiege+0x208`
  is a CArmyID, not the public CUnitID. The bridge scans only the already
  generation-valid CUnits and publishes `besieging_army_id` after exactly one
  full-ID join; ambiguous/no matches stay null, while player participation is
  true if any exact match is controllable. A shared per-snapshot state budget
  of 256 rows keeps paused 250 ms heartbeats from multiplying engine getter
  calls. Each war publishes atomically; an over-budget war gets an empty
  unknown state array. The fixture constructs 257 complete county capitals to
  pin this boundary independently from the 4096-title hierarchy ceiling.
- A later minimized replay at checkpoint date raw `53174208` had player war
  score `41` and CUnit `83886341` at province `2598` in `sieging` state. After
  30 game days it was still not in combat. A wartime
  `disband-army-83886341` was rejected by the native validator as
  `CK3 army is not player-controllable`, with no state change, so wartime
  disband/re-raise is not a supported recovery strategy. After 60 game days
  of siege progress toward exact province `2585`, both enemy native routes
  ended at `2585`. Restricting the planner to exact `2585` and fallback `2543`
  therefore left both points blocked; exposing every de-jure county capital
  is the direct value reason for the multi-objective projection.
- `base + 0x570CC80` is a pointer slot whose single dereference is
  `ComponentStorage<CUnit>`. RVA `0xA84603` ends at `0xA8460A`; adding its
  signed RIP displacement `0x4C88676` resolves to `0x570CC80`. Do not repeat
  the discarded hand-arithmetic result `0x572CC80`: it points two MiB beyond
  the real slot. On 2026-08-23 the wrong RVA reproducibly caused `C0000005`
  during the first live snapshot at DLL RVA `0x890F` while reading the bogus
  storage object's `+0x20`; the minidump is in local crash bundle
  `ck3_20260823_213129`. `CUnit +0x10` is its
  component ID, `+0x174` is owner `CharacterID`, and `+0x20` is current
  `Province*` (`Province +0x10` repeats its positive ID). The controllable
  projection is owner equals the current played character. The earlier
  `0xC73D00` conflict was a type-confusion: that helper consumes a different
  aggregate object. On `CUnit`, RVA `0x26B51B0` proves `+0x38` is an
  eight-byte `SUnitPathProvinceInfo*` remaining-route array with
  capacity/count at `+0x40/+0x44`; every entry stores its ProvinceID at
  `+0x00`, and the native function reads the last entry as the destination and
  resolves it through the live province array. While paused, the exact adapter
  publishes all entries in their native order as `route_province_ids`. It does
  not prepend `current_province_id` or deduplicate repeated entries. Traversal
  is capped at 4096 entries and resolves every ID through the current province
  table before publishing; any invalid entry suppresses the whole route, never
  a prefix. While running, it does not traverse the mutable array and publishes
  `route_province_ids=[]`, but preserves the old single last-entry read as
  `move_target_province_id`/`move_target_observable`. Therefore an empty route
  means "no complete paused route observation", not necessarily "no route".
  Soldier count stays out of the heartbeat and is exposed only by the explicit
  paused `query-army-strengths-v1` path described below.
- `CUnit +0x178` is the generation-bearing ID for the linked `CArmy` in
  `ComponentStorage<CArmy>` at `base +0x570C730`. `CArmy +0x128` is its
  `CCombat` ID, resolved through `ComponentStorage<CCombat>` at
  `base +0x570C758`; `CCombat +0x08` repeats the full ID. The CCombat main
  vtable is `base +0x4300C78`; its `+0x08` function is RVA `0x10495A0`, which
  returns exactly `CCombat+0x08 != -1`. RVA `0xC7AAB0(CUnit*)` performs both
  storage resolutions, generation checks and that live-vfunc call before
  returning state code 2, so `in_combat` is not inferred from co-location.
- RVA `0xC7AAB0(CUnit*) -> int32` has the exact localization-backed mapping
  `1 regular`, `2 combat`, `3 sieging`, `4 embarked`, `5 gathering`,
  `6 retreating`, `7 moving`, `8 raiding`, `9 bartering`. Its tail reads
  positive `CUnit+0x170` for code 6 and nonzero route count `CUnit+0x44` for
  code 7. The snapshot also publishes `retreating` directly from `+0x170 > 0`
  so the actionable flag is retained independently of the prioritized state
  label.
- Read-only PID `144324` evidence on 2026-08-24: player CUnit `83886341` and
  enemy CUnits `33554657`/`357` were all in province `2598`. Their linked
  CArmy `+0x128` values all resolved the same live CCombat ID `318767109`, so
  all three published `state=2/combat`, `in_combat=true`; all three
  `CUnit+0x170` values were zero, so `retreating=false`. The player's seven
  path entries ended at province `2543`, giving an exact observable move
  target even while combat took priority over the moving state. No command
  was issued during this probe. PID `144324` later disappeared before soldier
  aggregation could be closed; the later exact-build static closure below did
  not retroactively turn that probe into live soldier evidence.
- `CUnit+0x178` is a full CArmyID. The exact CArmy storage is the pointer slot
  at `base+0x570C730`; its engine fallback/default is at `base+0x570C720` and is
  forbidden. `CArmy+0x38` is the full CRegimentID array data, `+0x40` capacity,
  and `+0x44` signed count. The exact CRegiment storage is
  `base+0x57BF4C8`; the adjacent fallback at `base+0x57BF4C0` is also forbidden.
  Every object must repeat the complete ID at `+0x10` after low-24-bit slot
  selection.
- RVA `0x27BD9E0(CArmy+0x38, flags=0)` generation-resolves every regiment,
  calls the `CRegiment+0x08` subobject vtable slot `+0x08` public-ID identity
  predicate, and sums `CRegiment+0x38` current soldiers. That predicate is RVA
  `0x10495A0` and proves only `CRegiment+0x10 != -1`; it is not combat activity
  or participation eligibility. RVA `0x226F350(CArmy*)` resolves every regiment
  and sums `+0x3C` maximum soldiers. Both original helpers can fall back internally;
  therefore the bridge first validates the complete exact graph, mirrors the
  loops, and publishes only when both original helper results equal the mirror.
- AI collector RVA `0x19179E0` repeats the same CArmy array, exact generation
  lookup and identity predicate before summing signed qword `CRegiment+0x40`
  into `SAIPowerAndStrengthEntry+0x10`. That value is published only as
  `ai_base_power_raw` with independently proven CFixedPoint scale `100000`.
  It is not named terrain-adjusted strength, ratio, or win probability.
- The fixed native step reads one paused snapshot and returns the first-seen
  union of top-level player armies, then every active war's allied and enemy
  armies. Public CUnit IDs deduplicate without reordering; role priority is
  player, ally, enemy and WarIDs union in snapshot order. One broken
  generation, bounded array, identity, checked sum, or helper comparison makes
  the whole row unavailable and all aggregates null; no bad entry is skipped.
  Offline fixtures cover identity-valid aggregation, legal empty arrays,
  generation mismatch, invalid array, missing identity predicate, and typed
  partial results. Paused revision `4` exact-build live acceptance later passed
  for the three public ArmyIDs recorded in the dedicated slice section below.

## Command queue and object layouts

The common submission wrapper is RVA `0x973E00`; the command manager object is
`base + 0x57621F0`. It calls the command virtual at `+0x40` to clone the source
object, then calls RVA `0x341D990` and returns that locked queue's `bool` in
`AL`. A false return means the queue rejected and destroyed the clone rather
than accepting it. For UI channel flags `7`, the normal path takes the queue
lock at the manager's internal queue `+0x78`, enqueues, and unlocks. This is
strong static evidence that the bridge worker may submit
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

## Typed pending-interaction context live replay

The production-only cold-reload acceptance on 2026-08-26 used immutable save
`xar_checkpoint_pre_white_peace_53175816.ck3` (SHA-256
`5BA2136911EAD0CAF1F7D2F3DE02EAFBD8039861C46F01F35F698B3B5CFFFC5F`).
A seed process sent an ordinary, non-religious white-peace interaction for war
`16777290`, switched from actor `29829` to recipient `36108` on the same day,
and saved a pending checkpoint (SHA-256
`3ABF8B9750911910D95B6AE2108B71BAA040613B3E4410578F1C4F76F16019DF`).
A fresh production-only process then cold-loaded that checkpoint and issued two
adjacent read-only typed queries against the same paused snapshot.

Both observations returned full pending component ID `738197506`, date raw
`53175816`, canonical interaction
`end_war_attacker_white_peace_interaction`, stable name hash `3450334569`,
runtime ordinal `294`, actor `29829`, recipient `36108`, no typed target,
exclusive empty send-options, local recipient routing, expiration age `0/60`,
and `accept/reject/block=true`, `acknowledge=false`. Only the query sequence
advanced; no reply action was submitted. Source metadata and hash remained
unchanged, and both managed user trees were removed after the run. The
acceptance report is
`C:\Users\xenoa\AppData\Local\Temp\xar-pending-interaction-context-v1-live-20260826-04.json`
(SHA-256
`D20E339D56AFEFF8EB53F90FFD120AA8C42216AD214D38B7AC1B0EA9A2B8BC89`).

This closes the ordinary-recipient observation path only. Structured costs,
exchanges, effect preview, and native AI acceptance terms remain explicitly
unavailable, so `interaction_semantic_decision_ready` remains false. The
intermediary route still needs a production live fixture. Acknowledgement is
also not production-reachable yet because the current snapshot discovery
filters `+0x5C6` auto-accept notifications before the typed query can bind their
full component IDs. Religion-specific interaction semantics remain
owner-deferred and were not explored by this replay.

`CRaiseTroopsCommand` is `0x50` bytes. RVA `0x224CC80(Character*)` resolves
the game's default rally province. Constructor RVA `0x26D6FC0` receives the
played `CharacterID` and one `{province_id, -1}` entry, installs vtables
`0x41226D8`/`0x41226A8`, and produces the same `+0x40=-1`, `+0x44=1`,
`+0x48=false` shape as the original path at RVA `0x27A2198`. The bridge calls
validator `0x26D7150(command, nullptr)`, submits with flags `7`, then calls
destructor `0x10E7950(command, 0)` after the queue synchronously clones it.

RVA `0x2248170(CUnit*, Province*, route_kind, mode_is_one)` is the canonical
plan-then-apply path. The preview intentionally stops before its apply call at
RVA `0x2248450`. It first calls `0x2248260` with an exact 0x18-byte origin
context (`uint8* mode_is_one`, `CUnit*`, destination `Province*`), constructs
a 0x130-byte `MovePath` with `0xC7BA70`, constructs a 0x70-byte caller-owned
`PathCtx` with `0x23C32F0`, then calls
`0x23C33D0(PathCtx*, origin, destination, 2, MovePath*)`. The fifth parameter
is the Win64 stack argument. `MovePath+0x00/+0x08/+0x0C` is its pointer-array,
capacity and count; each pointer's `+0x00` is a ProvinceID. The bridge copies
only a complete, <=4096-entry route whose every ID resolves and whose final ID
equals the requested destination. It embeds the path at a temporary complete
`CMoveArmyCommand+0x38`, so every post-construction success/failure exit can
use the already closed `0x26B46D0(command,0)` cleanup. `PathCtx` holds borrowed
pointers and the canonical caller does not destroy it.

A minimized paused live replay on 2026-08-24 captured army current Province
`8759`, its already active remaining route beginning at `2602`, and
`ResolveMoveOrigin=2602` for every candidate. This is a real mid-edge state:
the stable public origin must remain the same paused snapshot's `8759`, while
`2602` is the effective origin from which A* plans. Raw A* returned:

- target `2585`: `[2591,2589,2579,2586,2585]`;
- target `2596`: `[8759,2603,2595,2596]`;
- target `2600`: `[2600]`;
- target `2604`: `[8759,2604]`.

The adapter therefore requires the native effective origin to equal either
the observed current Province or the exact paused remaining-route front. It
always publishes the observed current as `origin_province_id`; when the two
differ, it prepends the effective origin to the raw A* vector without removing
duplicates or loops. The four normalized routes above consequently begin
with `2602`. This is gameplay-significant: enemy army `357` had remaining
route `[2595,2603,8759,2602]`, so every normalized candidate intersects it and
the route-safety policy correctly stays paused. Publishing `origin=2602` with
an unprefixed tail had violated the stable upper-layer contract and rejected
the preview as malformed.

If a target equals the differing effective origin, the normalized remaining
route is `[effective]` and A* is skipped. An empty route is valid only when
observed current, effective origin, and target are all equal. If the target is
the observed current while the army is mid-edge, the unit must finish that
edge and A* may route back; the fixture pins this as `[effective,...,current]`.
Any effective origin outside current/route-front fails closed before path
construction.

Static worker-thread audit found no world write, TLS/global path cache write,
main-thread assertion, or apply/queue path in origin/context/A*. A* recursively
constructs fresh 0x70/0x130 per-call scratch, which is direct reentrancy
evidence. It does not acquire a world-state read lock, however. Therefore the
bridge rejects preview unless the current snapshot is paused. The passive
snapshot likewise traverses the full CUnit route only while paused; while
running it performs only the legacy final-entry read and publishes
`route_province_ids=[]`. That empty running array means "not fully read", not
"no route".

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

`CSplitHalfArmyCommand` is the original player-facing path behind
`window_army.gui`'s `ArmyWindow.SplitHalfSelected`; its adjacent enabled gate
is `CanSplitHalfSelected`. GUI body RVA `0x1242100` calls
`0x26B8030(1, source CArmyID, played CharacterID, nullptr)`, constructs a
`0x30`-byte stack object with primary/secondary vtables
`0x432D5C0/0x432D658`, writes player kind `1` at `+0x20`, the current played
`CharacterID` at `+0x24`, and the source generation-bearing `CArmyID` at
`+0x28`, then queues with flags `0x0E`. The public bridge step remains
`split-army-half-<public CUnitID>`: it generation-resolves that CUnit through
storage `base+0x570CC80` and reads the distinct internal ID from
`CUnit+0x178`; it never passes the public CUnit ID as the command target.

Primary validator wrapper RVA `0x26B7EF0` forwards those three payload fields
to complete validator `0x26B8030`. That validator independently resolves the
source CArmy through `base+0x570C730`, its `CArmy+0x124` CUnit, the unit owner
and both full-generation Characters, requires the played actor to equal the
owner, runs the player command-kind gate, and calls complete split predicate
`0x26B6A90(..., split_half=true)`. The latter rejects not-owner, combat, raid,
barter, retreat and movement-lock states and requires at least two total plus
two live/nonempty regiments. It has no in-war or siege blocker; ordinary
movement is not a blanket blocker apart from retreat and the committed
movement-lock phase. These are native validator facts, not bridge guesses.

Heap clone RVA `0x26C2270` allocates exactly `0x30` bytes and copies all three
payload fields. Serializer RVA `0x26B7F10` records actor tag `0x28AA` and
source-army tag `0x296A`; schema/type RVA `0x26C2300` returns `0x2C0B`.
Bridge submission uses common wrapper `0x973E00`, which synchronously
dispatches the primary-vtable `+0x40` clone and returns the locked queue's
`bool`; false maps to `submission_failed`. The bridge then destroys its
original stack object with RVA `0x963C60(command,0)`. The offline fixture deliberately uses different
public CUnit and internal CArmy IDs, emulates that synchronous clone, poisons
the destroyed source object, and verifies the clone retains kind/actor/source.
It also pins validator rejection and queue rejection, and verifies queue acceptance does not
fabricate a second army in the same snapshot.

The executor is secondary vfunc RVA `0x26B73E0`. It resolves `object+0x28`,
calls `0x26B67C0`, and only then partitions regiment/component data between
source and returned sibling. RVA `0x26B67C0` resolves the source CArmy's CUnit,
calls original creation RVA `0x27BF0A0`, obtains a distinct CArmy whose
`+0x124` resolves to a new CUnit, and copies relevant unit/movement state.
Therefore execution is capable of producing a separately snapshot-visible
and movable public CUnit rather than an internal regiment grouping. The
stable command result is nevertheless only `split_submitted`; a later paused
snapshot must prove the source persists and the player-controllable public
CUnit set gains exactly one ID. Independent control requires a subsequent
move of only the non-besieging sibling while the other remains in place.
The slice was initially frozen without a live command. On 2026-08-24 a
minimized, paused exact-build session submitted the step for public CUnit
`83886341`. The immediate native result remained correctly limited to
`split_submitted`; within two wall-clock seconds, without advancing the game
date, the paused snapshot retained the source and exposed exactly one new
player-controllable sibling, `67108903`. After merging that proof sibling, a
second split produced `83886119`. The two public CUnits were then routed
independently: the sibling created player siege `67108912` in province `2596`
while the original created player siege `83886106` in province `2585`. This is
the live postcondition proof for a distinct, independently controllable CUnit;
it does not change the stable synchronous result from `split_submitted`.

CK3 also has a distinct `CHaltUnitsCommand`; it is not a move-command flag.
The original `ArmyWindow.GetOrders.GetHalt` / `PostCommand` player path builds
kind `1` at RVA `0x123C4F0` and submits with flags `0x0E`. The command is
`0x40` bytes, uses primary/secondary vtables `0x432C0D8/0x432C0A8`, constructor
`0x26B52C0`, destructor `0x26B5330`, validator `0x26B5400`, executor
`0x26B5370`, and heap clone `0x26C1F60`; its serializer type ID is `0x6A`.
The payload is a deep-copied native array of full generation-bearing CUnit IDs
at `+0x28/+0x30/+0x34`, while `+0x20` stores the player command kind. A bridge
request must contain one CUnit only because the validator accepts when any
array member is actionable whereas the executor visits all members.

The executor calls `0x2246CD0(CUnit*)` to choose the halt destination and then
the canonical `0x2248170(unit,destination,2,0)` plan/apply path. Before the
movement commitment threshold, the destination is the observed current
Province and apply clears the route. After the threshold, the destination is
the old route front; apply removes the suffix but reinserts that front, so the
exact postcondition is `[old_route.front]`. A committed route that already has
only one entry is rejected by halt eligibility RVA `0x2248940`, since no
suffix remains to cancel. Therefore Halt cannot reverse a mid-edge unit. In
the minimized live deadlock with observed Province `8759`, route front `2602`
and enemy route ending at `2602`, Halt could only have produced `[2602]` and
was not a safe alternative to exact checkpoint restore. This ABI is frozen as
research only; no Halt capability is advertised until implementation,
fixture coverage and a recoverable live postcondition replay are complete.

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
WarOverview builder `0xC569F0(context, war, player_is_attacker)`. That builder compares the
played CharacterID with primary sides at `CWar +0x288/+0x28C`, chooses the
opponent, and uses the enforce-demands interaction at
`CCharacterInteractionDatabase +0x1018`.
WarOverview send RVA `0xF54FA0` proves the remaining native path is validation,
`CSendCharacterInteractionCommand` construction, submit flags `0x0E`, and
embedded-context destruction. Its visual confirmation window is only a UI
wrapper and is not part of the headless gameplay command.

`query-war-termination-options-<war_id>` is the paused, strictly read-only
counterpart. It accepts one positive full-generation WarID, re-resolves the
same live `CWar`, verifies participant side and the total against the current
semantic snapshot, and constructs all contexts only for the played primary war
leader. Surrender and victory both use RVA
`0xC569F0(context, war, attacker_victory)`: `true` selects absolute attacker
victory and `false` selects absolute attacker defeat. WarOverview's Victory tab
therefore passes `true` for a primary attacker and `false` for a primary
defender; its Defeat tab passes the inverse. The published labels remain
attacker-relative (`attacker_defeat` or `attacker_victory`). No context is
built for a participating ally who is not their side's primary leader.

White peace first requires the active CB type's `+0x1718 & 0x80` gate and a
primary opponent. Exact helper RVA `0x2225D40(context, uint8 index=3, actor,
recipient)` reads the interaction from independent
`CCharacterInteractionDatabase +0x1008 + 3*8 = +0x1020`. It uses the generic
two-role constructor when the interaction's first virtual predicate passes and
otherwise returns the default empty context. The bridge therefore does not
construct this option for a null CB, a false permission bit, a non-primary
participant or an unresolved opposite primary. A permitted empty context stays
`context_constructed=false`; it is not converted into a fabricated validator
rejection.

Every nonempty context is checked with common validator RVA `0x2C43F00`. Answer
score helper RVA `0x2C44320(context, int64* out_raw)` returns its output pointer
and writes signed `CFixedPoint` raw units; public scale is 100000 and the bridge
does not apply the GUI's display clamp. `auto_accept` exactly follows the
interaction data: optional trigger pointer `+0x2580` is evaluated with RVA
`0x334C510(trigger, context+0x08 event-target scope)`; when the pointer is null,
byte `+0x2A48` is the scalar bool. Each temporary 0x338-byte context is then
destroyed. The query never constructs `CSendCharacterInteractionCommand`, calls
the queue or publishes a command ACK.

The successful `command_result` wraps one `war_termination_options` object with
`war_id`, player side/primary status, player-relative score, nullable duration,
absolute attacker/defender totals, nullable four-part breakdown, active-CB
presence/identity, nullable white-peace permission and an `options` object.
Each `surrender`, `white_peace` and `victory` item publishes
`outcome`, `hostage_variant="none"`, context/validator/availability,
nullable `{raw,scale:100000}` AI acceptance and nullable exact auto-accept.
Terms are intentionally fixed to
`{status:"unavailable",reason:"cb_specific_terms_not_observable"}`. This build
does not prove CB-specific title, gold, prestige, piety, legitimacy, truce or
prisoner effects, and no such terms may be inferred from an absolute outcome or
a valid context.

The separate read-only
`query-war-termination-terms-v1-<war_id>` resolves `CWar+0x270` ordered
declared TitleIDs and claimant `+0x290`, then calls
`0x28B1AA0(out_0x18, claimant, title)` for every target. Present rows require
vptr `base+0x40E3060`, title-ID readback and canonical booleans, then invoke
vtable slot 0 with delete flags 0. Absent rows do not inspect or destroy the
getter's unspecified remaining bytes. Whole-war before/after identity,
target-array, claimant and active-CB rereads make the union atomic. Only
`claim_cb_claim_disposition` is available; other CBs return a complete narrow
unsupported branch. The native fixture closes all four claim states, absent
no-destructor, present failure cleanup and stale-generation rejection. Real
getter/destructor live acceptance remains pending.

`surrender-war-<war_id>` requires a
paused map, the current played Character to participate and to equal one of
`CWar +0x288/+0x28C`, then rebuilds the player's absolute defeat
(`attacker_victory = player_is_primary_defender`), requires non-null
special data and common validator success, constructs the common 0x368-byte
send command, and submits with flags `0x0E`. It honors the queue's bool result
and destroys both context copies on every path. Typed success is only
`submitted`; disappearance of the exact WarID from a later snapshot is the
war-ended postcondition. `offer-white-peace-<war_id>` follows an independent
typed path: it also requires the played primary leader, generation-resolves
the opposite primary, checks the active CB `+0x1718 & 0x80`, constructs
special context index 3, runs the same validator, and submits with flags
`0x0E`; queue false stays `submission_failed`, and both constructed context
copies are destroyed. The exact adapter advertises both mechanical native
capabilities, but the Python driver advertises neither literal and rejects
direct MCP submission until structured `claim_cb_exit_terms_v2` and campaign
decision readiness exist. This implementation slice used only static
exact-build evidence, offline fixtures and the offline executable scanner; it
did not access or submit a command to a CK3 process.

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
declare war, raise, movement, paused termination query, surrender/enforce
demands, and disband; event and save are no longer pending live acceptance.

## Assault Fort exact native slice

The full frozen contract is
[`docs/ck3-native-assault-contract.md`](../../../docs/ck3-native-assault-contract.md).
This is exact-build static plus native-fixture evidence for CK3 1.19.0.6
SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The exact adapter now advertises the Assault snapshot and Start/Stop command
capabilities; this is not a live acceptance result. No CK3 process was accessed
and no command was submitted to CK3 during this implementation slice.

Original GUI reflection dispatches `SiegeWindow.StartStopAssault` through thunk
RVA `0x131E910` to action `0x131D770`. Start and Stop are separate `0x30`-byte
Jomini command objects. Start uses primary/secondary vtables
`0x432CB30/0x432CB00`, ctor `0x26C69B0`, clone `0x26C2FC0`, validator
`0x26BE8C0`, executor `0x26BE450`, and type `0x3163`; Stop uses
`0x432CBC8/0x432CA08`, ctor `0x26C6960`, clone `0x26C30C0`, validator
`0x26BEA90`, executor `0x26BE9A0`, and type `0x3164`. Both use destructor
`0x963C60`, carry kind/played CharacterID/SiegeID at `+0x20/+0x24/+0x28`,
and the original GUI submits player kind `1` with flags `0x0E`.

For this build, `CSiege+0x3D8` is `breach_level` with the closed valid range
`0..2`, and `CSiege+0x44C` is the assault-active flag. Start requires a live
breach and eligible besieging strength at least equal to the current garrison;
Stop requires the active flag but does not repeat those two gates. Native daily
casualties are calculated by `0x229F410`; pre-start progress projection must
use core `0x229F610`, while active-only wrapper `0x229F580` intentionally
returns zero before Start. See the contract for fail-closed snapshot semantics,
one-day Start/Stop postconditions, migration gates, and the bounded 53-day
decision. The pinned scanner now closes the two complete validators, both daily
calculators and all four primary/secondary vtables; the fixture closes paused-only
publication, exact payload cloning, full-generation IDs, validator rejection,
bool queue rejection and original-object destruction. Live outcome acceptance
remains pending.

## Merge Armies exact native slice

The frozen contract is
[`docs/ck3-native-merge-contract.md`](../../../docs/ck3-native-merge-contract.md).
This slice was first closed from offline/static and native fixture evidence for
the exact pinned build. A later minimized, paused exact-build replay supplied
the live postcondition described below.

Original `window_army.gui` dispatches `ArmyWindow.MergeSelected` through
reflection RVA `0x1241FD0` to action `0xC71B10`. The underlying
`CMergeUnitsCommand` is a batch command, size `0x40`, with primary/secondary
vtables `0x432D3C8/0x432D398`, player kind at `+0x20`, destination public
generation-bearing CUnitID at `+0x24`, and a native array of source public
CUnitIDs at `+0x28/+0x30/+0x34/+0x38`. Neither payload field is the linked
internal CArmyID.

The bridge deliberately exposes only
`merge-armies-<destination>-with-<source>` and fixes count to one. It uses
zero-argument engine-heap factory `0x26C6CE0`, which initializes the array
allocator, then canonical range insertion `0x975ED0(header,0,begin,end)`.
Object validator `0x26BA050` resolves destination/owner and tail-calls complete
validator `0x2947D10`. Submit wrapper `0x973E00` queues with player flags
`0x0E`, synchronously invokes deep clone `0x26C26B0`, and returns the locked
queue's `bool`; false maps to `submission_failed`. Deleting destructor
`0x26B5330(command,1)` releases the original source buffer and `0x40` object.
The array has no borrowed/inline ownership state, so a stack pointer at `+0x28`
would be invalid and is never used.

Complete validation owns same-province, destination/source combat, owner,
land/naval, destination retreat/movement-lock and raid-territory gates. The
bulk executor wrapper/core are `0x26B9F60/0x2948680`: compatible sources are
transferred into the destination, destination identity is preserved, and the
source CUnit/CArmy is removed. The only stable success is `merge_submitted`;
a later paused snapshot must prove destination remains and source disappears.
For Split Half recovery, preserve the desired original army as destination and
add siege-ID/backlink continuity when it is the besieging army. On 2026-08-24,
`merge-armies-83886341-with-67108903` returned `merge_submitted`; within two
wall-clock seconds at the same paused game date the source CUnit disappeared,
the destination retained its public ID, owner and province, and the player
controllable ID set was exactly the prior set minus the source. A later merge
of `83886119` into `83886341` at game date `53176104` repeated the same
source-removal/destination-preservation postcondition while both armies were at
the same active siege province. The latter snapshot retained siege
`83886106` and reported combined eligible besieging strength `1501`; this is
evidence for same-frame siege continuity, not a claim that queue ACK alone
proves a merge or that arbitrary merge timing is safe.

## War termination exact native slice

This slice is frozen from exact-build static evidence and offline native
fixtures only. It advertises paused read-only options plus claim-disposition
v1 discovery and contains typed native surrender/white-peace mechanics for
CK3 1.19.0.6 SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`;
Python advertises neither terminating literal until structured exit terms v2
and campaign readiness. No CK3 process was read, attached, focused or
commanded while this slice was implemented or verified.

The final Release build used a fresh
`build-war-termination-msvc-release-2` directory with MSVC. CTest passed all
four targets: game-access fixture, adapter registry, suspended-injection
fixture, and running-attach fixture. The two injection tests use repository
test targets, not CK3. The offline executable scanner matched `121` unique
signatures and `19` vtable prefixes, including every newly bound termination
helper. Diagnostic artifact SHA-256 values are:

```text
xar_ck3_bridge.dll          C388A913CA214DF3EC399F6D330C040C1AA25624C75CCBC21B1A9B36EEB31947
xar_ck3_bridge_injector.exe 0616F828A8AD4464CAED804F3F19FD718F4F47C075F3A4901768C1D0B891106C
```

These hashes freeze this offline build evidence only. The build directory is
not versioned, and this record is not a live gameplay acceptance or release
channel marker.

## Main-thread mailbox counter-only artifact and application-main disposition

The first production-wired `main_thread_query_mailbox_v1` artifact was built
from scratch on 2026-08-25 in
`.build-main-thread-mailbox-counter-fresh-msvc` with MSVC 19.51 and Ninja.
CTest passed all 14 configured targets, including the mailbox source contract,
the process-lifetime reinstall and late-hook fixtures, the war-entry typed
mailbox adapter, both combat-v3 serializers, the phase-event trace ring, and
the suspended/running bridge-host tests. The exact-build scanner matched all
`138` unique signatures and `23` vtable prefixes.

This artifact installs the IAT hook only when the selected adapter ID is
exactly `ck3-1.19.0.6-msvc-x64`. It publishes dynamic counters only in the
existing heartbeat metadata. `executor_submission_enabled` is hard false,
`executed_requests` remains zero, and there is no mailbox capability, command
literal, action step, or MCP projection. It was not injected into CK3 in this
build pass; paused and minimized pump reachability is therefore still a live
acceptance gate rather than an offline claim.

The subsequent paused live counter established that this exact return boundary
is on the application/startup-main HandlePdxEvents TLS path: the TLS global,
context and `+0x20` marker passed while failure bit `32` reported only that the
generic scoped RNG owner was not held at that instant. RNG ownership is now
diagnostic provenance, not a readiness or execution gate. The production
follow-up is deliberately typed to `query-war-entry-assessments-v1` only: the
worker freezes one target and one declarable-war set from the same paused
expected snapshot; reader before/middle/after callbacks each perform a fresh
`ReadSnapshot` and require exact equality. This evidence does not rename the
boundary simulation-main and does not authorize generic effects, phase queries
or evaluators.

```text
xar_ck3_bridge.dll          529408 C0ADCFD88FABD3F5BF616B331160471D2E9412A20E84FDCB12E67D3823A6016D
xar_ck3_bridge_injector.exe  38912 F4AC2FE2EF41AF5529157B273595FDE823E2D2E27972D2C6CCAECC32D9BC296B
xar_ck3_bridge_host.exe      69632 AC06E5E8FB5E19AA30897F9324A7DA964C5E177DB5077C5C2F9893D741EA10F4
```

These hashes freeze the counter-only offline artifact. They are not a release
marker and do not raise any query executor, gameplay capability, combat
fidelity, planner, or attack-decision readiness gate.

### Application-main typed war-entry production artifact

The bounded follow-up was configured and built from scratch on 2026-08-25 in
`.build-war-entry-app-main-production4-msvc` with MSVC 19.51 and Ninja. All 14
CTest targets passed. The read-only exact-build scanner matched 138 unique
signatures and 23 vtable prefixes. It did not start, attach to or inject CK3.

This build advertises only the canonical single-target
`game.command.query-war-entry-assessments-v1-N` contract. The mailbox admits
only `ExecuteWarEntryAssessmentMailboxQueryV1`, at most one request per pump.
The worker performs one fresh same-paused-snapshot declaration scan for the
single requested target and freezes that scope. It does not enumerate every
character in storage. Reader before/middle/after callbacks each perform a
fresh complete snapshot equality check; resolver, network and assessment rows
are sampled twice. RNG owner TID remains diagnostic only. An available typed
live result is still pending, and this boundary does not authorize generic effects or
combat phase evaluators.

Production4 then ran one official-MCP single-target live query while paused.
The application-main mailbox stayed ready, the typed executor entered the
reader, and the query returned atomically unavailable at `actor_ai_context`;
the process/date remained stable and normal Stop cleanup was proven. Static
review showed the retired manager span excludes human actors before creating
or refreshing `extension+0x278`, so that source is not a valid player reader.
The production5 fix binds the authoritative native State16 builder at
`0x18784D0`: every sample zeroes all 16 caller-owned bytes, requires the
`module+0x570C638` dependency to remain nonnull and pointer-stable, calls the
builder once, passes that exact State16 to `0x1878A00`, rejects any assessment
mutation, and requires the second State16 to match byte-for-byte. Until that
artifact returns an available live result, `live_executor_observation` remains
false even though `typed_executor_invoked_live` is true.

```text
xar_ck3_bridge.dll          572928 D5E5A5433880B33151CA299807ED4F7E45F3CA26EE7B9D196E61CE925472DD63
xar_ck3_bridge_injector.exe  38912 F165935E691F6210D33466A9288AE2F49E7969BB7DC318D116A18E0B567CC2AF
xar_ck3_bridge_host.exe      69632 8AC36A81BD5D18AFC6C79D712FF9E4E9E72EF0838401FAFE37D971F33C22EB44
```

These hashes freeze this offline production candidate only. They are not a
release marker or a claim that the typed live result has passed.

### Authoritative State16 war-entry production6b artifact

The actor-context failure was rebuilt from scratch on 2026-08-25 in
`.build-war-entry-state16-production6b-msvc` with MSVC 19.51 and the Visual
Studio Windows CMake/Ninja toolchain. The DLL timestamp is later than the
State16 reader source. All 14 CTest targets passed; the exact-build scanner
matched 138 unique signatures and 23 vtable prefixes. The targeted Python
war-entry/gameplay suite ran 158 tests successfully with three optional cases
skipped. No CK3 process was started or attached.

```text
xar_ck3_bridge.dll          572928 3A0AADEB538C7595DAAE35CF8A722FD06689862FF9F0F1CC32C5838F9BE97499
xar_ck3_bridge_injector.exe  38912 A6954F3037AAB2201FB59B52A71517B41D300E150431009D406AA7045B7FE8C6
xar_ck3_bridge_host.exe      69632 E3529C7FA1ACF82ABB68D12C74B21A033CD4DBC51D47C83D9F38CECA226BD864
```

This artifact replaces the invalid human manager-context lookup with the
exact `0x18784D0` zeroed State16 builder and dependency stability gates. It is
the next paused single-target live candidate, not evidence of an available
live result; `live_executor_observation` remains false until that acceptance.

### Claim-disposition v1 and frozen native white-peace final artifact

The combined final artifact was configured and built from scratch on
2026-08-25 in `.build-war-terms-wp-final-msvc` with MSVC 19.51. Fresh CTest
passed all five targets: game-access fixture, adapter registry, combat-v3
test-only serializer, suspended injection and running attach. The exact-build
scanner matched `138` unique signatures and `20` vtable prefixes, including
`read_character_claim` and `CCharacterClaim.present`. The targeted Python
driver/service/contracts suite passed `253` tests; three optional official-MCP
SDK cases were explicitly skipped because that SDK is not installed. No CK3
process was accessed and no termination command was submitted.

```text
xar_ck3_bridge.dll          size=364032 SHA256=AC8F716B186A1C91A079958A65E627F6B2913EDA68F5702BAC62593192CAA14A
xar_ck3_bridge_injector.exe size=38912  SHA256=9196F79F242B257CCADE7C69B6EBE436151EF536B8A6E50B7393BEFDB391308E
```

These hashes are deployment artifacts for the pending paused read-only
claim-getter/destructor acceptance. They are not evidence that
`0x28B1AA0` or its vtable destructor has run inside CK3, and they do not unlock
the Python surrender or white-peace action surface.

## Combat simulation inputs exact native slice

This strictly read-only hypothetical-contact slice is frozen for CK3 1.19.0.6
SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
Capability `game.command.query-combat-simulation-inputs-v2-N` accepts only
`query-combat-simulation-inputs-v2-<target>-<entry>-a-<Acount>-<A...>-d-<Dcount>-<D...>`.
The former v1 literal is superseded and is not advertised or dispatched. Its
offline implementation required an existing move/current-position contact
shape; the paused `83886341@2596` versus `357/33554657@2581` scenario could not
construct one target accepted for all three armies before a move order, making
that admission rule a reproduced live blocker. Every
numeric token is a positive canonical ASCII decimal; both exact counts are
1..63, the combined count is at most 64, target differs from entry, and all
public full-generation ArmyIDs are distinct across partitions. One paused
snapshot must place every requested army in player/active-war scope, prove all
IDs share an active WarID, and prove each partition is one coalition opposite
the other; player and active-war allies may share the friendly partition. This
is the conditional
`explicit_hypothetical_fixed_at_contact_no_reinforcements` participant model.
Attackers are fixed at the supplied final-edge entry and defenders at target;
their current positions, move targets, routes, route timing, and later
reinforcements do not control admission.

The root graph uses exact storages and full-ID readback throughout. Public
`CUnit` storage is `base+0x570CC80`; its ID is `+0x10`, current and target
Province pointers are `+0x20/+0x30`, owner CharacterID is `+0x174`, and CArmyID
is `+0x178`. `CArmy` storage is `base+0x570C730`, never fallback
`base+0x570C720`; ID is `+0x10`, regiment IDs are the bounded array
`+0x38/+0x40/+0x44`, commander CharacterID is `+0x120`, backing CUnitID is
`+0x124`, and CCombatID is `+0x128`. Owner resolution follows that CUnitID back
through exact CUnit storage, reads `CUnit+0x174`, then resolves Character storage
`base+0x570C130` with full ID readback at `CCharacter+0x18`. The resulting
Character modifier owner supplies native counter efficiency/resistance indices
`0x106/0x107` in Q100000.

Commander helper RVA `0x2278F70` receives `CArmy*` and consumes the full
CharacterID at `CArmy+0x120`; it is not a CUnit or owner helper. Generic points
come only from RVA `0xBC5410(CCharacter*,-1,false)`. Paused code never calls
the RNG-consuming roll helper. It mirrors its inclusive min/max operands from
signed default globals `base+0x570ED7C/+0x570ED80`, the Character modifier
aggregator returned by `0x26172C0`, fixed-point reads through
`0x20AB950`, generic indices `0x108/0x109`, and the two **modifier indices**
stored as uint16 at terrain `+0x76E/+0x770`. Each Q100000 contribution is
individually divided with signed truncation toward zero. A proven absent
commander has exact bounds `[0,0]`; a broken non-null generation is unavailable.

`CRegiment` storage is `base+0x57BF4C8`, never fallback `base+0x57BF4C0`, with
ID `+0x10`, current/maximum soldiers `+0x38/+0x3C`, and public-ID identity
subobject `+0x08`. Nullable `CRegiment+0x118` is used only for the stable MAA
database key at type `+0x18`; absent cannot be inferred to mean levy. Combat
classification instead follows original side-population RVA `0x23C9100`:
`combat_type=*(regiment+0x18)`, call its vtable slot 0 validity predicate and
RVA `0x239CEB0(CRegiment*)`; only `!type_valid && !special` is `levy`, while
every other case is `men_at_arms`. Main-phase eligibility is exactly byte
`combat_type+0xA0A != 0`. These two buckets are the only CRegiment combat kinds;
knights are projected independently as Characters.

Target-specific regiment evaluation calls synchronous wrapper RVA
`0x239CAE0(CRegiment*, Stats38* caller_owned_out, CProvince* target)`. Its
0x38-byte output carries max size at `+0x08` and signed Q100000 siege, damage,
toughness, pursuit, and screen at `+0x10/+0x18/+0x20/+0x28/+0x30`. Counter
operands use class `combat_type+0x270`, bounded targets at
`+0x2B8/+0x2C4` with 0x10-byte `{class,effectiveness_q100000}` rows, and RVA
`0x23D2B90` against a zeroed synthetic 0x60-byte side entry containing only the
full RegimentID at `+0x08` and checked `current_soldiers*100000` at `+0x18`.
RVA `0x82DC40()+0xF14` supplies the positive bounded class count. Directional
resolution calls `0x2946B50` for the owner-derived context scale and
`0x23CF1B0(countered,countering,out,scale)` into caller-owned class storage.
The original side primary participant is the first inserted CArmy owner. The
hypothetical side therefore uses its explicitly frozen ArmyID request order and
the first owner for the directional context scale, including mixed-owner sides;
this is not inferred actual arrival order.

Knight identity starts at each generation-valid participant regiment:
`CRegiment+0x148` is a full CharacterID, `-1` means no knight, and any non-null
ID must resolve through exact Character storage. Membership is cross-checked in
both directions: `CRegiment+0x140` must equal the requested CArmyID and
`CCharacter+0x1B0`, then link `+0xF8`, must repeat the source RegimentID.
Effective prowess is `CCharacter+0xE8`. Direct effectiveness uses the borrowed
context from `0x2613480(CCharacter*)` followed synchronously by
`0x28FD990(int64* out, context, mode=0)`; it is published in Q100000 without
lossy back-solving. The same `0x239CAE0` result must supply the knight's native
damage/toughness contribution, cross-checked against the exact signed int32
defines at `base+0x570EDF8/+0x570EDFC` rather than hard-coded stock values.
Duplicate CharacterIDs or RegimentIDs, failed
membership, generation drift, context failure, or contribution inconsistency
rejects the strict graph rather than skipping a knight.

The requested target and attacker-entry Provinces resolve through
`game_state+0xA0` game data and its
`+0x140/+0x14C` positive-ID pointer table with ID readback at `CProvince+0x10`.
Terrain RVA `0x220D940(CProvince*)` follows the Province terrain chain; key is
the bounded PdxString at terrain `+0x18` and width multiplier is signed Q100000
at `+0x58`. The explicit entry `CProvince+0x08` map node exposes bounded
adjacency rows at `+0x50/+0x5C`, stride `0x30`, with kind `+0x00` and target
ProvinceID `+0x04`. The target edge must be unique: kind 0 is `none`, 1 is
`strait` (source encoding sea adjacency), 2 is `river`, and 3 is `large_river`;
impassable 4 and non-contact 5/6 reject. Missing edges reject and malformed or
duplicate adjacency storage is unavailable. Native side orientation is side 0
attacker and side 1 defender.

The original `0x2209450` contact builder scans the target's full CUnitID array
at `CProvince+0x748/+0x754`, generation-resolves each `CUnit+0x178` CArmyID,
and passes stored-order `CArmy*` opponents through `0x27FB7C0` to the combat
constructor. The constructor inserts defenders into side 1 and holding uses
that side's first CArmy owner. A hypothetical contact
instead freezes explicit `defender_army_ids` request order as its conditional
insertion order and uses the first defender owner, even on a mixed-owner side.
Holding status is the read-only predicate RVA
`0x2900BB0(CCharacter* defender_owner,CProvince* target)`; no effect or script
value is applied by this query. Initial width mirrors the native first-contact
path with previous base zero: sum current soldiers per side, take the
integer-truncated average, multiply by signed Q100000 `BASE_WIDTH_RATIO` at
`base+0x570EDB8`, clamp base to at least 1, then multiply by the terrain width
and clamp final to `MINIMUM_COMBAT_WIDTH` at `base+0x570ED84`. The frozen vector
`1000` versus `800` with ratio 1.0 and terrain 0.8 gives base `900`, final `720`.

If a selected CArmy already links a generation-valid `CCombat`, the optional
ongoing row reads ID `+0x08`, Province `+0x6B8`, phase/day `+0x6B0/+0x6B4`,
base/final width `+0x6C0/+0x6C4`, side rolls `+0x6D0/+0x6D4`, and
base/resolved advantage `+0x6C8/+0x710`. No combat produces no row, never a
zero-filled placeholder. Side orientation is explicitly
`native_side_0_attacker_side_1_defender`.

`completeness.observation_slice` is `precontact-composition-context-v2` and
`completeness.input_observation_ready` is true only when every advertised
input subdomain is available; any read failure makes the result `partial` and
adds its concrete input-domain name. A fully available observation still has
`monte_carlo_ready=false` and exactly four simulator—not MCP—gaps:
`damage_to_casualty_allocation`, `pursuit_transition`,
`battle_end_and_retreat_transition`, and `phase_event_rng_and_effects`.
The native query submits no command, applies no effect, advances no date, and
consumes no RNG. Exact available transport shape is frozen in
`research/fixtures/combat_simulation_inputs_v2_available.json`; malformed
literal, generation, levy/MAA/special/main-phase-false, absent type/commander,
counter, knight, crossing 0..6, explicit-side relation, mixed-owner insertion
order, width, and typed-partial cases are covered by offline fixtures. Exact-build live acceptance
remains pending and this section must not be read as live gameplay evidence.

The final offline Release build used the fresh
`.build-combat-context-native-v2-final-msvc` directory with MSVC 19.51. CTest
passed all four targets: game-access fixture, adapter registry,
suspended-injection fixture, and running-attach fixture. The latter two use
repository test targets, not CK3. The executable scanner matched `137` unique
signatures and `19` vtable prefixes, including all 14 newly bound combat
helpers. Diagnostic artifact sizes and SHA-256 values are:

```text
xar_ck3_bridge.dll          336896 305DA2DBBB8F161543A437EB7C77D18C55CDE1A569FF33CCEE333BE45F4F6CAA
xar_ck3_bridge_injector.exe  38912 5159F2D2740DF31FEDC154E7AB2B6C914D6FB50941BA5145E54DCCB3BC7E561C
```

These hashes freeze this offline build evidence only. The build directory is
not versioned and the record is not a live gameplay acceptance or release
channel marker.

## Army strength exact native slice

This paused, strictly read-only slice is frozen from exact-build static
evidence and offline native fixtures for CK3 1.19.0.6 SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
It advertises `game.command.query-army-strengths-v1`, does not accept native
caller-supplied IDs, and never submits to the command queue. One call derives
its full allowed scope from one snapshot: player armies first, followed by
each active war's allied armies and then enemy armies, with first-public-ID
order, stable WarID union and role upgrades. Exact-build live acceptance is
live-confirmed on paused revision `4`: player ArmyID `83886341` returned
`1482/2243` current/maximum soldiers, `38` regiments and AI base power
`5,522,300,000` raw (`55,223` at Q100000); active-war enemy `33554657`
returned `1011/1011`, `22`, and `3,160,000,000` raw; enemy `357` returned
`1801/3751`, `23`, and `5,846,800,000` raw. All three rows came from the same
read-only paused query and revision, not from GUI estimation or command ACKs.

The final Release build used the fresh
`build-army-strength-msvc-release-2` directory with MSVC 19.51. CTest passed
all four targets: game-access fixture, adapter registry, suspended-injection
  fixture and running-attach fixture. The game-access fixture additionally
  closed identity-valid aggregation, full-generation rejection, strict
  data/capacity/count array validation, missing identity predicate, atomic
  partial rows and legal empty armies. The two injection tests use repository test
targets, not CK3. The offline executable scanner matched `123` unique
signatures and `19` vtable prefixes, including both soldier helpers. Diagnostic
artifact sizes and SHA-256 values are:

```text
xar_ck3_bridge.dll          235008 B92E5542655D115E4BAA419EBE14B73032138E0250655EAEDF5F931A82258197
xar_ck3_bridge_injector.exe  38912 6CF1758D0733512FE8804302BA590BB56449057421C9578C5A05BEBE308E9A7C
```

These hashes freeze this offline build evidence only. The build directory is
not versioned, and this record is not a live gameplay acceptance or release
channel marker.

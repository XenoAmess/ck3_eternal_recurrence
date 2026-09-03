# G2 generic war-bound current paused acceptance — 2026-09-03

## Result

[production launch / startup RED / zero query] The exact frozen G2 candidate at
HEAD `7858da1e28905b8f51fc1510095dfc8ea29bd5a3` passed its fresh no-launch
verification, then started exactly one CK3 process, PID `16564`. The managed
session exited with code `1` before native readiness. No MCP sequence existed,
so the required two `query-war-termination-terms-v1-50331699` calls were not
issued: observed query count is `0/2`, `mutation_commands=[]`, time did not
advance, and no readiness may be promoted.

The live report is
`Z:\ck3_mod_rewrite\artifacts\g2\2026-09-03\generic-war-bound-live-20260903T015828Z\live-report.json`
(SHA-256
`ABA236D51C99A22B593866892AC9D6FFDA4A2839F18E2B186A21174EB0753FE6`).
The first invocation attempt is also retained separately: it stopped before
creating CK3 because the sandbox identity triggered Git's dubious-ownership
check. That harness RED was corrected only through process-local
`GIT_CONFIG_COUNT` variables; no global Git configuration was changed and it
did not consume the single actual launch.

Cleanup is complete even though the acceptance is RED:
`shutdown_ok=true`, `tree_gone=true`, `cleanup_proven=true`, and
`driver_closed=true`. The final CK3 and injector inventories are both zero.
The checkpoint and driver-state hashes remained respectively
`60108A5D...AF164` and `4FB901C7...FF57E` before and after.

## Exact crash identity and causality

The minidump binds `ck3.exe` at `0x00007FF68DA70000` and the exception at
`0x00007FF68F81BD89`, therefore the exact module-relative fault is
`ck3+0x1DABD89`. The exception is `C0000005` read access at address `0x244`.
This is byte-for-byte the already documented particle2 null-slot family:
`null + 0x1F8 + 0x4C = 0x244`.

This result does not implicate the new generic war-bound reader as a direct or
necessary cause:

- prior no-DLL, full-profile-clone, and no-`-loadsave` main-menu controls
  reproduced the same exact RVA and read address;
- the new reader is reachable only after the bridge receives a
  `query-war-termination-terms-v1-*` request, while this attempt stopped before
  readiness and issued no request;
- the current DLL was loaded, but its production source fixes
  `kStartupFailureContainmentEnabledV1=false`, and its build has the separate
  no-suppression particle2 stage recorder OFF. It therefore leaves the
  crashing native bytes untouched.

Checkpoint/profile state and DLL injection are consequently excluded as
necessary triggers for this repeated fault. The narrowed cause remains CK3's
common startup particle2 resource slot being null when the unguarded consumer
at `0x1DABD89` reads it. The post-crash dump still cannot distinguish the
upstream source/VFS, variant-table, and backend-creation null exits.

The frozen crash bundle is under
`Z:\ck3_mod_rewrite\artifacts\g2\2026-09-03\generic-war-bound-live-20260903T015828Z`.
Its minidump SHA-256 is
`712B8A1A4BE500CE9534480D755B598A7854FE6F651EDFB1899E4434C822044D`;
the exception text SHA-256 is
`E15E164294CB677EABBD2603B3D0F365663BE2BD87DE8B4AAE8CADA65FE7F4DB`;
the full artifact index SHA-256 is
`A260CE4DCBB14386AB7A592A3FB3A44511003F04FAE548ADAF25006AEA6AE07B`.

## Guarded retry boundary

[no-launch / blocked] The current runner owns one bridge-DLL slot and invokes
that DLL's `XarCk3BridgePrepareStartup` while the new process primary thread is
suspended. It has no second startup-guard DLL slot. The old live-confirmed
guard DLL predates the generic terms reader and cannot replace the current
source DLL without losing the capability being tested. The current source
still contains all four verified guard implementations, but compiles their
startup transaction off; the stage-recorder option is observational and does
not contain the fault.

The minimum wiring is therefore a default-OFF build option that binds the
existing `kStartupFailureContainmentEnabledV1` constant, followed by a fresh
current-source DLL build and hash freeze. No `ck3_11906.cpp`, query contract,
policy, or runner control flow needs to change. The unchanged live contract
must still require exactly two paused terms queries, strict child/aggregate/
session/cache equality, and `mutation_commands=[]`.

This is only the next diagnostic startup seam, not a preclaimed fix: the
existing four-guard chain previously crossed `0x1DABD89` but later encountered
`ck3+0x369CB58`. A new launch remains forbidden until a current-source guarded
DLL exists and the no-launch verifier binds its hash and startup configuration.
The prepared blocked manifest and verify-only result are stored beside the
crash bundle; their SHA-256 values are
`48401B5E44C2A4FE14AEF1A85F110999E2071DA30EB7A0A00B80E5627D611887`
and
`15CED8022CD7CBBBFB2D06DF30B630A6FEEBB1F3905A91DCA3DB32472D1F2043`.

## Guarded retry implementation design and no-launch gate

The minimum source patch is deliberately limited to two existing production
files after the phase-two observer work releases them:

1. In `ck3_autonomous_player/native_bridge/CMakeLists.txt`, add
   `XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1` as a default-`OFF` option.
   When it is enabled, add the private definition
   `XAR_CK3_ENABLE_STARTUP_FAILURE_CONTAINMENT_V1=1` to
   `xar_ck3_bridge`.
2. In `ck3_autonomous_player/native_bridge/src/bridge.cpp`, replace only the
   hard-coded false constant with an `#if defined(...)` branch that sets
   `kStartupFailureContainmentEnabledV1=true` for that build and false
   otherwise.

The existing `static_assert` continues to reject simultaneous containment and
particle2 stage recording. The existing `PrepareStartup` transaction and its
order remain unchanged: particle2 null guard, particle2 consumer guard, DX11
render-context draw guard, then localize-current-root guard. The live runner,
`ck3_11906.cpp`, query schema, and policy require no edits. This is necessary
because the runner exposes exactly one `--bridge-dll` slot; there is no valid
way to attach the historical guard DLL alongside the current generic-reader
DLL.

Three independent no-launch files now encode this seam:

- `research/fixtures/raiktor_generic_war_bound_guarded_retry_contract.json`
  freezes the option, macro, four-guard order, single-DLL runner boundary,
  exactly two paused queries, empty mutation list, strict child/aggregate/
  session/cache equality, and honest readiness scope. SHA-256:
  `8148D960A068480151C1767A8F76E9CC6A9E2346226C196EE840B04BAB34060B`.
- `research/verify_raiktor_generic_war_bound_guarded_retry.py` reads source,
  `CMakeCache.txt`, manifest, binaries, attempt absence and the global process
  inventory. It contains no CK3/profile/session launch path. SHA-256:
  `7CEFAEF0BDD05FBD5390B4356A16D2BACAC8ED0BACFC2F89D158A9F46AAC3762`.
- `tests/unit/test_raiktor_generic_war_bound_guarded_retry.py` covers a ready
  proposed wiring, the current hard-disabled source, stage-recorder conflict,
  query/mutation/identity drift, runner slot drift, process/attempt exclusion,
  and absence of launch primitives. SHA-256:
  `A334C729BEB836609F79CCF04318DE9564EDDBC986CE331674785BE622004F5E`.

Both normal and Python `-O` unittest modes pass all eight cases; `py_compile`
also passes. `git diff --check` is clean. A real no-launch verification against
the frozen current source and binaries correctly returns `BLOCKED`, with only
these five expected failed checks: option declaration absent, compile
definition absent, bridge macro binding absent, cache option not ON, and DLL
still equal to the unguarded frozen hash. All query/read-only/identity checks
pass, global CK3/injector inventory is empty, and the forbidden attempt path
does not exist. The report is
`Z:\ck3_mod_rewrite\artifacts\g2\2026-09-03\generic-war-bound-live-20260903T015828Z\guarded-retry-no-launch-current-source.json`,
SHA-256
`89559FD6153CA415B427C09CE43431B36CC1797E039602A6D977DF7D64E00DDC`.

After the two-file wiring is merged, a fresh current-source build must set
containment `ON` and stage recorder `OFF`; the verifier may then emit
`READY_TO_FREEZE` only if the new DLL hash differs from the unguarded hash and
every unchanged query/read-only/identity boundary still passes. It does not
authorize or perform the subsequent exclusive CK3 launch.

## Guarded build and the single consumed live attempt

[static/build GREEN] The default remains production-safe `OFF`. A fresh
Release build explicitly set containment `ON` and the stage recorder `OFF`.
The existing four-guard chain and the current generic war-bound reader were
linked into one DLL. The bridge is 2,158,592 bytes with SHA-256
`B96C3A0146BDC3DB17AE867423254B503EC21FE30EE02931830E790548EA4093`;
the injector SHA-256 is
`13CE2D7A53F179DD735DFD021D8A000ECE11F288A62DB69983FA0EDE4AE0A33A`.
The Raiktor generic reader, stage recorder, and four startup guard native
executables all pass when supplied the canonical exact-build CK3 executable.
The integration worktree's generated CTest paths alone point at an absent
ignored game payload; their initial path-only RED is not a native fixture
failure.

The dedicated guard verifier emitted `READY_TO_FREEZE` and the official live
wrapper emitted `ready-to-run`. Their reports are
`guarded-freeze-verify-only.json` (SHA-256
`D27F8E9FA8E99F4A1E5BF6ABF4F2ECB3A68BD8BD2E0061F1083AD0F29BF15F33`)
and `live-preflight-verify-only.json` (SHA-256
`C1B7BD7FED485E01AC4F1599C0A8A76010CB3214EDD35D86C9B2791EB2AAA30A`).
The exact prelaunch manifest is retained as `prelaunch-manifest.json`,
SHA-256
`6B66FC222685686C46667D51C55EB59F7EA6BE052B11E65CD7E5F2757408C1AC`.

[production launch / startup RED / zero query] The one authorized guarded
attempt launched PID `7676` and terminaled after 17.695 seconds with process
exit code `1`. It stopped before readiness: `mcp_sequence=null`, observed
query count `0/2`, `mutation_commands=[]`, time did not advance, and no
readiness was promoted. The live report SHA-256 is
`43351F9FF5FAF9C5BF3715E8F2B75FA98918DEC2567DC8B7CF1C4E19945AA80B`.
Cleanup is proved by `shutdown_ok=true`, `tree_gone=true`,
`cleanup_proven=true`, and `driver_closed=true`; final CK3 and injector counts
are zero. Checkpoint and driver-state SHA-256 values remained unchanged.

The new dump moves beyond the former unguarded particle2 fault. CK3 was based
at `0x00007FF68DA70000`; the exception at `0x00007FF69110CB58` is exactly
`ck3+0x369CB58`. It is a `C0000005` read of `0xD0`; the exception context has
`RCX=RSI=0`, `RDX=1`, and `R8=0`. The stack binds the immediate return to
`ck3+0xAF4EED`, following the direct call at `ck3+0xAF4EE8`. Static
disassembly shows the caller obtained the object in `RDI`, tested it, called
the native failure helper `0x369AF20` when null, but still executed
`mov rcx,rdi; call 0x369CB30`; the callee then immediately reads
`[rsi+0xD0]`. This reproduces the previously observed four-guard successor
fault rather than reaching the generic reader.

The complete frozen directory is
`Z:\ck3_mod_rewrite\artifacts\g2\2026-09-03\generic-war-bound-guarded-ready-20260903T034100`.
The minidump SHA-256 is
`4D430A32157AFC08ADB27B8E2126564D950BF86D67383FDE0DED0943662734F6`;
`live-terminal-result.json` has SHA-256
`DB2FCA905A566C5B32734CB04F27B6382027449E825CA2D31FF3BC8F0B798A68`.
The source manifest is now deliberately marked
`consumed-live-red-no-retry`; its post-run SHA-256 is
`4EB5DA0D47B5268EA86746C1F729355259BEF8E7326D7ECEC6734DEE552303C0`,
so the runner's prelaunch hash pin also prevents an accidental second launch.

## Next distinct startup seam

No existing source guard targets `0x369CB30`, `0x369CB58`, or the confirmed
caller `0xAF4EE8`; therefore there is no already implemented and live-proven
fifth guard to enable. The narrowest static candidate is the confirmed caller,
not the widely shared GUI-state callee: preserve the original argument setup
at `0xAF4EE0`, skip only the `0x369CB30` call when `RDI` is null, and resume at
`0xAF4EED`. Patching the callee entry would affect hundreds of unrelated GUI
callers and is not the minimum seam. This candidate remains static-only and
unimplemented pending an exact-byte/PData fixture; it is not a readiness or
launch claim, and no second live attempt was made.

Focused post-live closure remains GREEN: all six built native fixtures pass,
the guarded retry verifier passes `8/8` in both normal and optimized Python,
and the existing generic aggregation suite passes `6/6` in both modes when
invoked with its documented source/unit import roots. An earlier package-style
invocation of that aggregation module failed during collection because it
does not use package-qualified imports; no test body ran, and the corrected
discover invocation closed the harness-only RED. `py_compile` and
`git diff --check` also pass.

## Fifth caller-local guard static freeze

[static-ready / no launch] The successor fault now has a deliberately narrow
implementation. The exact-build source contract binds the owning function to
PDATA `0xAF4C90..0xAF4F22`, unwind info `0x4C5D434` with a 33-byte prologue,
the 13-byte patch window at `0xAF4EE0`, direct call at `0xAF4EE8`, target
`0x369CB30`, and continuation `0xAF4EED`. The live dump identity remains
`C0000005`, `ck3+0x369CB58`, null `RCX/RSI`, read address `0xD0`.

The new default-OFF option
`XAR_CK3_ENABLE_STARTUP_WIDGET_NULL_FLAG_CALL_GUARD_V1` compiles into the same
bridge DLL and also requires the preceding four-guard containment chain. At
the one confirmed caller only, its stub replays `xor r8d,r8d; mov dl,1; mov
rcx,rdi`; non-null `RDI` calls the original `0x369CB30`, while null `RDI`
increments a diagnostic counter, skips only that call, and resumes at
`0xAF4EED`. The shared callee is untouched. The heartbeat exposes enabled,
installed, failure, and suppressed-count fields. `ck3_11906.cpp`, the exactly
two paused terms queries, strict child/aggregate/session/cache equality, and
`mutation_commands=[]` remain unchanged.

The independent Release build used containment `ON`, widget guard `ON`, and
stage recorder `OFF`. Its bridge SHA-256 is
`A1EFF67B1D985821B812A23DF7F507AB78E290B8B33E6522EAE2136CBEE6136C`;
the injector SHA-256 is
`CF848D94C145C6D5385B52640EE8B7AB1A1B405BA50199D2183C581799352E34`.
The native executable proves both branches: null skips the target and counts
one suppression; non-null calls the original target exactly once with the
preserved `RCX`, low-byte `RDX=1`, and `R8=0`; uninstall restores the exact
13 production bytes. Admission, suspended-thread, production-override,
anchor-drift and exclusive-owner failures are also covered.

Python normal and optimized modes each pass six focused contract/verifier
tests; `py_compile` and `git diff --check` pass. The guard freeze verifier is
`READY_TO_FREEZE`, the official runner preflight is `ready-to-run`, both state
`ck3_started=false`, and the forbidden future attempt directory is absent.
The frozen no-launch directory is
`Z:\ck3_mod_rewrite\artifacts\g2\2026-09-03\generic-war-bound-widget-guarded-static-ready-20260903T075500`.
This is not a live success claim and promotes no G2 evidence. CK3 was not
started; the candidate waits for the shared exclusive launch scheduler.

The candidate manifest SHA-256 is
`0C38241A7B9736BE4520F25B1C73F6864CE7C6BECA2F62EDC1B144F1D9A63033`;
the source-contract SHA-256 is
`E4DBAA0D64F9F523DDDB193540ADC0550F3D446B03486F3452E16D9C4E67A5A2`;
the guard-freeze report SHA-256 is
`A035742A67D7EDD1FA440B7B6C3BE8C1D83BE6D5B000EB46923619B417A189D7`;
the official no-launch preflight SHA-256 is
`FCEDA3197850E978790DD49C3C15E4BA0B9D8B1C941D51427C3E8B4571733A70`;
and `artifact-index.json` SHA-256 is
`9266A1A1F55E0CFFD9768F7E8FF48BC734670819353C885D02473B8551501E7C`.

`open_kaishek` verdict: **NO-CHANGE**. Its clean fixed checkout remains
`main == origin/main == 0390b9a959fa1a59a968000ed49e827a03b8d4e4`; the current CLI JAR SHA-256 is
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
This G2 increment is confined to exact-build native code, bridge startup
wiring, native diagnostics and a no-launch wrapper. It changes no Paradox
`.txt/.gui` corpus, parser/validator/IR/runtime profile, open_kaishek API, or
fixture vocabulary, so fabricating a schema/descriptor update would not cover
any new deterministic semantic subset. Existing `certified=false` remains.

## Fifth-guard single live result

[production launch / startup RED / zero query] After P0 released the exclusive
CK3 slot, the frozen fifth-guard candidate executed exactly one actual launch,
PID `6796`. A preceding runner invocation under the wrong Python environment
failed before launch because `win32api` was absent; its harness-RED report is
retained separately and CK3/injector inventory remained empty. The actual run
used the already verified `tools/.venv` and a fresh attempt.

The process terminaled after 17.390 seconds with exit code `1`. It crossed the
previous `ck3+0x369CB58` null-call fault but stopped before MCP readiness:
`mcp_sequence=null`, queries `0/2`, `mutation_commands=[]`, no time advance,
and no readiness promotion. Cleanup is GREEN:
`shutdown_ok/tree_gone/cleanup_proven/driver_closed=true`; final CK3 and
injector inventories are empty. Frozen checkpoint and driver-state hashes are
unchanged.

The successor crash is exact and distinct. With `ck3.exe` based at
`0x00007FF68DA70000`, `C0000005` occurred at VA `0x00007FF6915D7345`, RVA
`0x3B67345`, reading address `0x8`. The instruction is
`mov rdi,[rcx+0x8]` and exception `RCX=0`. Its PDATA owner is
`0x3B67330..0x3B6735C` with unwind info `0x4CA4FD0` and a 21-byte prologue.
The stack's return at `RSP+0x28` resolves to `0x390A9F2`, immediately after the
direct call at `0x390A9ED`. The exact caller sequence loads `RCX` from `RBX`;
exception `RBX=0`. The caller owner is `0x390A700..0x390AA46`, PDATA row
`0x5A9DAB4`, unwind info `0x4ED3A9C`, 41-byte prologue. It even tests `RBX`
immediately after the failing call.

This closes the next minimum static seam without implementing it: at this one
caller, null `RBX/RCX` may skip only `call 0x3B67330` and resume at
`0x390A9F2`; healthy input must replay the original store/arguments/call.
Patching the shared callee is not justified. No sixth guard was added and no
second launch was attempted.

The terminal report SHA-256 is
`92E182644F4430896DA918DDECC6AE70E7D53FC30B6A4C367EC24F2CF59ED3AD`;
minidump SHA-256 is
`596171DF429F18A92FA3C3FDB915BFB2501FFFF0B8403C555B73B9D5C78CFF27`;
exception text SHA-256 is
`AA52848DDFEE607FF55B54DB23E39BCA4BAF6C3AB4E6A609C7A6EB7CD7EE40A8`;
typed terminal result SHA-256 is
`2822CE8F92C0A95DA28116FEA17081E30DC7695F1A175AFB20251B23F62AAE6F`;
and static diagnostic SHA-256 is
`1285E120CCDBC4B762F516D9A9C6C6DAA7E375A45E7B80EBE9FB86B63D70FDD3`.
The source manifest is deliberately consumed and no longer matches the
runner's prelaunch pin; its post-run SHA-256 is
`1F0CD3799CAA4CCA0940EBDADDB7F432905D724E2A0303F0C35C583B6C7F1876`.

## Sixth caller-local guard static freeze

[static-ready / no launch] The fifth-guard successor evidence now has a
minimal implementation at the confirmed caller only. The exact-build contract
binds CK3 `1.19.0.6` / EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
caller PDATA owner `0x390A700..0x390AA46` (row `0x5A9DAB4`, unwind
`0x4ED3A9C`, 41-byte prologue), and callee owner
`0x3B67330..0x3B6735C` (row `0x5AB60E4`, unwind `0x4CA4FD0`, 21-byte
prologue). The single 16-byte patch window begins at `0x390A9E2`; its direct
call is `0x390A9ED -> 0x3B67330`, and continuation is `0x390A9F2`.
The source contract remains anchored to the actual fifth-live C0000005 at
`0x3B67345`, null `RCX/RBX`, and read address `0x8`.

The default-OFF option `XAR_CK3_ENABLE_STARTUP_RBX_NULL_CALL_GUARD_V1`
compiles into the existing bridge and requires the preceding five-guard chain.
Its stub always replays `mov [rbp+0x6f],rbx`; for non-null `RBX` it also
replays `mov rdx,[rbp+0x77]; mov rcx,rbx` and calls the original target once.
For null `RBX`, it increments a diagnostic counter, skips only this direct
call, and resumes at `0x390A9F2`. It does not patch the shared callee. The
bridge heartbeat reports enabled, installed, failure and suppressed-count
fields, while `ck3_11906.cpp`, the two paused terms queries, strict
child/aggregate/session/cache equality and `mutation_commands=[]` are
unchanged.

The independent Release build used containment `ON`, fifth guard `ON`, sixth
guard `ON`, and stage recorder `OFF`. Bridge SHA-256 is
`A4B81851B74095A6A0AB3C09B1C751FB40B22775C79F9D9E74DB481EFA9946F1`;
injector SHA-256 is
`D715D4A859024037022262FB0F63098E4107FF75318F6DF51A846CBE004F242D`.
The native synthetic executable proves null suppression/counter/store,
healthy original-call arguments, admission, suspended-thread,
production-override, anchor-drift, exclusive-owner and uninstall semantics.
The exact-build Python suite passes `4/4` in normal and optimized modes;
`py_compile` and focused `git diff --check` pass.

The dedicated freeze verifier is `READY_TO_FREEZE`; the corrected official
runner preflight is `ready-to-run`. Both report `ck3_started=false`,
`profile_prepared=false`, zero queries/mutations/readiness promotion, empty
process inventory, and an absent future attempt directory. One earlier
official verify-only report is retained as a harness-only RED because two
command-line identity hashes were mistyped; its own fields prove that it did
not cross the profile/launch boundary. The frozen directory is
`Z:\ck3_mod_rewrite\artifacts\g2\2026-09-03\generic-war-bound-rbx-guarded-static-ready-20260903T092500`.
This is a no-launch candidate awaiting CK3 exclusive scheduling, not a live or
readiness claim.

Manifest SHA-256 is
`E3DA9CB61322730F00E9C772779D94F5060032723FEE4E0156756EA01D3BA0A5`;
source-contract SHA-256 is
`91C532F49C301F8575AEC2C7879C6C622F955B7DA60B1A7AA516F7A8FD425EF2`;
freeze-verifier report SHA-256 is
`8AE709649AAD64CEDECB3C58060687B2B827AC0828DACB2B97A354C514D98BF3`;
corrected official preflight SHA-256 is
`15F520BF506510E753D0558112CE2D4CC6E4E6BD6496DDC4332153F220F70373`.

`open_kaishek` verdict remains **NO-CHANGE**. Its clean checkout is
`main == origin/main == 0390b9a959fa1a59a968000ed49e827a03b8d4e4`, and
the CLI JAR SHA-256 remains
`421F49C93B21DBE5D96BFD81FFBFE422EB098B2170ECC498A415D4125490F2CB`.
This increment changes only exact-build native startup containment, bridge
wiring and no-launch evidence; no adapter/API/profile/fixture vocabulary or
Paradox `.txt/.gui` corpus changed, so `certified=false` remains honest.

## Sixth-guard single live result and VFS successor

[production launch / startup RED / zero query] After the exclusive slot was
released, the frozen sixth-guard candidate performed its one authorized actual
launch, PID `46068`. The launch-entry verification was GREEN. CK3 exited with
code `1` after a 14.392-second managed session (18.692 seconds end to end),
before bridge/MCP readiness. Therefore `mcp_sequence=null`, queries are `0/2`,
`mutation_commands=[]`, time did not advance, and no readiness was promoted.
The source checkpoint and driver state remain byte-identical. Physical cleanup
is GREEN: `shutdown_ok/tree_gone/cleanup_proven/driver_closed=true`; final CK3
and injector inventories are empty. This launch is consumed and will not be
retried.

The sixth guard crossed the prior `0x3B67345` null-object fault. The distinct
successor is C0000005 at VA `0x00007FF6916533A9`, with CK3 based at
`0x00007FF68DA70000`, hence RVA `0x3BE33A9`. The exact instruction is
`cmp byte ptr [rcx+8],0`. Exception `RCX=RBX=0x206E65704F534656`, whose
little-endian bytes spell `VFSOpen `; the exception record reports a read of
`0xFFFFFFFFFFFFFFFF`. The callee PDATA owner is
`0x3BE3360..0x3BE33F6`, row `0x5ABB55C`, unwind `0x4C78000`, 9-byte
prologue. The return at `RSP+0x38` is `0x3B55D8B`, after the direct call at
`0x3B55D86`; that caller is owned by `0x3B55D50..0x3B55DB7`, row
`0x5AB534C`, unwind `0x4C38E20`, 6-byte prologue.

Dump memory closes the bad-word source. The caller's operation object at
`0x000002ADD35C06A0` has the expected VFS-operation vtable at RVA `0x4556930`.
Its variant at `+0x38` is tagged `1` at `+0x58` and contains the legitimate
error string `VFSOpen Error:  not found`, while the polling state at `+0x0C`
is still `0`. The poll method therefore follows the pending-object path,
loads the error string's first eight bytes as an object pointer, and faults.
The upstream map-loader object contains an empty base path at `+0x18` and
`/default.map` at `+0x38`; construction flows through `0x3B55A40`, variant
move through `0x3B56830`, then poll through `0x3B55D50`.

This is not a simple missing-installation or sandbox-denial result: physical
`game/map_data/default.map` exists with SHA-256
`BD13123017E53EA9A1CB7E4D8FE3279DBE02B4415BA4CAFEE1730CC4D91CE2B1`,
and the runner used CK3's normal `binaries` working directory. There is no
static data-flow edge from the sixth guard's remote GUI null-call seam into
this VFS object. The most specific current classification is an asynchronous
VFS error-state/tag mismatch during cold map startup. An indirect timing
effect from the containment chain cannot be proved or excluded because an
unguarded run cannot reach this later frame. Accordingly no seventh guard is
justified. The minimum next seam is read-only observation of constructor
`0x3B55A40` input path, variant move `0x3B56830` tag/payload, and poll
`0x3B55D50` state/tag; neither the poll nor global callee `0x3BE3360` should be
skipped from this evidence.

The actual report SHA-256 is
`EB5ECAB0CC503EB1DE8927A8B6B11FD0F728676564F860C9A7A0172A9984D08C`;
live-entry verification SHA-256 is
`2B6D9FB53B5759A4B7D51EC289BFCEF71E9F54D993BEDA9E723E9486BFDFEE66`;
typed terminal SHA-256 is
`81196AFB476B42FE7FE6B4F65779C1E772FC0C89793B90B4E96950F84A0E02CC`;
minidump SHA-256 is
`F08D7EC24540D70005CB2D222D8EC4F8A4B65F2A5EACA8A47544E0CCC4DC8908`;
exception text SHA-256 is
`9DB3D6B9C5CC4D4707FFD0CCDDD38D275BE674F4950BE691C2C0293F01D6732E`;
and the enriched static diagnostic SHA-256 is
`9AE56F6BCC5860DD5B61DB1019384D3969CC64BCD0E30A7F78BA7803FDEC3202`.
The source manifest is now `consumed-live-red-no-retry`; its post-live SHA-256
is `F8898D8EAC0EA11DB02B8EBE39A6D35A6FED480F4EDCFA2B434FED3699EF3A6A`,
so its runner pin also prevents another launch.

## Cold-map VFS three-point observer (static only, no launch)

The successor work is deliberately an observer, not a seventh containment
guard. `XAR_CK3_ENABLE_COLD_MAP_VFS_OBSERVER_V1` is default-OFF and installs
three exact-build detours as one all-or-none unit while the primary thread is
suspended:

- `0x3B55A40` records the constructor's RDX path descriptor (`data`, `length`,
  and flag) before replaying the exact 15-byte prologue;
- `0x3B55ADE` first replays the original call to variant move `0x3B56830`, then
  records destination `R14+0x38` payload/length/capacity/tag before replaying
  the original `cmp`;
- `0x3B55D50` records operation state `+0x0C/+0x0D` and the variant at `+0x38`
  (tag `+0x58`) before replaying the exact 15-byte prologue and comparison.

Each thunk preserves flags and volatile GPRs around an allocation-free,
lock-free, syscall-free atomic snapshot. It neither selects a branch nor
changes a return value, object byte, or poll state. The global callee
`0x3BE3360` remains untouched. Exact anchors and PDATA ownership are frozen in
`native_bridge/research/fixtures/cold_map_vfs_observer_v1_source_contract.json`;
the synthetic native test proves all-three install/restore and the three
snapshot layouts, while the Python contract test binds the anchors back to the
CK3 `1.19.0.6` executable SHA.

This is `static-ready-no-launch`, not live evidence and not a fix. Its intended
next use is a separately authorized, same-candidate A/B capture behind the
already frozen six-guard chain: one `Default` desktop run versus one
`CodexSandboxDesktop` run, with checkpoint/profile and observer binary held
constant. Comparing the constructor path, post-move variant and poll state can
distinguish a desktop-initialization difference from a producer/poller
publication race. No CK3 process was started while implementing or validating
this observer.

## Frozen two-query runner: normal-desktop execution audit

The original frozen `generic_war_bound_current` package remains mechanically
executable from a normal Windows desktop without any runner rewrite. A fresh
2026-09-03 `--verify-only` pass rechecked the checkpoint, driver state, exact
game executable, bridge DLL/injector, manifest, runner and every pinned
production source. It returned `ready-to-run`, did not prepare a profile and
did not start CK3. The frozen future attempt directory is still absent.

The desktop boundary is inherited, not selected: the common launcher creates
`win32process.STARTUPINFO()` without assigning `lpDesktop`, then calls
`CreateProcess` with `CREATE_SUSPENDED`. Consequently, calling the unchanged
runner from Windows' `Default` desktop launches on that same normal desktop;
calling it from a Codex sandbox desktop keeps it in that sandbox. The added
no-launch verifier binds this source fact to the fresh frozen-input report,
requires an empty CK3/injector inventory, and reports the current desktop name.
During this audit it correctly returned
`candidate-ready-current-desktop-ineligible` because the caller was
`CodexSandboxDesktop-*`, while
`normal_desktop_direct_execution_supported=true` and the process inventory was
empty.

No frozen runner, manifest, checkpoint, binary or production bridge source was
changed. The runner still permits exactly two
`query-war-termination-terms-v1-50331699` commands, checks child/aggregate/
session/cache identity, and requires `mutation_commands=[]`; source-specific,
pre-soldier, proven-loss, action and automatic gates remain false. This audit
is neither a new live attempt nor authorization to repeat the old live. Its
artifacts are under
`artifacts/g2/2026-09-03/generic-war-bound-normal-desktop-audit-20260903T041200/`.

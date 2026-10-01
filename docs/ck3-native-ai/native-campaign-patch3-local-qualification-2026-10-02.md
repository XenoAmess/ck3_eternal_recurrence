# Ordinary campaign consumer and local CK3 1.20.0.3 artifacts

This package makes the existing ordinary campaign tools available for a new
project run on CK3 **1.20.0.3 / Steam build 25652598**, EXE SHA-256
`94b55397abb687a3dcd436805a5d885e6be90fa6c693feb44a9e3bbeeade02a6`.
The authoritative generic owner is this repository; the calling suite supplies
its mod/load-order/run/profile data and remains the sole live operator. No
desktop, Steam, CK3 launch, live attachment or input occurred in this package.

## Consumer repair and ownership

The migrated native reader already supported the exact .3 identity header and
reviewed .2 layout. `ck3_clock_pause_mcp.py` still rejected every profile version
except .2. Commit `6a0130d1e4f09b1224122e6603746246e8549acd` fixes that concrete
consumer blocker: allow the two supported patches and require the returned
clock source-contract version to match the frozen profile. Mixed patches and
unknown versions reject before input. The seven-field schema, fixed scan-code
SPACE, guards, one-shot latch and actual bounded paused readback stay unchanged.
[The controller contract](clock-pause-mcp.md) includes the added fixture scope.

Offline qualification: 58 controller/policy/clock tests, 25 bootstrap/campaign
projection tests and 4 real-provider delayed-postcondition tests passed.
Fixtures cover actual .3 memory-layout replay through the controller for zero
input when paused and one input with delayed true readback when running. These
87 distinct Python tests are not live gameplay or a century result.

## Frozen local production build

The remotely documented .3 candidate under `Z:/ck3_mod_rewrite` was absent on
this machine. Old C2/C4 .2 binaries were not reused. Committed native source
`6a0130d1e4f09b1224122e6603746246e8549acd` was exported to `C:/cb123`, with
2,755 native files and no working-tree overlay. Its complete source-tree digest
is `208c9ee65c12bc8a076c577514766b4610aa454da7acd495849666156e0c6f4f`.
The native source-binding JSON SHA-256 is
`db40af2add92e876f2dd61360d1f830ba4d16b08a9e247ee7f9b0f8f4e9ac9d0`.

Fresh Ninja/MSVC Release build `C:/cn123` compiled the default production
bridge/injector and the required existing fixture targets in 401 steps with
two compiler jobs. Private options remained at their default OFF settings.
Ninja recorded both required `ck3_11906.hpp` dependency edges, and the frozen
production source fingerprint was unchanged after the build. A first developer
environment command failed before configure; the ignored orchestration was
corrected to use a batch file, without changing frozen source bytes.

| Actual artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `C:/cn123/xar_ck3_bridge.dll` | 4,073,472 | `6cd8a0a3fcb91a426d043adbc311c04bf540fcd3321659b45f74951c4a8fee2d` |
| `C:/cn123/xar_ck3_bridge_injector.exe` | 39,936 | `00fe3853594ada9eeab9aa235f78188b509bc7da8f74ef497f423cc6fa8b9a03` |

The production DLL contains the exact `.3` version, descriptor
`ck3-1.20.0.3-msvc-x64` and EXE SHA strings. Nine scoped native CTests passed:
adapter, commands, context, event window context, events, semantic adapter,
thread runtime, explicit `.3 semantic worker`, and adapter registry. The
ordinary command fixtures exercise the existing pause/resume/speed/save queue
and event selection contracts; the explicit .3 worker and registry qualify
new-version admission/identity over the reviewed reused layout. Old-named
fixtures alone are not evidence of .3 admission.

The reviewer separately ran the existing exact ABI verifier against the
installed .3 EXE: exit 0, `GREEN: exact .3 offline ABI verification; live
validation=False` (tool receipt `88f686`; no separate output JSON). The permanent
ABI manifest and [migration evidence](crozier-1.20.0.3-native-migration.md) are
reused. `open_kaishek` is not applicable to Windows PE/thread/byte ABI and Python
transport; no Clausewitz script semantics changed here.

The ignored evidence is under the main repository's `_runtime/`:
`native-12003-source-bindings.json`, `native-12003-scoped-qualification.json`,
the configure/build/ordinary CTest/dependency logs, separate registry log and
receipt, `native-12003-local-input-qualification.json`, and
`native-12003-final-qualification.json`. The final receipt SHA-256 is
`0cae844d68e08db67fb41dfbe0fc8f0fe947801f53dd0d8412902c00334a4ff5`;
the scoped build receipt SHA-256 is
`fef52c501c741553c9cd9b0f48f84146f699d27a189929d93d86d15fdbe364b6`.

This is a scoped production/ordinary-fixture result. A full all-target build
and all CTests were not executed. Historical C4 full-build RED and unrelated
private fixture limitations remain recorded. The other machine's actual .3
one-day/save result retains its original source/artifact/run identity and does
not count toward the calling project's new three-mod century test.

## New persistent client/profile consumption

Use the existing [profile bootstrap](frozen-native-profile-bootstrap-2026-10-01.md)
with `game_version="1.20.0.3"` and the actual DLL/injector paths/hashes above.
Its exact nine fields remain `schema_version`, `guard_profile`,
`guard_profile_sha256`, `userdir`, `state_directory`, `evidence_directory`,
`game_version`, `dll`, and `injector`. State/evidence directories belong to the
new isolated run. The project run name is configuration; bootstrap does not
call the canonical mod-key allocator, so no allocator expansion is needed.

The root must build a fresh current guard: actual PID/create time/EXE/build,
HWND/foreground/geometry/userdir, current legitimate Steam UI host and core
process continuity, fresh reviewed offline evidence, and its exclusive lease.
Attach requires initialized independent `paused=true`, then matching exact
hello/map/date/paused readback. One exclusive claim consumes attachment; failed
attachment or an ended native transport is not authorization to inject again.

The optional independent pause provider uses its own seven-field profile,
session, evidence and profile hash. The current installed shortcut is 29,312
bytes, SHA-256
`d2aa3a6f3a9de9729d778e240920e5a15f724d1f5b0adee5861ef6831797cd66`;
it must still pass the actual source check when the server loads. The clock's
.3 identity header SHA-256 is
`ef7a8a1854e6c8c129fd66bf5397bdf453a1f0d46ff855b57ec3c5d70b1f1c6a`,
and reader SHA-256 is
`ce96b681e035d6378b685f61db448b101251d26262a475c029684995b7905ff3`.

Keep the official client alive through a persistent queue and use `cache=None`.
Consume `await native_campaign_autoplay.run(native_client, config,
pause_provider=controller_client)`; the optional provider's real target identity
must match the native bridge. Event choices, resume, speed and checkpoint saves
remain existing strict native tools. Independent save date/readback establishes
the new baseline and progress; fixtures do not establish calendar milestones.
Do not invent an XAR game rule, use observer/date jumps or add a suite copy of
generic control code. The root must verify actual first attach, native event
choices, gameplay saves and continued natural simulation in the new run.

# C4 ordinary-player scope and preserved full-build RED

The production bridge and fixture graph are owned by this authoritative
repository. The frozen C4 input is main commit
`710cdef6544ae9161246f223e28a4835cbe936f9` with a fixture-only CMake overlay.
All 2,743 tracked native-bridge files, including research inputs, are bound by
`_runtime/native-build-c4-source-bindings-20261001.json`; tree SHA-256 is
`fe05fb1c378a63339a9bb11b0635ef9dc7e17ad6f51287d8dda154485e02c9fb`.
The official `native_bridge/tools/build_fresh.py` used unused directory
`C:\cn120d`, Release defaults, 12 build jobs, and the actual CK3 1.20.0.2
executable SHA-256
`ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d`.
No private feature was enabled or fixture disabled.

The complete default build is **RED**, preserved in
`_runtime/native-build-core-c4-20261001.log`. It links the production artifacts
but fails in private feast planner-open/start fixtures owing to missing pure
helper linkage. The all-target build and all-CTest qualification did not pass;
this receipt must not be called a complete fresh-build GREEN. C1, C2, C3 and
the first C4 scoped attempt remain preserved separately.

The following immutable artifact copies were made before scoped fixture linkage:

| Artifact | Absolute path | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Bridge | `C:\workspace\ck3_eternal_recurrence\_runtime\native-c4-artifacts\xar_ck3_bridge.dll` | 4,226,048 | `728bf6f86d62db7aecfa734e54879bede2f6cd70b386e2cef051794c70b69de4` |
| Injector | `C:\workspace\ck3_eternal_recurrence\_runtime\native-c4-artifacts\xar_ck3_bridge_injector.exe` | 39,936 | `c8c0d5bd5fc227caa9c59b1a14e85a1aead92291900cb63a520d5f46550be6ff` |

The existing C4 frozen source/runtime library then built and ran seven specific
ordinary-player contract fixtures. This did not edit the frozen source or
rebuild/change the production artifacts. Their hashes were checked again after
the fixture build and all 2,743 native source hashes were reread unchanged.

| Fixture | Qualified offline scope |
| --- | --- |
| `xar_ck3_12002_adapter_test` | Selected 1.20 descriptor, exact build denial, core/map-ready/clock/player snapshots and synthetic adapter callbacks. |
| `xar_ck3_12002_commands_test` | Native pause/resume/speed 1–5/save payloads, submitted/already-state handling and missing-map/build denial. |
| `xar_ck3_12002_events_test` | Active event identity and authored option command layout/dispatch. |
| `xar_ck3_12002_event_window_context_test` | Exact event-window context contract and rejected/incomplete inputs. |
| `xar_ck3_12002_context_test` | Current native context bindings. |
| `xar_ck3_12002_semantic_adapter_test` | Existing semantic adapter contract. |
| `xar_ck3_12002_thread_runtime_test` | Existing 1.20 native runtime/thread contract. |

All seven passed. The bound receipt is
`_runtime/native-build-c4-ordinary-qualified-02-20261001.json`, SHA-256
`6856446abb960453ad86250dcece70e4d82a791c3175658429a527530ec1720e`.
It includes the original RED receipt/hash, full source binding/hash, unchanged
production artifacts, runtime library hash, each fixture EXE hash and scoped log
hash. Build log: `_runtime/native-c4-ordinary-abi-build-03.log`; test log:
`_runtime/native-c4-ordinary-contract-fixtures-02.log`.

`bridge.cpp::HelloFrame` emits the descriptor of the actually selected adapter,
including version, executable SHA and ready/unsupported status. These static
and fixture contracts qualify a bounded first live attachment with mandatory
readback; they do not establish a live hello or gameplay result on their own.
The exclusive desktop owner must independently verify the new isolated run's
paused loaded HUD and use the frozen profile consumer. Its additional paused
read-only clock before attach, exact target/Steam/lease/userdir/crash guards,
contained injector proof and first map-ready matching raw-date snapshot are
mandatory. The persistent server fixes `episode_projection="native_campaign"`;
this is an internal constructor mode, not a caller/profile identity override.
The seven narrow MCP tools accept no arbitrary process, command, key, coordinate,
observer, date jump, seed reset or AI policy. They retain their native/save-file
postconditions. A claimed attach is never replayed after RED or server restart.

Current Python consumer validation is 35 clock/profile/ordinary-player/campaign
projection/semantic tests, plus five existing relevant legacy-driver regressions.
No live attachment, desktop input or game operation was performed by this work
package. Live acceptance, normal succession across an actual death, periodic
save metadata and a full century remain the consuming project's evidence scope.
Private feast fixtures, old-ABI executable contracts and the complete native
CTest set are outside this scoped PASS and retain the full-build RED limitation.

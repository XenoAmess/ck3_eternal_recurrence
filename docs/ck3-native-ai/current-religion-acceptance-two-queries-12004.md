# Current religion evidence for CK3 1.20.0.4

The More Tenets Slots(XA) October 2026 repair needs evidence after applying a
draft and after a cold reload. The existing draft queries cannot supply this:
they observe the currently open editor. Enable the two already implemented
read-only queries independently in a successor runtime:

| MCP tool | Existing native compile definition | Evidence |
| --- | --- | --- |
| `ck3_query_player_religion_doctrines_v1` | `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINES_PRIVATE_QUERY_V1` | Current rite effective doctrine rows, their groups, and separate faith-main rows |
| `ck3_query_player_religion_tenets_v1` | `XAR_CK3_ENABLE_G2_PLAYER_RELIGION_TENETS_PRIVATE_QUERY_V1` | Current rite core tenets, separate faith-main/personal collections, and effective native tenet states |

The exact supported executable remains 1.20.0.4,
SHA256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The provider and its exact-build bindings already existed. This package changes
build selection, public case admission, and offline tests; it does not change
production religion readers or add write/AI interfaces.

## Interpret the collections separately

`current_rite.core_tenets` is the current core membership list.
`effective_tenet_states` also contains main-rite known states and personal
tenets, evaluated against the current rite. A replaced core tenet can therefore
remain in that latter list with a known/permitted state. Its presence alone
cannot prove that replacement failed. State values 0 through 4 mean unknown,
known, prohibited, permitted, and core, respectively; preserve the actual core
collection as an independent observation.

For ordinary doctrines, inspect `current_rite.rows`, compare each
`doctrine_key` and `group_key`, and count the selected keys for the specific
edited group. Do not substitute the faith-main list for the current rite.
Both queries require the admitted paused player frame and preserve the complete
native reference IDs and owner-frame metadata.

The acceptance case should call the two tools with `expected_revision` only.
The existing optional tenet target/catalogue arguments remain at their defaults;
the new fixture verifies those optional native callbacks are not invoked.

## Explicit public admission

The shared case inventory and host parser now accept either tool through
`--case-read-only-mcp-tool`. Each corresponding driver permission is set only
when that exact tool is declared. Neither tool is enabled by default, nor does
declaring one grant the other. Existing SDK discovery and service permission
checks remain in force.

## Successor production and evidence

`tools/build_native_flag_successor.py` accepts an optional
`baseline_successor_report`. It validates the same original Ninja baseline and
source root, successful predecessor archive/link results, and exact baseline,
source, and object pins. It borrows predecessor objects read-only, carries its
explicit flags forward, and recompiles only the new flag closure and explicitly
added sources. Requested flags must still be disabled in the original cache and
must not already be enabled by the predecessor. A predecessor fixture failure
is retained as `original_status`; a successful link never grants fixture or
live qualification.

The actual October build inherited the four draft flags, added these two flags,
compiled five translation units and reused 738 objects. It retained the earlier
context/personal queries. The resulting DLL has 13,214,208 bytes and SHA256
`2229cdb1fd382460f059c32f1b3f139cf7503aeff42399cc9b7f4bc88c129c19`.
The exact compile commands and all input/output pins are in the external
`mts-religion-current-native-20261015-001/build-002/RESULT.actual.json`.
The first configuration attempt requested baseline-present sources; it was
rejected before production compilation and remains preserved as `build-001`.

The narrow `.4` fixture reuses the established synthetic memory/callbacks via
`XAR_CURRENT_RELIGION_ACCEPTANCE_FIXTURE_ONLY`. That test macro excludes the
broader fixture main and its unused Doctrine-knowledge executor registration.
The original broader fixture is unchanged when the macro is absent. The narrow
fixture executes exactly the two production owner mailboxes, adapter, core
reader, serializers and complete command-result renderer. It checks a known
tenet remains outside current core membership and emits the two unmodified
business wires. Two preliminary fixture links failed due to the broader
fixture's unused knowledge references; both attempts are retained separately.

`test_religion_12004_current_acceptance.py` consumes the newly emitted files via
`XAR_RELIGION_12004_CURRENT_NATIVE_WIRE_DIR`, then exercises the production
driver, protocol ingest, registration and official MCP SDK. It checks exact
business-body equality, complete build identity, independent default-off
permissions, and one native request per query. It skips unless a freshly built
wire directory is explicitly supplied.

Actual final qualification is in the external
`mts-religion-current-native-20261015-001/QUALIFICATION-004.actual.json`:
the two native cases passed 41 checks; both emitted whole wires passed the
registered production driver/protocol/MCP SDK test. The focused shared-entry,
successor and independent-opt-in suite passed 29 tests, and the two existing
Doctrine/Tenet SDK regression tests passed. No game process was contacted.

Defender registration is independently **RED**. A valid exact-EXE manifest was
submitted once with an administrator token; WMI `Add` failed with COM general
failure `-2147217407`, and fresh readback did not contain the requested path.
The failed actual receipt and original settings are preserved. The test EXE
then ran normally under unchanged protection; its original `Popen.wait` returned
0. No Add retry, global exclusion, opt-in change, or permanent-exclusion claim
was made. An earlier attempt also preserved the provenance rejection of CMake's
`-c` form; the actual final fixture compiled with equivalent MSVC `/c`, and the
generic producer now normalizes this spelling for future exact-EXE manifests.

These are offline build/fixture checks only. Actual apply, cold-load persistence,
GUI, notification behavior and product release gates remain separate. The
shared `20261015-native-religion-003` runtime owns the one selected DLL and host;
no parallel product-specific runtime is selected.

## Ownership and provenance

The producer, host admission and native/SDK fixtures are reusable framework
capabilities. Product scripts, hidden padding keys and acceptance business
assertions remain in the independent product repository. Origin and follow-up:
`ck3_mod_more_tenant_slots/docs/bugfix-plan-2026-10-15.md`,
`docs/bugfix-report-2026-10-15.md`, and
`docs/native-runtime-progress-2026-10-15.md` in that product repository.
The evidence does not certify POD or another mod.

# Four existing religion queries in the common 1.20.0.4 runtime

The More Tenets Slots investigation required the already implemented draft
readers. Native058 had their four feature flags disabled. This package reuses
the existing exact-build providers, rather than adding another religion API.
Product mechanisms, fixtures and business acceptance remain in
`ck3_mod_more_tenant_slots`; the shared runtime, opt-in routing and reusable
collection-scale fixture belong here.

The target is CK3 **1.20.0.4**, executable SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The user explicitly selected this version and requested native-runtime reuse.
This package does not authorize general religion AI work.

| MCP query | Actual existing observation |
| --- | --- |
| `ck3_query_player_religion_reform_context_v1` | Current religion and open draft; native cost, final create/edit gates, current popup and Doctrine selection |
| `ck3_query_player_religion_draft_groups_v1` | Ordered selected-slot keys/groups, native category slot and materialized caches |
| `ck3_query_player_religion_draft_doctrine_choices_v1` | Each actual selected slot's source definitions, duplicate exclusion and native final selection gates |
| `ck3_query_player_religion_draft_tenet_choices_v1` | Actual Tenet slots, native default placeholders and source/final gates |

All four collections use the existing **8192-record** bound. They do not assume
three Tenets or truncate at 32/64/128 records. The added fixture mode
`--expanded-slots` exercises 128 selected Doctrine records, 128 popup records
and 100 Tenet slots, preserving the final ordinal and native blank placeholder.
This is a generic synthetic-memory qualification, not proof that a particular
mod's loaded draft is correct.

## Native reuse and local selection

The preserved Native058 DLL is `C:/cbr3/xar_ck3_bridge.dll`, SHA-256
`4bb79c021c95f66e786eaa8c539a4d0631ab476a1e881800ab8fb980c516bcb9`.
Its actual native source is **C:/csr12**, while **C:/csr19** is the later frozen
Python/host source. Neither is modified.

The new shared mapping is
`C:/workspace/ck3-common-runtime/20261015-native-religion-001/runtime.local.json`.
There is no discovered automatic global/current pointer: callers select this
single common manifest through their machine mapping. This does not deploy it
to another machine. The historical R90 mapping remains readable.

The successor enables only the four existing
`XAR_CK3_ENABLE_G2_PLAYER_RELIGION_{REFORM_CONTEXT,DRAFT_GROUPS,DRAFT_DOCTRINE_CHOICES,DRAFT_TENET_CHOICES}_PRIVATE_QUERY_V1`
flags. Actual production compilation covers seven units: Bridge, the nonwar
mailbox/router, and the four existing query mailboxes. The archive and DLL reuse
**734** unchanged production objects. Protocol and Injector remain unchanged.
No CMake reconfiguration, whole-platform rebuild or old full test matrix is
required.

[`tools/build_native_flag_successor.py`](../../tools/build_native_flag_successor.py)
reads a caller-supplied JSON configuration with explicit baseline/output/source
paths, runtime/bridge targets, existing disabled definitions, newly enabled
sources, optional fixture sources and jobs. It obtains original compiler
commands from Ninja, scans each production unit's local include closure for
the enabled definitions, writes changed objects into a separate output,
then creates a new archive and DLL from changed and borrowed original objects.
`fixture_whole_bridge: true` uses the established whole-Bridge fixture closure.
This tool handles this project's existing MSVC/Ninja bridge layout; it does
not infer a new source migration or qualify live native getters.
Fixture EXEs use the existing successful-command Defender manifest/receipt
helper before execution when the machine's existing Git opt-in is enabled.
The original local build has that opt-in disabled; no new exclusion setting
or verified registration is inferred from successful fixture execution.

The first runtime-only fixture link produced a real unresolved
`GameAdapter::supports_snapshot` error. Adding only GameAdapter's object exposed
its broader Bridge dependencies. Both failures are retained. The final fixtures
use the already established whole-Bridge object closure; no production stub or
replacement getter was introduced, and the seven production units were not
recompiled for this fixture repair.

The public acceptance allowlist and host parser/driver permissions now admit
these four read-only tools **only when explicitly declared by the case**. The
R90 effective host's endpoint fixes are retained. Its successor normal-exit
profile uses the new native paths and pins, and records the actual selected
shared manifest; an outer mapping change alone would have left the old native
guard binding in place.

## Evidence and boundary

The external work directory is
`C:/workspace/ck3-common-runtime/mts-religion-native-20261015-001/`.
`build-001/RESULT.actual.json` preserves the seven production commands and the
first fixture-link RED. `QUALIFICATION.actual.json` records the repaired native
fixtures, expanded-slot fixture and unchanged native packets through registered
MCP/Driver/protocol. The public acceptance finite opt-in regression is run
directly from `tools/test_ck3_mod_acceptance.py`.

No CK3, Steam, desktop, screenshot or screen lease is used by this package.
`open_kaishek` prevalidation is not applicable to these C++ pointer-layout and
owner-mailbox fixtures: they execute no CK3 script semantics. The product's
script prevalidation and live acceptance remain separate.
Compile/link and synthetic native/MCP qualification do not grant live or
product-business PASS. Existing generic in-game navigation covers Character,
Army, Combat and Knights, and does not currently expose Rite draft opening or
selection. The narrow future action entrypoints are vanilla
`RiteCreationWindow.GetDoctrineCategoryWindow.ShowWindow/ShowWindowSortList`,
`RiteCreationWindow.SelectDoctrine` and `SelectTenet`; the product investigation
can retain an official-UI fallback and verify its result with these readers.

The outputs fit the Root-owned 2 GiB task reservation. The new objects/archive,
fixture outputs and immutable-source links are active inputs for this
investigation; review protection by **2026-10-22**, then apply the shared storage
policy. Historical source and binary are preserved for the current comparison,
not declared permanently exempt from retention review.

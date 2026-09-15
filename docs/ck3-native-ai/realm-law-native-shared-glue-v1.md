# CK3 1.19.0.6 realm-law native shared/private glue v1

Status: `static-ready private operation-table glue; shared registration and
paused live receipt pending`.

This glue is fixed to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
and LAW6 mutation ABI manifest
`C9D4D2347646A3A4A95C1F6D735F9582D57DBD55729BFF9337136B0808F5D16B`.
It connects the LAW5 native binder to LAW6's reviewed `CAddLawCommand`
construction, final validator and clone-and-queue boundary. It adds no public
schema or MCP capability.

## Preparation boundary

The caller supplies the already reviewed LAW3/LAW5 source operation table, a
transient target resolver and an RVA-addressed LAW6 image reader. Preparation
requires the source table to be complete except for `submit_enact`; any upstream
submit callback is rejected so there is only one mutation owner. It then:

1. samples the source runtime proof twice and requires equal exact-build,
   module-base, source-manifest, signature-generation, connection-generation,
   application-main-thread, paused and proof-epoch values;
2. verifies the complete LAW6 mutation ABI twice against the admitted module
   base;
3. pins the source generations and exports a complete LAW5 operation table whose
   proof manifest is the LAW6 manifest.

The expensive exact-image proof is confined to preparation. Steady-state
callbacks still recheck the pinned source runtime proof; they do not repeatedly
hash the executable. A new source generation, connection, module, thread or
source manifest fails closed.

## Immediate submit transaction

`submit_enact` accepts only LAW4's pointer-free submission. On the application
main thread it reads the pinned proof, resolves fresh actor/group/law leases,
reads the proof again, resolves all leases a second time and reads the proof a
third time. Both target samples must have equal round-tripped identities,
generations, keys, connection generation and proof epoch.

Only then does the glue construct the exact `0x30` byte `CAddLawCommand`:

| Offset | Value |
| --- | --- |
| `+0x00` | primary vtable, module `+0x4323730` |
| `+0x18` | secondary vtable, module `+0x4323700` |
| `+0x20` | full generation-bearing played character ID |
| `+0x28` | freshly resolved target `CLaw*` |

It calls command validator adapter `0x25E2690`, rechecks the pinned proof, then
calls `0x973E00` with manager module `+0x57621F0` and flags `0x0E`. The stack
command and all target leases expire when the call returns; only the engine's
owned clone may remain. Queue acceptance maps to LAW5 `submitted`, which still
produces only `submitted_verification_pending`. Effective law, charged resources
and succession shape require a later fresh paused LAW5 receipt.

The native function addresses are used only when `offline_fixture=false`.
Focused tests use explicitly labelled validator/queue callbacks to inspect the
command bytes without executing CK3 code. Production preparation rejects those
callbacks.

## Verification and remaining work

The standalone C++20 fixture is compiled with MSVC `/W4 /WX` in normal and
`/O2` modes and receives the exact CK3 executable path. It covers the exact ABI
and LAW5 binding path, exact command layout and single queue call, mutation ABI
drift, upstream submit override, disabled mutation, target/proof drift, final
legality denial and queue rejection.

LAW8 now compiles this glue into the shared DLL and registers its private fixed
application-main executor as documented in
`realm-law-application-main-v1.md`. A real eligible paused submission and a
later effective-law/resource/succession receipt remain pending. Until that
artifact exists, this component is neither `fixture-live` nor
`production-live primitive`.

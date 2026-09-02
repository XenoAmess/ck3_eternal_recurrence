# Phase-two loader callback probe: bounded NO-GO (2026-09-02)

This note records the result of one bounded capability inventory for the
phase-two loader callback. It is an evidence boundary, not a claim that a
debugger or instrumentation tool can never exist outside this repository.

## Decision

**NO-GO for a callback identity probe or loader detour in the current
environment.** The repository has no reusable debugger attach path, hardware
breakpoint capture path, or loader-specific callback recorder that is already
bound to the exact build and supported by the acceptance harness. The existing
loader log parser exposes node names and timings only; it cannot identify the
callback vptr, callback completion, or the changed source file. Starting a
new CK3 attempt without that missing observation would reproduce the same
loader timeout rather than close the blocker.

This is a bounded infrastructure decision. It does **not** assert that the
Windows host has no debugger installed, and it does not prohibit a future,
explicitly provisioned debugger/instrumentation session.

## Frozen evidence

- Exact build: CK3 `1.19.0.6`, `ck3.exe` SHA-256
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
- The static callback slice is retained at
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-callback-native-slice-20260902.json`
  (SHA-256
  `DB578C67A98FC131B829B718C356E11E31DE84CCC649E81D79EB9EFE5C25452A`).
  It closes the loader loop, prologue/PDATA, `RCX -> node+0x88 -> vptr ->
  slot 2` call shape, eight direct callers, and same-function continuation.
  It explicitly leaves runtime vptr identity, callback return/lifetime,
  thread identity, quiescence, source attribution, and readiness unknown.
  See [the static slice note](phase2-loader-callback-static-slice-2026-09-02.md)
  and its machine-readable contract
  `ck3_autonomous_player/native_bridge/research/phase2_loader_callback_static_slice_v1_abi.json`.
- The one current exact-build telemetry run remains
  `RED/loader_stage_timeout` with
  `reason_code=database_callback_stall`. Its retained report is
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\phase2-live-recheck-20260902\artifacts-a89282d-f20-loader\runner-report.json`
  (SHA-256
  `187E1A438F0DCDE838BAC1AF02AAB878393BBAF999D704E3C9F2D843627FBBA9`).
  The run saw only two completed database callbacks (`CGameConceptTypeDatabase`
  and `CJominiLoadScreenDatabase`), no `PostInit`, and
  `database_callback_quiet_seconds=286.430`; it never entered event/native
  readiness. Cleanup was green and no action or save write occurred.
- The paired `open_kaishek` preflight was performed before that run and is
  retained beside the report as
  `open_kaishek-preflight.json` (SHA-256
  `E18ECD37F2EC8AAA56BCE5CE271F968CB58CEF8ACACEB710E14D5001A272B8DC`).
  This preserves the required MCP-first ordering; its known schema-only
  validator RED is not a CK3 runtime result.

## Why existing hooks do not close this gap

The bridge injector's `CreateRemoteThread(LoadLibraryW)` path loads the DLL;
it is not a debugger, hardware-breakpoint facility, or loader callback
observer. Existing exact-build detours are scoped to other gameplay anchors
and have their own paused-quiescence, trampoline, and rollback contracts. The
phase-two callback contract remains `production_installed=false` and
`detour=false`; reusing a gameplay detour or widening the public wire would
be an unsupported ABI change. The existing feasibility boundary is documented
in [the local API/MCP feasibility note](../ck3-local-api-mcp-feasibility.md).

The loader's retained `database_dependencies.cpp:433` lines provide a useful
join key (`timestamp`, source line, node, init time, inclusive time), but they
contain no callback identity or script filename. Consequently, neither an
offline parser replay nor the current two-node live report can attribute the
stall to a production source file.

## Minimal next evidence entry

Do not repeat the same timeout. The next work package is one separately
authorized, read-only, exact-build observation after the owner provisions a
debugger or equivalent in-process instrumentation path:

1. Run the current `open_kaishek` preflight first and freeze the EXE, bridge,
   source-tree, and session generation.
2. At the static callback anchor, capture one invocation into a preallocated
   in-memory ring (no callback-side file I/O): runtime `node+0x88` vptr, slot-2
   target, callback entry/return, OS thread ID, and object validity before and
   after return.
3. Join that record to the existing node/timing key and prove completion or a
   bounded failure, then drain it only after the process is paused/quiescent.
4. Keep the result private/test-only until the callback ABI, lifetime,
   quiescence, and cleanup are all evidenced. A successful capture may then
   justify a narrowly scoped follow-up; a failed capture remains a retained
   NO-GO artifact.

The entry must not add a public bridge field, production detour, timeout
extension, callback-side I/O, save mutation, or readiness promotion. The
phase-two status therefore remains `static-ready + loader telemetry +
native-readiness RED + not-live`.

## Related boundaries

- [Phase-two bounded gate](phase2-bounded-gate-2026-09-02.md) — frozen source
  and live loader evidence.
- [Phase-two loader callback static slice](phase2-loader-callback-static-slice-2026-09-02.md)
  — exact-build static facts and unknowns.
- [Native bridge research index](../../ck3_autonomous_player/native_bridge/research/README.md)
  — production capability advertisement rules.


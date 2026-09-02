# Phase-two loader callback static slice (2026-09-02)

This note records one bounded, offline inspection of the exact CK3
`1.19.0.6` executable. It complements, and does not replace, the existing
`phase2-loader-callback-v1` fixture contract.

## Provenance

- Executable: `Crusader Kings III/binaries/ck3.exe`
- Size: `95,206,008` bytes
- SHA-256: `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- PE timestamp: `0x6A1EEE6D`; image base: `0x140000000`; image size:
  `0x5C2D000`
- Reused fixture:
  `ck3_autonomous_player/native_bridge/research/fixtures/phase2_loader_callback_v1_source_contract.json`
- Fixture SHA-256:
  `5C70182102BA3BA16D606B8ACAB89F9F952DB9D38E785DF04067265F58A80DE9`
- Machine-readable contract:
  `ck3_autonomous_player/native_bridge/research/phase2_loader_callback_static_slice_v1_abi.json`

The reproducible extractor is
`ck3_autonomous_player/native_bridge/research/extract_phase2_loader_callback_slice.py`.
The retained output artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-callback-native-slice-20260902.json`
with SHA-256
`DB578C67A98FC131B829B718C356E11E31DE84CCC649E81D79EB9EFE5C25452A`.

## Closed static facts

- The loader loop is `[0x3B9AB00, 0x3B9ACED)`; its exact prologue is the
  35-byte sequence recorded in the contract. The matching PDATA row points to
  `UNWIND_INFO` at `0x4F0FE28` (`version=1`, `flags=2`, 11 unwind codes,
  prologue size `0x23`) and records handler RVA `0x3E27DD0`.
- The Win64 flow is `RCX` (entry context) → `[RCX+0x08]` (owner context) →
  owner `+0x70/+0x7C` node range. At the callback site, `RCX=[node+0x88]`,
  `RAX=[RCX]`, and the call is `[RAX+0x10]` (vtable slot 2). Only `RCX` is
  explicitly initialized at that callsite; additional argument registers are
  not established by this slice.
- Two exact-build MSVC `_Func_impl_no_alloc` callable vtables are statically
  constructed near the database helpers (`0x4558700` and `0x4558770`); both
  have slot 2 at `+0x10` targeting `0x3B9BA70`. This closes a static candidate
  owner/slot, not the vptr of any particular live node.
- Eight direct relative callers pass a local 16-byte pair address in `RCX`.
  The callback returns to `0x3B9AB93` and the same function immediately reads
  timing/dependency fields. No thread handoff or wait is observed inside this
  bounded range.

## Explicit limits

The runtime node vptr, callback return semantics for a live node, operating
system thread identity, callback object lifetime, lock/quiescence guarantees,
source script filename, loader readiness, and any production detour remain
`unknown`. The static candidate wrappers have a void-callable shape, but that
does not promote the runtime callback to a public ABI. No CK3 process was
started, no detour or bridge field was added, and no save or game state was
written.

Focused contract tests (normal and optimized) are `8/8` GREEN; extractor
execution and Python compilation are offline-only checks.

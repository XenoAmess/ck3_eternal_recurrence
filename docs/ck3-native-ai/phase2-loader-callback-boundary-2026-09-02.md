# Phase-two loader callback boundary (2026-09-02)

This note adds one bounded, read-only increment to the existing
`phase2-loader-callback-static-slice-v1` contract. It records the complete
guarded dispatch window and the fall-through continuation of every direct
caller. It does not install a detour, change the public bridge ABI, or start
CK3.

## Exact-build evidence

- CK3 `1.19.0.6` executable SHA-256:
  `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`
- Dispatch window: `[0x3B9AB50, 0x3B9AB93)`, exactly `67` bytes;
  window SHA-256:
  `AF5F3A3C54CC163F415E7A04FC53BC89BD1200B3977E6044AE5D8BFE0E3CEC8C`
- Reproducible extractor:
  `ck3_autonomous_player/native_bridge/research/extract_phase2_loader_callback_slice.py`
- Contract extension:
  `ck3_autonomous_player/native_bridge/research/phase2_loader_callback_static_slice_v1_abi.json`
- Retained extractor output:
  `Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-callback-boundary-next-20260902.json`
  (SHA-256 `D2E0677813EC641DB77F0F8F81ECB6F57F611254A8A183A77776465B24424295`).

The window is instruction-contiguous from the current-node load through the
indirect callback. Its two explicit control-flow edges are:

1. `je` at `0x3B9AB5B` skips to the post-callback continuation `0x3B9AB93`
   when the first `node+0x88` gate is null.
2. `je` at `0x3B9AB87` targets the exact-build failure path `0x3B9ACE1` if the
   receiver recheck is null after the diagnostic helper call.

The callback instruction is `FF 50 10` at `[0x3B9AB90, 0x3B9AB93)`. The first
post-call instruction is `mov r9,[rsi+0x98]` at `0x3B9AB93`, preserving the
existing `init_time` observation boundary. The extractor records all 14
instruction spans and their bytes, so a future private probe can preserve the
two null paths and the exact fall-through without guessing instruction
lengths.

All eight direct `E8 rel32` callers are also recorded as five-byte spans with
their exact bytes and fall-through continuation (`callsite + 5`). None of the
continuations lies inside the target function; the records are static call
graph evidence, not proof that a runtime caller is safe to intercept.

## Limits and next entry

This closes only static byte/CFG boundaries. Runtime node vptr identity,
callback return semantics, callback object lifetime, thread identity,
quiescence, script-file attribution, loader readiness, and any production
detour remain unknown. The next legitimate entry is still a private paused
exact-build observation of callback identity/completion, with no callback-side
file I/O and no public ABI widening. No CK3 launch, save mutation, or timeout
retry was made for this slice.

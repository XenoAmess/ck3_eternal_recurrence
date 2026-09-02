# Phase-two loader callback CFG/null edges (2026-09-02)

This is one bounded extension of the existing
[static callback slice](phase2-loader-callback-static-slice-2026-09-02.md).
It records only instruction boundaries and local control-flow facts that were
not present in the original contract. The exact executable remains CK3
`1.19.0.6`, SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.

The machine-readable contract is
`ck3_autonomous_player/native_bridge/research/phase2_loader_callback_cfg_v1_abi.json`.
The extended extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-bounded-gate-20260902\loader-callback-native-slice-cfg-20260902.json`
with SHA-256
`0BB03760C6F204F703D2A11AF573CBBE0C1A911D3E95CD0AA9AA7E0161762A5A`.

## New exact-build facts

- `0x3B9AB36 -> 0x3B9ACC4` is the empty-node-range edge to the normal
  epilogue; the normal return is `0x3B9ACE0`.
- `0x3B9AB53` first compares `node+0x88` with zero. Its branch at
  `0x3B9AB5B -> 0x3B9AB93` treats a null field as an ordinary callback skip
  and continues timing/dependency aggregation.
- The non-null path performs the intervening helper call at `0x3B9AB78`, then
  reloads the same field at `0x3B9AB7D`. The second test at `0x3B9AB84` has a
  distinct null edge, `0x3B9AB87 -> 0x3B9ACE1`, which enters an opaque direct
  call to `0x3E22A88`. Therefore the exact static path condition is “first
  read non-null, reload null”; the cause is not established.
- The dependency sentinel exits at `0x3B9ABAE -> 0x3B9ABC7`; otherwise
  `0x3B9ABC5 -> 0x3B9ABB0` continues the dependency loop. The outer node loop
  returns through `0x3B9ACBE -> 0x3B9AB50`; its fall-through is the normal
  epilogue.
- The function has a second opaque error call at
  `0x3B9ACE7 -> 0x3E34DF0`, reached from the allocation-header distance
  check at `0x3B9ACB0`. No business meaning is assigned to either error
  target.

The extractor now checks all 11 direct conditional branch encodings,
relative targets, fall-through boundaries, the normal return byte, and both
opaque error-call targets. It uses no debugger or running process.

## Boundary

The double-read path is not proof of a scheduler race, use-after-free, or
thread identity. Runtime node vptr, callback lifetime, callback return,
quiescence, source attribution, and loader readiness remain unknown. No CK3
process was started, no detour/public ABI was added, and the existing
callback-probe NO-GO remains unchanged.

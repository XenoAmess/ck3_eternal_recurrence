# G2 Raiktor source-specific war-loss provider

Status: **static-ready / default-OFF private capture / live not run**.

## Delivered offline boundary

The exact CK3 `1.19.0.6` source seam was already closed in
`raiktor_spawn_army_execute_v1_abi.json`, and the standalone private observer
already existed behind
`XAR_CK3_ENABLE_G2_WAR_BOUND_PRIVATE_CAPTURE_V1=OFF`. This package does not
add a detour to the shared bridge DLL. It supplies the missing typed consumer
for that observer and a pure offline preflight which is independent of the old
UI/live runner's historical open_kaishek pins.

The exact observation window remains:

- `spawn_army::Execute` RVA `0x2E7F010`;
- stop after attach/finalize at RVA `0x2E7F951`;
- stop consuming locals before cleanup at RVA `0x2E7F9A6`;
- loaded `spawn_army` node in `R14`;
- created CArmy in `RSI`;
- new persistent-regiment pointer vector at `[RSP+0x60]`, count at
  `[RSP+0x6C]`;
- evaluated name at `RBP+0x70`, supporting evidence only.

`raiktor-source-specific-war-loss-attribution-provider-v1` accepts only an
existing standalone capture with the exact action-arm proof for
`bookmark.1071.a`, six ordered unique loaded nodes, six unique created CArmy
generations, one exact full-generation WarID, and complete persistent/current
generation mapping. Per-current-regiment soldier values are summed from the
capture; no expected `500` per execution or authored `3000` total appears in
the normalizer.

The normalized source set carries:

- all six execution rows;
- created CArmy generation IDs;
- created persistent CRegiment generation IDs;
- current CArmyRegiment generation IDs and measured soldiers;
- persistent-to-current mapping;
- exact WarID and deterministic `source_set_sha256`.

This is deliberately only a capture shape. Until a real private capture is
classified, the typed result retains:

- `private_live_evidence_classified=false`;
- `action_bound_current_ready=false`;
- `postwar_cleanup_ready=false`;
- `source_specific_loss_ready=false`;
- `comparison_input_ready=false`.

## No-launch evidence

The new source contract is
`native_bridge/research/fixtures/raiktor_source_specific_war_loss_attribution_v1_contract.json`
(SHA-256
`1633808E42C324EF6C282481040B905DAF7FE9B0147F7072382919CA5064F9CE`).

The pure offline preflight rehashes the exact CK3 executable, existing ABI,
verifier, private observer source/manifest, CMake source, provider source, and
fresh standalone executable. It reruns the exact-build ABI verifier and the
standalone self-test. It never inventories, launches, or attaches to CK3 and
does not require an independently owned CK3 process to be absent.

Current GREEN evidence:

- preflight
  `Z:\ck3_mod_rewrite_process_assets\zg361\g2-source-specific-war-loss-provider-20260905\preflight-r3.json`;
- preflight size `3995` bytes and SHA-256
  `FE3CDDF93E07B0028ED40BF472F55C89589CF497B2395DC587806ED4C913EB4B`;
- standalone Release executable size `113152` bytes and SHA-256
  `B8328D5C0B52AF667BB71D2BBE660C803BF46EC0A7549A514083B7DBB8BA5A72`;
- exact-build ABI verification GREEN;
- standalone self-test exit `0`:
  `PASS: private=1 action_arm=1 loaded_nodes=6 exact_war_id=1 public_abi=0 readiness=0`;
- no capture supplied, hence `private_capture_live_executed=false`.

On this machine bare `cmake` resolves to the Cygwin installation, whose
compiler probe failed and interpreted the Windows output path as a relative
directory. The successful build used the exact Visual Studio 18 CMake binary,
generator `Visual Studio 18 2026`, architecture `x64`, configuration
`Release`, and MSVC `19.51.36248.0`. The mistaken generated directory was moved
out of the shared worktree into this artifact root as
`cygwin-path-mistake`; it contains no source modification or live evidence.

## Remaining live completion

A future exclusive fresh natural `bookmark.1071.a` run must produce all six
source executions before this provider may be called private-live. That source
set must then remain in the same lifecycle through:

1. a measured current checkpoint for those exact generations;
2. one typed termination action;
3. exact-generation postwar cleanup for the same source set.

Only that join can publish source-specific current loss or set
`comparison_input_ready=true`. The historical R3 rows cannot be retroactively
attributed because their lifecycle never captured the source executions.

Campaign dominance, owner budget, and white-peace comparison are separate
providers and were not changed. Public/action/decision/automatic-surrender and
`GEN-034` readiness all remain false.

No CK3 effect file was changed and no loading or single-file-size performance
RED occurred, so the effect-file sharding rule was not exercised.

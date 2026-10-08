# Actual4 direct carrier in the existing character query

Source sealed before integration on 2026-10-09, Asia/Shanghai. Exact build is
1.20.0.4 / Steam 25734779 / EXE
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
This package reuses the [direct carrier source](battle-person-next-direct-carrier-12004.md)
and its 328 unique bytes; it reads no additional executable bytes.

The existing registered tool `ck3_query_battle_terminal_transition_v1` accepts
`prior_combat_id=null`, `subject_public_cunit_id=null`, `character_ids=[full ID]`,
and `expected_revision`. The encoder produces
`query-battle-terminal-transition-v1-none:characters:<ID>`.
`NativeBridgeDriver._execute_battle_terminal_transition_v1_query` sends this
existing private query, normalizes its frame, and adds same-frame mirrors.
`GameplayBridgeService.query_battle_terminal_transition_v1` consumes those
mirrors without changing the requested actors.

The production native route is `ExecuteTypedQuery12002<battle_terminal>` ->
`BindBattleForQuery12004` -> actual4 `BindBattleImage` ->
`ReadBattleTerminalTransitionV1`. Its two `TerminalSample` passes resolve each
requested Character through the actual4 character storage and check the full ID.
`CharacterObservationSample` currently emits current-person leaves only when the
exact .3 factory flag is enabled. That factory correctly excludes actual4.
The new exact4 carrier-only binding is independent of that flag and the older
numeric, trait, prior-context, and pending-death readers.

## Native association and contribution

The already cached actual4 getter `28C3AC0..28C3B9C` proves this owned branch:
Character `+1B0` -> scratch `+258` -> model; model `+8` must equal the requested
Character; only then does the getter select model `+10`. Its other branch selects
an inline default context and may initialize it. The observer copies only the
proved owned branch through guarded reads; it binds the exact getter identity
for provenance and never calls that getter or initializer. Missing scratch/model,
failed copy, and owner mismatch remain a precise unavailable direct leaf.

The independent direct reader then consumes the actual model receiver, and
publishes `current_person_state.carrier_1c8_b70_direct`. It preserves carrier
absence and wrong magic as zero occurrences, actual mapped/fallback PC bytes,
signed Q64 values, raw array order, and lazy-default partial state. Model `+10`
is destination identity only. The held model is not a fresh stage-start baseline.

```mermaid
flowchart TD
  T[Registered existing terminal tool: requested full Character IDs] --> D[NativeDriver existing primitive route]
  D --> F[actual4 Battle factory and character storage]
  F --> R[Resolve each requested Character; two terminal samples]
  R --> S[Guarded Character1B0 / scratch258 / model8]
  S -->|owner equals requested Character| C[Source-closed direct carrier reader]
  S -. absent, unread or different owner .-> U[Precise unavailable leaf]
  C --> P[Production current-person serializer]
  U --> P
  P --> W[Production command_result envelope]
  W --> N[NativeDriver main terminal normalizer]
  N --> V[Service same-query mirror and registered MCP result]
  V --> O[Pure ordered zero or one contribution]
  O -. fresh baseline and later2921AB0 remain unknown .-> E[Full Entry not promoted]
```

## Integration and FIRST boundary

The actual4 Battle factory installs only `PersonCarrierDirect12004Bindings`.
The common reader admits the new optional state through that binding, without
enabling old .3 fields. The existing private serializer gains one optional leaf;
the strict main normalizer joins its copied full Character ID to the observation
row. NativeDriver and Service keep their existing same-frame path and registered
tool. The shared command-result formatter is used by both production dispatch
and the new fixture, so the registered consumer receives the original full packet.

The one new native target will publish eight complete command_result packets
through the real query reader and serializer. A single registered MCP compound
will consume those packets through the production NativeDriver and Service,
including the requested enemy actor independently of the player. Native and
Python FIRST are NOTRUN; Root owns their execution. No game, SDK, runtime pipe,
build, test, historical GREEN replay, or further function research occurs here.

The candidate target is `xar_ck3_12004_person_carrier_direct_mcp_test`, with CTest
`xar_ck3_12004_person_carrier_direct_mcp_first`. Its sole fixture source is
`tests/person_carrier_direct12004_mcp_fixture.cpp`; it reuses the entire production
Bridge object closure and Runtime archive with no replacements or scheduler
stubs. The sole registered case is
`test_person_carrier_direct12004_registered_mcp.py::test_person_carrier_direct12004_registered_mcp_eight_whole_packets`.
The existing `mcp==2.0.0` server and Client APIs are used unchanged.

The current Service and NativeDriver mirrors already retain normalized current
person leaves. They need no new dispatch policy; the main terminal normalizer
adds the exact4 leaf and Character join. The tool's existing accepted ID range
and same-paused-frame checks remain in force. Native fixture player29829 and
requested full enemy ID67108867 are deliberately different.

The shared header change has a concrete compilation cost. The retained Native39
dependency/owner metadata names 423 existing production owners (149 Bridge,
274 Runtime); the new direct reader adds one Runtime owner. Four existing CPP
bodies change: `bridge.cpp`, `battle_terminal_transition_v1_mailbox.cpp`,
`ck3_12002_battle.cpp`, and `ck3_12004_battle.cpp`. Root joins Native40's two
replacement Bridge objects as the actual next parent. This is a source/include
dependency list, not a new build result or a replay of historical qualification.

## Root offline qualification — October 9

The bounded direct carrier leaf is now **static-ready** through the existing
registered character query. Compiled native and fixture source is
`c928804c8afd61b6ded61c52b191b329e754d2da`; Python qualification source is
`45ce81348ab7fcdde6900dfa95b9e5fbf546c927` in the complete independent tree
`Z:/gbs-runtime41-person-mcp-qualified-source`. The sole registered eight-scene
compound passed in **6.7175118 s**, at 01:26:31.590847–01:26:38.308356 CST.
It consumes the original eight native command-result packets from attempt04,
whose native FIRST passed in **0.2673182 s**. Normal readable cases require
the leaf's readiness to be true; missing initialization and partial numerical
reads retain their explicit unavailable reason. Requested character67108867
and fixture player29829 remain distinct through the actual production route.

[Canonical41](Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/entry-live-fix41/ROOT-PARENT-RUNTIME-INCREMENTAL-DLL.json)
records the mixed object lineage and actual compiler/link/FIRST receipts.
[Consumer-only receipt](Z:/g2-native41-build01/root-consumer-retry05/ROOT-ACTUAL-RESULT.json)
binds the final Python source and original packets. The qualified DLL is
`Z:/g2-native41-build01/attempt04/binaries/xar_ck3_bridge.dll`, 13,293,056 bytes,
SHA-256 `81b22f1a91465029a7747aec62c5eb26bb2ccf33491a4cd6c882e4f6a406b7a5`.
Root hashed this new DLL and its small manifest once; old binary hashes were
reused. The first 425-input compiler batch had actual peak concurrency64 and
lasted170.462886 seconds. Four existing implementation files omitted from the
inherited object ledger were subsequently compiled once, yielding429 unique
compiler inputs and730 production owners: Bridge299, Runtime430, Protocol1.
Those four recovered implementations are not new gameplay features.

Failed attempts are retained. Attempt01's basename-based archive removal
reported LNK4014 and kept old factory/reader definitions, which caused LNK4006
and the native binding assertion to fail. A fresh archive then exposed missing
existing PlayerClaims/TitleOwnLaws implementations and their two title helpers;
attempts02/03 preserve those link failures. Building Runtime430 from its explicit
objects resolved the actual definition selection without replaying425 compiles.
Attempt04's native packets passed, but the first Python normalization rejected
their lossless Q64 decimal strings. The one-file Python fix decodes those strings
and accepts subsequent normalized integers through the existing signed64 check.
The final retry runs only the same registered consumer; it changes neither
native code, the original packets nor their assertions.

Complete person/Entry reconstruction, R78 live crash causality, cold startup,
paused live observation, actions and G2 outcome credit remain unqualified.
This work used no local Game, SDK, game pipe or UI operation.

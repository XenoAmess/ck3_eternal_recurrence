# Actual4 M4 raw signed EAX at28BE0B0

This leaf copies the memory operands required by actual `28BE0B0` and projects its signed `EAX`. It supplies the actual `2468F77` child of the construction mode3 input reader. The receiver is the same paused query's actual `2467660` return, supplied by continuation06; it is not selected from the played Character.

The source identity is CK3 1.20.0.4 / Steam25734779, image SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. The complete held source is `[28BE0B0,28BE106)`,86 bytes, with returns at `28BE104` and `28BE105`. The retained detail packet is `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/existing-mcp-factories-12004/general-combat/piety-gap11/maa_piety_rank-DETAIL.json`; its actual cache is `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/shared-span-cache/new-028BE0B0-028BE106.bin`. No new executable acquisition was needed.

The held parent instructions show `2468F74 MOV RCX,RAX`, `2468F77 CALL28BE0B0`, and `2468F7C MOV [RBP+250],EAX`. The saved signed32 return is extended by `246921B MOVSXD RAX,[RBP+250]`, then scaled by `2469222 IMUL RBX,RAX,100000`. Continuation03 owns the subsequent raw numeric composition and its property keys.

The actual source reads `receiver+1B0` first. A copied null carrier returns signed zero immediately at `28BE105`, without requiring any global or carrier fields. A nonnull carrier reads signed32 count at `module+54582E4`, signed32 cap at `carrier+120`, then signed64 score at `carrier+118`. These three loads occur even when count is zero or negative. For positive count it loads the array pointer at `module+54582D8`, then compares consecutive signed64 thresholds in their original order. Equality increments the rank. The first threshold greater than the score stops the loop, so later entries are not demanded. A negative cap is ignored; a nonnegative cap returns the smaller of cap and rank. The main path returns at `28BE104`.

`ReadRaw28BE0B0Eax12004` is an inline, allocation-free reader in `construction_owner_mode3_raw_eax_28be0b0_12004.hpp`, under `xar::ck3_12004::construction_owner_mode3`. It reuses continuation06's `RawReceiverAccessV1` and guarded address-copy helper. It carries the unchanged `CampaignRootFrameV1.snapshot_revision`, actual receiver, copied carrier/count/cap/score, threshold prefix count, last copied threshold, return RVA and optional signed EAX. Failed demanded reads leave the EAX unavailable. `ReadRaw28BE0B0EaxAdapter12004` exactly matches continuation03's `Mode3SignedEaxChildV1` callback and writes the output only on success:

```cpp
Mode3SignedEaxChildV1 child{
    nullptr, ReadRaw28BE0B0EaxAdapter12004, true};
```

There is no production translation unit, native getter invocation, initialization or memory mutation. Identity, Model, title and property-key reads are absent because this source does not demand them. `observed` describes a copied-input software projection; `observed_native_producer_call` stays false. The owning query supplies and validates its paused frame.

The new test fragment has no main. It exports `RunConstructionMode3Raw28BE0B0Eax12004NewCases()` and `ConstructionMode3Raw28BE0B0Eax12004NewCaseCount()` (12 groups). Cases cover null carrier, signed comparisons and equality, ordered early stop, count zero/negative, full threshold prefix, cap branches, demanded-read failure, unchanged adapter output and source-load order. Only central10's single new M4 compound may compile/run these cases. At worker handoff they are authored, not built or run.

Source and delivery receipts live in `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-11c/`. The active dependency is protected until review on2026-10-17; small records are reviewed on2027-04-08 under storage policy1.0.0. This packet stays below its4MiB light-work ceiling and adds no binary copy, old qualification replay, Git operation or game execution.

# Actual1233A40 readonly raw EAX

`ProjectSelectedPietyPriceEax12004` connects the selected create/edit expression to the single source owner of actual `A0F0B0`. It returns that reader's optional signed raw EAX and source frontier unchanged. It does not invoke a native evaluator, duplicate an existing price query or compute the scalar twice.

The shared actual wrapper is `[1233A40,1233B38)`,248 bytes, in CK3 1.20.0.4 / Steam25734779, image SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. Its exact held pdata owner was captured once into `D:/codex-ck3-background-spill/native71-continuation-20261010/shared-span-cache/new-01233A40-01233B38.bin`, span SHA-256 `6bbefe85557e5ee0788768327bd6562df8d8a97e306491e0108c53734606cbeb`. The complete literal, instruction and relative/RIP metadata cross-check passed. No old executable, full hash, section scan or active evaluator was used.

The create caller `31D9930` selects original definition+760, calls `1233A40` at `31D99C5`, saves EAX into EBX at `31D99CA`, and returns that raw value at `31D9A39`. The edit caller `31DF3B0` separately selects original definition+2A8, calls at `31DF445`, saves EAX at `31DF44A`, and restores it at `31DF4B9`. Each caller retains its own actual current Rite; neither selection is replaced by a cloned or generic definition.

The wrapper passes the selected expression in RCX. It copies the original context pointer into three consecutive Q64 fields of a local argument pack, adds a pointer to its `3736040` scratch object and a byte loaded at module+5D1DADC, then calls `A0F0B0` at `1233AB4`. R8 is the caller's zero. R9 is the caller's named tuple, passed through without any direct dereference by this wrapper. EAX is saved in EBX at `1233AB9`, preserved across cleanup, restored at `1233B1D`, and returned at `1233B37`; the wrapper applies no clamp, default or scaling.

Continuation40 owns the sole `ReadPietyPriceA0F0B0Readonly12004` reader and result type. Its actual source first compares signed mode DWORD at selected expression+B8 with zero. Mode zero immediately returns the raw DWORD at+98 before context, name, profile or RNG inputs are consumed. The shared11 header delegates this operation once and retains signed EAX bits, selected expression identity, unchanged snapshot revision and unavailable reason. Missing required memory is unavailable. Modes outside the reader's closed branches retain their source frontier; they do not become numeric zero.

The shared access type comes from continuation22's `piety_price_numeric_access_12004.hpp`. Create and edit producers call the header `piety_price_evaluator_1233a40_readonly_12004.hpp` in namespace `xar::ck3_12004::piety_price_raw_inputs`. The result `PietyPriceEvaluator1233A40Readonly12004` extends the40 result with an independent optional `scratch_source` record; all scalar fields retain the40 result without extra data reads or readiness gates:

```cpp
const auto result = ProjectSelectedPietyPriceEax12004(
    access, selected_expression_identity, unchanged_snapshot_revision);
```

The static numeric path does not depend on a physical Rite context, scratch/frame initializer or name tuple projection. The independent32 scratch record retains raw bytes, per-byte source/numeric masks, two relative self-pointer operations and an absent physical identity. Its pure provider performs no memory reads or native calls; an unavailable source record does not reject a known numeric value. Pointer placeholders and untouched holes are not known numeric zeros. The dynamic path's R9 use remains a source question for40's actual reached children; it is not assumed to be diagnostic-only. Continuation18 owns the Rite context projection,32 owns `3736040`,43 owns `3735F90`, and40 coordinates its numeric children. The still separate43 frame frontier is not qualified by a scratch record.

This leaf is header-only. It adds no production translation unit or standalone test fragment. It links the existing owned40 numeric and32 scratch provider translation units once each. The create/edit owners' new connected cases exercise the wrapper and40 reader through the one central compound. At handoff this header is authored, not compiled or run by11. Dynamic expression support remains limited by its actual source frontier.

The evidence, source freeze, patch and delivery pins are retained under `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-11e/`. Storage policy1.0.0 applies, with a4MiB light package ceiling, seven-day active-input protection and finite class TTLs. Z, Git and game state were not changed by this leaf.

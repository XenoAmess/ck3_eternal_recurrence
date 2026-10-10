# Native71 actual4 assault eligible contributor composition

2026-10-10. Exact source is CK3 1.20.0.4 / Steam25734779, EXE identity `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. All new files are external under `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-38`; the repository remains read-only in this lane.

The source-defined eligible Province B and native current expected loss are already available. The old [manager input topic](army-monthly-manager-prepared-stage-inputs-12003.md) named `247F1D0` as the next source entrance. That body was subsequently closed and implemented in [Province besieging current](army-province-besieging-current-12003.md), with repeated FullID/flags0/DATA semantics and an independent observed scalar. Actual4 retained Province factory mapping proves the current entrance `247F1B0`, 404 bytes; the actual Siege getter is `25205A0`, 357 bytes. `ck3_12004_army_support.cpp` already binds these, `24E8340`, `2C16670`, source fallbacks and the loaded percentage table at `5452384/54524C8`. The existing collector is reused. No frozen executable or PE metadata was read for this package.

## Actual admission and reducer

The actual4 getter walks Province `+740/+74C` Unit FullID occurrences in stored order. Resolve the complete signed Unit ID or its native fallback. Read the Unit `+20` qword Province pointer or Province fallback, then compare pointed Province `+10` with the caller Province identity. Require Unit DWORD `+18=0`, signed `+170<=0` and `+44=0`; resolve its Army/fallback, require native `24E8340` false, caller Province `+788!=-1` and native `2C16670(Army,Province)` true. Re-resolve the Army after that qualification call. Its `Army+38` descriptor feeds whole-current flags0 and the result is added with signed32 wrap. Unit, Army, ArRg and DATA occurrences keep their repetitions. Raw invalid IDs can select a native fallback; only the final ArRg refresh receiver has the magic/FullID-not-minus1 guard.

This reducer is distinct from the supply contributor admission and flags2 count. It is not a supply-mode0 replacement. The native current `25205A0` scalar is a current observation; when physical/current inputs evolve, its old value cannot be labeled a post-refill scalar. Actual group Siege breach and loaded percentage remain fixed explicit input context for the conditional calculation.

## Concrete production gap and minimal reuse

`ReadGroup` in `ck3_12003_current_daily_assault_loss.cpp` already captures the actual table group Siege's Province B family as `besieging_inputs_v1`, replaces its assault context with that actual group Siege receiver, and keeps `native_current_expected_loss`. The daily loss model presently starts its physical and cached values from observation. The existing ordered subject B model has its own target refresh scope. A current subject row alone cannot prove refresh membership for another group's Province.

The existing `ReadOrderedBesiegingRefillInputs12003(b, army, unit, family)` can collect the necessary group scope without a new getter or collector algorithm. Its input `family` determines the actual Province and target ArRg set. Subject Army/Unit provide capture labels; whole primary `+50/+5C` traversal selects every matching target refresh occurrence, including native fallback and original repeated ArRg positions. Complete traversal proves a known no-refresh target; failure does not. It also derives the target DATA persistent union and ordered primary `+30/+3C` occurrences. Root can call this collector for each captured group B family and attach the standard `ordered_besieging_refill_inputs_v1` family to that group. Public DTO, normalizer/serializer, observer hook, manager shared capture and service changes remain Root-owned.

## New pure entrance

`assault_eligible_contributors_12004.py` exports:

```python
project_assault_eligible_contributors_12004(
    group,
    derived_physical_chunks=explicit_final_physical_rows,
    refresh_selection=group_ordered_besieging_refill_inputs,
)
```

The group is the existing normalized loss group. Selection must match its Province, carry complete membership and the exact target identity set, and preserve manager/ArRg occurrence indices and full signed IDs. The final physical map is a supplied derived stage, never produced by this leaf. `None` means absent; `[]` means an explicit unchanged map. Rows use `(persistent_regiment_id, chunk_index)` and explicit availability. Missing/unknown affected rows replace the captured value with unknown. Current/max-only overlays keep captured state; an explicitly supplied state applies to every DATA alias. Conflicting final values for one physical identity are rejected.

The leaf refreshes only positively selected target stored counts through the existing production `project_observed_raised_regiment_refresh`; it executes zero refill ADDs and zero physical cores. Repeated refresh occurrences remain receipts; the final stored identity value changes once per subsequent B occurrence. Every admitted ArRg repetition gets its signed delta from captured current to derived current; each original Unit occurrence recounts its native flags0 baseline. Known nonmembers retain their stored native counts even if unused DATA is missing. Complete original Province roster is required for nonempty B. An actual nonpositive Province count or invalid Province magic keeps the native source-zero path and does not demand unused physical/refresh/table operands.

The result has `group_native_index`, `physical_slot_i64`, independent readiness, conditional B, `expected_loss`, final refreshed counts and original `native_besieging_strength`/`native_current_expected_loss`. A ready `besieging_inputs_v1` is an explicitly marked **simulation copy**: its legacy baseline field names and per-Army/per-ArRg stored counts are rebased to the derived stage. This copied operand is never published as a new native DTO. Continuation37 must rebase the isolated kernel copy's `native_current_expected_loss` to derived `expected_loss`, because the existing unchanged-B branch consumes that scalar; the original observation remains separately visible outside the model. Later target-only cached deltas then evolve relative to the correct derived entry.

Admission, character predicate, raw links and nonphysical contexts stay fixed from the capture. New members or actual after-stage eligibility are not inferred. Capture/stage identity and complete prior-write overlay proofs are owned by continuation37. Preparation, actual post-stage capture, native execution, full daily assault and full monthly remain separate.

## One new focus and remaining handoff

The sole new `focus.py` execution was GREEN, 10 new cases, 0.0032843001 seconds in the case body. It imported only this new leaf and existing pure production primitives, with bytecode writes disabled. No old tests, native wires or FIRST were executed. The main case retains negative signed FullIDs and native raw-minus1 fallback, repeats DATA/ArRg/Province contributions, and changes B `640->800` / expected loss `64->80`; native comparison values stay `640/64`. It additionally covers known nonrefresh without unused DATA, unknown membership, absent physical input, explicit unavailable slot, explicit state3 current0, source-empty zero, captured negative percentage, another-Province rejection and conflicting physical identity rejection. `FOCUS-RESULT.json` pins the exact code and executed argv.

Qualification is **bounded pure adapter static-ready**. The existing actual4 native collector/source qualification is reused; no new native observer, native compile, serializer wire, game artifact or live credit is granted. Root still needs group-scoped shared wiring and a newly qualified integrated stage input before actual consumption. Actual post-stage remains null; actual replenishment/loss/effects and full daily/monthly remain false.

Source/input identities and the source-first plan are in `SOURCE-FREEZE.json` and `SOURCE-FIRST-PLAN.md`. Storage policy1.0.0 applies; the new small package budget is250000 bytes and no automatic reservation or cleanup is claimed. An initial broad JSON search accidentally traversed large runtime JSON; it created no export or retained duplicate and was discontinued. All subsequent source reads were exact bounded paths.

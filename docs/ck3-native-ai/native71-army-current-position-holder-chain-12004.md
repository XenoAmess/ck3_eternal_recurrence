# 1.20.0.4 Army current-position holder chain

The actual `2C097F0` position predicate passes its original holder in RCX and a complete Character ID in EDX to `28B2800`. This package closes that required predicate and its sole selector using retained 1.20.0.4 source, then provides an independent guarded-read implementation. It does not invoke either native function.

The build identity is CK3 1.20.0.4, Steam build 25734779, with the previously retained executable SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`. The identity was inherited, not rehashed. The package reused the complete 160-byte predicate `[28B2800,28B28A0)` and 118-byte selector `[28BFC50,28BFCC6)`, with no executable reads or new decoding.

## Actual caller and result

The complete 465-byte parent source belongs to continuation-34b. Its original actor is r13 and holder is r15. At `2C0995E`, the holder is RCX and the selected War-side participant's complete ID from participant `+8` is EDX. The actor-ID participant is skipped before this call. AL true selects `2C099A0`; AL false advances the participant traversal. At `2C09984`, RCX is the same holder and EDX is the original actor's complete ID from actor `+18`. AL true again selects `2C099A0`; AL false continues to `2C3A0E0`. This establishes the required receiver and target direction without renaming other relations.

The source ABI is `(holderCharacter RCX, complete target DWORD EDX) -> AL boolean`. Equality between the target ID and the initial receiver's `+18` returns false before any selector input is read. This is a strict chain predicate. False exits at `28B288D`; true exits at `28B289F`.

## Selector fields

`28BFC50` preloads both Character `+1C0` and `+1B8`. When `+1C0` is nonzero, it reads that carrier's `+1C0`, then the selected relation object's `+28` pointer. A selected Character requires tag `+1C == 43686172` and ID `+18 != FFFFFFFF`; otherwise the selector returns its original Character. The native code supplies no extra null checks on this path. A failed guarded read is unavailable, never a fabricated native fallback.

When Character `+1C0` is zero, a nonzero `+1B8` link supplies the complete handle at `+C8`. The native store pointer is image RVA `5C67568`. The handle's low 24 bits index the unsigned count at store `+2C`; a valid index selects from table `+20` with 16-byte stride and pointer offset `+8`. The selected Character's full DWORD `+18` must equal the complete handle, including generation bits. Missing store, out-of-range index, null entry or full-ID mismatch uses the actual fallback pointer at image RVA `5C67570`. The selector contains no calls or stores.

## Native traversal

The outer predicate rereads the current Character's `+1C0` after selecting the next Character. When this field is zero, it validates the selected tag and full ID, rejects sentinel or equal current ID, returns true for the target ID, and otherwise promotes the selected Character to current. This branch has no native numeric iteration limit and can later enter the nonzero branch. The observer's occurrence guard yields an unavailable result on exhaustion; it does not turn exhaustion into native false.

The nonzero branch validates and compares at most seven selected IDs. After each unmatched comparison, including the seventh, it selects the next Character and checks that next ID against the previous selected ID. An equal ID returns false. After the seventh comparison, it returns false even when the eighth selected ID equals the target. The independent implementation preserves this extra selector and ID read before the counter stop.

## Candidate and validation boundary

`ReadArmyPosition28B280012004(const ArmyRegularCoreReadonlyAccess12004&, uintptr_t holder, int32_t target_full_id) noexcept` returns `ArmyRegularCoreReadonlyPredicate12004`. It uses continuation-34b's shared guarded-read callback and frame budget. Every required read failure remains an empty optional with a concrete reason. Root must supply the qualified 1.20.0.4 Access for the same current frame. The candidate does not bind, call or persist native getters.

The unique new-focus export `RunArmyPosition28B2800NewFocus12004()` supplies ten owned-buffer cases: strict self, direct carrier match, rejected carrier selection, registry match, same-index generation mismatch using the actual fallback, zero-to-nonzero traversal, seventh/eighth comparison limits, occurrence exhaustion, and an unread preloaded field. It checks that input storage is unchanged. These cases are authored and have not been compiled or run by this worker. Root's 33b/34b compound central10 run owns their single execution; they have no separate main or CTest entry.

The source-plan check passed before candidate authoring. This package provides no live current-position observation, field-writer contract, invalidation timing or future post-state claim. The remaining parent War/side routes belong to continuation-34b. The earlier continuation-54 conception helper and its fixture are not part of this package.

## Evidence

- Package root: `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-54b/`; see `SOURCE-CLOSURE.json`, `SOURCE-PLAN.json`, `PLAN-CHECK.json`, `RELATION-ACTUAL4.asm`, `SELECTOR-ACTUAL4.asm` and `DELIVERY.json`.
- Parent: `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-34b/readonly-dependency-source01/unit-position-predicate-2C097F0.json`.
- Predicate: `Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/army-world-family/native-main/map01/holder_owner_relation-DETAIL.json`, retained `.new` actual 1.20.0.4 body.
- Selector: `Z:/ck3_mod_rewrite_process_assets/g2-parallel-20261007/adopted-lifestyle-building-faction-12004/faction/leaf01/immediate_liege-DETAIL.json`, retained `.new` actual 1.20.0.4 body.

The package is a D-only handoff. Root owns repository adoption, central CMake/fixture changes, shared caller integration and any current-frame runtime observation.

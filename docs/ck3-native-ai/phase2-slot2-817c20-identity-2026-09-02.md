# Phase-two `0x817C20` list identity (2026-09-02)

This package is static-only. It does not launch CK3, change the public bridge,
or promote native readiness.

## Frozen live tuple

The full list-identity report SHA-256 is
`109CB334D56B6A50F75F8AA8C4A9EBD349B2703A28ED71694E90E0262BE15471`.
Its cleanup report SHA-256 is
`2B60336D7ADBCE222618B618A97C49D24CE9B8DCE7B2605DC2936B39E22A7621`.
The typed postprocessor validates one installed, failure-free, consistent
capture: list/scan/sample counts are all 27, every loss/overflow counter is
zero, all 27 descriptors have the same owner `0x2686F59B440`, task equals
callback, and both task and descriptor addresses advance by `0xC0` bytes.
States are 25 entries at 1 and two entries at 0. The only callback slot2 RVA is
`0x817C20` (27 entries); the frozen loader callback RVA `0x88B480` occurs zero
times. Therefore this bounded list is not the loader completion list.

The postprocess artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\post-call-list-identity-live-postprocess.json`,
SHA-256 `8F549C73A71BF2054FAE10AC851D11F41FF153C3C6145AB553E3979856931959`.

## Exact function and task semantics

On the pinned CK3 1.19.0.6 executable
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
`0x817C20` is a 124-byte logical function ending at `0x817C9C`, SHA-256
`3EFBF1BCD7A64FF8ACD10A7E6E954D9561DB8C77EE755171CB284F3E81F76C3C`.
Its PDATA comprises a primary fragment `[0x817C20,0x817C43)` and chained
fragments `[0x817C43,0x817C8E)` and `[0x817C8E,0x817C9C)`.

The bounded CFG establishes a parallel range worker:

- `[RCX+0x8]` is the shared range state;
- offsets `+0x0`, `+0x14`, `+0x1C`, and `+0x28` hold the atomic next index,
  total bound, batch size, and pointer-array carrier;
- `0x817C3B` and `0x817C81` use `lock xadd` to claim batches;
- the worker clamps the batch end to the total, loads each array element at
  `0x817C6A`, and invokes its virtual slot 1 at `0x817C71`;
- it returns once the claimed index reaches the total bound.

This is a generic `SPdxParallelForOverArray` range-worker `std::function`
callback, not a completion-state callback.

## RTTI and owner boundary

The exact image contains 278 valid MSVC RTTI vtables whose slot2 points to
`0x817C20`. Every corresponding type is a specialization of
`std::_Func_impl_no_alloc<reference_wrapper<SPdxParallelFor<SPdxParallelForOverArrayOperatorFromCallTraits<...>>>>`.
The canonical 278-row vtable/COL/type-descriptor digest is
`BCE3AAEEA887157CC07FE219D6BDC545C1EB63883C993C4EC096530AE96C7222`.
Specializations cover many unrelated array domains, including cached icons,
game rules, scripted GUI/effects, load screens, notifications, portraits,
cultures, and activities.

Consequently, the slot2 target closes the generic parallel-for task domain but
does not uniquely identify the runtime RTTI specialization. The v1 live schema
retained callback and slot2 target but not `[callback]` vptr, so choosing one of
278 specializations would be an unsupported inference.

## Next distinct seam

Loader progress must stop following the unrelated `0x3407D9C` caller-local
parallel-for list. The next primary observation belongs at the already frozen
true completion producer: immediately around `0x3B9CFD2`/`0x3B9CFD7`, capture
the `RBX` producer task, `[RBX+0x38]` callback, callback vptr and slot2,
`[RBX+0x58]` owner, and `[RBX+0x60]` before/after the state-2 publication. The
exact task identity can then be carried outward to its real carrier/consumer.

Recording `[callback]` vptr in the existing list observer would resolve this
parallel-for list's concrete RTTI specialization, but it is secondary forensic
work and is not required for loader progress. The completed `0x3407DA1` slot2
histogram live must not be repeated.

The static extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\slot2-817c20-static-extract.json`,
SHA-256 `8B5083889D8D9FEC9A6F2ED67FA8C43400FA43CA11B77AABC2733B0E113F35A8`.
Readiness remains **native-readiness RED + unrelated parallel-for task domain
excluded**.

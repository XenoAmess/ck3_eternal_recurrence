# Native71: current conception child-limit inputs, actual 1.20.0.4

Recorded 2026-10-10 / 2026-W41. Exact build is CK3 1.20.0.4,
Steam build 25734779, retained executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
This independent leaf supplies the signed child-limit operand of the M7 pair
provider. It has no shared service, public serializer, build or Game changes.

The exact helper body is `[0x2B94ED0,0x2B950DC)`, 524 bytes, actual runtime
unwind `0x510A168`. Its full body and sole return at `0x2B950DB` are frozen in
[SOURCE-FREEZE.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-49/SOURCE-FREEZE.json).
The contract was frozen before the leaf implementation in
[SOURCE-CLOSED-CONTRACT.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-49/SOURCE-CLOSED-CONTRACT.json).

## Actual role and argument boundary

Continuation 17 holds the complete actual pair provider. Its call at
`0x2B95BAA` supplies RCX=selected Character, EDX=the signed maximum of both
`0x2B94DC0` lineage-tier helper results, R8=first Character, R9=second
Character. Continuation 48 owns those recursive lineage-tier values. They are
not fertility, and the observed fertility values 40000/25000 are not valid
replacements for this table index.

The selected Character was chosen earlier at `0x2B95AB4..0x2B95ADA`: first is
chosen only if first `+0x1C0` is nonzero and its **own** actual highest tier from
`0x28AC690` is strictly greater than second's. Otherwise second is chosen,
including ties. This differs from the origin of continuation 48's lineage
maximum, whose ties retain first. The existing
`ck3_12004_family_abi.hpp::kFamilyHighestTierRva` qualification is reused;
this leaf does not capture, qualify or invoke that callback again.

After the helper, `CMP ESI,EAX` at `0x2B95BAF` and signed `JL` at
`0x2B95BB1` pass when the selected role's native offspring count is below the
limit. A count at least the limit with the actual fifth argument zero returns
the first provider qword zero. Continuation 50 owns the offspring predicate
and count; continuation 55 owns same-query composition. This leaf returns
only the separate signed EAX operand.

## Current operands and exact arithmetic

| Current input | Actual source |
|---|---|
| Base limit | QWORD table pointer `0x545CE80`, then signed DWORD at pointer plus signed EDX times four. |
| Either role `+0x1C0` nonzero | Adds current DWORD `0x5C69E80`; native short circuit is preserved. |
| Either complete ID in the manager list | Slot `0x5C68C50` -> manager `+0xA0` -> DWORD list data `+0x22358`, signed count `+0x22364`; a match adds current DWORD `0x5C69DB0`. |
| Selected `+0x1A8`, list `+0x20` | Counts ordered resolved entries whose QWORD `+0x1D0` is zero. Duplicates and actual fallback behavior are preserved. Above one, adds `(count-1)` times current DWORD `0x5C69D9C`. |
| Selected extended list `+0x50` | Uses its raw signed DWORD count at `+0x0C`; above one adds `(count-1)` times current DWORD `0x5C69DB4`. |
| Four selected role qwords | Only `+0x1C8`, `+0x1C0`, `+0x1B8` all zero and `+0x1B0` nonzero adds DWORD `0x5C69E88`; native short circuit is preserved. |
| Deterministic adjustment | The selected complete ID's actual unsigned32 mixing instructions produce a masked31-bit value, reduced by the native multiplication-high divisor100000. It subtracts one exactly when the remainder is less than current signed QWORD `0x5C69E78`. |

For a null selected extended pointer, both list descriptors use the actual
static fallback `0x5459588`. The `+0x20` list resolves full IDs using the store
slot `0x5C67568`, low24 index, store count `+0x2C`, 16-byte slots with pointer
at `+8`, full-ID comparison at Character `+0x18`, and fallback slot
`0x5C67570`. A stale generation does not become a valid character because its
low24 index matches. The list's living count is distinct from the offspring
count supplied by continuation 50.

All DWORD addition, multiplication and subtraction use mod2^32 arithmetic;
the final EAX is interpreted as signed32. The decrement comparison widens the
nonnegative remainder to signed64 and compares it with the actual QWORD
threshold. No limit clamp, stock define value, probability or default current
value is introduced.

## Independent reader and composition API

The header is
[conception_child_limit_12004.hpp](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-49/conception_child_limit_12004.hpp),
namespace `xar::ck3_12004`, with three independent entry points:

```cpp
SelectConceptionChildLimitRole12004(first_1c0_nonzero,
                                  first_own_highest_tier_raw,
                                  second_own_highest_tier_raw);
EvaluateConceptionChildLimit12004(current_inputs);
ReadConceptionChildLimitForPair12004(bindings,
    first_pointer, first_full_id, second_pointer, second_full_id,
    selected_pointer, selected_full_id, pair_lineage_tier_max_raw);
```

`BindConceptionChildLimit12004` takes exact build/version, module base,
guarded-copy callback and context. The reader verifies both current complete
IDs and the actual helper's 16-byte signature. Selected must be one of those
two roles with its matching complete ID. Root supplies already-qualified own
highest-tier selection in the same application-thread frame. The reader only
copies current inputs; it invokes no native provider, predicate, compiler
dispatch or mutation API.

The result's `value.child_limit_raw` is optional signed32. Missing branch-required
inputs, copy failures, signature or identity failures, malformed collections,
or a collection above the explicit 4096-row query budget leave it unavailable.
They do not become a numeric zero or a partial count. The query retains native
signed indexing, including negative EDX if supplied, with checked address
arithmetic. `inputs` is a complete record only when `status == "complete"`;
unavailable results may contain partial optionals and default internal booleans,
which consumers must not serialize as observed false values.

The manager-list relation is rooted in the complete 91-byte actual
`0x2BAA6F0` wrapper, reused from the existing actual4 span cache without a new
image read. The necessary `0x880430` search's complete 288-byte scalar/SSE
branches prove full DWORD equality and first-match-or-end behavior. The
independent guarded equality reader uses those current IDs directly. It does
not execute the CPU-dispatched library path `0x3F90870`, acquire that generic
chain, or claim a complete delegated-library/native execution tree. That
library boundary does not substitute a missing current value in this reader.

## Focused validation and delivery boundary

One new C++ focused fixture exercises the production reader and pure gate:
[test_conception_child_limit_12004.cpp](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-49/test_conception_child_limit_12004.cpp).
Its 15 cases cover strict and signed64 thresholds, DWORD wrapping, missing
required inputs, distinct current coefficients, duplicate and stale-generation
list rows, current threshold changes, selected-role identity, signature failure,
null-extended fallback, full-ID versus low24 membership, negative signed table
indexing, and native short-circuit reads. The header and fixture compiled with
warnings treated as errors; DLL compile took 2.3587 seconds and the single
fixture call took 0.0100 seconds. The result is
[FOCUS-RESULT.json](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-49/FOCUS-RESULT.json),
**GREEN**. An initial compiler include-path failure executed no fixture; its
original receipt is preserved as `FOCUS-ATTEMPT01-RESULT.json`.

New exact raw image reads were 524 bytes for the reached provider and 288
bytes for its necessary full-ID search, 812 bytes total. The already held
91-byte predicate was reused. No section scan, full-image hash, old FIRST,
Game operation, game EXE output, shared-core mutation or Git operation occurred.
No new pregnancy, birth, probability, pair eligibility, schedule or G2 credit is
claimed. Same-query wiring and actual current output are owned by continuation
55 and Root.

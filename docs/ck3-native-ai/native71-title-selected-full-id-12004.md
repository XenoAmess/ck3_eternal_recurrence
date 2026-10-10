# Native71 actual2C42820 Title selected FullID

The actual1.20.0.4 child reached by `2C4293F` writes a full32 value through
`RCX`; `RDX` is the original selected Title. `RAX` returns the same output
pointer. The readonly implementation reproduces its memory loads, retaining
all generation bits, without invoking the native getter.

The direct CALL entry has no containing pdata row. The next held pdata starts
at `2C428E0`. One cache-first finite capture of `[2C42820,2C428E0)` acquired
192 new bytes: 188 code bytes and four `int3` bytes. All paths close at returns
`2C42883`, `2C4288F` and `2C428DB`; the body contains no CALL.

| Input Title byte `+130` | Native selection | Output32 |
| --- | --- | --- |
| Nonzero | Character registry `5C67568`, fallback `5C67570`; request is original Title `+128`, compare selected `+18` with the entire FullID | Read pointer selected `+1C0`; null yields `FFFFFFFF`, otherwise read pointed object `+1B8` |
| Zero | Title registry `5D1DAF8`, fallback `5D1DAE0`; request is original Title `+12C`, compare selected `+10` with the entire FullID | Read selected Title `+128` |

Both registry paths index by low24 bits, check unsigned store `+2C`, load the
stride16 table object at `+8`, and compare its entire32-bit generation. Only
native null-registry, out-of-bound, null-object and unequal-FullID branches
select the exact fallback. A failed copied read remains unavailable; it does
not manufacture a fallback or the sentinel. A null registry skips the input
FullID load, matching the original instruction order.

`ReadTitleSelectedFullIdAdapter12004(void*,uintptr_t,uint32_t&) noexcept`
accepts a live `TitleSelectedFullIdAccess12004` context and matches38d's child
callback. Success preserves every raw32 output, including `FFFFFFFF`.
Failure preserves the caller output. Optional source metadata contains only
loads visited by that branch; the fallback object's FullID is not queried.

The parent `2C42930`, owned by38d, substitutes original Title `+128` only when
the child output is `FFFFFFFF`, then resolves a Character. This substitution
is outside the child. The meaning of the linked object and output is not
expanded into tax, yield or active state semantics.

The exact source proof is the external
`native71-continuation-20261010/continuation-22c/SOURCE-PROOF.json`;
the finite span SHA256 is
`01ea0535f38635ca1057aea31af076aad1c49762a60287310f01afe01dbfff17`.
The parent95B proof is38d's held source SHA256
`b6f45709084364156e00538b9fc69be9895627a493317c8ad754d0ba6ca39d11`.
New source cases have no main and are delivered to03's single fresh compound
for central10 execution. This leaf does not repeat previous qualifications.

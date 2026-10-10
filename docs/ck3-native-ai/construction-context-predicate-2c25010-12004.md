# Actual 1.20.0.4 construction context predicate `2C25010`

The readonly candidate reproduces the local control and data path of the complete
205-byte actual function `[2C25010,2C250DD)`. It returns a copied optional native
boolean. An unavailable reached input leaves the boolean unknown. This predicate
does not assign a tax, ownership rule, holder transfer or per-building benefit.

## Actual caller and inputs

The retained executable is Steam CK3 1.20.0.4, SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The held complete `2468DA0` source calls `2467660` with original slots at
`2469343`, keeps its returned receiver in RBX, reads the original slots' first
qword into R14, calls `28C2DF0` with that receiver at `2469351`, then calls
`2C25010` at `246935F` with RCX=first pointer, RDX=raw returned receiver and
R8=returned selector object. The owned callee never uses R9. AL is tested at
`2469364`; true branches to `24694BC`, while false sets the aggregate base to
zero at `246936C`.

The API `ReadConstructionContextPredicate2C25010V1` uses the existing 06
`RawReceiverAccessV1` and copied `AggregateRawReceiverV1`, plus the 04 copied
object-only `ReturnedObject28C2DF0Result12004`. It requires the selector's input receiver
to equal the raw receiver and its `frame_key` to equal the unchanged existing
`CampaignRootFrameV1::snapshot_revision`. It reads `[slots+0]` through the same
readonly callback. The caller owns one paused read boundary across all three
leaves; the 06 result does not contain a separate revision token, so comparing
the 04 token alone cannot establish that boundary. The 04
`ResolveReturnedObject28C2DF012004` entry closes only the actual returned-object
path; this predicate does not demand the separate factor consumer's `4D6` BYTE.

## Local source path

1. `2C25026` calls `30A6080(selector object, first pointer)`. True returns AL=1.
2. Otherwise, global `5D1E2F8` selects storage. Nonnull storage reads the raw
   receiver's uint32 full ID at `+B4`, indexes by low 24 bits, reads the object
   pointer at `table + index*16 + 8`, and requires full uint32 equality at
   object `+8`. Null storage, an out-of-range slot, a null object or a generation
   mismatch uses the loaded fallback at global `5C67670`. There is no positive
   ID, signed-ID or sentinel-validity gate. `2C25080` calls `A11CC0` on the
   selected object's collection at `+8D8` with a pointer to a stack qword
   containing the original first pointer. True returns AL=1.
3. Otherwise, `2C2508C` calls `28BFC50(raw receiver)`. It reads the returned
   object's pointer at `+1C0`; a nonnull context supplies DWORD `+1B8`, while a
   null context supplies native `0xFFFFFFFF`. Unequal DWORD bits against the
   original raw receiver's `+18` return AL=0. Equal bits reach `D2BE00` at
   `2C250AF`, then `31C1D10(returned singleton, first pointer)` at `2C250BA`.
   Its AL determines the final boolean.

All five child interfaces are readonly memory-model callbacks. The `A11CC0`
callback receives the qword key by value, not an observer stack address. Missing
callbacks on an unreached branch do not reject an already known result. Missing
copies or models on the reached path never become native false. No callback is
a native getter, initializer or function-address invocation.

## Source and delivery

The pre-read freeze and complete decoded actual source are external:

- `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-21c/SOURCE-FREEZE.json`
- `D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-21c/source01/ACTUAL-2C25010-DETAIL.json`
- Retained canonical cache: `shared-span-cache/new-02C25010-02C250DD.bin` under
  the same continuation root. One source read acquired 205 new bytes; no old
  executable, new pdata, executable census or game invocation occurred.

Required child owners are 37c (`30A6080`), 27c (`A11CC0`), existing 11b
(`28BFC50`), 28d (`D2BE00`) and 29d (`31C1D10`). The local body is closed;
the complete aggregate remains pending their actual readonly adapters and the
single fresh 03/10 compound fixture. Child callback declarations alone do not
close the child sources.

The existing 11b export `ReadPersonFirstTitleVectorReceiverForCharacter12004`
matches the held complete actual `[28BFC50,28BFCC6)` body. Its public receiver
entry only requires enabled exact-build bindings, a module base, a read callback
and the actual nonnull receiver. It does not demand Model, Title, PC or a native
context getter. Both receiver `+1C0` and `+1B8` loads precede the native context
branch, so neither is an extra metadata gate. The adapter accepts
`ready && selected_identity.has_value()` and preserves a copied null fallback.
The later `2C25091` dereference then determines whether this predicate can
continue. `REUSED-28BFC50-CHECK.json` freezes this comparison without another
executable read or another implementation of the existing body.

`construction_context_predicate_new_case.cpp` exports
`ExerciseConstructionContextPredicate2C25010NewCaseV1(std::string&)` without
`main`. Its nine new cases check local branch order, full-generation registry
matching, fallback, native null-context/-1 equality, unavailable child handling
and copied frame attribution. Synthetic child values validate this local leaf's
control flow; they do not qualify the child models or native gameplay. No build
or test was run in lane 21c.

The light package stays within the admitted 4 MiB scope. The current source and
candidate inputs are protected for this active compound, with review no later
than `2026-10-17T00:00:00Z` under storage policy 1.0.0. No indefinite historical
retention or heavy-write admission is claimed.

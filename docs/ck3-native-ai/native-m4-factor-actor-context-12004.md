# M4 factor actor context, actual CK3 1.20.0.4

2026-10-10. The exact executable is Steam25734779 /
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
This package owns only actual **B17C70..B17D46 /214B**. Its existing named
cache has complete decode; no executable, game, SDK, allocator or initializer
is called. Candidate source remains external under continuation-08c.

## Actual reached role

The held parent **2B9CBA0..2B9CDFC** calls B17C70 at **2B9CBF9**, only when
the raw selector byte read from `28C2DF0`'s returned object+4D6 equals5. Its
RCX is caller-owned local context `RSP+70`; its RDX is saved factor-entry RDX.
The next C86670 call receives that same context, index4E, and a signed Q64
output. The byte5 has no new named government/resource meaning in this lane.

Parent evidence is continuation-05c/ACTUAL-2B9CBA0-SOURCE.json and its selected
instruction text. Own evidence is continuation-08c/ACTUAL-B17C70-SOURCE.json,
SHA-pinned to the existing new-00B17C70-00B17D46.bin and metadata row
`[11631728,11631942,84975180]`. No old ordinal or guessed version shift selects
the function.

B17C70 reads **saved receiver+18 as uint32**, zero-extends it into a qword
at scope+8, writes scope DWORD0=0 followed by WORD0=4, and writes DWORD10=-1.
The whole existing typed actor scope footprint is **0x168 =360 bytes**. Tag4
and the receiver's identity are retained as actual raw values; generation bits
are preserved. The existing exact4 Core Character storage/identity layout and
the realm-law typed actor constructor contract provide the Character identity
round-trip algorithm, not another active getter invocation. The supplied factor
receiver itself must resolve from its fullID storage entry; a played-character
pointer is not substituted.

Its only reached child is **CALL8895D0 at B17C98**, RCX=scope+18. Child48 owns
that source and its necessary actual virtual-slot semantics. Own outer writes
after the call are:

| Scope offsets | Actual value/source |
| --- | --- |
| 100q,108q,128q,130q,140d,148q,150q,164w,166b | Zero |
| 110q,158q | Image+54DE270 |
| 118q | Image+448D1F8 |
| 120q | Image+448D268 |
| 138q | Image+54DE278 |
| 160d | FFFFFFFF |
| 8q, last identity store | Zero-extended saved receiver+18u32 |

Child48 has now closed its constructor and necessary actual virtual-slot
semantics, with source frozen independently of this parent's214B capture.
Its final defined ranges are child-relative **[0,20) and[E0,E8)**,40 bytes:
data=self+20, capacityDWORD8=8, countDWORDC=0, allocator=self+18,
vptr18=image+448D2A0 and backingE0=image+54DE2E0. The two self-pointer operations
are `{offset0,target20}` and`{offset10,target18}`. Its actual first release
path receives null and performs no writes; the nonnull free branch is excluded
by the constructed arguments. No generic allocator/free tree is adopted.
Unwritten padding, including root4..8,14..18 and167,
is explicitly undefined; zero-initialized software storage is not evidence
that native padding was written as zero.

## Read-only equivalent interface

`m4_factor_actor_context_12004.hpp/.cpp` takes actual `context_receiver`, exact
module identity, and **uint64 frame_key copied directly from
CampaignRootFrameV1.snapshot_revision**. The existing construction mailbox
assigns that from expected_snapshot_revision. It is not a hash, public revision
conversion or actor binding. Existing outer before/after full-frame comparisons
and other context/province/definition identities stay with their owners.

The three-argument production `ReadM4FactorActorContext12004` directly calls
child48's pure `ProjectM4FactorActorInnerInit12004`; it accepts no fabricated
external complete flag. The explicit-inner overload remains a partial/join
interface and focused fixture entry. Both use the supplied read-memory callback for the
receiver+18 and actual Character storage identity round-trip. It applies the
source-defined stores into its own stable 0x168-byte buffer. Child48's inner
packet retains raw bytes, a defined-byte mask and typed self-pointer patch
operations; those pointers are rebased into final stable storage+18. Actual
outer writes take priority over child writes at overlapping tail positions.
No native constructor, allocator, evaluator, destructor or action is invoked.

The output cannot be copied or moved while its raw self pointers are in use.
Its owned buffer is a **source-equivalent software scope**, never an observed
caller stack scope. An input requiring an actual original dynamic-context
witness must carry that witness independently; this constructor projection
does not invent one.

The return value means **actual actor header available**. Full
`complete_source` becomes true only when the required same-image/same-frame
inner source is complete. The two states deliberately differ: child12's actual
37542D0 source proves that the constant/zero4E branch does not read the inner
state, so it may consume the qualified root prefix without waiting for unused
initialization. Its dynamic-expression branch separately requires the complete
context and appropriate supplied context input. Neither state changes an action
gate or pretends a measured construction outcome.

## New focused cases and next integration

The external no-main case TU exports
`RunM4FactorActorContext12004NewCases()`. Six authored cases cover full-generation
zero-extension and actual receiver identity, stable self-pointer rebasing with
outer-store precedence/undefined padding, incomplete inner source, different
frame input, storage object mismatch, and unqualified image performing no read.
Synthetic child overlays test this join protocol only; child48's own cases
qualify its actual pure projection in the shared compound.

No local compile, test or prior qualification is run. **First execution belongs
to 03/10's one connected new-case compound.** Candidate paths and source evidence
are listed in continuation-08c/RESULT-08C.json. Child12 consumes the header by
const reference; child05 consumes only its same-receiver/same-frame signed4E
packet. Root owns source adoption, shared build/serializer/Driver and the sole
runtime. All Game/SDK requests and Git mutations in this source package are0.

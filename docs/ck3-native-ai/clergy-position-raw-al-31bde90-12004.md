# Base clergy position raw AL, actual1.20.0.4

Actual `31B4A10` reaches `31BDE90` at `31B4A70` on the existing occupied-seat
mode0 current base clergy query. ECX is the Task `+44` full uint32 owner ID,
RDX is Position `+2377`, R8 is Position `+20A8` and R9 is the current null
tooltip. The parent tests AL for nonzero; it does not require an AL value of1.
This leaf provides the literal-input raw byte to26's existing base packet.
It creates no CanFire/query, frame, native binding or policy/yield inference.

The complete actual body is `[31BDE90,31BE10B)`, 635 bytes, runtime row
`[52158096,52158731,86921312]`. Its finite SHA-256 is
`0acab34471b2a8f249031abeec4b7b4ba67de56491afca86f17ddb49c1b73333`.
The exact build is1.20.0.4 / Steam25734779, held executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The parent was reused from `continuation-26c/MODE0-BODY-SOURCE.json`, whose
exact packet pin and literal setup are frozen in `continuation-06e/SOURCEPLAN.json`.
Only the own635-byte new span was read; no child body was acquired by06e.

## Actual raw byte branches

`31BDEC3` zero-extends BYTE `[RDX]` into EAX. If it differs from1,
`31BDEC8` goes directly to the epilogue with that original byte in AL.
The R8 member read and every scope/predicate call are skipped. Values0 and
2..255 remain raw values; the existing parent interprets only zero/nonzero.

When the byte is1, `31BDECE` compares DWORD `[R8+4C]` to zero. Equality
goes directly to the epilogue with original AL1. This field is recorded as
raw `predicate_4c_raw_u32`; this body does not authorize a semantic name or
a signed/positive-count rule for it.

For a nonzero DWORD, `31BDEDD` calls actual scope initializer `889F60`
with RCX=&stack `+70`. The caller then overwrites scope WORD0 with4 and
scope qword8 with the zero-extended original ECX full uint32 owner ID.
It imposes no extra positive/high-bit owner-ID gate. `31BDEFA` calls actual
`372DF10` with RCX=the original R8 input and RDX=&that initialized scope.
The raw returned AL is saved in SIL at `31BDEFF`.

Current R9 is null. `31BDF05` skips the complete tooltip/formatting arm.
After ordinary scope cleanup, `31BE0E4` restores EAX from saved SIL. The
saved raw byte and complete cleanup effects are separate facts. This leaf
qualifies the byte only and does not claim that a constructor, evaluator,
cleanup, appointment action or current gameplay outcome was executed.

## Read-only composition

`ClergyPositionRawAlOperands12004` preserves the literal full ID and pointer
arguments. `ReadClergyPositionRawAlInputs12004` reads the original byte and
only reads input `+4C` when that byte is exactly1.
`ReadClergyPositionRawAl12004` returns optional raw AL, an actual branch and
an unavailable reason. A missing value differs from a known0. It uses the
existing `Bindings::ReadMemory` and `read_context`; the father retains the
current query envelope and owned Task/Position/full-ID checks. This leaf
does not create another clock/frame or add a native guarded-read fallback.

For the predicate branch, `ClergyPositionRawAlChildReader12004` accepts only
an independently source-closed read-only `372DF10` resolver using the same
read callback/context, actual input pointer and logical WORD4/full-ID payload.
The child's actual ABI cannot be bound directly to this typed callback.
The full default scope shape comes from15f's actual `889F60` defined-mask
provider `ProjectOwnedRootScopeInitializer889F6012004`. Its literal extent
is `0x167` through the last actual write, with155 defined bytes. It leaves
holes unknown and rebases self pointers `+18 -> +38` and `+28 -> +30` only
into the caller-owned recipe buffer. The caller then applies the actual
WORD4/QWORD zero-extended owner stores. This recipe buffer is not an observed
native stack or a new frame. Existing09d/42c/63c supply the shared `372DF10`/`372E000` truth
source; a dynamic returned byte without an actual current witness remains
unavailable. An initialized0, slot address, static schema or callback ACK
is not a predicate result.

Eleven new no-main cases cover only06e's literal branch selection, read skips,
zero/high-bit forwarding, known0/noncanonical nonzero bytes and missing child
source. Synthetic child values test this interface and do not qualify the
initializer or shared truth source. The exported function returns failure
count, so0 is success. Father26 owns the one current-base connected main and
central10 owns execution; M4/ransom cases and old clergy qualification are
not replayed here.

This small D packet is an active source/adoption input under storage policy1.0,
with a 48-hour review. Re-evaluate the derived packet after source adoption
and central results, preserving only inputs still required by current callers
or unresolved source questions.

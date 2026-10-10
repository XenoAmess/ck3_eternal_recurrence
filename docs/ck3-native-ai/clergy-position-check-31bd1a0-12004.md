# Current base clergy: literal31BD1A0 raw AL

The existing occupied-seat clergy base query calls `CanFire` with mode0 and
nulltooltip. Its `31B4A10` branch reaches `31BD1A0` at `31B4A96` only after
two preceding helpers pass. The new software leaf reconstructs closed
branches of this exact call. It does not issue a query or call any native
validator, constructor or evaluator. Existing aggregate `native_can_fire`
does not prove that this child was reached or that it returned false.

## Source and actual operands

Exact CK3 1.20.0.4/Steam25734779 image SHA:
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The complete actual body is `[31BD1A0,31BD602)`,1122B, body SHA
`340a6117e616e95e8f154a67488e231260939c5ddc83426983c3592908b15183`.
It was absent from named retained caches and acquired once through the
Root-shared D O_EXCL/new-only finite mapper. No old executable was read.

The caller supplies `RCX=QWORD[QWORD[Task+18]+40]`(Position),
`EDX=Task+44` raw32 ownerFullID, `R8=&Task+28`, and raw `R9D` from
`Task+30 != Task+40`(incumbentFullID). Stack argument5 is the actual RIP
literal pointer `module_base+48C8710`; argument6 is zero. Every operand stays
literal. The different `CanReassign` operands/literal are not substituted.
Parent26 owns current Task/Position/fullID/frame qualification.

## Closed branch relation

At `31BD1DE`, the mandatory `31BDDA0` child receives raw ownerFullID in ECX,
`Position+2378` in RDX, and `Position+2178` in R8. The production software
leaf calls20f's guarded readonly implementation with those exact operands.
Its availability is computed from its actual byte/DWORD reads and branch;
no supplied ready Boolean is accepted.

If the initial raw AL is nonzero and incoming R9D is zero, current
nulltooltip jumps to the false epilogue: own raw AL is0. No `Position+2338`
or date input is needed. Noncanonical initial bytes2..255 stay visible and
are tested for nonzero without masking the ownerFullID.

Otherwise, DWORD `Position+2338==0` returns own raw AL1. This branch needs
the actual DWORD read and has no other child demand. Failed reads remain
unavailable. An initial child requiring its dynamic `372DF10` stays
unavailable until that child's actual source and result are joined.

## Reached nonzero numeric frontier

When `Position+2338!=0`, the body reads QWORD `image+5C68C50`, then the
pointed clock DWORD+8 and incoming Task+28 DWORD. It subtracts with DWORD
wrap and divides the signed32 result by24 with truncation toward zero.
The leaf preserves these raw inputs and the source-equivalent integer.

This branch constructs a root scope (`889F60`), writes WORD kind4 and QWORD
zeroextended original ownerFullID, initializes3736040/3735F90 locals, obtains
the Position+18 name through3F79B00/3F79DD0, and calls `A0F0B0` at31BD3E4
with RCX=`Position+2280`, RDX=`{&actorRoot,0}`, R8D=0, and R9=named lookup
state. Cleanup of the constructed locals precedes the signed comparison.
Current nulltooltip excludes later formatting, not this numeric path.

The caller's `Position+2338` is exactly `A0F0B0` expression+B8. Thus this
nonzero path selects that helper's dynamic mode. Its closed static+B8zero
constant at+98 cannot replace the needed result. Actual40e source is reused;
dynamic37540B0,37498A0/virtual producer,3755500 and named/context cleanup
contracts remain the specific next source entries.15f's closed889F60 defined
mask is retained for that future join. No dummy native stack, constant,
ready flag or aggregate CanFire value is substituted.

Once the needed source-qualified signed EAX and cleanup relation are joined,
the own-body relation is exact: signed elapsed/24 >= signed EAX returns1;
otherwise current nulltooltip returns0. The current production reader leaves
raw AL unavailable on this frontier and records its concrete next functions.
The assigned child owners continue those source trees under02; this package
claims neither whole-function capability nor a live positive.

## Parent callback and validation

`ReadClergyPosition31BD1A0Callback12004` matches26's final software callback:
`bool(void*,uintptr_t Position,uint32_t ownerRaw,uintptr_t Task28,uint32_t
comparison,uintptr_t staticArg5,uint8_t&rawAL) noexcept`. Its context carries
only the existing guarded read adapter and exact image/module identity. It
returns true only when the computed result is available with raw AL, and
leaves output untouched on false. There is no native fallback, new frame,
capture epoch, resolver, CanFire call, CanReassign call or gameplay gate.

The no-main export `RunClergyPosition31BD1A0NewCases12004` supplies13 new
cases for literal operands, high fullID bits, read order/demand, raw byte
preservation, unknown child/mode, DWORD wrap/signed division, source image,
literal/nulltooltip boundaries, and the exact parent callback's availability.
Worker compile/test runs are zero.26/02 integrate the new connected clergy
compound and10 executes its sole first acceptance; prior08c/08d checks are
not replayed. The current source gap and next entries remain explicit.

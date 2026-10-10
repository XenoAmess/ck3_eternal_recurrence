# Shared clergy condition at 31BDDA0

The read-only helper preserves the raw AL returned by the actual
31BDDA0 body. It reads the literal RDX byte first. Any nonzero byte is
returned unchanged, including 2 through 255, without reading the support
or resolving the owner. A zero byte then demands DWORD[R8+4C]; zero
returns raw AL=0. Unread inputs remain unavailable. A nonzero DWORD
requires the distinct condition helper at 372DF10 and currently retains
that dependency explicitly.

The exact build is CK3 1.20.0.4 / Steam 25734779, executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The retained runtime row `[52157856,52158082,86921268]` covers
`[31BDDA0,31BDE82)`, 226 bytes, through both reachable RETs. One finite
cache-first acquisition produced raw SHA-256
`294c62224bdd23df2ec71cb915ab48e05955df1eab9e6556aadd620a71b7eef2`.
[The frozen own-source contract](D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-20f/SOURCE-CONTRACT-OWN-FROZEN.json)
predates the candidate header and implementation.

Two callers use this same function with different literal operands:

| Caller and CALL | ECX raw32 | RDX | R8 |
| --- | --- | --- | --- |
| 31B4810 at 31B483C | DWORD[Task+44] | Position+2374 | Position+1E38 |
| 31BD1A0 at 31BD1DE | Original owner ID saved from EDX | Position+2378 | Position+2178 |

The first Position is loaded through QWORD[Task+18], then QWORD[type+40].
The second is the original Position receiver. These operands are retained
separately. The helper's ECX is a raw uint32 value; it does not qualify an
ID or return frame validity. The existing 26 current base producer owns
the paused frame, exact build, IDs, Task/Position identities and final
consistency checks. CanReassign has its own literal operand setup and
does not supply this helper's result.

On the nonzero DWORD branch, the native body constructs a local scope
with 889F60, then writes WORD(scope+0)=4 and QWORD(scope+8)=zeroextended
raw ECX. It calls 372DF10 with RCX=the original R8 support and RDX=that
scope. MOVZX EBX,AL stores the condition's exact raw byte. After applicable
cleanup returns normally, MOVZX EAX,BL restores it. Own-body decoding
does not close the condition helper's semantics or cleanup allocator
effects. No native callback is used as a fallback. The retained 15f
889F60 initializer source supplies a separately frozen local-scope
definition; later tag/owner writes remain this caller's contribution.

The production entry `ReadClergyShared31BDDA0RawAL12004` reuses
`Bindings::ReadMemory` and the existing read context. Its result includes
the original raw ECX/RDX/R8, optional copied byte/DWORD, optional raw AL,
computed availability, branch and reason. It has no caller-provided
readiness switch. Pointer addition and read-width overflow are checked.
The +4C read is exactly four bytes, and the nonzero-byte branch does not
demand an otherwise unread support pointer.

Nine new no-main cases cover noncanonical bytes, exact read widths,
short-circuit demand, unread versus zero, and address overflow. They are
authored for 26/10's single future connected compound and have not been
compiled or run here. No old 20 qualification, Game/SDK call, new query,
validator, full-ID resolver, Git operation or Z write is performed.

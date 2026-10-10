# Actual 37498A0 fixed Q64 to signed DWORD conversion

This source-owned leaf applies only to CK3 1.20.0.4 Steam build 25734779,
held executable SHA-256 `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The actual function is `[37498A0,3749A69)`, 457 bytes, source span SHA-256
`d29b7c86f001527c99e006fa515f56d706c504ff43137f3f57ef4ab105cdd701`.
The complete assigned extent was captured once into the shared D cache. The
callee and the exact caller were frozen before this leaf was written.

At parent A0F185 the provider receives `provider+8`, a pointer to the temporary
QWORD, the unchanged pack, literal R9 zero, and the original named tuple as its
fifth argument. A0F18B loads that temporary QWORD value into RCX. A0F188 forwards
the original named tuple to RDX. A0F18F calls this conversion; A0F194 copies EAX
into EBX for the parent's numeric return. This conversion input is a signed
Q64 value. The virtual provider's returned RAX is not the operand used here.
The historical source capture's phrase “rawvariant pointer” is corrected in
`SOURCE-FROZEN.json`; its original record remains unchanged.

The exact native guard is the unsigned, wrapping comparison
`uint64_t(raw) + 0xC35000000000 <= 0x1869FFFFE7960`. It admits the signed raw
interval `[-214748364800000,214748364700000]`. Its taken branch goes directly
to 3749A20, rounds by adding -50000 for negative inputs or +50000 otherwise,
and divides by 100000 toward zero. Half values round away from zero. The
native multiply constant, arithmetic shift, and sign correction implement
that division on this interval. The adjusted value fits int64 and the output
fits int32; the projection does not clamp or saturate.

The taken branch reads no original tuple data and calls no child function.
The callee does not read its entry R9. A null tuple and full64 revision zero
therefore remain valid carriers for this conditional branch. The shared
exact-build binding must hold. The projection preserves the caller's raw
optional Q64, tuple identity, module identity, and unchanged revision, and
returns an optional signed EAX with a concrete unavailable reason.

The raw Q64 must be supplied by an exact actual provider-output witness owned
by the parent consumer. Missing output stays unavailable; this leaf performs
no query, dynamic virtual evaluation, native conversion, or guessed tag/zero
substitution. Its source-ready result qualifies this conversion alone and
does not prove the upstream provider or the whole dynamic numeric path.

Outside the native guard, the function reads tuple data and can reach logging,
TLS/global state, allocation cleanup, and an abort path. The leaf keeps the
raw input and leaves EAX unknown there. Literal child targets were reported
to the coordinator without further captures. Even a value whose mathematical
rounding fits int32 must remain unknown when the exact native guard fails.

This packet adds a pure production header and source. It makes no repository,
Git, game, native evaluation, test-tree, compiler, or fixture-run changes. Its
conditional consumer is the actual A0F18F parent branch; the coordinator owns
any later source-connected qualification. Source retention is seven days
pending active consumer closure; small handoff records are reviewed at 180
days under storage policy 1.0.0.

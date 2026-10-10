# Compiled expression variant and the actual A0F2D6 caller

This companion reuses the retained 842-byte CK3 1.20.0.4 source at
`[03755500,0375584A)`, SHA
`76665f652651c1163f17a684ff8ada07d2b037fa3ef25e1c88cdcbce91089115`.
Its image is fixed to Steam25734779, executable SHA
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
No new source-body read or acquisition is required.

The actual `A0F0B0` caller reaches `A0F2D6 CALL3755500` with RCX equal to
expression `+8`, RDX pointing to its raw output variant16, R8 equal to the
existing pack, and R9 equal to the original named tuple. Its fifth BYTE and
sixth DWORD arguments are both zero. This is a distinct source binding from
the prisoner `9D7252` descriptor call. The old prisoner API and its already
qualified cases remain unchanged.

`ReadCompiledExpressionVariant3755500Readonly12004` uses the common generic
`PietyPriceNumericAccess12004` and copied pack operands. It requires no prisoner
role IDs, context metadata, new clock, or nonzero revision. The unchanged
full64 revision is copied to the result. A copied source shape does not create
a physical native stack address. If a physical pack address is supplied, the
primary alias is read and checked against the supplied copied alias.

The actual source demands differ by branch:

| List count at `+C` | Returned conditional value | Demanded input |
|---|---|---|
| Zero | Known tag WORD0 and payload QWORD0 | Count only; no pack or named tuple |
| Negative, with actual skip DWORD0 | Initial primary root16 | Primary alias and its root16; no other pack alias or named tuple |
| Positive | Unavailable dynamic value | First row receiver, virtual type-mask `+30` and value producer `+20`, copied pack, selected tuple |

For a positive count, `37555D5..37555E7` selects the inline list `+70` 32-byte
tuple if its first QWORD is nonzero. Otherwise it selects R9 and copies those
32 bytes into the real value-producer context. R9 therefore participates in
the numerical input path when that fallback is selected; this source does
not permit a blanket diagnostic-only label. The two actual virtual targets
remain unclosed. Their identities and copied input witnesses never stand in
for a returned variant or a known tag0.

The adapter recopies the demanded count and root16, the physical primary alias
when present, and selected tuple bytes when available. These are copied-query
bookends, with before/after bytes retained; equality grants conditional input
consistency, not native invocation or freshness. A changed or unavailable
bookend cannot publish a known raw variant. The positive result remains
unknown even when its copied input bookends agree.

The parent consumes tag1 using its own literal signed high-half multiply by
`29F16B11C6D1E109`, SAR14 and sign correction, then takes low EAX. That numerical
conversion belongs to `A0F0B0` and is not replaced by a guessed scale here.
Other known tags follow the parent's flag/cleanup/fallback source. Missing
tags cannot select that fallback. No native provider, script evaluation,
cleanup, old case, QA, build, or Game is executed by this companion.

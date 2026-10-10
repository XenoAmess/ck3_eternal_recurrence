# Actual 31C1D10 copied-pointer predicate

The source is reached by the literal `2C250BA CALL31C1D10` in the 205-byte
`2C25010` context predicate. The parent passes the copied `D2BE00` singleton
return as RCX and its first-pointer operand as RDX, then consumes AL. This leaf
does not invoke the singleton provider, initialize it or assign a realm policy.

The actual logical instructions run from `31C1D10` through `31C1DFD RET`
(238 bytes). The five cache-first finite reads total 240 bytes; the last two
bytes are INT3 padding. No cached `.pdata` row contains the entry. All literal
branches are inside the closed span and there are no native child calls.
The held executable identity is
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
Logical instruction bytes SHA-256 is
`58a7e458dec6b58d97970d5dda6b2667f841857141e3ac1b276eab2af67485d1`.

The function hashes all eight bytes of the RDX pointer value with FNV1a32,
least significant byte first (`811C9DC5` seed, `01000193` prime, DWORD wrap).
It loads singleton `+F08` entries and `+F14` signed DWORD mask. Both the hash
and mask are sign extended before the initial index AND. Each record occupies
16 bytes, with control at `+4` and the complete pointer key at `+8`; the stored
hash is not read by this predicate.

The byte probe distance starts at one. Initial control below one skips the
key comparison. Otherwise a mismatch advances one record, increments the
distance with byte wrap and continues while distance is at most the next
control byte. The native loop does not wrap the record address by the mask.
On a miss it reads singleton `+F18` tail byte and selects the record at signed
DWORD-wrapped `mask + tail + 1`, widened to signed64. Both a match and a miss
reach the final selected-control reread. AL equals `control != FF`; matching
a key alone does not imply true, and a malformed non-FF end marker retains
the source's true result.

`ReadPointerKeyPredicate31C1D10V1` uses the existing 06 copied-memory access.
The caller supplies the same admitted frame's singleton and first-pointer
operands. `value == nullopt` denotes missing reads, an unrepresentable copy
address or exhausted observer probe budget. This is distinct from known false
AL. Zero and high-bit pointer keys receive no extra native validity gate.
Negative in-range signed indices remain supported. Wrapped copy addresses
are partial rather than relabelled as a native false branch.

The default 4096-key-read limit is an observation budget, not a native table
capacity or domain rule. Known miss branches can complete without a key-read
budget. The 12 new cases have no main and export
`RunPointerKeyPredicate31C1D10FreshCases12004` for 03/10's one fresh connected
compound. This leaf has not independently compiled or executed them. Old
FullPerson/Army arithmetic and native qualification are not replayed.

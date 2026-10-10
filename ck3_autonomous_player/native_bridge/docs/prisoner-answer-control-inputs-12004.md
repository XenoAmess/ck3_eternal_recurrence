# Prisoner answer control inputs, exact 1.20.0.4

This new read-only child package supplies the two control inputs reached by
`307BD70`: the complete-DWORD membership result from `2BAA6F0` and the
conditionally available flag bytes returned through `A75D00`. Its public entry
is `ReadPrisonerAnswerControlPackage12004`. It returns the existing
`PrisonerAnswerByteChild12004` and `PrisonerAnswerDebugFlags12004` carriers for
`ProjectPrisonerAnswerModeBranch12004`; the selected query remains owned by the
parent package. No native helper, initializer, membership routine or TLS getter
is called.

The input frame is the existing `PrisonerQuoteSourceFrame12004`, including exact
executable SHA, module, native revision, query sequence, proof epoch, date, full
role IDs, definition, interaction context and original scope. The input key is
the actual copied `interaction_context+2D8` DWORD. The parent still verifies the
carrier's complete frame, actual callee and exact key before consumption.

## Membership source and copied data

The retained actual parent body `[307BD70,307C016)` calls `2BAA6F0` at
`307BDD8` after placing the context DWORD in ECX. The exact child body is
`[2BAA6F0,2BAA74B)`, 91 bytes, SHA-256
`ceee3223e68d7452f54785295f4daa9a959954d469f54626804730d55f4d10cf`.
It reads `module+5C68C50` as a QWORD instance, `instance+A0` as the collection,
then the QWORD list pointer at `collection+22358` and signed DWORD count at
`collection+22364`. At `2BAA71F` it calls `880430(begin,end,&copied_ECX)`.
The returned end pointer is converted to zero before the nonzero AL test.

The already closed source contract for `[880430,880550)`, 288 bytes, SHA-256
`f94421877d87cc27d31cc7585a20fc1047eaac80b7c8b7aac2f58811367260b6`,
establishes scalar/SSE full 32-bit equality and the first matching pointer or
end. This package reuses the separately authorized guarded software equality
reader contract. It does not execute that library routine or claim a closed
generic CPU dispatch tree.

The reader preserves complete DWORDs, order, duplicate values and the actual
argument. A copied first match determines AL=1; absence is available as AL=0
only after observing the complete list. A present empty list is distinct from
missing data. A missing key, missing required object/count/element, negative
count, excess read budget or overflowing extent remains unavailable. Zero and
all-ones keys are copied values, rather than missing input sentinels.

## Conditional debug source

The retained parent calls `A75D00` at `307BDF5` before reading BYTE+0 and at
`307BE65` before reading BYTE+1. Its exact child body is `[A75D00,A75E2F)`,
303 bytes, SHA-256
`a0565a1d3cc53abd5a57d1e9f203cc5d89c64628cc629d90a7911773a71fd5e9`.
It compares the signed DWORD guard at `module+5D1E370` with a literal signed
DWORD epoch from the current thread's `GS:[58]` first TLS block+10. When
`guard<=epoch`, the direct return at `A75D26` returns `module+5D1E330`.
When `guard>epoch`, an initialization and registration path is reached.

`PrisonerControlTlsEpoch12004` therefore carries a separately supplied literal
epoch, its complete current frame and the fact that it was copied from the
current query thread. Revision, query sequence and collection proof epoch are
never converted into that TLS epoch. The copied object/guard/flag fields remain
observable raw inputs; exported flag bytes require the same frame, exact static
object identity and the original signed direct-return comparison. Missing
epoch or a reached initialization route leaves exported flags unavailable.
Initialization is not reproduced. Each flag byte remains separately optional,
because the parent demands BYTE+1 only on its corresponding branch.

The combined entry reads these debug fields only after membership AL is known
nonzero. Father 35 currently has no copied literal TLS epoch, so its membership
input can be closed while a reached debug branch remains unavailable. This is a
current input boundary, rather than a guessed zero flag.

## Parent result and validation boundary

The two child carriers retain their actual callees and are consumed by the
existing parent selection. Debug BYTE0 nonzero yields parent AL0; BYTE0 zero
and demanded BYTE1 nonzero yields parent AL2. Reporter effects are independently
qualified by their owners and remain separate from the numerical result.

`RunPrisonerAnswerControl12004NewCases()` is a new no-main fragment with 16
cases. It exercises these new readers and joins their outputs through the
actual parent projector, including source width, unavailable data, signed TLS
comparison, exact operand/frame binding and separate reporter effects. The
fragment is authored and unrun. It belongs to father 35's single
`--prisoner-selected-quote-source-connected-12004` compound; central 10 performs
the first compile/run together with these new source files and the parent.

The exact source packets, freeze contract, dependencies and candidate pins are
external under `continuation-05d`. Source acquisition reused 394 child bytes
from existing exact caches and read zero new executable bytes. No repository,
Git, game, shared report or prior factor/film package was edited. This candidate
does not establish runtime execution or live quote availability.

# Prisoner selected-query mode0 scalar, actual1.20.0.4

Actual helper `307C340` is reached at `307BEE9` by `307BD70` in mode0.
The call uses RCX=current owned interaction context and RDX=&local scope
output. The parent reads the qword through the returned pointer. This leaf
records actual raw score inputs and conditional output; it does not invoke
the helper, a scope constructor, numerical evaluator or cleanup.

The own source is `[307C340,307C435)`, 245 bytes, actual runtime row
`[50840384,50840629,86863024]`, finite body SHA-256
`efb624a3ee86a574fec6d1d6a3d03fdb9d0dac20a03bdb4595fc1d3a18ad459f`.
The exact build is1.20.0.4 / Steam25734779, held executable SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The caller was reused from
`continuation-39c/actual-helper-source/answer-mode-branch-307BD70.json`;
its packet/body pins and actual call setup are in `continuation-06d/SOURCEPLAN.json`.

## Actual branches and owned inputs

`307C353` reads context DWORD `+2E8`. If it is `FFFFFFFF`, the helper writes
qword `10000000` directly through the original output pointer. It skips the
`+2D8` read and every child call. Otherwise `307C362` compares context DWORD
`+2D8`; equality takes the same constant branch. Raw uint32 identity, including
zero or high-bit generations, has no extra positive/sign admission here.

The remaining branch calls `373ACF0` at `307C377` with output scope at
stack `+20` and input scope=context `+8`. After this copy, it writes root
WORD4 and qword payload=zero-extended uint32 context `+2E8`. It then calls
actual `3761680` at `307C3A4` with RCX=`[context]+18C8`, RDX=original scalar
output and R8=&copied scope. Mode1's separately held `307C440` uses `+1918`;
that block cannot be substituted for mode0's source.

The held actual `3761680` wrapper is `[3761680,3761771)`, 241 bytes, row
`[58070656,58070897,87373940]`. Its retained source packet is
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261007/upstream-build-migration/prisoner/current4-ransom/named-map01/support_owner_layout-DETAIL.json`,
packet SHA-256 `8c8974c3b5e6764dd9e2d065a2222c6cbda5225d972cfc2ca1855c2dbda39a4b`.
Only its actual new instructions were consumed; it was not captured again.
It calls `3761780` at `37616F0` with the original score block/output and
internal aliases `{copied scope,null,copied scope,&support118,global5D1DADC byte}`.
The same actual score body supplies the raw base at block `+28`, ordered
pointer rows at `+30` and signed count at `+3C`.

Each source virtual slot30 call receives the existing qword output pointer.
A source-qualified occurrence post value replaces the preceding output;
there is no generic addition of modifier values. A virtual address and a
missing post value remain different facts. The raw reader reuses35's same
score-body input reader; this leaf's projection binds the caller block to
`definition+18C8` instead of calling the fixed `+1918` recipient projector.

## Conditional output and integration

The leaf reuses `PrisonerQuoteReadOnlyAccess12004` and
`PrisonerQuoteSourceFrame12004`. The existing selected-query frame's
`original_scope_identity` is context `+8`; it does not identify the newly
copied scope or the internal stack aliases. The copy's root/payload and the
score aliases require their own source or actual same-query witness.

`ReadPrisonerMode0ScalarInputs12004` reads the owned inputs.
`ProjectPrisonerMode0Score12004` exposes the raw score projection when every
ordered occurrence has a matching source post transition.
`ProjectPrisonerMode0Scalar12004` exposes the constant branch immediately.
For the scoring branch it keeps the projected score separate from the final
returned qword until a matching same-frame final-out witness supplies the
copied-scope facts and complete reached source effects. A source-defined
copied shape has no physical clone identity and no observed native clone; it
does not borrow the original scope as a fake clone. An actual native final
value remains the father's independent observation and is never copied back
into this conditional source projection. This API performs neither operation.

Actual outer cleanup calls `889700` on stack `+138`; if stack `+120` is
nonnull, it calls `889780` and virtual slot10. A further nonnull pointer at
scope `+18` triggers another virtual slot10. These are actual source edges,
not proof by destructor names that the output is unchanged. Clone source is
owned by43c and outer cleanup source by44c; unresolved reached effects keep
the scoring branch's final output unavailable. The held wrapper's own
support/init/cleanup facts likewise remain independent of its numerical body.

Twelve authored no-main cases cover this leaf's real constant conditions,
18C8 binding, zero extension, raw negative/zero values, output replacement
and missing/mismatched witnesses. Synthetic witnesses in those cases do not
qualify constructors or cleanup. Father35 includes the new cases in its one
connected selected-quote compound; central10 alone executes
`--prisoner-selected-quote-source-connected-12004`. No prior qualification,
Game result, ransom outcome or material benefit is claimed here.

The packet is a small active source/adoption input under storage policy1.0,
with a 48-hour review. After adoption and central validation, re-evaluate its
derived copy against current references and unresolved source questions.

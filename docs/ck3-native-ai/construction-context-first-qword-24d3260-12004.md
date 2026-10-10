# Actual context first QWORD at24D3260

This leaf supplies the first signed QWORD consumed by the actual
`2C399C0` parent. It reads the already-qualified context object and exact
loaded registry inputs; it does not invoke the native child or assign a
tax/yield name to its fields.

The exact source is CK3 1.20.0.4, Steam25734779, EXE SHA-256
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.
The parent packet is
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-20c/source/ACTUAL-02C399C0-DETAIL.json`.
The closed child proof and generated graph are
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-30d/SOURCE-CLOSED-CONTRACT.json`
and that directory's `research-graph.md`. The graph comes from the same
`research-plan.json` record; unknown producer edges remain explicit.

The held runtime-function table contains no row for24D3260. The actual
parent CALL at2C399DB identifies the target directly. Two finite,
cache-first source reads acquired 64+128 bytes, stopping before the next
held function entry24D3320. The complete child occupies
`[24D3260,24D331B)`,187 bytes, SHA-256
`c0f817eba49c21b524883d3d0a92e2089938e671c2dffe529ca5d9fba5666c56`.
The remaining five bytes are INT3 padding. Both returns and every branch
are closed; the body has no CALL or indirect dispatch. No old executable,
full executable/hash/PE/pdata scan or game operation was performed.

At2C399DB the parent passes RCX equal to its context+848 object, and RDX
equal to stack30. Incoming R8/R9 are not read before being overwritten in
the child; the below-threshold path uses neither. Both child returns set
RAX=RDX after storing exactly one QWORD. The parent ignores RAX and reads
the first signed QWORD at2C399E0. These concrete facts do not add an extra
native invocation or impose a new return observation.

| Source instruction | Literal consumption |
| --- | --- |
| 24D3260..24D326E | Signed QWORD context+398; signed comparison with10000000 |
| 24D3274..24D32A9 | Registry slot5D1DAF8; context+18 full32 ID; indexlow24; unsigned registry+2C bound; registry+20 slots; stride10/object+8; object's full ID+10; fallback slot5D1DAE0 |
| 24D32B0..24D32EA | Registry slot5C67568; selected first object's+128 full32 ID; same slot shape; object's full ID+18; fallback slot5C67570 |
| 24D32F1..24D3304 | Second object's QWORD link+1C0; nonnull linked object's byte+4AB |
| 24D3306..24D3313 | Nonzero gate selects exact QWORD loaded from slot5C69698 |
| 24D3314..24D331A | Below threshold, null link or zero byte selects the initial context+398 QWORD |

The registry shapes match the current exact4 LandedTitle and Character
bindings, but this reader follows the child's literal full-ID tests and
fallbacks through03's existing memory callback. It does not call an active
resolver/getter, enumerate registries, infer a generation from a low24
index, or interpret an unread value as a native null/mismatch. A known
null registry, out-of-range index, null slot or known full32 mismatch takes
the exact fallback. Failure to read any selected operand is unavailable.
The loaded override may be negative or zero. Initial negative/zero values
are below the signed threshold and require no registry/global reads.

`ReadContextFirstQword24D3260V1(access,image_base,context_object,frame_key)`
uses03's `LoadedInputAccessV1`, `ReadOffsetV1` and `AddOffsetV1`. The exact4
access admission and original `CampaignRootFrameV1.snapshot_revision`
are supplied by03. It records only visited scalar inputs and compares
those copies again before marking the provider ready. The largest
literal path contains at most18 source scalar reads plus their bookends;
there is no scan, variable payload or dynamic allocation in the reader.

The returned observation exposes20c's exact
`ContextFactorProviderFirstQwordV1` as `.provider`, including source pin,
unmodified frame key, original context object and optional signed QWORD.
Other fields retain threshold/lookup/gate/override diagnostics, including
partial raw reads when the provider is unavailable.03 passes `.provider`
to20c's pure `EvaluateContextFactor2C399C0V1` with that same original
context/source frame.20c owns the following wrapped scale arithmetic.
The include direction is30d→20c→03's access header;20c has no30d include.

The new no-main export
`VerifyContextFirstQword24D3260ConnectedCasesV1()` contains16 focused
reader cases for the first03/10 connected compound. This worker performed
no compiler, fixture or old Person/release/arithmetic qualification run.
Central execution receipts remain independent of this static source
closure. No actual paused output, native child execution, field writer,
complete construction benefit, M4 milestone or live result is claimed by
this package alone.

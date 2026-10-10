# Selected-query answer predicate 3148BB0 (1.20.0.4)

The actual initial helper `307B340` compares context DWORDs `+2D8/+2DC`. When they differ, `307B453` reaches `3148BB0` with `RCX=[context]`, `RDX=context+8`, and the current selected-query diagnostic `R8=null`. Parent AL becomes 3 when this predicate's raw AL is zero, or 0 when it is nonzero. Equal context DWORDs skip the child in the independently owned parent.

The held pdata interval is `[3148BB0,3148DBD)`, 525 bytes, ending with the native normal return and terminal allocator-error branch. Its exact source SHA is `b840d630abee5c00c7cf1f9f78eb549e347711baa7e32c3c040e6e73993b8795`. Cache-first capture acquired exactly 525 new actual bytes through the shared D range claim; no old executable, whole-image or section scan was performed. Exact build is CK3 1.20.0.4 / Steam25734779, image SHA `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

The current query has two reached branches:

1. `MOV3148BD1` loads definition QWORD `+2290`. When null, `MOVZX3148BDD` returns definition BYTE `+2718` directly. The byte is not normalized to a Boolean.
2. When nonnull, `CALL3148BE9` invokes actual `372DF10` with that expression pointer as RCX and the unchanged second argument. Its AL is saved. AL zero leaves immediately; otherwise `TEST3148BFA` finds the selected-query null diagnostic output and jumps to `MOVZX3148D9F`, returning the same raw AL.

The longer nonnull diagnostic-output path allocates an evaluation packet and formats a diagnostic. It is not reached by this selected query and is not reconstructed or invoked by this package. `372DF10` is the sole necessary reached child for the nonnull-expression branch and must have its own source owner.

`ReadPrisonerAnswerPredicate3148BB0Raw12004(access, parent_raw)` reuses the parent's copied actual definition and complete `PrisonerQuoteSourceFrame12004`; it copies only `+2290` and, when null, `+2718`. `ProjectPrisonerAnswerPredicate3148BB012004(raw, expression_child)` returns the existing `PrisonerAnswerByteChild12004` DTO for `3148BB0`, including actual input identities and separate raw-AL/effects readiness. The expression child must identify actual `372DF10`, the same complete frame, the loaded expression receiver and the unchanged `context+8` second argument. An unknown child remains unknown.

The returned DTO feeds `ProjectPrisonerAnswerInitialGate12004` in the unique selected quote collector. This memory-only candidate creates no new frame, clock or qualification; no native getter, expression call or diagnostic is executed. The new no-main cases join the single current strict compound verification. This source closure supplies no live reply, dispatch, ransom success or M4 credit.

# Phase-two selected outer callable owner (2026-09-02)

This exact-build static package freezes the selected sequence-2 outer function
`[0x88B480,0x88B649)` and its normal return `0x88B648`. It does not start CK3
or change the public bridge/readiness state.

The extractor artifact is
`Z:\ck3_mod_rewrite_process_assets\zg361\phase2-native-gate-20260902\selected-outer-callers-static-extract.json`,
SHA-256
`77E277CFF70C0A6231174C52476B73C1B7EB61DB337C78EDFEB7FA49B50920C7`.
The function's 457 exact bytes have SHA-256
`0434F6BAD0F0DC15301E30408EAE2705CA65C4C5B54A422FB75EA4D643AE5F37`;
its PDATA unwind RVA is `0x4C42814`.

There are zero direct `E8 rel32` callers and therefore zero statically known
continuations. The executable contains exactly one absolute pointer to the
function, at `0x408DC00`. It is slot 2 of vtable `0x408DBF0`, with COL
`0x45BE710`, type descriptor `0x5158290`, and RTTI identity
`std::_Func_impl_no_alloc<lambda_68c316810e9676445097b6e1817a6010,
void>`. The vtable has exactly two bounded LEA references: construction at
`0x82193B` inside `[0x821870,0x821A0A)`, and assignment stub `0x88B650`.

This uniquely binds the callable owner and invoke slot, but not the generic
indirect callsite that invokes it. The next distinct stop point remains
`0x88B648`; immediately before its `ret`, `[RSP]` is the exact runtime
continuation. A separately authorized observation must preserve the existing
callback → vector exhaustion → `0x88B480` teardown → outer-return ordering.
Phase two remains **native-readiness RED + not-live**.

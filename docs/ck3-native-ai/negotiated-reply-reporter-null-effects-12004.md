# Negotiated reply reporters: exact1.20.0.4 null effects

For a reached reporter, the current negotiated quote's existing `1,1,null,null`
answer inputs select a branch with no external writes or child calls. This is proved from
actual `307B910`470B and `307BAF0`355B, not inferred from reporter names.
Image SHA is `98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`.

## Actual caller and pointer levels

The current4 binder in `ck3_12004_prisoner_negotiated_preview.cpp` supplies the
actual4 shared interaction callback to the reused preview implementation.
`ck3_12003_prisoner_negotiated_preview.inc` calls the supplied answer callback
with `context,1,1,nullptr,nullptr`. This is a current callsite fact, not a
qualification based on the old implementation's filename or old executable.

Parent `307BC60` builds its five-word mode-helper bundle, with `+10` pointing
to the incoming argument5 slot and `+20` to argument4. Mode helper `307BD70`
reloads their contents at `307BDA6..307BDCA` into local `RBP+30`(arg4) and
`RBP+20`(arg5). At `307BDE5..307BDF1`, it builds `307B910`'s two-word bundle
as `{&RBP20,&RBP30}` and passes its address at `307BE54`/`307BEC5`.

The other path reloads arg5 at `307BECF..307BEDA`. At `307BEFC..307BF07`, its
`307BAF0` bundle is `{&RBP20,scopeQwordBits}`; calls are at `307BF76`,
`307BFC4`, `307BFFD`. Its second word is a raw scope atom, not a second pointer
slot on the proved path. The literal strings/root-field reads before reporter
entry remain the caller's source and effects responsibility.

## Source-closed null branches

`307B910`: `307B93D` reads `slot0_address=[RCX]`, `307B943` compares
`[slot0_address]` with zero. Zero content jumps to `307B9F7`, reads
`slot1_address=[savedRCX+8]`, then its content at `307B9FB`. Zero second
content jumps at `307BA01` to the restore/return epilogue. These are exactly
four required QWORD reads; no CALL or external object write executes.

`307BAF0`: `307BB1B` reads `slot0_address=[RCX]`, `307BB1E` compares its
content with zero, and `307BB21` jumps to the epilogue. Exactly two QWORD reads
are required. `RCX+8` is not read. There are no child calls or external writes.

Both helpers save and restore registers through their own stack. Thus this
claim concerns external effects, not zero machine writes. The native bodies
do not guard slot addresses against null; valid readable addresses pointing
to zero content are required when reading the original bundle. Nonnull
content reaches output formatting/move/append work and remains outside this
leaf's effects closure. No null-path child needs further expansion.

## Pure consumer contract

`ProjectNegotiatedReplyReporterNullContents12004` accepts exact reporter/SHA,
an unchanged caller-supplied `uint64_t` frame token, and optional raw contents.
For the actual caller, slot0 is incoming arg5; only `307B910` requires slot1,
incoming arg4. Missing required content stays unavailable; nonzero content
does not become a no-output proof. `307BAF0` never requires the scope atom.
Projection leaves native bundle/slot addresses absent and labels contents
supplied. It is a source-equivalent branch relation, not a captured native
stack or native return.

`ReadNegotiatedReplyReporterNullPath12004` is the separate readonly seam for
an original supplied bundle address. It reads only the exact required guards,
checks address/read availability, and never invokes native reporters or their
formatters/destructors. A directly-null bundle entry is unavailable rather
than an empty output. It stops once nonnull content exits this null contract.

39/35 copy their full existing `PrisonerQuoteSourceFrame12004` and qualify its
equality/readiness before producing `PrisonerAnswerReporterEffects12004`.
An opaque token echoed by this leaf does not replace that actor/context/date/
revision/role binding. Neither API computes answer AL, prices, UI reasons,
actions, nor new gameplay gates.

## Delivery and validation

Source closure/frozen body pins and actual caller ABI are in external
`continuation-08d/SOURCE-FROZEN.json` and `CALLER-SOURCE-CLOSURE.json`.
Both reporter bodies were absent from the retained named caches and acquired
once through the shared D O_EXCL/new-only cache:825B total. Existing39c parent
and mode-body evidence was reused, with no additional capture.

The no-main fragment exports `RunNegotiatedReplyReporterNullPath12004NewCases`
with11 cases: exact guard/read order, first-only skip, nonnull boundaries,
null-address distinction, unavailable content, exact-image admission,
supplied projection without fake native addresses, and required/unused second
content. Worker compile/test runs are zero. 35 integrates it into the new
connected quote compound;10 executes the sole first acceptance. Existing08c
actor and earlier qualification cases are not replayed. No Game/SDK/Git or
shared driver/service/report edits were made by this package.

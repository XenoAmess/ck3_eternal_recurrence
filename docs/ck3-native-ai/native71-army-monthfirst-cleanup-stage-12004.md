# Native71 actual4 saved-month cleanup stage

Source-first continuation43, CK3 1.20.0.4 / Steam25734779, 2026-10-10.
Inherited EXE SHA256 is
`98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518`;
Native71 physical pin prefix16da is inherited from Root. The package adds a
bounded readonly cleanup-entry capture and a conditional source-derived
postimage for `2A9A66D→2A98C90(primary,CDate*)`. It does not observe a native
callback return. Actual poststage observation and whole daily/monthly remainfalse.

## Caller and stage provenance

The held complete `[2A9A570,2A9AB73)`/1539B caller is reused through
`../continuation-41/SOURCE-PROOF.json`, held instruction-byte SHA256
`60520f156b0b4c3a9f0846d67f322f620ac0ed9e946052e7cf328f4f2a4ca4a7`.
`2A9A655` reads GameState+C0; `2A9A65D` saves mask2, mathematical bit1.
`2A9A665` skips cleanup when the saved mask iszero. Otherwise `2A9A667`
passes RDX=GameState+8 CDate*, `2A9A66A` passes RCX=primary=secondary−8,
and `2A9A66D` calls2A98C90. RAX is not consumed. Unconditional gathering
`2A9A678→2A9AF20` follows, then further prefix queue/removal/ArRg work,
then saved-bit regular core `2A9A8DD→2A98AC0`.

The existing current C0 and full CDate readers and already qualified calendar
arithmetic are reused. A current query is not the saved callback register or
cleanup entry. The new DTO explicitly distinguishes `captured_current_context`
from `conditional_cleanup_entry`; evaluation rejects the former. Root must
supply coherent manager/frame/capture provenance and thread stage outputs.
No independent timestamp or fabricated callback observation is introduced.

## Actual source closure before candidate code

`SOURCE-CLOSED.json` and `NATIVE-TREE-CLOSED.mmd` were frozen before candidate
code. Root's named literal packets establish these logical blocks:

| Actual interval | Bytes | Selection |
| --- | ---: | --- |
| 2A98C90..2A98CBD |45|Actual callee entrance|
| 2A98CBD..2A98E22 |357|Literal nonempty fallthrough|
| 2A98E22..2A98E2F |13|Literal empty branch and body epilogue|

They close415B of direct cleanup source. Neighboring runtime rows were selected
by those actual edges, not joined by adjacency. Old.3 2A98CB0 remains only a
historical role locator. No globaldelta or oldbyte FIRST is used.

The sole direct call at `2A98E0B` names actual `2634C80`. Its exact runtime
interval `[2634C80,2634D56)`/214B was captured once under Root's updated
`FINITE-CAPTURE-POLICY.json`, using the canonical cache-first mapper and D shared
O_EXCL cache. Span SHA256 is
`23cd43da6e8a3e4e262d191fc2d06873462d8d386397b167ddef5c762a49ffb5`.
`helper-source/queue-resize-2634C80.json` holds complete decode and one214B
new-read receipt. Old/full EXE reads, EXE hashing, section scans and game calls
werezero in this lane. Root's415B supplied spans are separate from this worker read.

The helper invokes removed physical record slot0 with EDX0. Existing actual4
`8863D0..8863F1`/33B source is reused from
`docs/ck3-native-ai/army-ordered-detachment-callback-12004.md:52`: mode0 performs
no object/game-field reads or writes and returns the original record pointer.
Only an observed actual slot0 equal to exact imagebase+8863D0 receives that
replacement. No guessed canonical vtable or record FullID substitutes for it.
Missing/other reached target is a concrete unresolved callback effect. This
existing callback proof was neither recaptured nor retested here.

## Exact transition

The queue header is primary+468: data pointer+0 and signed count+C (primary474).
Records have stride16, vptr+0, requested FullID DWORD+8, signed ordinal DWORD+C.
The outer reverse endpoint is computed once from the original count; backing
physical slots remain in scope after the live count shrinks.

Each current physical outer slot selects Regi using global5D1EB68, low24 index
unsigned against registry2C, registry20 stride16 payload+8, and exact object10
generation match. Otherwise native fallback global5D1EB58 is selected. The
fallback's FullID need not equal the requested FullID. Magic14 must equal
52656769 and selected FullID10 must differ fromFFFFFFFF.

For a valid selection, source forms
`chunk = Regi+0x18+36*signextended(ordinal)` with no ordinal range gate. A literal
computed-null pointer takes pair removal without a date read/store. Otherwise
it compares **signed passedDate.low32** with **signed chunk.date1C.low32**.
If passedDate is smaller, this outer slot advances without removal or callback.
If due, source stores the entire QWORD **FFFFFFFF029C77F8** atchunk+1C.
The high DWORD of either input is not part of the due predicate.

An invalid Regi, null computed chunk, or due valid chunk removes all currently
live records matching the original raw requested FullID/ordinal pair. It copies
only DWORD+8/+C from the lastlive slot into each matching slot and rechecks that
position. Physical record addresses, vptrs and slot0 targets do not move.
Ordering is native swap-last order, not stableerase.

The resize helper receives start=newCount/end=oldCount, so its surviving-tail
copy leg is skipped in this caller. It invokes each removed physical slot in
`[newCount,oldCount)` with mode0 and then stores the reduced count. An unknown
callback blocks before this count store. Prior date stores and pair swaps are
retained as exact prefix events; they are not final returned values because
the unresolved callback could subsequently change them.

The pure fold keeps all original backing slots and a separate live count.
Physical chunk aliases share the date overlay, so one request's sentinel store
can change a later alias request's due predicate. Generation/fallback and raw
pair identities remain separate. Missing inputs remain unavailable. A negative
count is an unmaterialized native reverse cursor, not a fabricated empty list.

## Bounded raw capture and software leaf

Owned candidate files are `army_monthfirst_cleanup_stage_12004.hpp/.cpp` and
`test_army_monthfirst_cleanup_stage_12004.cpp`. Binding requires exact.4 SHA and
nonzero imagebase. It binds only Regi registry/fallback globals and known
mode0 callback identity; it exposes no native mutator pointer.

The readonly memory view captures primary468 data/count and at most256 original
16B records, including actual vptr.slot0 targets. Overbound inputs stop before
record/registry reads. Capacity and allocator are not new source gates. An
optional same-primary/same-frame queue seed converted from existing
`ArmyDetachmentPendingInputsV1` avoids duplicate queue reads; its count/slot
addresses and bound are checked before copying records. Original raw pairs
select only needed Regi objects and chunk dates; dates are captured once per
physical address. The already supplied full CDate/saved flag are not reread.

Local materialization limits are explicit: negative counts, missing raw
operands, inconsistent alias entry dates, and concrete date-store overlaps with
queue storage or captured generation/magic/manager fields remain unavailable.
Those limits are software representability failures, not new native predicates.
Signed ordinals are kept and actual computed addresses are checked, never
clamped to seven slots. No cleanup, helper, record virtual or allocator is called.

`EvaluateArmyMonthfirstCleanupStage12004` exposes returned/ready, live count,
full backing records and physical-address date-store events. Unknown callback
exposes blocked physical slot/actual target and preceding exact prefix effects.
Caller-skipped input can be available without queue materialization; its unread
unchanged queue remains unknown rather than becoming empty.

## Output for following stages

When ready+returned, Root may overlay only date writes by exact physical chunk
address and primary468 pair/count postimage. The direct callee has no other
writes when all reached callbacks are the exact known mode0 target:

| State | Cleanup effect |
| --- | --- |
| chunk+1C QWORD date |due selected slots become FFFFFFFF029C77F8|
| primary468 record DWORD08/C |native matching-pair swap-last compaction|
| primary474 count |reduced after successful helper callbacks|
| chunk max00/current04/owner08/ordinal0C/association10/flag14/state18 |no other direct writes|
| primary30/3C,prepared148,roster158/164 and ArRg fields |no direct writes|

Primary158/164 can therefore pass through a complete cleanup stage into42's
following gathering stage. Missing/other callback gives no such unchanged
claim. Even a complete cleanup frame is not34's regular-core frame: gathering
and remaining manager prefix effects must be threaded first. Prefix events from
an unavailable cleanup must not be presented as a returned cleanup frame.

## Qualification and storage

`FOCUSED-RECIPE.json` freezes the sole new focused argv
`monthfirst_cleanup_stage_12004_fixture.exe monthfirst-cleanup-actual4-stage`.
Six source-specific cases cover due duplicate removal/swap order and fixed
backing cursor, unknown physical-slot callback prefix, signed low32/unreached
callback, fallback physical alias, invalid/empty/skipped/missing/current frame,
and bounded readonly capture with generation mismatch, signed ordinal and
existing queue-seed reuse. Existing calendar arithmetic/FIRST suites are not
replayed. `OWNED-CANDIDATE-PINS.json` pins exactly compiled owned inputs.
Central10 owns the external MSVC build/run and exact EXE setting receipt.
The actual `focused-build/RESULT.json` receipt reports one MSVC18
`/std:c++20 /W4 /WX /EHsc /MD` compile exit0 and one sole focused invocation
exit0, all6 casesGREEN, with candidate pins unchanged. The built120832B EXE
SHA256 is `a98da7042158b3e0c0428b612207d477d5b59eaff8000d968096c33afe5f0b85`.
Exact permanent Defender registration was attempted once; actual receipt says
`admin_required_for_verified_readback`, no Add attempted, no UAC. Permanent
exclusion remainsPENDING independently of fixture success. Actual native
poststage/full daily/full monthly remainfalse.

Z/source/shared core/Driver/Service/serializer/CMake/report/Git/Game remain
Root-owned and unchanged by this lane. D-only output uses storage policy1.0.0,
TASK-START-STORAGE.json and Root's shared20GiB capacity receipt; new focused
output peak is16MiB. Structured records have4320-hour review, literal raw
source720-hour review, derived helpers48-hour review and build outputs336-hour review, using the universal
versioned parameters. Close receipt and category ledger are recorded separately.

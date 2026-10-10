# Native71 Army post-date callback initial stage — 1.20.0.4

Status: source ordering and direct late-body stores closed; owned event-stage
adapter authored; one new synthetic offline method executed **GREEN** by
central owner 10 on 2026-10-10. No new native observer, game call, build, saved day
or qualification replay occurs in this package. The existing qualified
original-once `24E3410` observer and soldier-writer journal are reused.

Exact input is CK3 `1.20.0.4`, Steam `25734779`, EXE SHA-256
`98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`.
The held actual dispatcher is `[2A9A570,2A9AB73)`, 1539 bytes. It is selected
from actual4 `new.instructions`, rather than by shifting the old `2A9A590`
address. Its held instruction-byte SHA is
`60520f156b0b4c3a9f0846d67f322f620ac0ed9e946052e7cf328f4f2a4ca4a7`,
reconstructed from the already held contiguous DETAIL instructions; this
worker does not reopen or hash the EXE or raw cache.

The source was frozen before adapter authoring in
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-41/SOURCE-PROOF.json`.
The later three-body Root increment has its own immutable
`LATE-CALLEE-SOURCE-PROOF.json`. The common storage receipt, research plan and
rendered graph remain beside these files. Z is read-only in this package.

## Actual receiver and order

Actual instructions at `2A9A984..99C` load `GameState` from slot `5C68C50`,
read its `+A0` GameData, add `2A540` and call `2A97880` with the selected Army.
At `2A9A661` the dispatcher obtains that primary manager by subtracting eight
from its secondary receiver. These actual source uses bind primary
`GameData+2A540` and secondary `GameData+2A548`. This package does not claim
the outer constructor/virtual18 attachment from an old vtable.

| Source boundary | Actual stage |
|---|---|
| `2A9A655/65D` | Save GameState `C0 bit2` once |
| `2A9A66D -> 2A98C90` | Saved-bit2 cleanup, primary manager and GameState+8 date pointer; continuation43 owns effects |
| `2A9A678 -> 2A9AF20` | Unconditional gathering/due work with the same arguments; continuation42 owns effects |
| `2A9A8DD -> 2A98AC0` | Saved-bit2 regular refill; continuation34 owns its changed state |
| `2A9A8E5 -> 2A97EB0` | Unconditional daily assault; continuation37 owns its changed state |
| `2A9A8EA` | Start late original Army roster after the assault return |
| `2A9AAF8` | Read storedD and select the original pointer bucket after that roster |
| `2A9AB46 -> 24E3410` | Callback with the stored CArmy pointer and saved GameState+8 date pointer; actual return address `2A9AB4B` |
| `2A9AB6E -> 2A98E30` | Later manager tail, outside this callback-entry result |

The late roster uses secondary `+48/+54`, hence primary `+50/+5C`.
It captures a fixed initial end and advances four-byte FullID occurrences.
Generation lookup can select the native fallback. Wrong Army magic or fullID
`-1` follows the diagnostic path; it does not receive the direct reset stores.
Valid selections first write byte `22=0`, copy DWORD `24 -> 1FC`, and copy
QWORD `28 -> 200`, before testing flag31. Repeated occurrences remain distinct.

Flag31 nonzero calls `2A97880(primary,Army)` and skips the remaining per-Army
work. Only its 41-byte prefix is held here: `2A97896 -> 2A981E0` precedes an
Army-tag check and a branch beyond the captured prefix. Complete removal and
registry/bucket consequences remain unknown; the prefix is not a full wrapper.

Flag31 zero calls the bare-Fleet getter `24E8440`. True writes loaded DWORD
`5C69984` to Army `1D0`; false decrements only signed-positive `1D0`. It then
conditionally clears byte20 before `2639A90`, clears byte21 before `2C44710`,
and, for nonzero byte30, calls `24DD630` before refreshing QWORD `1D8` through
`3242F50`. The flag tests are ordered; a preceding native event can change the
inputs of a later test. A captured current flag does not represent that later
test after intervening calls.

## Three actual late bodies

Root supplied only the named actual .pdata bodies; their `.json` receipts bind
each interval, exact4 identity, SHA and new finite read. Worker source reads
use those receipts, with zero new EXE reads.

| Body | Bytes / source SHA | Direct Army behavior and boundary |
|---|---|---|
| `2639A90..2639D7C` | 748 / `44d66545946132dc0543d980aff9914170e4543821a2dbdf6e10525dfa5ce885` | Takes the Army in RDX. Resolves Unit124 and owner Character174, then owner1C0+318 or static header5459D38; reads header DWORD+C. For signed Army1E0<=0 and header count0, returns without Army stores. Nonzero header clears WORD1D4 and QWORD1E0. Positive1E0 builds an Army kind27 event context, calls native event paths, then clears1E0 and conditionally WORD1D4. |
| `2C44710..2C4497E` | 622 / `3364b7fec95107e1944b880cfa17ce3b2a2e35e8cdf2400430a33a70a491fc2e` | Takes Army in RCX and performs the same full-generation owner/header resolution. For signed Army1F0<=0 and header count0, returns without Army stores. Nonzero header clears QWORD1F0 and BYTE1EC. Positive1F0 calls context builder2C44580 and native event paths, then clears1F0 and conditionally BYTE1EC. |
| `24DD630..24DD829` | 505 / `87e4eae29dc4ae5e3fb9bf10f72a0d7e71d6fa56f7059b7215dd4e604581a1a5` | Captures entry Army1D8, builds a kind27 Army context with named owner, executes an event path and appends the context to saved1D8+230. It has no direct Army scalar store; nested effects remain separate. |

These positive paths reuse actual4 `889F60` context construction and `373A0F0`
named-scope insertion already closed and qualified by the existing religion
context/battle-trigger work. No repeated context qualification is requested.
Actual event-definition lookup `393EE20`, dispatcher `37CCC30`, append
`3765760`, and the flag21-specific `2C44580` remain concrete child boundaries.
The event paths use loaded definitions, context names and table slots; a stock
script, inferred no-op or guessed event outcome cannot supply their effects.

Returned calls sent to the coordinator for disjoint continuation work are:
`2C44817 -> 2C44580`; `2639C9F/24DD7B1 -> 3765760` with savedArmy1D8+40/+230;
and `2639CF1/2C448F0/24DD7A0 -> 37CCC30` with event table slots168/640/170.
Whole late transitions remain incomplete while those effects and full flag31
removal are unresolved. Direct stores remain useful without claiming that all
callee effects are modeled.

## Real bucket and retained callback initial state

At `2A9AB00`, storedD is the raw DWORD at GameState+9C. Unsigned arithmetic
computes `uint32(D)%30`, independent of the passed CDate at GameState+8. The
selected pointer bucket is secondary `+190+24*bucket`, with signed count at
`+19C+24*bucket`. The initial end is captured once. Every eight-byte pointer
occurrence calls `24E3410` in stored order, including repeated pointers.
There is no generation resolver or repeated Army validity check in this loop.

The existing all30 `future_daily_supply_schedule_inputs_v1` collector already
publishes current subject pointer membership. A new current bucket collector
would duplicate it. Its query-time membership cannot be used to fill an older
callback event's storedD, bucket index, ordinal or earlier roster processing.

The existing qualified `actual_supply_callback_observations_v1` is sufficient
for a smaller result: event `caller_return_rva == 2A9AB4B` binds the actual
dispatcher callsite, while its recorded before stock, last-update date and
byte22 represent the callback entry fields after the preceding dispatcher
stages. Its passed date is the actual invocation argument. This does not prove
which branches ran on this subject, that it occurred in the late FullID roster,
or that zero byte22 came from that roster's reset. Repeated matching events are
independent; their entry values are not chained by the consumer.

The owned `army_post_date_callback_stage_12004.py` joins only the existing
normalized event family. It retains partial entry captures and unmatched
caller records, preserves global journal counters, and leaves historicalD,
bucket and ordinal null. It performs no memory read, native call, model of a
prior mutator, new detour or stock/casualty inference. An empty retained family
means no retained matching completed invocation. It cannot prove no callback
or unchanged preceding state.

One new synthetic offline focused consumer was executed once by central owner
10 at 09:22:28 UTC, exit 0. It verifies
real-callsite classification, independent repeated entry fields and full64
passed dates, partial capture, unmatched route, zero retained records, and
refusal to use injected later-query membership. It does not replay the existing
native callback fixture, journal qualification or registered Service compound.
The actual receipt is
`D:/codex-ck3-background-spill/native71-continuation-20261010/continuation-41/root-first/RESULT.json`.
This receipt covers the unchanged Python leaf and one test method. The dated
continuation63 source category correction below adds no execution credit.
Root owns the shared Service addition, the single new focus and subsequent
integration. Full daily/monthly execution, complete prior manager transition,
actual historical bucket ordinal and new live evidence remain false.

## Source correction — 2026-10-10 continuation63

The subsequent actual 252-byte `3765760` body closes its category: it is a
compiled-effect execution wrapper, rather than a direct history append. It
builds a wrapper context and calls `3765E50`; it has no direct receiver/history
store. Earlier references to append in this topic and the initial immutable
source increment were caller-role hypotheses while that callee was unresolved.
The source-bound arguments remain exact: `2639C9F` receives Army1D8+40 and
`24DD7B1` receives entry-saved Army1D8+230, both with context50. Those receivers
are compiled-effect context sources. Their child effects remain separate.
Continuation63 owns `army_compiled_effect_entry12004.hpp` and actual ingress
return routes `2639CA4`/`24DD7B6`; Root owns any safe reader/publication hook.
This correction adds no current-query-to-historical association or live credit.

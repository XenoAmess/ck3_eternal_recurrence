# R0266 H3911 attempt-05: passive topbar RED, offline diagnosis

## Frozen evidence and limit

The formal selected query returned `same_paused_query_postcheck_passed` for
`query-war-termination-options-16777231`, actor `29829`, unchanged treasury
`120644281` Q100000 raw. This validates that query's native before/after frame;
it does **not** validate the independent GUI cache. Its receipt SHA-256 is
`10F4A8B67D0635743EF2E41F82A17B063F66B32BD5B4CBED2A6B0F1F6FA73460`.

The immutable `attempt-05/formal-query-receipt/passive-topbar-raw.json`
(SHA-256 `9D1A25DF8B33109B5F82917832951A6061956AA73A4A173BBAF5A7730AF1E5BE`)
reports two bounded read passes, 5,716 target bytes and 10 reads each. The
topbar owner path, its bytes, and global played CharacterID `29829` match
across passes. Both passes reject the expense array as “not an aligned
user-mode address” and the render epoch as “render tick or refresh interval is
invalid”. `expense_layout` and `render_epoch` are null, and the combined
status is RED. The paired diagnostic SHA-256 is
`EA46AEEEC87E303B0E691C8211F3DDEE3EC9C478D05A212E03A70420DB7F48CA`.

The old raw receipt preserved hashes of the 0xF90 topbar block, but **not its
raw bytes or individual rejected scalar values**. Consequently the two
stable block hashes prove that the rejected header did not change across the
two samples; they cannot distinguish zero, unaligned, out-of-range, tagged,
or wrong-offset row pointers. The same loss applies to the last-update tick,
current render tick, and refresh interval. No row or currency amount can be
recovered from these hashes. This attempt remains five cash values null and
`formal_cash_eligible=false`.

## Exact-build interpretation

The pinned EXE static verifier and `game/gui/hud.gui:6121-6131` support these
*layout candidates*: the expense getter checks a render context at global
RVA `0x576CC68`, reads its tick at `+0x180`, reads signed refresh interval
at RVA `0x570D8D0`, and compares topbar `+0xF88` before a possible refresh.
The refresh path uses played CharacterID global RVA `0x4FE7EE0`, constructs
ValueBreakdown at topbar `+0xAD8`, writes signed total at `+0xB50`, and
back-pointer at `+0xB68`. The row vector header is `+0xAD8/+0xAE0/+0xAE4`.
See `verify_war_cash_topbar_expense_candidate.py` and
`r0266-topbar-expense-static-2026-09-28.md` for instruction anchors.

These static anchors do not prove that the live cache was initialized in the
headless/paused sample. A topbar tooltip getter may refresh it only on normal
GUI use; **calling that getter from the bridge would write cache state** and
is outside this read-only probe. No evidence yet distinguishes an
uninitialized cache from an incorrect live-object interpretation. The
render-clock rejection might be a zero last-update tick, zero/out-of-range
interval, or reversed/invalid tick order; the old receipt cannot decide.

## Minimal next passive diagnostic

`war_cash_topbar_bounded_sample.py` now records scalar candidates from bytes
it already reads: vector pointer/class/capacity/count; topbar last-update
tick; and, when each read succeeds, render context pointer/current tick and
signed refresh interval. It does not follow a rejected pointer, add process
reads, call a getter, or convert any candidate to a cash receipt. Preserve
the existing exact EXE/managed-session/paused-frame gate in a **new** attempt
and use the changed tool only after that gate. The screen owner can obtain
natural GUI refresh under the project's desktop and Steam contracts if a
future read remains uninitialized.

Interpret the next scalar diagnostics fail-closed:

| Header observation | What it can indicate | Gate still needed |
| --- | --- | --- |
| pointer `0`, count/capacity `0` | likely never populated or reset cache | inspect natural GUI lifecycle; do not infer zero expense |
| nonzero unaligned pointer | wrong offset, tagged representation, or corruption | exact native instruction/object proof before changing pointer interpretation |
| aligned pointer, invalid count/capacity | partial or stale vector, or wrong layout | no row follow until bounds pass |
| last-update tick `0` or interval nonpositive | uninitialized or unavailable GUI clock | establish natural refresh, then same-frame player and cache binding |
| `last_update > current` or enormous interval | clock/ABI mismatch or stale context | do not use epoch for freshness |

Even if all headers pass, the existing double read is diagnostic only.
Formal monthly military spend additionally requires row identity/units and
current player/war/frame attribution. A monthly rate cannot by itself bound
dated future costs, committed spend, instant fees, or policy reserve.

# Construction active progress: exact 1.19.0.6 source

The first derived paused runtime read and its zero-divisor boundary are
recorded in [R0256 construction progress](construction-r0256-zero-divisor-readback-2026-09-27.md).

This is a private read-only source for an already active building. The frozen
`ck3.exe` SHA-256 is
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The byte assertions are in
`native_bridge/research/verify_player_world_building_action_private_v1.py`.

The stock start path `0x21F6860` writes `CBuildingType+0x50 * 100000` to
`Province+0x620+0x88` at `0x21F69BD`. The stock progress path `0x21F6D40`
reads `Province+0x620+0xE8` at `0x21F6D57`; when this divisor is positive,
it subtracts the integer quotient `10000000000 / divisor` from `+0x88`
at `0x21F6D72`. A nonpositive divisor sets the remaining work to zero.
The same path checks `+0x88 <= 0` before its completion branch. The start
path also calls `0x21FBD10`, so the authored 1095 days for `hill_farms_01`
alone cannot be treated as an effective completion date.

The existing private `g2_player_construction_view_probe_v1` active row now
copies `native_remaining_work_raw` and `native_progress_divisor_raw` from
the same province and paused frame as its active building, slot and initiator.
Inactive rows carry `null` for the new fields. This is a raw source projection;
it does not yet schedule watches or claim an adjusted duration/date. A matching
paused runtime read, progress across a date advance and eventual completion
must qualify cadence and conversion before the formal scheduler consumes it.
Until then, the existing 30-game-day watch interval remains the running policy.

The source, serializer and exact-byte checks pass normal Debug and optimized
Release fixtures. This work did not launch CK3 or observe a new completion or
income increase. Unknown runtime progress remains an explicit observation gap.

## C71: manager cadence and completion boundary (exact-source only)

The same frozen EXE places `0x21FDAC0` and `0x21FDDB0` in slots 2 and 3 of
the `CHoldingManager` `CLegacyGameManagerInterface` vtable at `0x43426B8`
(RTTI Complete Object Locator `0x4998148`, type
`.?AVCHoldingManager@@`). In slot 2, `0x21FDD25..0x21FDD83` traverses the
manager's active-construction list at `+0x20/+0x2C`. For every active row it
calls `0x2919390` with base `100000` at `0x21FDD6D` and stores the returned
raw divisor in the row's `+0xE8` at `0x21FDD75`. An earlier part of this same
method selects a province bucket using a value modulo 30; the active-list
divisor refresh is **after** that bucket and is not limited to the selected
province bucket.

Slot 3 `0x21FDDB0` traverses the same active list at
`0x21FDE1B..0x21FDE70`. It passes `edx=0` to `0x21F6D40` at `0x21FDE3A`;
that callee subtracts the signed integer quotient
`10000000000 / progress_divisor_raw` when the divisor is positive. It sets
remaining work to zero for a nonpositive divisor. With the normal `edx=0`,
positive remaining work returns without completing. When the callee returns
true, the manager removes the row from its active list. The other two direct
callers at `0x21D34E8` and `0x2EBCEFE` pass `edx=1`, which also enters the
completion branch with positive remaining work; they are not evidence for
normal elapsed-day completion. The adjacent manager slots identify the two
routes, but this source check alone does not establish their global ordering
relative to other managers or a live per-day delta.

For a normal building completion, `0x21F6FC9..0x21F7030` writes the finished
`CBuildingType*` into the same built-slot array at `+0x18` and slot index
`+0x78`; `0x21F7033` then calls `0x21F7970`, which invokes the holding
recalculation functions `0x21FB690` and `0x21FB720`. The active definition
pointer at `+0x70` is cleared only at `0x21F7070`, immediately before return.
Thus the first safe completion proof is an independent paused snapshot **after
the full manager update returns**, matching the previously active province,
slot and type against the built-slot row and observing no matching active row.
The recalculation call is not proof that the player's reported monthly gold
income rises on that same frame or that any observed total-income delta is
caused solely by this building. The existing root-income follow-up remains
necessary.

The next bounded live probe can attach to an already authorized Robert run
with the matching DLL and paired save: read `date_raw`, active tuple,
`native_remaining_work_raw` and `native_progress_divisor_raw` on a paused
frame; after a normal one-day advance (`date_raw + 24`), read the same tuple
again. If the divisor is positive and unchanged and no speed modifier changed,
compare the work difference with the integer quotient above. A zero divisor,
changed divisor, vanished row or date that did not advance is a distinct
observation, not a calculated ETA. On a later completion frame, read the
built-slot row and player monthly income independently, then consume the
existing completion receipt and next turn. This source work added no CK3
action, game date, completion or income evidence; the formal 30-game-day watch
policy is unchanged.

## C156: retain the paused active-progress read in the material receipt

The existing private construction material query already reads the matching
active row on a paused actor frame. Its native row includes
`native_remaining_work_raw` and `native_progress_divisor_raw`, but the formal
receipt previously retained only `in_progress`/`completed` and income fields.
The additive `construction_progress_observation` now binds those two raw
integers to the same snapshot, native revision and game date as the matching
material receipt. A missing raw field remains `null` with status `unavailable`;
a completed slot has status `not_active`. Neither status predicts a finish
date. The receipt stays in the construction ledger, the immediate formal turn
result and the next turn's `construction_receipt_consumed` report field. This
changes no action or watch cadence. Focused normal and optimized Python tests
cover active and completed material receipts plus both report views; paused
CK3 progress and completion remain unobserved.

For the R0249-derived h223 pair, the saved ledger last checked at raw
`53154936`, so its old 30-day threshold is raw `53155656`, 25 game days after
h223/raw `53155056`. A new-PID cold material recheck happens immediately and,
if still active, updates `completion_last_check_date_raw` to the current date.
If that first read occurs at h223/raw `53155056`, the next warm threshold is
raw `53155776`, 30 game days later. Any derived-line observation must use the
actual receipt date to calculate the next watch; it cannot promise a warm
watch exactly 25 days after the source pair. The derived dates do not add to
the official Robert high-water count.

# Construction active progress: exact 1.19.0.6 source

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

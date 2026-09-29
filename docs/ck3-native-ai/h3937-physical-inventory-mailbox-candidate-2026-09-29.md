# H3937 physical army inventory mailbox candidate (2026-09-29)

Status: **static candidate; live and formal date admission RED**. This work
starts from the reviewed physical scanner at `920c17533803ae96226b7f37d5ec61a095bfc2c9`.
Its bridge extension is disabled unless
`XAR_CK3_ENABLE_H3937_PHYSICAL_INVENTORY_MAILBOX_V1=ON` is set for a private
build. No CK3 process, desktop, or game date was used during this attempt.

The existing route-contact read-only mailbox performs a physical CUnit scan,
the CK3 route-contact read, then another physical scan within the same
application-main ticket. A complete receipt requires both scans and the
underlying game/Jomini/CUnit/CArmy/Character/Province/War source identities,
slots, capacities, rows, and public roster to agree. The reader records
`storage_capacity`, `slots_scanned`, `empty_slots`, `canonical_units`,
`invalid_id_slots`, `noncanonical_slots`, and `unresolved_slots`; an invalid,
unresolved, or retreating hostile makes the result partial. The mailbox also
requires both physical contact hostile sets to equal the route request and
result, plus the execution stamp's game/Jomini source, paused state, and date.
The private source addresses remain in C++ memory and are never serialized.

The native result carries its mailbox pump epoch/thread/date, query sequence,
native snapshot revision, full physical roster and per-unit route/state rows.
The Python driver accepts the optional receipt only from its own native pipe
query result. It checks exact schema and joins it to the unchanged public
snapshot ID, driver/native revisions, date, episode and connection generation;
the played actor, active war/player armies, event, pending interaction, map
readiness and advertised capability fields must also match before/after.
For this candidate the episode, actor, war and subject army are pinned to
H3937. The full hostile set and non-retreating route-contact set are checked
separately. A successful shape check still returns
`date_or_action_authorized: false`; no receipt, bare `complete`, or shape-only
result is a formal date or movement credential.

This branch is isolated from the H3937 all-date hold in `b1f49428d55f0b06428adaef030c270865cc3341`.
They must be integrated atomically before any live driver use. Even after
integration, the pending joint war/cash risk decision is an independent formal
hold. A live paused query and readback are still needed before this static
candidate can be promoted. Multiple simultaneous active wars remain
unavailable in this V1 rather than forming an unproven union.

The earlier `d22636e57` native fixture DLL and executable were physically
overwritten by the later `920c17533803ae96226b7f37d5ec61a095bfc2c9`
relink in the original external build directory. Their source commits, hashes
and logs remain, but their old binaries were not preserved. Mailbox build
attempts use fresh external directories. Attempt 01 was compiling while the
Python validator changed after `81d3cdc77`; its combined source/build
provenance is RED and cannot certify the repaired HEAD. A fresh attempt is
required for the final source tree.

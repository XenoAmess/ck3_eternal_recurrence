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

## Integration correction — local dry run, 2026-09-29

The isolation statement above describes the original `4e622c6ce2cb3ee629f63722bc1e0b2b12e211f5`
candidate. The later local integration branch
`research/h3937-mailbox-dateguard-dry` starts from #612's all-date hold
`b1f49428d55f0b06428adaef030c270865cc3341` and replays all seven mailbox
candidate commits without conflicts or patch changes. Its frozen dry-run HEAD
is `88f0ec98cbbc04477ec032b277871ec167a36ef9`; the range-diff marks all
seven patches equivalent. The all-date hold, strategy finalizer, and formal
`authenticated_physical_inventory_for_route_contact` seam have no diff from
`b1f49428`. The mailbox adds optional read-only native receipt validation and
returns `date_or_action_authorized: false`. Even a shape-valid receipt remains
candidate evidence; the authenticated formal seam stays closed, and the joint
war/cash risk decision is still absent. The dry run did not build or launch.

The append-only local dry-run receipt is
`D:/ck3-research-artifacts/h3937-mailbox-datehold-dry-attempt01/receipt.json`
(SHA-256 `0C3E7E4F94EE5879B71B3135DD3CC76FA2BF2F3BBECACDF40E6F9F4CA66601C8`).
It pins the full diff and range-diff plus normal and optimized Python logs:
24 focused inventory/date-hold/combined tests and 231 native-driver tests
passed in each mode. These are static checks, not a live inventory readback.

Attempt 01's mixed source/build provenance remains RED as recorded above.
The separate native mailbox build attempt 02 under
`D:/ck3-research-artifacts/h3937-physical-inventory-mailbox-attempt02/`
recorded clean before/after source HEAD `4e622c6ce2cb3ee629f63722bc1e0b2b12e211f5`.
Its native fixture executable returned exit code 0 when invoked directly;
CTest found no tests in that attempt and must not be reported as a CTest pass.
Its DLL and injector belong to that source attempt. The integrated
`88f0ec98c` source is a different checkout and needs
a new exact Release build, official pair, no-launch checks, and independent
review before any live use. It cannot inherit executable authorization from
the `4e622c6ce` artifacts. Complete physical inventory, formal date credit,
war action, and gameplay remain **RED**.

# H3937 physical CUnit inventory candidate

Status: **static candidate only; no authenticated mailbox, live receipt, date
or action authorization**. The direct exact-build
`ReadPhysicalArmyInventoryV1` API is not called by the bridge protocol or
formal driver. It does not launch CK3 or advance time.

## Why this read exists

The existing `ReadArmies` returns an empty vector for a missing or malformed
CUnit storage header. It silently skips nonempty slots when the full-generation
ID does not match the slot or the CUnit is not a canonical direct CArmy-linked
orderable unit. War `enemy_armies` and the route-contact hostile-scope check
both derive from this vector. Their agreement alone cannot prove physical
enumeration completeness.

This candidate performs a separate paused scan of every slot in the same
exact-build CUnit storage. It records capacity, scanned and empty slot counts,
canonical units, bad-ID slots, noncanonical slots and unresolved candidates.
It classifies each canonical unit by the live CWar participant relation and
retains separate sorted full-generation sets for player, allied, **all
hostile**, nonretreating contact-eligible hostile, and retreating hostile
armies. A bad header is `unavailable`, not an empty army set. A nonempty
noncanonical or bad-ID slot is unresolved, not silently stale. The reader
freezes the source pointers, samples a second bound native snapshot, scans
the physical storage twice, and samples a final native snapshot. It requires
all three snapshots, both scans and the source pointers to agree, then
compares player/allied/hostile sets against the published
native row. `complete` also requires one allied controllable subject, valid
owner and Province for each canonical unit, valid state, complete routes for
the selected war's units, no active combat, no retreat-state ambiguity and no
retreating hostile excluded by Q2.

The Python `physical_army_inventory_v1.py` validator checks a proposed JSON
shape for exact build, frame, episode and connection identity, scan arithmetic,
row classifications and all three independently supplied sets. Its result has
`date_or_action_authorized=false` even for a valid shape. No existing native
command emits that JSON; creating one by hand cannot satisfy the source
contract.

## Remaining source and policy gates

The candidate has **no authenticated main-thread mailbox or native driver
projector**. A future producer must bind its native receipt to exact
`snapshot_id`, public/native revisions, `episode_run_id` and connection
generation in the same execution slot as S/Q. It must expose source-build
identity and compare the physical set with the Q2 request/result before any
formal consumer can use it. A Python field or bare completeness boolean is
insufficient. If the CK3 CUnit storage has a second physical live-unit source
outside this slot array, that ABI must also be proven before this scan can be
called complete for the whole game. CFleet carrier semantics, stale slots and
ambiguous owners remain typed partial pending exact-build authority.

Even a certified current frame does not guarantee that orders or raised units
stay fixed during a day. One bounded day needs a separately reviewed formal
risk and cash decision, one-shot native execution guard and fresh post-day
read. The future 2629 siege participants remain unresolved.

Static evidence is the native `xar_ck3_game_access_test` fixture, which probes
the complete canonical case and negative retreating, bad-generation,
noncanonical CFleet and bad-header cases, plus the Python shape validator's
identity, count, route, side and set-mismatch negatives. No H3937 live
inventory result exists in this commit.

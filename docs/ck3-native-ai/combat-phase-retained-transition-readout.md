# Exact-build retained combat entry transition readout

Build: CK3 `1.19.0.6-steam23530548`, EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
The layout and casualty interpretation come from the native chain already
documented in [ongoing-battle-frame.md](ongoing-battle-frame.md). This file
records the additional seven-boundary trace projection; it does not qualify a
forecast or a production attack.

At each original phase-event boundary, the prearmed trace reads both side
entry vectors in their native order: levy `CCombatSide+0x28/+0x34`, then
men-at-arms `+0x40/+0x4C`, stride `0x60`. For each retained row it copies
full-generation regiment ID `+0x08`, starting/current/soft Q100000
`+0x10/+0x18/+0x20`, and effective damage/toughness Q100000 `+0x40/+0x48`.
The paused arm phase resolves levy IDs in addition to the already resolved
men-at-arms IDs. Every hook record rechecks the exact regiment generation and
membership in an ordered side CArmy, without calling a game helper.

For an entry whose exact combat type `+0xA0A` says it fights in the main phase,
`hard_casualties_raw` is derived as `starting-current-soft` after nonnegative
range checks. A non-main entry's residual may be an uncommitted reserve, so
its hard value is emitted as `null`. Separately, each side copies its ordered
participant-owner hard ledger from `+0x58/+0x64` (stride `0x18`, owner ID
`+0x08`, cumulative hard Q100000 `+0x10`). A disappeared regiment cannot be
reconstructed from the retained entry vector; the owner ledger is not
redistributed among remaining rows.

This is a **research-only, read-only** projection. The prior seven-boundary
trace still has `full_mutable_transition_bundle_complete=false` and
`original_trace_ready=false`. In particular, the same-boundary outgoing
damage frozen before casualty application, effective `0x18C/0x18D` conversion,
winter `0x19F`/guard, and full event effect mutation feedback remain to be
bound and compared with a managed live transition. The new fields alone do
not produce a calibrated win probability, and they do not authorize a
sub-2× attack.

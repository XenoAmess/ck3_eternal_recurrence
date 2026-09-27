# Construction: retain two active receipts for completion follow-up

Source baseline: `230931997cda22a4302e881bceab05bd7a930368` on 2026-09-27.
The exact 1.19.0.6 native construction tree and build hash remain in
[`domain-construction-ai.md`](domain-construction-ai.md). This note changes
the private formal consumer, not the native construction policy or public
capability advertisement.

The formal consumer already admitted a second final-legal affordable building
on a later game day. Its focused production-path fixture submitted two
different building tuples and verified both material receipts. Before this
change, the second `query_construction_receipt` replaced the one
`ledger.applied` entry. The first building could remain under construction in
CK3, but the formal planner had lost its completion watch, opening income
baseline, and cold recheck target. The old fixture asserted the second receipt
only; adding an assertion for the first receipt failed with missing
`applied_prior`.

The private ledger now keeps the newest verified receipt in `applied` and
older receipts still awaiting completion or actual-income readback in optional
`applied_prior`, oldest first. Legacy one-receipt sidecars read as an empty
prior list. The consumer resolves a pending action first, then an older cold
receipt, an observed completion missing income, or a due 30-game-day watch;
only after these checks may it seek another building. The typed material
query updates exactly the matching request ID without overwriting a separate
construction. The test exercises two starts, independent receipts, a new
process reading both original slots, and successive due watches. Completed
records with observed income need no earlier portfolio entry when a new
building starts.

This is source and fixture evidence only. R0256 and R0257 observed one
existing `hill_farms_01` in progress, with the same slot's remaining work
decreasing over three derived days. They did not submit a second building or
observe completion or an actual income gain. A matching DLL, official
save/driver/sidecar pairing, paused material readbacks, following turn, and
new-PID restore are required before claiming a multi-building live loop.

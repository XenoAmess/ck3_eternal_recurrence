# Exact-day private receipt wake candidate

`machine_id: xenoamess-full-tower-eb9d2c1186`. This is a source and synthetic
qualification package under the Root performance lane, observed 2026-10-20.
It is not deployed to Source25, T04, CK3, or a running SDK.

The exact Source25 Driver is read once from commit
`9b791aae9bb1314162aa5cab923e6cca2892e6d8`. Only
`NativeHeadlessGameplayDriver._wait_for_life_advance_change` changes. Its
existing exact-day B collector is the scope gate. Outside that collector's
validated identity and Arm generation, the original public wait is used.

While this scope is active, a private Condition predicate can return after a
different accepted heartbeat sequence on the same PID/connection, a public
revision change, or a connection boundary. The next operation is the existing
`take_internal_semantic_snapshot`; the unchanged outer predicate and absolute
deadline decide whether anything happened in the game. No frame, date,
revision, result, cycle, or success is manufactured by the helper. An identity
boundary is passed back to normal snapshot/error handling, never admitted as
same-identity progress. Repeated heartbeat sequence values do not wake it.

The candidate does not change public_revision, public wait semantics, timeout
values, pause cleanup, sentinel/Arm ownership, the B DTO or its flags. It adds
no timer polling, Native query, RPC, Game/Task/desktop call, I/O, or thread.
The Condition consumes existing receiver notifications. Candidate snapshots
still read the existing semantic cache and may remain identical.

The necessary counterexample is explicit: 120 heartbeats over the original
30-second wait, with no changed semantic frame, cause additional local
candidate observations but still return the unchanged date at the original
deadline. This does not repair the stalled game clock or produce throughput
credit. Additional cache reads may cost time. A semantic date change already
wakes the original public wait, so this candidate does not improve its wake
time. The possible benefit is narrower observation gaps and prompt transport
boundary handling during an exact-day wait; actual need and cost remain
unknown until Root reviews the first real FULL and B result.

Run once with `py -B -X utf8` on `qualify_candidate.py`. It executes selected
actual generated Driver methods against a deterministic, in-memory Condition
model; it never imports the full Driver. The actual public state wait is used
as the comparison. No old test matrix is repeated. Full input inverse and
unowned function AST equality guard source scope. Generated full Driver bytes
remain in RAM. Only a small patch and qualification JSON are materialized in
the exact assigned D performance lane; no temporary fixtures are needed.

Budget: source/test allocated bytes plus conservative filesystem overhead
must fit 65,536 B; D evidence plus overhead must fit 196,608 B. Review expires
2026-10-20T06:30:00Z. Retain this compact source/proof until that review; no
runtime adoption or automatic renewal is authorized by this package.

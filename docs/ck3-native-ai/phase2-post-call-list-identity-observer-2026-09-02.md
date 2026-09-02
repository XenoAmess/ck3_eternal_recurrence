# Phase-two post-call list identity observer (2026-09-02)

The prior exact-build live captured one complete 27-descriptor producer list at
`0x3407DA1`, but none matched callback slot 2 `module+0x88B480`. Its v1
telemetry retained only the last raw descriptor, so it could not distinguish a
stale selector from a different task population.

This distinct private observer keeps the same frozen 14-byte anchor and scans at
most 4,096 descriptors without modifying them. For the most recent hit it keeps
up to 64 descriptor samples with descriptor index, task, owner, callback,
slot-2 target/RVA and task state. A separate 64-bin histogram records the count
and first/last task-owner association for each slot-2 target. The current
27-item target therefore fits in full; sample, histogram, scan and capture
contention overflows are all explicit rather than silently truncated.

The observer is default OFF behind
`XAR_CK3_ENABLE_PHASE2_POST_CALL_LIST_IDENTITY_OBSERVER_V1`. It has its own
exact-anchor transactional install, recoverable rollback and standalone
quiescent unload. Its atomic odd/even snapshot sequence keeps heartbeat reads
consistent with the bounded writer. It does not coexist with the older private
observer because both own the same RVA.

This package is source-ready only. It does not start CK3 and does not change the
public bridge ABI or readiness. A future single bounded live can directly list
the 27 slot-2 RVAs, state whether `0x88B480` occurs, and map every retained
task/owner to its callback target.

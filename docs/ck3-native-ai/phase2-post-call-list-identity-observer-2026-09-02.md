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

The single bounded live subsequently captured one internally consistent
27-descriptor snapshot. All 27 callback slot-2 RVAs were `0x817C20`, all shared
one owner, states were 25 at 1 and 2 at 0, and `0x88B480` occurred zero times.
There were no read, truncation, capacity, or contention errors. Exact-build
static classification then identified `0x817C20` as the
`SPdxParallelForOverArray` range worker: 278 RTTI vtable slot-2 references point
to it. It is not a loader completion callback, so this observer/live shape must
not be repeated.

## Acceptance wiring for the next observer

The seed/paused runner has an opt-in static handshake:

```text
--list-domain-observer-gate
--acceptance-observer-manifest <frozen-native-seam.json>
```

The canonical source contract is
`tools/zg361_phase2_list_domain_acceptance_contract.json`. With only the first
flag, no-launch preflight preserves its source/ZIP/dependency manifests and
returns typed `native_observer_manifest_pending`; it cannot reach the native
supervisor or bridge driver. Supplying a native manifest also freezes that
manifest as an external dependency and checks the exact source commit, game
build, private DLL/injector hashes, and source-relative ABI/source-contract
hashes. Existing seed/paused calls that do not opt in are unchanged.

The verified next seam is the real producer pair `0x3B9CFD2` and `0x3B9CFD7`.
At each entry it observes the `RBX` task and the callback object at
`[RBX+0x38]`. The first private producer observer reached both seams 1,838
times and retained `0x817C20` as its last slot-2 RVA, but its last-value-only
shape cannot establish the distribution. It must not be repeated.

The distinct v2 contract therefore requires a bounded 64-bin slot-2 histogram,
an exact `0x88B480` selected count and the first/last selected task, state,
callback, vptr and slot-2 identities. Overflow and read failure are explicit.
Acceptance does not choose another address. The remaining native-owned
manifest fields are the two anchor hashes, private option, ABI/source-contract
paths and hashes, and final report artifact name. The heartbeat and report
schema are fixed by the acceptance contract. Until the native v2 manifest
arrives, this remains static wiring and no CK3 attempt is authorized. See
`phase2-producer-histogram-live-postprocess-2026-09-03.md` for the parser and
decision matrix.

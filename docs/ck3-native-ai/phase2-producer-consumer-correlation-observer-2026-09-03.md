# Phase 2 producer-to-consumer correlation observer (2026-09-03)

## Source-ready result

The histogram live at exact source commit
`161962558e78d2351d136fb6d9fe15a35f12e983` proved that the loader callback
`0x88B480` published state 2 once, while the existing completion consumer
hook at `0x3B9DEA7` previously ran 1,908 times without observing any state 2
or 3. The remaining bounded question is whether that consumer ever receives
the same task identity after completion. The live evidence index SHA-256 is
`5F5985701FF304D59ABA611806E85A5CA5696ACC5078BC8A63A55DBAB3FFA468`.

This package adds a distinct private-only dynamic correlation seam. The D7
producer observer retains the exact `0x88B480` selected task pointer. The
completion observer compares each complete-state `RBX` against that retained
pointer and records match count, task state, reference count, callback pointer
and presence, thread, and QPC. This comparison is independent of the old
callback-slot equality filter, so it remains informative after callback
identity changes.

## Exact-build and lifecycle boundary

The contract remains bound to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`.
It composes the already frozen producer transaction at `0x3B9CFD2` /
`0x3B9CFD7` and completion consumer hook at `0x3B9DEA7`; it introduces no new
patch address. Both existing transactions keep their exact-anchor install,
recoverable rollback, quiescent uninstall, and original-flow replay contracts.

The build option
`XAR_CK3_ENABLE_PHASE2_PRODUCER_CONSUMER_CORRELATION_OBSERVER_V1` is OFF by
default. Enabling it privately includes both underlying observers and emits a
separate `phase2_producer_consumer_correlation_observer_v1` heartbeat object.
The default heartbeat, public bridge ABI, readiness decision, and game state
are unchanged.

## Decision boundary

- A selected producer count greater than zero with zero consumer matches means
  the complete-state consumer did not present the retained task during the
  bounded window.
- A nonzero match records the exact consumer-side state/reference/callback
  context and closes the producer-to-consumer identity edge.
- Any correlation context read failure is a typed diagnostic RED.

The consumer thunk calls the recorder only for state 2 or 3. Therefore a zero
match does not say whether the scheduler saw the task in state 0 or 1, nor
does it prove absence from all other containers. It is nonetheless the
minimum distinct observation that tests the evidence-backed identity edge;
it does not repeat the old unfiltered timeout or broaden into generic loader
scanning.

No CK3 process was started for this source-ready package. A future live run
requires a fresh exact integration freeze and serialized authorization.

The MSVC x64 Release private DLL SHA-256 is
`6066A60C01F7F6D9AC4F967C3953EDD95C93409976F54A908711C91864B92305`;
the private injector SHA-256 is
`7AB181019C70EB789C358B61AD6FA7E5C210398835B82B84E894F5BC21069382`.
The default-OFF DLL SHA-256 is
`D7BBC5B04445CB20F2DDB2C0AD068147F30CA26BA532C34A93C2708015953B68`,
and its bytes do not contain the correlation heartbeat token. Both native
fixtures and the Python source contract passed in normal and optimized modes.

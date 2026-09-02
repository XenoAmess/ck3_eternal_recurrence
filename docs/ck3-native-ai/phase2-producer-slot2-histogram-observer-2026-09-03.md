# Phase 2 producer slot2 histogram observer v2 (2026-09-03)

## Evidence boundary

This private observer is bound to CK3 `1.19.0.6`, executable SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
and the already frozen producer transaction at RVAs `0x3B9CFD2` and
`0x3B9CFD7`. It reuses the transactional install, rollback, and uninstall
lifecycle of `XAR_CK3_ENABLE_PHASE2_PRODUCER_IDENTITY_OBSERVER_V1`; the option
remains OFF by default and does not change the public ABI or readiness.

The preceding single live run observed 1,838 paired D2/D7 entries but exposed
only the final callback identity (`slot2 RVA 0x817C20`). That evidence could not
answer whether the same producer transaction ever publishes the loader callback
at exact RVA `0x88B480`. This v2 seam is the minimum distinct read-only
observation needed to answer that question without repeating the old loader
timeout or the list-domain scan.

## Frozen private report contract

Heartbeat object `phase2_producer_slot2_histogram_observer_v2` reports a fixed
64-bin `callback_slot2_rva_histogram` over D7 observations. Each bin contains
`slot2_rva` and `count`. It also reports explicit capacity, occupied-bin count,
overflow, and histogram read failures. The exact target `0x88B480` has a
selected counter plus first/last task, state, callback, vptr, slot2 target/RVA,
owner, thread, and QPC identities.

A terminal candidate is eligible for GREEN classification only when:

- D2 count equals D7 count;
- `sum(bin.count) + histogram_overflow_count + histogram_read_failure_count`
  equals D7 count;
- general read failures, histogram read failures, and overflow are all zero;
- if selected count is non-zero, first and last identities agree except that
  first QPC may precede last QPC.

The canonical JSON Schema remains at
`ck3_autonomous_player/native_bridge/research/phase2_producer_identity_observer_v1_report.schema.json`;
the legacy filename is retained because v2 intentionally reuses the existing
private build option and hook lifecycle. Live classification is owned by the
acceptance-side `analyze_phase2_producer_histogram_live.py`; this package does
not add a competing postprocessor.

## Static verification

Both the private-enabled and default-OFF Release configurations compile with
MSVC. The native fixture exercises selection, 64 distinct bins, one bounded
overflow, and the invalid-slot2 read-failure path. The Python contract test
locks the option boundary, exact anchors, capacity, selected RVA, heartbeat
name, manifest artifact name, and report fields. The v2 heartbeat token is
present in the private DLL and absent from the default DLL.

No CK3 process was started for this package. Final source ZIP and acceptance
manifest must be regenerated only after this commit is integrated with the
acceptance implementation, so the candidate represents one exact product
state.

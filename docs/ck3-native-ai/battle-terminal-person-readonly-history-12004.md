# Person query transcript export on CK3 1.20.0.4

The registered `ck3_query_battle_terminal_transition_v1` uses one existing
Service and NativeDriver. It does not construct or reload a driver per request.
Before this correction, five internal frame snapshots exported the complete
retained command history: the Service precheck, Driver precheck, primitive
submission snapshot, Driver postcheck, and Service postcheck.
`_history_snapshot` deep-copies every retained result. These frame checks consume
semantic identity, pause, revision,
date and connection fields; they do not consume the exported transcript.

The correction selects `include_native_command_history=False` only at these
five sites. Public snapshot defaults, explicit full-history export, native
packet validation, pre/post frame checks, command-result recording, and
persistence barriers retain their existing behavior.

The registered `ck3_take_snapshot` already defaults to omitting command history.
It therefore follows a different export path from the former Person query.

## Disk I/O and startup boundary

`NativeHeadlessGameplayDriver.__init__` starts its endpoint. The first received
hello invokes `_adopt_bridge_session`; only its first-connection branch calls
`_read_driver_state`. The loader reads and parses the entire Driver JSON, then
detaches its history. Same-PID adoption copies that restored history and requests
a complete state rewrite. This work belongs to hello/adoption, which may overlap
an initial snapshot request, rather than to every stable readonly query.

Successful `query-*` commands append a detached result to in-memory history and
mark it dirty while deferring the full state write. Failed commands retain the
existing immediate persistence barrier. `_persist_driver_state` serializes the
entire history and atomically replaces the Driver state file; `close` flushes
dirty history. Episode binding, identity changes and newly observed marriage
outcomes also have conditional persistence paths. They do not prove a write on
every snapshot. The `native_campaign` episode projection bypasses one-life
episode binding.

Root observed the SDK085 initial snapshot take 51.36 seconds and Person002 take
87.66 seconds on 2026-10-10. Source inspection establishes the repeated export
cost, not its measured share of either duration. A separate cached native-reader
47 ms value is uncorrelated and cannot be subtracted from these timings.
The source-flow receipt is retained in
`Z:/ck3_mod_rewrite_process_assets/g2-background-20261010/r85-snapshot-performance-metadata/SOURCE-FLOW.json`.

## One new connected regression

`test_registered_terminal_query_omits_history_and_preserves_command_evidence`
uses the unchanged qualified Native60 `matching-final-tail-ordered-i64.json`
through real registered MCP, Service, NativeDriver primitive transport and
normalizers. A retained-payload copy detector checks that the query exports no
full transcript while preserving prepared PC order, full signed64 values and
command evidence. The same compound checks explicit detached history export,
stale submission rejection and changed post-query frame rejection. Root alone
runs this new test; the native producer and earlier compounds are not replayed.

This source correction assigns no new live, FullPerson, Entry or whole-helper
readiness credit. Runtime latency improvement remains unmeasured at author time.

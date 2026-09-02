# Phase-two producer histogram v2 postprocessor (2026-09-03)

## Why v2 is distinct

The producer v1 live reached both `0x3B9CFD2` and `0x3B9CFD7` 1,838 times and
retained `0x817C20` as its last callback slot-2 RVA. That is useful proof that
the real producer seam is active, but a last-only value cannot distinguish a
uniform parallel-for population from a mixed population containing the
selected loader callback at `0x88B480`. Repeating v1 cannot answer the question.

The next native observer must publish
`phase2_producer_slot2_histogram_observer_v2`. It records a cumulative,
read-only histogram at the `0x3B9CFD7` producer publication seam with exactly
64 bounded bins keyed by callback slot-2 RVA. It also records:

- entry counts for `0x3B9CFD2` and `0x3B9CFD7`;
- exact selected count for `0x88B480`;
- first and last selected task pointer/state, callback pointer, callback vptr,
  absolute slot-2 target, slot-2 RVA, owner, thread and QPC;
- histogram overflow, histogram-specific read failure and general read failure.

The heartbeat uses `callback_slot2_rva_histogram` bins shaped as
`{slot2_rva,count}`. Because sampling is D7-only, the terminal relation is
`sum(bin.count) + histogram_overflow_count + histogram_read_failure_count ==
producer_0x3B9CFD7_entry_count`; the paired terminal counters must also satisfy
`D2 == D7`.

The authoritative field list and native-manifest handshake are in
`tools/zg361_phase2_list_domain_acceptance_contract.json`. The postprocessor
contract is
`ck3_autonomous_player/native_bridge/research/phase2_producer_histogram_live_postprocess_v2_contract.json`.
Neither contract supplies native anchor or implementation hashes; those remain
inputs from the native observer implementation.

## Frozen identity boundary

Before any outcome is classified, the runner gate binds the native manifest to
the exact Git commit, clean-source tree hash, source ZIP hash, CK3 executable,
private bridge DLL, injector and named pipe. The postprocessor then rechecks the
manifest SHA embedded by that gate and requires every heartbeat PID to equal
the runner's bound bridge PID. A mismatch is RED, not an observation result.

The parser is read-only and never starts CK3:

```powershell
py -B ck3_autonomous_player/native_bridge/research/analyze_phase2_producer_histogram_live.py `
  --runner-report <attempt>/artifacts/runner-report.json `
  --observer-manifest <frozen-native-seam.json> `
  --output <attempt>/artifacts/producer-histogram-v2-postprocess.json
```

## Decision gate

- Schema, source/session identity, installation, counter or histogram relation
  failure is `RED`.
- No producer hit, any overflow/read failure, or `selected_count == 0` is
  `NO-GO` with `next_gate_allowed=false`.
- A selected hit whose first and last task/state/callback/vptr/slot2/owner or
  thread differs is also `NO-GO`; first QPC may precede last QPC but may not
  regress. The result is not promoted using the last sample alone.
- Only a complete histogram with `selected_count > 0`, an exact selected bin
  count, and identical valid first/last selected identity is `GREEN` with
  `next_gate_allowed=true`.

GREEN authorizes only the next Phase2 acceptance gate. It does not make the
private observer public, change loader readiness, or claim a paused seed.

# Phase-two completion observer RED analysis (2026-09-02)

The single frozen live attempt at commit `25b6036` ended in the typed RED
`loader_terminal_missing_after_database_completion_publish`. Its final
heartbeat proved that the private observer was installed with no failure, but
all selected counters remained zero. The runner report SHA-256 is
`25A3C8C56A46A674D7E4F064D5FB7E02577F15737CD2ADC907CAC44038C13FE7`;
the terminal evidence index SHA-256 is
`AF847AEF53B7E16AAFAEC06916D8A7BE1D1206A8AF4B374FB4235B41298C8FB9`.
Cleanup, source identity, and runtime-tree checks were GREEN. This package did
not start CK3 or repeat the timeout.

## Exact-build ordering

The bounded wrapper `[0x3B9E030,0x3B9E266)` calls the completion consumer
`[0x3B9DD50,0x3B9E025)` at `0x3B9E10B` and `0x3B9E175`. Only after those two
calls does it enter the producer loop at `0x3B9E230..0x3B9E246`, where it calls
helper `0x3B9CF50`. The selected callback publishes state 2 at `0x3B9CFD7`,
and the wrapper returns at `0x3B9E265`.

Therefore the consumer at `0x3B9DEA7` cannot observe that newly published
selected task during the same wrapper invocation. It requires a later wrapper
invocation. The prior zero selected count is consequently consistent with the
wrapper never returning to the consumer after the publish; it does not by
itself prove an incorrect callback selector.

## Minimal private diagnostic

The observer now increments `raw_hit_count` inline before state classification.
This adds no function call to the non-complete path. For state 2 or 3, the
existing telemetry thunk records unfiltered state counts and the last callback,
slot-2 target, and reference count before applying the unchanged `0x88B480`
selector. A future bounded run can distinguish:

- no execution of the patched consumer read;
- consumer execution without any completed task;
- completed tasks whose callback identity misses the selector; or
- the selected task reaching the existing retire telemetry.

The diagnostic remains behind the existing private build option. It neither
changes game state nor expands public ABI, default heartbeat schema, or
readiness. The machine-readable contract is
`phase2_completion_observer_red_analysis_v1.json`.

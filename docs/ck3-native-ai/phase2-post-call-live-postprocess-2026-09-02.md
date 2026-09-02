# Phase-two post-call live postprocessor (2026-09-02)

The read-only postprocessor freezes the exact private
`phase2_post_call_observer_v1` schema: three control fields and the 27 telemetry
fields from the observer ABI. It validates installation/failure state, monotonic
counters and QPC, list begin/count and the 4,096-descriptor bound, scan and
selection counters, raw and selected descriptor/task/owner/callback identities,
callback slot 2, task state, thread and timestamp context.

Its typed matrix separates harness/schema RED from evidence outcomes:
`no-hook-hit`, `empty-list`, `scan-no-selected`, `selected-state0`,
`selected-state2`, `selected-state3`, and `context-incomplete`. A typed GREEN is
only a valid private observation; it does not promote native readiness.

The sole live report SHA-256
`35174DC74CE6D8B5301ABDD07B29AE02FCC9BC0CE8ECCA2104E983AEE805025C`
classified as `scan-no-selected`: installed was true, failure was zero, the hook
ran once, its non-empty list held 27 descriptors, all 27 were scanned, and there
were no read failures or truncations. No descriptor matched the frozen
`module+0x88B480` selector. The last raw descriptor had state 0, but the v1
schema retains only one last raw identity, so that value cannot characterize the
other 26 callbacks.

The next distinct private observation is therefore a bounded histogram of every
scanned callback slot-2 RVA keyed by task and owner identity. This distinguishes
an outdated selector from a different producer-list task population. Repeating
the current last-value-only capture would not add that evidence. No CK3 process
is started by the parser, and no public ABI, readiness, daily report or weekly
report is changed.

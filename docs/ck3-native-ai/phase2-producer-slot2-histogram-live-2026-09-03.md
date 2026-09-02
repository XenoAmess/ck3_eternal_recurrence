# Phase 2 producer slot2 histogram live (2026-09-03)

## Result

The one authorized exact-build live run closed the producer-domain ambiguity.
The seed runner still ended RED at the existing loader terminal timeout, but
the private histogram observer and its read-only postprocessor were GREEN.
This is not public native readiness and it does not justify repeating the same
loader run.

The run used source commit
`161962558e78d2351d136fb6d9fe15a35f12e983`, CK3 `1.19.0.6`, executable
SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`,
and PID 26828 from `2026-09-02T17:10:38.460176Z` through
`2026-09-02T17:16:00.156849Z`.

## Native evidence

The D2 and D7 counters both reached 1,838. The 64-bin bounded histogram used
25 bins and accounted for all 1,838 D7 observations, with zero overflow,
histogram read failures, or general read failures. The prior range-worker
callback `0x817C20` appeared 107 times, so the earlier last-only sample was not
representative of the complete producer domain.

The exact loader callback `0x88B480` appeared once. Its selected first and last
identities were identical:

- task and callback: `0x2498E2CE410`;
- state: `2`;
- callback vptr: `0x7FF699DFCF20`;
- slot2 target: `0x7FF6965BB480`;
- owner: `0x249FCB33E38`;
- thread: `43840`;
- QPC: `553004480436`.

The canonical postprocessor decision is
`selected-consistent-next-gate` with `next_gate_allowed=true`. This proves that
the real loader callback did execute and publish completion state in the
generic producer transaction. It does not prove that the scheduler later
visited that exact task, nor that loader readiness was published.

## Evidence and cleanup

- runner report:
  `Z:\p2r-histogram-1619625-live-artifacts\runner-report.json`, SHA-256
  `1A6D4FD930F9C4BC4B7AB14D02A769666933F3A833884329865CC2D958BB46F1`;
- histogram postprocess:
  `Z:\p2r-histogram-1619625-live-artifacts\phase2-producer-slot2-histogram-v2-postprocess.json`,
  SHA-256 `F50DF3775DCB34F393A4E0DAF1D4B9036EA3F19975B21C5CE37819C6A824E990`;
- cleanup:
  `Z:\p2r-histogram-1619625-live-artifacts\09_phase2_native_session_cleanup.json`,
  SHA-256 `9C801DA2C7E9FC518BF42881D56B5656C458553E4150398C6094FD463ED9D6A9`;
- frozen source ZIP SHA-256
  `29CDF95B17599BA4C0138AA32D8E71D58EEAD73C2F37797414E48832CA93D9A4`;
- observer manifest SHA-256
  `795B6F1517EB756CB0A08EB018D2F6CF0DAC797AAE88CE69BE9304DB7CE9FBD9`.

Cleanup, clean-source immutability, runtime projection immutability, and
external dependency immutability were all GREEN. No legal modal appeared and
the legal handler made zero clicks. CK3 and the injector were absent after the
managed session ended.

## Next distinct seam

The old unfiltered consumer observation proved that `0x3B9DEA7` executed many
times but never saw state 2 or 3, while this run proves that one exact loader
task published state 2. The remaining gap is task identity flow between the
selected producer task and the scheduler consumer, not callback execution.

The minimum next private observation should therefore retain the selected task
identity from D7 and compare it against each `RBX` presented at `0x3B9DEA7`,
recording match count, first/last state, reference count, callback-present
state, thread, and QPC. This dynamic pointer correlation distinguishes
"consumer never enumerated the selected task" from "consumer reached it after
callback destruction or state transition" without scanning generic callers,
guessing an OS wait, changing public ABI/readiness, or repeating this producer
histogram live.

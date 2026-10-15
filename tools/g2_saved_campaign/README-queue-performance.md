# Queue metadata scanning and P12 timing baseline

P12 adopted the existing four-directory artifact budget using `os.scandir`.
Each guard enumerates fresh directory entries, tests regular files with
`follow_symlinks=False`, and uses one cached `DirEntry.stat` per counted file.
The four flat roots, capacity limit, reply reserve and volume guards remain
the caller's existing values. No recursive traversal, cross-guard byte cache,
ledger, Game read or Native capability is added.

The generic preparation tool changes only the legacy `artifact_bytes` method
and asserts that the rest of the module AST is unchanged:

```text
python -B -X utf8 tools/g2_saved_campaign/prepare_queue_artifact_scan.py --input ORIGINAL_QUEUE.py --output NEW_CANDIDATE.py
python -B -X utf8 tools/g2_saved_campaign/test_queue_artifact_scan.py
```

The output must be a new file. The tool targets the original flat
`Path.iterdir/is_file/stat` comprehension; an already optimized queue does not
need this preparation. Session names and roots come from the input AST.
The portable tests retain tiny exact P11/P12 method excerpts and check byte
equality, changed-file refresh, flat scope, no-follow flags, and source identity.

A read-only metadata benchmark of the halted P11 directories counted exactly
177,877,170 bytes in all three comparisons. Median time fell from 1.738966 to
0.036291 seconds. The source calls the guard before each RPC and once more
before each full-loop AUTO. Around 438 guards in the measured window could
therefore account for about 746 seconds of the 785-second inter-RPC gaps.
That is a source-call estimate, not an end-to-end live speed measurement.

The adjacent checkpoint helper also carries an already due checkpoint through
pure readonly query chains. This prevents SAVE from invalidating the current
revision-bound declaration/assessment chain halfway through it. It does not
reuse those observations across a revision, change war willingness or extend
the existing opportunity-check cooldowns. See [checkpoint cadence](README-checkpoint-cadence.md).

## Fixed actual baseline for P13 comparison

The retained [P12 timing baseline](fixtures/p12_actual_timing_baseline.json)
comes only from completed immutable response files:

| Window | Game days | Wall seconds | Seconds/day | RPC seconds | Inter-RPC seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| P12 responses 4-137 |63|571.600|9.073|524.203|47.397|
| P12 after first opportunity sweep, 18-137 |56|469.714|8.388|464.015|5.699|

The second window spans 2026-10-15 01:23:08.741532 to 01:30:58.455293 UTC,
raw dates 53195784 to 53197128. Median inter-RPC gap was 0.023671 seconds.
It includes eight actual seven-day ordinary advances and five successful
checkpoint RPCs. Declaration queries remained 14.520 seconds median,
assessment33026 6.812 seconds, assessment30380 5.315 seconds, and faction
queries 7.035 seconds. These step-level figures support a like-for-like P13
query comparison without treating the whole phase mix as identical.

Frozen P12 queue SHA256:
`3cf69857efa9e6ef911d9e9375093c6d795389e45ca3fd697329a74b2a6a14c1`.

Frozen P12 carry-helper SHA256:
`d0137da2ca039836f63a612630cdfed341861bd302468477b48d34371eeb8d79`.

P11's last 300 response rows advanced 63 days at 31.437 seconds/day, with 1195.487
RPC seconds and 785.023 inter-RPC seconds. P12 starts smaller directories and
has a different query distribution; the observed difference is not a pure
causal estimate of either patch. The baseline is a short peace/opportunity
sample, not a 30-year throughput promise. Nested service timers are wall time,
not disjoint CPU costs, and Driver-state file size is not command-history size.

Raw external reports remain at `p11-fullcycle-perf01` and
`p12-durable-performance01` under the Robert demo evidence root. They may
expire under the storage policy; the compact baseline, method excerpts and
provenance hashes are retained in the repository. No live Driver was read.

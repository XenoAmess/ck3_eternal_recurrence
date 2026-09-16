# User picture corpus v10 — high-resolution hybrid repair

Status: **browser quality gates passed; superseded by v11 for final preview-projection evidence**.

This run moved the 256px repair phase onto the hybrid candidate that still had unused user budget and made
the phase render with the complete emblem texture map. Each accepted layer had to be Pareto-safe at 256px
and non-regressing at 96px for both total and edge loss.

| Case | v8 instances | v10 instances | v8 total | v10 total | v8 edge | v10 edge | 256px layers accepted |
|---|---:|---:|---:|---:|---:|---:|---:|
| picture-02 | 580 | 640 | 0.035329 | 0.033979 | 0.064976 | 0.063220 | 60 |
| picture-05 | 881 | 917 | 0.057423 | 0.052995 | 0.100367 | 0.095896 | 36 |
| picture-07 | 956 | 986 | 0.053918 | 0.049606 | 0.090944 | 0.086218 | 30 |

picture-01/03/04/06 had already consumed all 1,024 slots and remained exactly at their v8 metrics. All seven
cases passed complete copy, parse, instance-count, serialize and same-data-URL preview gates. This run
predates the visible candidate-card projection fix and is therefore not the final UI evidence. No CK3 native
run was made for v10.

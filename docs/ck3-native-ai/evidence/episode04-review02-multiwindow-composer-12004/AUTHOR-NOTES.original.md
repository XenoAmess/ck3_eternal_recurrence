# Multiple explicit windows from one raw — candidate

The single-cue rule is an implementation constraint in `episode04_review02_mixed_rough.compose`, not a rule found in the current director or research-status documents. The old `raw_windows[resolved_path]` both rejected a second cue and supplied the seek inside `planner(**kwargs)`.

This candidate uses the existing `SegmentDraft.start_seconds` field, which xar_promo 0.3.0 forwards to its render planner. Each cue keeps its own seek. A shared path must retain identical bytes, SHA-256 and source frame count. Existing interval bounds, measured cue duration, pending guards, rough labels and FHD subtitle area remain intact. No media engine or CLI is added. Root can review the candidate module as a replacement for the current project composer; main was not changed.

The supplied new input adds only R194 C05-10 to the R196 candidate:

| Cue | Encoded frames | Seconds | Existing evidence |
|---|---:|---:|---|
| C05-06 | [0,857) | 0–28.566667 | Actual samples 0=250 and 189=75; split context, precise action frame unknown. |
| C05-10 | [1055,1887) | 35.166667–62.9 | Sample1055 already merged; post-merge rereading context. It does not show marching to a rendezvous. |

Both reference the same R194 raw SHA `763bbbec18149543f7ed4d36dc761aa8fe258366037d2727390a25f64d18f1e4`, 71,202,833 bytes /3467 frames. These are authored windows, not new event PTS or independent experiments. Old voice is unchanged. The conditional rendezvous definition in C05-10 must not be represented as a filmed arrival.

Candidate counts are 4 rough /20 cards /45 pending; canonical counts remain 3/20/46. Research, business, 11 dynamic cards and ABC gain no credit. R196 remains on its existing single window. Continuous clean, event synchronization and signoff remain unclaimed.

`verify_multiwindow_a01.py` checks one behavior: the baseline rejects these two windows, while the candidate produces two immutable engine plans with different actual input seeks and the existing display geometry. No ffmpeg, probe, raw/audio read, new frame, native run or render is executed. The initial check's redundant-zero-seek assumption is retained in `CHECK-ATTEMPT01.actual.json`; the corrected check passes. All 69 unchanged cues remain in the draft.

Latest official release was freshly queried as v0.3.0; the installed interpreter already reports 0.3.0, so the shared environment was unchanged. `ROOT-DELIVERY.actual-a01.json` carries exact file pins and current machine identity.

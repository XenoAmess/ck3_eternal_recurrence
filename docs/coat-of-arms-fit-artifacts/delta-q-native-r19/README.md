# Delta-Q quality-first native r19

This managed CK3 `1.19.0.6` run applies the seven final quality-first documents
from `delta-q-residual-repair-v1/real-budget-1024-v9-final-quality-first`.
Steam remained offline. Navigation, bounded chunk upload, Apply, native Copy,
reference-independent framebuffer calibration/capture, and Copy re-Apply used
structured MCP only; OCR, keyboard, mouse, and fixed screen coordinates were
not used.

The aggregate runner exits RED because it intentionally treats every literal
source-field change as a failure: CK3 normalizes fractional rotations in
picture-01/02/04/05/07. All seven preserve logical-layer, colored-emblem-block,
and actual-instance counts. The two pixel gates required by Delta-Q are GREEN:
browser exact-DDS preview → first CK3 Apply is 7/7, and native Copy → re-Apply
is 7/7. The Copy-normalized source itself is stable on the second round-trip.

## Native pixel gates

The nine-point UV calibration recovered the canonical surface at
`2560×1440`; maximum reprojection error was `0.3396 px` against the frozen
`2.5 px` limit. Browser → CK3 limits are MAE/MSE/edge/worst-spatial
`0.10 / 0.03 / 0.16 / 0.25`; Copy → re-Apply limits are
`0.01 / 0.001 / 0.02 / 0.03`.

| Case | Instances | Browser→CK3 MAE | MSE | Edge | Worst block | Copy re-Apply MAE | Copy edge | Strict source fields |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| picture-01 | 739 | 0.015853 | 0.001568 | 0.067764 | 0.049226 | 0.0000347 | 0.000220 | rotation normalized |
| picture-02 | 729 | 0.019482 | 0.001811 | 0.094466 | 0.053355 | 0.0000370 | 0.000270 | rotation normalized |
| picture-03 | 1,024 | 0.021867 | 0.003095 | 0.090896 | 0.078919 | 0.0000336 | 0.000202 | pass |
| picture-04 | 971 | 0.036482 | 0.006373 | 0.132058 | 0.083766 | 0.0000581 | 0.000346 | rotation normalized |
| picture-05 | 922 | 0.037478 | 0.007890 | 0.117909 | 0.116166 | 0.0000700 | 0.000365 | rotation normalized |
| picture-06 | 1,024 | 0.024540 | 0.005918 | 0.068414 | 0.112940 | 0.0000515 | 0.000221 | pass |
| picture-07 | 1,024 | 0.025318 | 0.004187 | 0.095729 | 0.102397 | 0.0000264 | 0.000175 | rotation normalized |

The worst first-Apply values are `0.037478 / 0.007890 / 0.132058 / 0.116166`;
the worst Copy re-Apply values are MAE `0.0000700`, MSE `0.000000275`, edge
`0.000365`, and worst-spatial `0.000289`. Every value is below its predeclared
limit. Literal source-field equality is 2/7, while the native pixel contract,
Copy re-Apply pixel contract, and instance/block/layer preservation are all
7/7.

## Provenance and cleanup

- Compact [`summary.json`](summary.json): 65,408 bytes; exact SHA-256
  `93893817DD11018893A02057CA9C15FA06F929ACAE3686909D47A8CBBA9FCE5A`.
- Payload-heavy `raw-report.json`: 21,528,101 bytes, SHA-256
  `BB9A865DE8BD8FD497E3C035F22209DF152A4218ABB9DF65B0E56D83EE3F0863`;
  retained locally and excluded from Git like earlier native raw reports.
- Source head recorded by the runner: `d044e7523dc87ffa4613da2e9a72b2328abf31f8`.
- Native bridge SHA-256:
  `5479AB468CDAC9240CBE6684743DFF7104D654F3B8C4D13D7629026408C22B57`.
- Injector SHA-256:
  `880885ABBF26C0D4147CFB55B70C5608B581F40C4229099D44A610B5CD589137`.
- The shared launch/state locks were acquired and released. CK3 PID 27692 and
  watchdog PID 23120 were both proven absent; final active-process count was
  zero and `cleanup_proven=true`.

This evidence closes Delta-Q's native visual gate. It does not relabel CK3's
fractional-rotation normalization as literal source preservation, and it does
not claim cross-session A/B values that the run did not measure.

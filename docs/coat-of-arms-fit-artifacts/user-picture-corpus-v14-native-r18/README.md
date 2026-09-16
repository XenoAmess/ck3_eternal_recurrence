# user-picture-corpus-v14-native-r18

This managed CK3 1.19.0.6 run applies the quality-priority result for every
case in `user-picture-corpus-v14-pareto-budget-1024`. Steam remained offline.
Navigation, bounded chunk upload, Apply, native Copy, framebuffer calibration,
capture and Copy re-Apply used structured MCP only; OCR, keyboard, mouse and
fixed screen coordinates were not used. The exclusive launch/state locks were
acquired and released, and the CK3/watchdog process trees were proven gone.

The aggregate runner exit is RED only because CK3 normalizes fractional
rotation values in picture-02/05/07. Those three cases fail literal source
field equality at `rotations` and nothing else. Every case preserves logical
layers, colored-emblem blocks and actual instances; native Copy is stable when
re-applied, with no truncation.

## Absolute native gates

Reference-independent v3 calibration recovered canonical UV from nine native
markers at 2560×1440. Maximum reprojection error was 0.333 px against the
frozen 2.5 px limit. Browser → CK3 limits are MAE/MSE/edge/worst-spatial
`0.10 / 0.03 / 0.16 / 0.25`; Copy → re-Apply uses the stricter
`0.01 / 0.001 / 0.02 / 0.03` limits.

| Case | Instances | Browser→CK3 MAE | MSE | Edge | Worst block | Copy re-Apply MAE | Copy edge | Strict source fields |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.016431 | 0.001992 | 0.065070 | 0.058980 | 0.0000353 | 0.000225 | pass |
| picture-02 | 586 | 0.016325 | 0.001790 | 0.071822 | 0.044069 | 0.0000216 | 0.000162 | rotation normalized |
| picture-03 | 1,024 | 0.021694 | 0.003228 | 0.086067 | 0.084848 | 0.0000361 | 0.000218 | pass |
| picture-04 | 1,024 | 0.033106 | 0.005807 | 0.107784 | 0.125901 | 0.0000773 | 0.000362 | pass |
| picture-05 | 904 | 0.033540 | 0.006278 | 0.107656 | 0.088064 | 0.0000780 | 0.000395 | rotation normalized |
| picture-06 | 1,024 | 0.020595 | 0.004081 | 0.056741 | 0.095583 | 0.0000331 | 0.000154 | pass |
| picture-07 | 987 | 0.024496 | 0.003599 | 0.085987 | 0.158394 | 0.0000468 | 0.000268 | rotation normalized |

Thus browser → CK3 pixels pass 7/7, Copy → re-Apply pixels pass 7/7, strict
source field sequences pass 4/7, and all seven documents preserve their
instance/block/layer counts. The maximum absolute MAE/MSE/edge/worst-spatial
values are `0.033540 / 0.006278 / 0.107784 / 0.158394`, all within the
predeclared gates.

`same-native-reference-comparison.json` rescores v13 and v14 canonical browser
PNGs against each exact r18 native crop. All seven pairs are numerically equal
for MAE and edge, which is expected: the v14 fix changes the comparison-card
presentation from 96px to canonical 230px; it does not rewrite the already
canonical quality-priority document/preview. This isolates the reported
right/lower browser mismatch from the browser/native renderer relationship.

`summary.json` is 65,284 bytes, SHA-256
`5255F643880849FBE2992D3D8F4F2EB37D5740E22DB44CD42A82F36CA0408D44`.
The ignored raw report is 22,031,974 bytes, SHA-256
`F25EAF97A955EF9995C727C9BD529E117EAFEFF89E7CD9150C85242250A1F426`.
The same-native comparison is 49,060 bytes, SHA-256
`D771944F97EAF099B89331C6DDB2563EB5085060AF9730B76A3FE739B57FEFAC`.

Reproduce the compact summary and offline same-native comparison:

```bat
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\summarize_native_picture_corpus.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-native-r18\raw-report.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-native-r18\summary.json
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\compare_native_aligned_previews.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-native-r18\summary.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v13-mip-aware-budget-1024 docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-pareto-budget-1024 docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-native-r18\same-native-reference-comparison.json
```

# user-picture-corpus-v13-native-r17

This run validates the v13 DDS mip-aware browser renderer against CK3 1.19.0.6
for all seven images from the user's `pictures.zip`. Source commit is
`fc27c72c`; Steam remained offline. Navigation, chunked Apply, native Copy,
framebuffer calibration/capture and Copy re-Apply used structured MCP only,
with no OCR, keyboard, mouse, fixed screen coordinates, or user-content
network transfer.

The run succeeds r16, which stopped before the ruler-designer route and
executed zero picture cases. r17 completed all cases in 249.014 seconds. Its
aggregate process exit remains non-zero only because CK3 normalizes fractional
rotation values in picture-02/05/07; those three cases fail strict source-text
field equality but retain every layer/block/instance and pass the independent
pixel round-trip.

## Absolute native gates

The reference-independent v3 calibration recovered canonical UV from nine
native markers at 2560×1440. Maximum reprojection error was 0.464 px against a
2.5 px limit. Browser → CK3 used frozen MAE/MSE/edge/worst-spatial limits of
0.10/0.03/0.16/0.25. Native Copy → re-Apply used the stricter
0.01/0.001/0.02/0.03 limits.

| Case | Instances | Browser→CK3 MAE | MSE | Edge | Worst block | Copy re-Apply MAE | Copy edge | Strict source fields |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.020594 | 0.002791 | 0.085592 | 0.082469 | 0.0000387 | 0.000252 | pass |
| picture-02 | 586 | 0.021297 | 0.002858 | 0.098394 | 0.077996 | 0.0000272 | 0.000190 | rotation normalized |
| picture-03 | 1,024 | 0.025701 | 0.004349 | 0.100884 | 0.086414 | 0.0000348 | 0.000217 | pass |
| picture-04 | 1,024 | 0.044204 | 0.010881 | 0.140401 | 0.160847 | 0.0000424 | 0.000185 | pass |
| picture-05 | 904 | 0.043153 | 0.012207 | 0.130025 | 0.148522 | 0.0000742 | 0.000315 | rotation normalized |
| picture-06 | 1,024 | 0.023956 | 0.006189 | 0.065130 | 0.109728 | 0.0000362 | 0.000161 | pass |
| picture-07 | 987 | 0.034237 | 0.007439 | 0.122599 | 0.112879 | 0.0000501 | 0.000268 | rotation normalized |

Thus browser → CK3 pixels pass 7/7, Copy → re-Apply pixels pass 7/7, and strict
source field sequences pass 4/7. All seven Copy documents are themselves
stable on re-Apply; no case is truncated.

## Same-native-frame v11 → v13 comparison

Absolute metrics from different CK3 sessions are not a valid renderer A/B:
native frame geometry and surface presentation vary between sessions. The
checked-in `same-native-reference-comparison.json` therefore rescores both the
v11 and v13 browser canonical PNGs against each exact r17 aligned native crop,
using the same v3 eroded mask and metric implementation. Candidate values
reproduce the live summary within a predeclared `1e-6` numeric tolerance.

| Case | v13 MAE improvement vs v11 | v13 edge improvement vs v11 |
|---|---:|---:|
| picture-01 | 14.05% | 8.15% |
| picture-02 | 29.42% | 17.43% |
| picture-03 | 10.06% | 5.31% |
| picture-04 | 5.53% | 5.23% |
| picture-05 | 6.23% | 5.11% |
| picture-06 | 5.94% | 4.36% |
| picture-07 | 59.01% | 37.82% |

Both MAE and edge improve in 7/7 cases on identical native pixels. This passes
the comparative native gate and promotes v13 over v11. It also confirms that
the v13 rejection of the false billet/letter replacements in picture-05 and
the retained `ce_desdichado` in picture-07 improve browser/native agreement.

`summary.json` is 65,218 bytes, SHA-256
`02322F00CC701EDE0AB8B2A536BD7186E245C1F1B0E1237A36EC855F587D2195`.
The ignored raw report is 21,631,094 bytes, SHA-256
`6A6B9F99512784CDD2CB32F713BC840ECF40D8E793A1854BD650DFD0920AD742`.
The same-native comparison is 49,797 bytes, SHA-256
`ACE42F0F52BE5064B3FE992AA8352DCECC777AFB998101E265E4E6887ED9DCA6`.

Reproduce the offline A/B without launching CK3:

```bat
tools\.venv\Scripts\python.exe coat_of_arms_editer_of_ck3\tools\compare_native_aligned_previews.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v13-native-r17\summary.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-preview-projection-budget-1024 docs\coat-of-arms-fit-artifacts\user-picture-corpus-v13-mip-aware-budget-1024 docs\coat-of-arms-fit-artifacts\user-picture-corpus-v13-native-r17\same-native-reference-comparison.json
```


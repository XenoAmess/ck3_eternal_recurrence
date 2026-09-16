# User picture corpus v11 — final browser candidate

Status: **7/7 browser gates passed; CK3 native revalidation pending**.

Source corpus: `pictures.zip`, 6,240,071 bytes,
SHA-256 `0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`.
Every archive member is present; no sampling was used.

v11 keeps the v10 high-resolution hybrid repair and fixes the remaining visible preview discrepancy:

- fit report, main editor and current candidate all reference the same canonical PNG;
- fit report, main editor and candidate use the same 260:315 shield projection and identical clip-path;
- transform outlines/handles are editor chrome, not rendered pixels, and are hidden by default behind an
  explicit bilingual toggle;
- every case asserts full copy, parse, serialize and instance-count consistency.

| Case | Instances | Total loss | Edge loss | Relative improvement | UTF-8 bytes / lines | Result vs v8 |
|---|---:|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.018757 | 0.039032 | 58.73% | 403,155 / 14,343 | exact |
| picture-02 | 640 | 0.033979 | 0.063220 | 43.90% | 253,660 / 8,967 | improved |
| picture-03 | 1,024 | 0.021254 | 0.044994 | 64.22% | 403,604 / 14,343 | exact |
| picture-04 | 1,024 | 0.052426 | 0.096459 | 60.02% | 401,598 / 14,343 | exact |
| picture-05 | 917 | 0.052995 | 0.095896 | 76.53% | 359,771 / 12,845 | improved |
| picture-06 | 1,024 | 0.008202 | 0.017361 | 92.15% | 399,357 / 14,343 | exact |
| picture-07 | 986 | 0.049606 | 0.086218 | 67.16% | 388,782 / 13,811 | improved |

The quality gains are not cosmetic: picture-02/05/07 accepted 60/36/30 independently scored 256px layers.
Relative to v8, their total losses improved by approximately 3.82% / 7.71% / 8.00%, and edge losses by
2.70% / 4.46% / 5.20%. The other four cases remained numerically identical.

The directory contains each case's complete CK3 source, canonical 230px PNG, fit/report screenshot, editor
preview screenshot and machine-readable `report.json`. Browser success does not extend the old v8 native
framebuffer claim to these changed sources; v11 requires a fresh MCP Apply/Copy/framebuffer run before that
claim can be made.

Reproduction used two filtered invocations to avoid rerunning already completed cases; omitting
`COA_CORPUS_CASES` runs all seven:

```bat
cd coat_of_arms_editer_of_ck3
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs\coat-of-arms-fit-artifacts\user-picture-corpus-v11-preview-projection-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1
```

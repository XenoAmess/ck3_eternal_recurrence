# User picture corpus v9 — rejected high-resolution ordering experiment

Status: **RED for quality promotion; browser safety gates passed**.

This append-only run used all seven cases from `pictures.zip` at a user budget of 1,024. It introduced a
256px residual-paint phase, but attached that phase to the pure native-tile lane after the 96px edge pass.
That lane had already consumed its entire budget, while the lower-layer hybrid lane was never offered the
high-resolution pass. All seven outputs therefore remained byte/metric-equivalent to v8.

The run is retained because it isolated an execution-order bug. It is superseded by v10 and the final
browser candidate v11; it has no new CK3 native claim.

Reproduction used:

```bat
cd coat_of_arms_editer_of_ck3
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs\coat-of-arms-fit-artifacts\user-picture-corpus-v9-high-resolution-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1
```

# Epsilon-Q real-image corpus, budget 128

This is the frozen seven-image 128-instance Epsilon-Q run. The later v14
Delta compatibility branch is reachable only at budgets of 512 or greater,
so this v13 artifact remains the formal 128-budget result for the final code
path.

| Case | Instances | Relative J improvement | All scales non-regressing |
| --- | ---: | ---: | --- |
| picture-01 | 128 | 1.924% | yes |
| picture-02 | 128 | 4.826% | yes |
| picture-03 | 128 | 1.717% | yes |
| picture-04 | 127 | 4.710% | yes |
| picture-05 | 128 | 9.285% | yes |
| picture-06 | 128 | 18.520% | yes |
| picture-07 | 128 | 1.884% | yes |

All cases improve over their same-run search incumbents, remain within budget,
parse/serialize exactly, and do not regress at 96/230/512px. The median
improvement is 4.710%, so the predeclared 5% target is **not met** by 0.290
percentage points. Total fitting time was 79.56 minutes.

`quality-summary.json` SHA-256 is
`EB56FDFD46AB860B6FF6E2CB4D546DCF45E25B183753434E3E94A846DE5EBF2D`.

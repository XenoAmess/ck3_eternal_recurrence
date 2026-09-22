# Epsilon-Q v14 real-image corpus, budget 1,024

This is the frozen seven-image browser artifact for the Epsilon-Q quality-first
fit. It compares against the historical Delta-Q v9 full-DDS multiresolution
baseline with the frozen objective:

```text
J = 0.20 * L_v2_96 + 0.45 * L_v2_230 + 0.35 * L_v2_512
```

Every selected result parses, round-trips exactly through the browser
serializer, matches the editor preview bytes, remains within the user budget,
and does not regress at any of the three scales.

| Case | Instances | UTF-8 bytes | Relative J improvement | All scales non-regressing |
| --- | ---: | ---: | ---: | --- |
| picture-01 | 740 | 289,491 | 0.034% | yes |
| picture-02 | 771 | 303,604 | 5.737% | yes |
| picture-03 | 1,024 | 401,694 | 0.017% | yes |
| picture-04 | 972 | 383,258 | 0.291% | yes |
| picture-05 | 920 | 359,950 | 3.308% | yes |
| picture-06 | 1,024 | 381,493 | 0.010% | yes |
| picture-07 | 978 | 381,707 | 5.524% | yes |

The median improvement is 0.291%. The predeclared 10% median target and the
picture-03/06 5% hard-example target are therefore **not met**. The 7/7
improvement, all-scale non-regression, parse/serialize, preview identity, and
budget gates pass. Total fitting time was 87.45 minutes; generation latency is
diagnostic only under the project priority.

The selected documents total 6,429 drawn instances versus 6,433 in Delta-Q
v9, but individual cases can increase because quality wins before size. This
four-instance aggregate reduction is not claimed as a meaningful CK3 render
pressure improvement.

`quality-summary.json` SHA-256 is
`859EE2AEE95CA15AE4FAC42A8587CC4DA77D4392EB8A1C098BA835A8A17A471B`.

## Native attempt

A managed CK3 1.19.0.6 run predeclared all seven sources and references. The
bridge connected on the exact executable, but its ApplicationMain executor
never became ready within 1,800 seconds (`executed_requests=0`). No case was
applied or compared, so this is an infrastructure RED and not a candidate
render failure. Cleanup was GREEN: the CK3 process tree and watchdog were
proven absent.

The complete `native-ck3-report.json` is 1,542,128 bytes with SHA-256
`979EF97721EC86FC9E222EF9CA07811601F6E15D8AF8AC30DD320A8B8C5F7775`.
It must not be cited as a native quality pass.

# user-picture-corpus-v14-pareto-budget-1024

This append-only run replays all seven original images from the user's
`pictures.zip` at a user budget of 1,024 actual draw instances. The archive is
6,240,071 bytes with SHA-256
`0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`.
Every case validates the original input receipt, completes the WebGL2 + CPU
reference fit, exports the full CK3 source, parses and serializes it exactly,
and freezes all three non-dominated Pareto candidates as complete source and
230px preview files.

This run also closes the reproduced browser-preview mismatch: candidate cards
previously rendered at the 96px scoring resolution while the fit/editor
preview rendered at the canonical 230px presentation resolution. Different
DDS mip selection could therefore make the same model look different. The UI
now renders every comparison candidate at 230px. In every case, the active
candidate, fit preview and editor preview are byte-identical, share the shield
clip path/aspect ratio, and hide transform guides by default.

| Case | Selected instances | UTF-8 bytes | Total loss | Edge loss | Background improvement | Pareto candidates |
|---|---:|---:|---:|---:|---:|---:|
| picture-01 | 1,024 | 403,676 | 0.017103 | 0.036077 | 61.89% | 3 |
| picture-02 | 586 | 232,313 | 0.033150 | 0.061314 | 45.23% | 3 |
| picture-03 | 1,024 | 403,410 | 0.019422 | 0.041974 | 66.93% | 3 |
| picture-04 | 1,024 | 401,670 | 0.046932 | 0.087176 | 64.10% | 3 |
| picture-05 | 904 | 355,217 | 0.044505 | 0.083329 | 80.28% | 3 |
| picture-06 | 1,024 | 399,366 | 0.006149 | 0.012750 | 94.08% | 3 |
| picture-07 | 987 | 388,484 | 0.047678 | 0.081570 | 68.42% | 3 |

All seven quality-priority results are no worse than their frozen v5
1,024-budget baseline for total loss, edge loss and relative background
improvement. Cases 02, 05 and 07 naturally converge below the available
budget; no layer is added merely to reach 1,024. Seam receipts report zero
background leakage at 96, 230 and 512px in every case. Reports bind the exact
input SHA-256, source revision plus worktree patch SHA-256, asset/scoring/
renderer contracts, evaluated candidates, stop reason, counts and every
candidate's source/preview SHA-256.

## Mixed native-element ablation

[`mixed-element-ablation.json`](mixed-element-ablation.json) deterministically
projects every report's candidate ledger against its best comparable
`ce_block_02.dds`-only path. All seven cases evaluated non-tile native DDS
elements and all seven returned at least one mixed-element Pareto candidate.
The quality-priority candidate actually selects non-tile elements in three
cases:

| Case | Selected non-tile DDS | Total-loss change vs pure tile | Edge-loss change vs pure tile | Interpretation |
|---|---|---:|---:|---|
| picture-02 | `ce_mena_polo_stick.dds` | -23.59% | -6.23% | improves both gates |
| picture-05 | `ce_border_circle_metal.dds` | -7.71% | +3.72% | real Pareto trade-off; not an all-metric improvement |
| picture-07 | `ce_pot.dds`, `ce_desdichado.dds` | -33.31% | -23.21% | improves both gates |

The other four quality-priority results remain pure tile because their tested
semantic/mixed candidates did not win the total-loss ordering; those candidates
remain available as genuine lower-complexity or edge alternatives. This proves
the search is not hard-wired to one rectangle while avoiding a false claim that
every image benefits from a semantic emblem. The selected result in every row
also retains the existing browser seam/parse/preview gates and its 7/7 native
quality-priority Apply/Copy/pixel evidence.

Evidence level is deliberately scoped: browser input-to-fit metrics, preview
identity, source integrity and parse/serialize are measured and pass 7/7.
The quality-priority document from every case was subsequently applied to CK3
through the managed MCP route; browser → CK3 and Copy → re-Apply spatial pixel
gates both pass 7/7. See
[`user-picture-corpus-v14-native-r18`](../user-picture-corpus-v14-native-r18/README.md).
The other 14 Pareto alternatives retain browser evidence only and are not
silently promoted to native-validated results.

Reproduce without CK3, Steam, MCP or a backend:

```bat
cd coat_of_arms_editer_of_ck3
set COA_CORPUS_BUDGET=1024
set COA_CORPUS_ARTIFACT_ROOT=docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-pareto-budget-1024
pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1 --reporter=line
```

Expected result: `7 passed`; the measured run completed in 14.1 minutes on the
maintainer workstation. Per-case `report.json` is authoritative for unrounded
metrics and candidate coordinates.

Regenerate and byte-check the mixed-element projection without rerunning the
fits:

```bat
python coat_of_arms_editer_of_ck3\tools\summarize_mixed_element_evidence.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-pareto-budget-1024 docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-native-r18\summary.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-pareto-budget-1024\mixed-element-ablation.json
python coat_of_arms_editer_of_ck3\tools\summarize_mixed_element_evidence.py docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-pareto-budget-1024 docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-native-r18\summary.json docs\coat-of-arms-fit-artifacts\user-picture-corpus-v14-pareto-budget-1024\mixed-element-ablation.json --check
```

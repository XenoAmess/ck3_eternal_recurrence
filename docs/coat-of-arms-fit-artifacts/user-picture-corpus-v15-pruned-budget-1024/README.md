# 七图最终候选 v15：零退化固定点剪枝

本目录保留 v14 的 21 个 Pareto 候选经完整 DDS/mip 重新渲染后的固定点剪枝结果，未覆盖 v14。

- 状态：浏览器门禁通过；CK3 Apply/Copy 与原生空间像素对照仍待 MCP 验收。
- 来源 commit：`4eda7a24a7cfccd4a604176d28ef88a21dc3cfe3`。
- 合同：96/230/512px；总损失与边缘损失累计允许增加量均为 0；数值容差 `1e-12`。
- 实例：17,234 → 16,660，删除 574（3.33%）。
- 代码：6,785,304 → 6,469,753 UTF-8 bytes，减少 315,551（4.65%）。
- 每个候选包含 `coat_of_arms.txt`、`preview-512.png`、摘要 `report.json` 与完整 `necessity-receipt.json.gz`。
- v14 有 14/21 个候选的旧指标来自 32px fit-index，与完整 DDS 重渲染不完全一致；v15 门禁统一使用完整 DDS，并保留逐候选漂移量。

复现：

```text
cd coat_of_arms_editer_of_ck3
set COA_RUN_FINAL_CANDIDATE_PRUNE=true
set COA_PRUNE_ARTIFACT_ROOT=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v15-pruned-budget-1024
pnpm exec playwright test e2e/user-picture-final-candidate-prune.spec.ts --workers=3
python tools/summarize_final_candidate_prune.py ../docs/coat-of-arms-fit-artifacts/user-picture-corpus-v15-pruned-budget-1024
```

`summary.json` 是汇总入口；逐候选报告提供源码、预览和完整必要性收据的 SHA-256。

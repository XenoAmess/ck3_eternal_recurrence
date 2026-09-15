# xenoamess-hunter-v5-candidate

这是 WP3 的首个多尺度/混合原生元素候选，不是已晋级的 hunter 交付物。它保留
`xenoamess-hunter-v4-pruned` 的 96 px 主评分合同，同时从同一次浏览器解码保存 96/192/256 px
金字塔，并让语义 emblem 与覆盖安全的 `ce_block_02.dds` 残差绘制进入同一候选集合。

## 结论

- 纯 tile 候选仍为 1,000 个绘制实例，总损失 `0.025898240475696027`、边缘损失
  `0.043043678580258954`，与 v4 基线一致。
- hunter 混合候选实际用了 `ce_norse_odins_raven.dds` 和 `ce_block_02.dds` 两种原生纹理，
  但总损失 `0.04201755718425561`、边缘损失 `0.06822335331473522`，未通过两项独立门禁。
- 选择器因此保留纯 tile 基线；测试证明混合路径会在合成输入上获得严格收益，但不能把这一事实冒充 hunter 质量提升。
- WP3 仍为 `in_progress`。该候选不做 CK3 原生回读，也不取代 v4/v4-pruned；下一候选必须实现局部
  replacement/轮廓细化，并在同一 96 px 合同下令边缘损失严格低于 v4。

完整机器可读摘要见 [report.json](report.json)。临时完整报告可由下列 E2E 确定性重建；其本轮
SHA-256 为 `77979F0E4BC720C720C80BD8A5EA7F000A2A68CCD2A69760E39D30BE0FE56705`。

## 复现

在 `coat_of_arms_editer_of_ck3/` 执行：

```text
pnpm exec playwright test e2e/reference-hunter-fit.spec.ts
pnpm test
pnpm run build
```

完整报告写入 `test-results/reference-hunter-v5-candidate/report.json`。输入复用 v4 的
`target.png`，SHA-256 为 `53BBDB2FB3B8252475A12098BAC4E1B0A5BBC4765CB6896B4397923EE54D8AC8`；
asset pack manifest SHA-256 为
`AD7F0A911A2B4F002E923FEAB13716566D9A7B61447E9092504826FE6498FE91`。

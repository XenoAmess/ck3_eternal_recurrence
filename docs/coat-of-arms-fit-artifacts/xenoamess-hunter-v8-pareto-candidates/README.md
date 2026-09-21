# xenoamess-hunter-v8-pareto-candidates

该目录是追加式 hunter 1,024 预算浏览器证据，不覆盖 v3–v7。它修复了
fit-index v2 的能量重心被错误用于铺砖几何后产生的高分辨率接缝门禁回归，并首次冻结
可分别复制的真实 Pareto 候选。

- 用户预算、实际实例、逻辑图层、`colored_emblem` 块：1,024 / 1,024 / 1,024 / 1,024。
- 主候选总损失 `0.022678530903300246`、边缘损失
  `0.03945563275337468`；共同合同下 v4-pruned 为
  `0.02800298761905512 / 0.04701502098920628`，两项均改善。
- 96 / 230 / 512 px 几何门禁均为 `backgroundLeakPixels = 0`。
- 输出 389,675 UTF-8 bytes、14,343 个序列化行槽、1,024 个
  `colored_emblem` 和 1,024 个 `instance`；复制、解析和再次序列化逐字节一致。
- Pareto 01：1,024 实例，质量优先，代码 SHA-256
  `C645E429633AD818028D5A2FFE29C9FE1D6364F16102764DEC86EE87B94D1FF0`。
- Pareto 02：989 实例，复杂度优先，总损失
  `0.028365430345243445`，代码 SHA-256
  `227E60159C55C46D6DE5A8FAC2A4A081CEE4BB6A090662098F683CB531EBDDC5`。
- 完整 `report.json` SHA-256：
  `C31A82FA387268BC890478723B19C781B3FBDEE9C5840CECBC7A8B41F8F1985F`。

`report.json` 记录了基准 commit、工作区补丁 SHA-256、输入/素材包 SHA-256、
评分与 renderer 合同、配置、计数、逐候选指标和前驱关系。浏览器回归与浏览器复制传输
已通过；后续 [R38 原生证据](../xenoamess-hunter-v8-native-r38/README.md)已对 Pareto 01 完成
CK3 Apply、校准 framebuffer、Copy/reapply，并通过预冻结门限。该结果仍不等于 GPU 逐字节一致。

```bat
cd coat_of_arms_editer_of_ck3
pnpm exec playwright test e2e/reference-hunter-fit.spec.ts
```

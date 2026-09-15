# CK3 家徽拟合候选对比证据

状态：`WP5 in_progress / candidate comparison sub-gate passed`  
日期：2026-09-15（Asia/Shanghai）  
实现提交：`cb59fa06`

编辑器现在可以并排保存、查看和重新载入 1–3 个完整构图候选。这里的 3 是 Beta 计划指定的候选输出数量，不是绘制实例或用户拟合
预算上限；每个候选仍可包含任意安全整数预算下实际生成的完整实例模型。

每个候选绑定确定性 CK3 源码、逻辑图层、`colored_emblem` 块、实际绘制实例、UTF-8 bytes、行数和当前浏览器预览。拟合结束时自动
保存当前候选；手工编辑也可显式保存。载入候选时从保存的完整源码重新解析，而不是从卡片摘要或预览图恢复。

损失比较采用 fail-closed 合同：只有原始输入 SHA-256、评分器版本、renderer 版本、评分分辨率和 surface-mask 开关全部相同，才在
总损失、边缘损失、绘制实例数三维上标记“同合同下非支配/被支配”。不同合同互不支配；没有精确拟合证据的手工快照只显示“未绑定
可比拟合指标”。因此 UI 不会把跨输入、跨 renderer 或单纯手工候选冒充 Pareto 结果。

自动化证据：

- `comparisonCandidates.test.ts`：4 项通过，覆盖三候选合同、三维支配、无指标和跨合同隔离。
- `candidate-comparison.spec.ts`：保存 3 个不同完整源码、阻止第 4 个对比槽、重新载入第 1 个、去重刷新、删除，并验证非 GET 请求为 0。
- `standalone-image-fit.spec.ts`：真实浏览器拟合完成后自动出现带总/边缘损失的“同合同下非支配”候选，生产路径零 `/api/` 请求。
- 全量 Vitest：15 个文件、74 项通过；生产 build 通过。

复现命令（`coat_of_arms_editer_of_ck3/`）：

```text
pnpm exec vitest run src/domain/comparisonCandidates.test.ts --reporter=verbose
pnpm exec playwright test e2e/candidate-comparison.spec.ts --reporter=line
pnpm exec playwright test e2e/standalone-image-fit.spec.ts --reporter=line
pnpm test
pnpm build
```

本子门禁不等于 WP3 已输出多个有质量收益的 hunter Pareto artifact；当前 hunter 仍只有一个晋级候选。它也不替代 WP4 的拟合
pause/resume/checkpoint 或 GPU 批量搜索证据。

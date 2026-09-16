# CK3 家徽拟合候选对比证据

状态：`WP5 passed / candidate comparison gate passed`
日期：2026-09-16（Asia/Shanghai）
实现提交：`cb59fa06`；布局回归修复：`9f41f719`

编辑器现在可以并排保存、查看和重新载入 1–3 个完整构图候选。这里的 3 是 Beta 计划指定的候选输出数量，不是绘制实例或用户拟合
预算上限；每个候选仍可包含任意安全整数预算下实际生成的完整实例模型。

每个候选绑定确定性 CK3 源码、逻辑图层、`colored_emblem` 块、实际绘制实例、UTF-8 bytes、行数和当前浏览器预览。拟合结束时自动
替换为算法返回的 1–3 个真实非支配完整构图；手工编辑也可显式保存。载入候选时从保存的完整源码重新解析，而不是从卡片摘要或预览图恢复。

损失比较采用 fail-closed 合同：只有原始输入 SHA-256、评分器版本、renderer 版本、评分分辨率和 surface-mask 开关全部相同，才在
总损失、边缘损失、绘制实例数三维上标记“同合同下非支配/被支配”。不同合同互不支配；没有精确拟合证据的手工快照只显示“未绑定
可比拟合指标”。因此 UI 不会把跨输入、跨 renderer 或单纯手工候选冒充 Pareto 结果。

自动化证据：

- `comparisonCandidates.test.ts`：4 项通过，覆盖三候选合同、三维支配、无指标和跨合同隔离。
- `candidate-comparison.spec.ts`：保存 3 个不同完整源码、阻止第 4 个对比槽、重新载入第 1 个、去重刷新、删除，并验证非 GET 请求为 0；
  同时测量每个操作按钮的边界都位于所属卡片内，防止相邻卡片拦截点击。
- `imageFitter.test.ts`：三维 Pareto 选择去重、排除被支配项，并验证返回完整模型与活动模型/指标一致。
- `standalone-image-fit.spec.ts`：合成浏览器拟合实际输出 2 个带总/边缘损失和独立预览的非支配候选，生产路径零 `/api/` 请求。
- 全量 Vitest：18 个文件、83 项通过；生产 build 通过。

复现命令（`coat_of_arms_editer_of_ck3/`）：

```text
pnpm exec vitest run src/domain/comparisonCandidates.test.ts --reporter=verbose
pnpm exec playwright test e2e/candidate-comparison.spec.ts --reporter=line
pnpm exec playwright test e2e/standalone-image-fit.spec.ts --reporter=line
pnpm test
pnpm build
```

hunter 与七图用户语料的真实 Pareto artifact 已分别冻结在 `xenoamess-hunter-v8-pareto-candidates` 与
`user-picture-corpus-v14-pareto-budget-1024`。候选比较门禁与同次 WP5 完整矩阵均通过；它仍不替代 WP4 的拟合
pause/resume/checkpoint 或 GPU 批量搜索证据。完整选择合同见 `coat-of-arms-pareto-candidates.md`。

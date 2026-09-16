# CK3 家徽拟合：真实 Pareto 候选合同

更新时间：2026-09-16（Asia/Shanghai）

## 结论

图片拟合不再只把胜者摘要加入候选区。Worker 现在返回 **1–3 个实际存在的完整构图**；每项都包含可编辑、可序列化、可复制的
`CoatOfArms` 模型、同合同损失、重建路径、纹理清单与多尺度指标。网页会为这些结果生成独立源码、计数和预览，并可载入任一候选继续编辑。

“最多 3 项”只是候选对比界面的有界展示合同，不是用户图层预算。拟合层数仍由用户输入决定，不受 3、1,024 或 10,000 的产品上限限制。

## 选择合同

候选只在同一次拟合、同一输入、评分器、renderer、分辨率和 surface mask 下比较。三个优化维度为：

1. 总损失越低越好；
2. 边缘损失越低越好；
3. 实际绘制实例数越少越好。

若另一项在三个维度均不差、且至少一个维度严格更好，则当前项被支配并不得进入结果。重复的稳定构图键只保留一次。非支配项超过三项时，
稳定保留最低总损失、最低实例数和最低边缘损失三个极值；极值重合时按质量顺序补位。第一项始终是编辑器载入的最低总损失结果。

每个入选构图都单独转换为 CK3 的 depth 顺序，并在返回 Worker 结果前与搜索态 RGBA8 帧逐字节比较；不一致会使整次拟合 fail closed。

## 浏览器证据

- 纯函数用例包含三个真实非支配点、一个被支配点和一个重复点；输出稳定为三个非支配点。
- 合成浏览器拟合实际产生 2 个不同候选；两项均显示为“同合同下非支配”，均有独立预览，活动构图与第一项源码一致。
- hunter 1,024 预算实跑产生 2 个可独立复制和重解析的候选：质量优先项为
  1,024 实例、总/边缘损失 `0.022678530903300246 / 0.03945563275337468`；复杂度优先项为
  989 实例、`0.028365430345243445 / 0.04705664835149984`。两项在
  总损失、边缘损失、实例数三维上互不支配。
- 用户 `pictures.zip` 的 7 张原图已逐张以 1,024 预算复跑；每张都产生 3 个可独立复制、精确重解析且互不支配的候选，
  共冻结 21 份完整代码与 21 张 230px 候选预览。7/7 当前候选、拟合预览和编辑器预览使用同一 canonical PNG 字节；
  质量优先结果为 586–1,024 个实际实例、232,313–403,676 UTF-8 bytes，未对自然收敛结果补无贡献层。
- 完整 Vitest：18 个文件、83 项通过。
- 独立浏览器拟合 E2E：合成 asset pack 与 exact 1.19.0.6 pack 共 2 项通过；观察到 `/api/` 请求为 0。
- TypeScript 与生产构建通过。

复现命令：

```text
cd coat_of_arms_editer_of_ck3
pnpm exec vitest run src/domain/imageFitter.test.ts src/domain/comparisonCandidates.test.ts
pnpm test
pnpm build
pnpm exec playwright test e2e/standalone-image-fit.spec.ts --reporter=line
```

## 证据边界与后续门禁

本轮证明候选是实际完整模型、选择规则可复现、页面可渲染、复制和载入；没有把摘要数字冒充候选。hunter 证据见
[`xenoamess-hunter-v8-pareto-candidates`](coat-of-arms-fit-artifacts/xenoamess-hunter-v8-pareto-candidates/README.md)。
七图证据见
[`user-picture-corpus-v14-pareto-budget-1024`](coat-of-arms-fit-artifacts/user-picture-corpus-v14-pareto-budget-1024/README.md)。
该浏览器证据不替代 CK3 原生 framebuffer：v14 的原生 Apply/Copy 与空间像素对照仍为待验，因此 WP3 继续保持 `in_progress`。

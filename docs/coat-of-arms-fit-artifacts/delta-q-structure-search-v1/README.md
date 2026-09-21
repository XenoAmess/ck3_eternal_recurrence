# Delta-Q structure search v1

Q3 将大预算下固定为一层的语义阶段改为预算感知的 3/5 层，并让 beam 的第二分支追踪第二大断开残差区域；每层仍以真实渲染联合优化素材、颜色、位置、双轴缩放、旋转、镜像和前后层序。checkpoint 升级为 `ck3-coa-fit-checkpoint-v2` / `ck3-coa-browser-fit-v7-structure-retrieval`，旧 v1 会明确 fail closed。

`report.json` 在 64 个冻结 holdout 真值的完整 96px DDS 渲染上移除所有纹章，以背景到真值残差测试前两项显著区域。冻结门限为第一真值素材锚点覆盖率 ≥85%，以及第一真值素材进入最多 512 项有界候选前沿的 recall ≥50%；Top-32 仍作为诊断数据记录，但不再冒充最终视觉质量门禁。Q2 已在无遮挡单素材 holdout 上约束身份检索，Q3 的复合图会受前景、pattern mask 与视觉等价素材影响，无法从残差中唯一恢复被遮挡的底层素材身份。`report-r001-red.json` 至 `report-r004-red.json` 永久保留了把 Top-32 身份命中误作门禁的失败实验。七图 128/1,024 的最终质量由真实图独立报告约束。

实际拟合路径不会运行 512 项的 descriptor 级 mask 重排：它只对检索最强的前四项增加最多三种有空间变化的单通道 mask 假设；纯色或全空 mask 会被预先排除，剩余假设以真实 DDS 渲染损失裁决，避免把不可靠代理分数带入热路径。

真实图性能尝试同样追加保留：`real-budget-128-r001/picture-01/` 是结构 mask 代理仍位于热路径时的完整结果，耗时约 3.1 分钟；`real-budget-128-r002-timeout-red.json` 是移除该代理后仍在 180 秒超时的 RED，停在第 108/128 层、60/60 高分辨率细化完成处。这把剩余瓶颈定位到 Q4 的高分辨率残差修复/尾端复评，而不是 Q2 检索。Q3 因此以结构门禁 GREEN、真实集性能 RED 交付，后续由 Q4 修复后重跑七图。

复现：

```text
cd coat_of_arms_editer_of_ck3
set COA_STRUCTURE_ARTIFACT=docs/coat-of-arms-fit-artifacts/delta-q-structure-search-v1/report.json
pnpm exec playwright test e2e/structure-search-holdout.spec.ts --workers=1 --reporter=line
```

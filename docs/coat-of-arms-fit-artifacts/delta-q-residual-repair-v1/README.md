# Delta-Q Q4：质量优先残差修复证据

> 状态：`GREEN / browser full-DDS`（2026-09-21）
>
> 算法：`ck3-coa-browser-fit-v9-quality-first`
>
> 最终器：`full-dds-rescore-repair-pareto-v3`
>
> 精确残差修复：`exact-dds-residual-tile-perceptual-v2`

## 冻结决策顺序

本工作包执行项目所有者在 2026-09-21 指定的优先级：

1. 首先最小化完整 DDS 上的校准感知 v2 loss；网页生成耗时不参与候选排序。
2. 感知 v2 loss 逐值相等时，才偏好更少的 CK3 绘制实例；稳定序和源码结构仅继续解开完全相等的结果。
3. legacy total/edge 继续逐候选报告并保留 legacy-safe Pareto 候选，但不允许它否决感知上更相似的第一候选。
4. 用户实例预算始终是硬上限。结构压缩只合并完全相同的相邻 block，不删除实例、不改变像素，并输出可回放 receipt。

网页拟合耗时仍用于发现无界增长或死循环，但分钟级计算不是失败理由。

## 实现边界

- 稠密图检索同时保留 legacy safety lane 与 component-aware 结构 lane；第一层保留单主体回归安全，后续层允许显著区域分解。
- 最佳多层语义种子和最佳单层安全种子都进入高分辨率原生绘制，不让单一路径提前截断候选空间。
- 最终 bounded frontier 在 exact decoded DDS/mip 上重绘；hybrid/high-resolution 候选最多追加 64 个 legacy residual tile、16 个 legacy-safe edge tile 与 64 个感知 v2 tile。
- 感知 tile 同时尝试 sRGB 与 linear-light 颜色；proxy 只做提案 shortlist，接受与否必须由完整感知 v2 重新计算决定。
- 原生 tile 另生成 `0.25 / 0.5 / 0.75 / 1.0` 四个 linear-light recolor 变体；最终选择仍遵循质量第一。
- checkpoint 升级为 `ck3-coa-fit-checkpoint-v4`，旧 revision fail closed。

## 追加式尝试账本

目录均保留原始 `report.json`、候选源码、canonical preview 与界面截图。RED 尝试没有被覆盖或删除。

| 尝试 | 目的与结论 |
| --- | --- |
| `real-budget-128-r009` | Q3 后的 128 层真实图起点；暴露尾端细化耗时问题。 |
| `real-budget-1024-r010`–`r013` | 有界化高分辨率与残差路径；改善可完成性，但尚未达到质量门禁。 |
| `r017`、`r019`、`r020` | hotspot 与 exact-DDS 修复原型；证明应在最终 DDS 像素上接受修补。 |
| `r026`–`r030` | 条件 legacy focus、单候选 exact repair、hybrid 与 edge 修复；逐步建立双 lane。 |
| `r031`、`r032` | picture-05 legacy seed/legacy36 探索；保留为未达到整体质量目标或代价过高的 RED。 |
| `r033`、`r034` | v14 safety lane 与初版 recolor；前者恢复 picture-05，后者未产生最终胜选。 |
| `r036`、`r038`、`r039` | 感知 LUT、64 层质量修复与 linear-light patch；picture-05 提升到约 12.5%，但整体门禁仍未闭合。 |
| `r041`、`r042` | 双 lane 定向复核；先修复 picture-04/07，再关闭 picture-05 回归。 |
| `real-budget-1024-v9-final` | legacy 容差仍能影响第一候选的过渡版；保留，不作为正式结论。 |
| `real-budget-1024-v9-quality-first` | 首个质量绝对优先全量尝试；用于验证选优方向。 |
| `real-budget-1024-v9-final-quality-first` | 正式七图 1024 层全量证据，7/7 感知 v2 非退化并通过总体门禁。 |
| `real-budget-128-v9-final-quality-first` | 同一 revision 的 128 层回归证据。 |

## 1024 层正式结果

权威机器汇总为 [`real-budget-1024-v9-final-quality-first/quality-summary.json`](real-budget-1024-v9-final-quality-first/quality-summary.json)。相对冻结 v14 感知 shadow：

| 图 | v14 v2 loss | v9 v2 loss | 相对改善 | 实例 |
| --- | ---: | ---: | ---: | ---: |
| picture-01 | 0.02769307 | 0.02656672 | 4.067% | 739 |
| picture-02 | 0.04206756 | 0.02992316 | 28.869% | 729 |
| picture-03 | 0.02047207 | 0.02046560 | 0.032% | 1024 |
| picture-04 | 0.04102907 | 0.03205788 | 21.865% | 971 |
| picture-05 | 0.03329762 | 0.02548970 | 23.449% | 922 |
| picture-06 | 0.00676148 | 0.00641033 | 5.193% | 1024 |
| picture-07 | 0.04000010 | 0.03306923 | 17.327% | 1024 |

- 中位改善：`17.327%`，通过 `>= 15%` 门禁。
- 最差改善：`+0.032%`，通过 `>= -2%` 门禁，且实际为 7/7 正提升。
- 实例预算：`7/7 <= 1024`。
- legacy total/edge 各有 4/7 个首选候选非退化；其余图的 legacy-safe 候选仍保留在每图 Pareto 证据内。
- 七图网页拟合合计约 `36.94 min`。它是诊断值，不参与本期质量判定。

## 128 层回归

[`real-budget-128-v9-final-quality-first/regression-summary.json`](real-budget-128-v9-final-quality-first/regression-summary.json)
验证了同一 revision 的低预算路径：7/7 报告完整，parse/serialize 与 canonical editor preview 投影 7/7
通过，所有指标有限且非负，最大实例数恰为 128，最大源码 45,561 bytes。七图合计约 `11.88 min`，
最慢单图约 `2.72 min`；这些耗时仍只作诊断。

## 证据边界

本目录证明浏览器、完整 DDS、源码 parse/serialize、实例预算与自动指标。`report.json` 中的
`browser-passed-native-mcp-pending` 是有意的 fail-closed 状态；CK3 原生 Apply/Copy/framebuffer/re-Apply
必须由 Q5 的 MCP-only 证据另行关闭，不能由这里的浏览器结果外推。

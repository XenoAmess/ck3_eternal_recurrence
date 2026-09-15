# xenoamess hunter v4-pruned：精确固定点剪枝证据

状态：**浏览器精确剪枝与无损结构压缩通过；压缩文本的 CK3 原生 Apply/Copy 复验待执行。**

本目录是 [`xenoamess-hunter-v4-compressed`](../xenoamess-hunter-v4-compressed/) 的独立后继，原始 v4 和 v4-compressed
均保留不变。输入是已经无损合并为 293 个 `colored_emblem` 块、仍含 1,000 个绘制实例的 260,932-byte 文本。

## 固定合同与结论

运行前固定 `exact-leave-one-out-fixed-point-v1` 合同：搜索分辨率 96，验证分辨率 230/512，数值噪声容差
`1e-12`，允许像素差为 0。算法按最终绘制顺序反向逐项移除；只有候选在 96、230、512 的完整 RGBA 渲染均逐字节相同
才接受删除，删除后继续新一轮，直到一整轮没有删除为止。

本次一轮评估了全部 1,000 个实例，移除 0 个并达到固定点。每个候选在首个 96px 门禁已经改变渲染，因此无需用更高分辨率
“补救”该候选；完整前后文档仍在 96/230/512 三个分辨率逐字节零差异。逐项结果全部保存在 `report.json`：

| 项目 | 结果 |
| --- | ---: |
| 剪枝前/后绘制实例 | 1,000 / 1,000 |
| 剪枝前/后 `colored_emblem` 块 | 293 / 293 |
| 候选评估 | 1,000 |
| 固定点轮数 | 1 |
| 单项移除后的差异 bytes | 3–108 |
| 单项最大通道差 | 60–255 |
| 单项颜色损失增量 | 0.0000180775–0.00390625 |
| 单项边缘损失增量 | -0.0000550396–0.00131579 |
| 单项总损失增量 | 0.00000147005–0.002921875 |
| 最终总损失 | 0.025898240475696027 |
| 最终边缘损失 | 0.043043678580258954 |
| 输出 | 260,932 UTF-8 bytes / 9,057 行 |

边缘损失在少数单项移除后会略降，但总损失和零像素差是独立固定门禁，不能互相抵消；所有单项移除都使总损失严格上升。
因此这份证据只证明在上述合同下无法继续逐项删除，不声称全局最少实例或全局最优。近似几何合并和颜色量化不属于本候选，
未消耗任何视觉损失预算。

## 完整性与哈希

- [剪枝后 CK3 代码](coat_of_arms.txt)：`40B935A32A8A5EEDBC6262BB3A74CEA07935801B104FFD5768A7C7D4C2E32D14`
- [机器可读逐实例报告](report.json)：`6001C4CF23DC69E01EAC1E7DF18B32CE3BEF19E1C86E4D9122405BE4907FCFA5`
- hunter 目标图 SHA-256：`53BBDB2FB3B8252475A12098BAC4E1B0A5BBC4765CB6896B4397923EE54D8AC8`
- 输入和输出源码哈希相同；parse errors 为 0，serialize → parse → serialize 精确相同。

报告绑定生成时 `HEAD=46f486e6` 与包含剪枝实现的工作区 patch SHA-256
`28B9876C1E20A6236FD59AD4BB419DCEB8752AA3116306FF310B8C868831CBF4`。报告中保留全部 1,000 条必要性证据，README
中的范围只是便于审阅的摘要。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 执行：

```text
pnpm exec vitest run src/domain/coatOfArmsPruner.test.ts src/domain/coatOfArmsOptimizer.test.ts src/domain/imageFitter.seams.test.ts
pnpm run build
pnpm exec playwright test e2e/reference-hunter-prune.spec.ts
pnpm exec playwright test e2e/standalone-image-fit.spec.ts
```

Playwright 默认会清空 `test-results/`；冻结报告前应最后运行 hunter prune 用例，并把
`test-results/reference-hunter-prune/{coat_of_arms.txt,report.json}` 复制到本目录。生产页面本身不运行 CK3、MCP、Steam 或后端。

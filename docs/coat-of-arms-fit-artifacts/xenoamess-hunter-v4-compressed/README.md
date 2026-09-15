# xenoamess hunter v4-compressed：无损结构压缩候选

状态：**相邻同样式块安全合并通过；最终 backward prune / leave-one-out 尚未完成。**

本目录是 [`xenoamess-hunter-v4`](../xenoamess-hunter-v4/) 的独立后继，不覆盖或重新解释 v4。输入是 v4 的完整
380,862-byte CK3 源码；没有重新拟合、调整颜色、量化数值、合并几何或删除实例。算法只合并源码中相邻、且 texture、三色和
mask 完全相同的 `colored_emblem` 块，并保持所有 instance 的原始顺序、变换与 depth。它不会跨越中间块做全局分组，避免
相同 depth 下的遮挡顺序发生变化。

## 预先固定的门禁与结果

运行前固定的最低目标是 bytes 减少 10%、块数减少 10%；允许像素差为 0，不能用视觉损失换压缩率。

| 项目 | v4 原始 | 本候选 | 结果 |
| --- | ---: | ---: | --- |
| `colored_emblem` 块 | 1,000 | 293 | 减少 707（70.70%） |
| 绘制 `instance` | 1,000 | 1,000 | 完全保留 |
| 逻辑图层 | 1,000 | 293 | 按编辑器块定义减少 707 |
| UTF-8 bytes | 380,862 | 260,932 | 减少 119,930（31.4891%） |
| 行数 | 14,006 | 9,057 | 减少 4,949 |

浏览器 CPU reference 在 96、230、512 三个分辨率分别对压缩前后完整渲染逐字节比较，三次均为
`differingBytes=0 / maximumDifference=0`。扁平化后的 texture/colors/mask/instance 序列完全相同；压缩代码重新解析错误为 0，
serialize → parse → serialize 精确相等。因此在当前 renderer 合同下，总损失、边缘损失和接缝指标与 v4 完全相同，不消耗
任何近似压缩损失预算。

这只证明结构合并无损，不等于每个剩余实例都完成了 leave-one-out 必要性验证，也不宣称 293 个块或 1,000 个实例是全局最少。
原生 CK3 Apply/Copy 将在最终剪枝候选形成后重新执行；v4 原始 1,000-block 文本闭环证据继续保留。

## 文件与哈希

- [压缩 CK3 代码](coat_of_arms.txt)：`40B935A32A8A5EEDBC6262BB3A74CEA07935801B104FFD5768A7C7D4C2E32D14`
- [机器可读报告](report.json)：`437AFE8EE73585B2138A61A5FB8DB25CFE15204A602E386AA9FCDAD705F1A2AB`
- 前驱代码 SHA-256：`C4648E2C98D3503252D9A9A298B4A39E27A8F4C7269944E607F34F86B3C60571`

报告绑定生成时 `HEAD=9e9b7711` 和工作区 patch SHA-256
`F4F829E6CB512D03D5A6D56BF37BF18592571E9021BEFB31D0CB82FE14A2E4E7`；实现提交将在本工作包提交后由进度台账补录。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 执行：

```text
pnpm exec vitest run src/domain/coatOfArmsOptimizer.test.ts src/domain/parser.test.ts src/domain/imageFitter.test.ts
pnpm build
pnpm exec playwright test e2e/reference-hunter-compression.spec.ts
```

# xenoamess-hunter-v6-pruned

本目录对 [`xenoamess-hunter-v6-compressed`](../xenoamess-hunter-v6-compressed/README.md) 执行 exact
leave-one-out 固定点剪枝。它是零像素差的结构门禁，不把“像素改变但评分更优”的实例误称为已证明必要；后者由后续 Pareto
剪枝工作包处理。

- 输入/输出绘制实例：1,008 → 1,006；2 个被后续层完全覆盖的实例被删除。
- 搜索固定点：2 passes；最终 1,006 个实例均逐项留有移除测量。
- 96/230/512 px 的剪枝前后逐 RGBA byte 差异均为零，总/边缘损失保持
  `0.024123983862988356 / 0.040769084120764576`。
- 输出：263,165 UTF-8 bytes、9,141 行；SHA-256
  `DB358668F2D0F33B0A8290E76844B9A210FF4A79EF3458ADA50DBE27AA64E375`。
- 报告 SHA-256：`A70FD26107254D6B981B7C7E28A8BC9D26DEA3CA0AA8ED06116BABFEEBCAD7B2`。

复现：`pnpm exec playwright test e2e/reference-hunter-v6-prune.spec.ts`。

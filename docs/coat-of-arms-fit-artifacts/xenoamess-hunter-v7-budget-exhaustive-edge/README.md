# xenoamess-hunter-v7-budget-exhaustive-edge

该追加式 artifact 是预算穷尽边缘修复后的 hunter 1,024 预算候选，不覆盖既有
`xenoamess-hunter-v6-edge-refined`。

- 用户预算、实际实例、逻辑图层、`colored_emblem` 块：1,024 / 1,024 / 1,024 / 1,024。
- 修正后的共同 surface-mask 合同：总损失 `0.028262524984546896`，边缘损失
  `0.0490719414479038`，相对背景改善 `85.28%`。
- 同一共同合同下重评 v4：总损失 `0.0320298797420984`，边缘损失
  `0.05429127496667292`；v7 两项均严格改善。
- 历史 `0.02590 / 0.04304` 是未应用 surface mask 的旧口径，保留但不与新数值直接比较。
- 输出 390,008 UTF-8 bytes、14,342 行，代码 SHA-256
  `2E7BC66DCA1A3E3F3E8444E4ACE2EE013CE4C26330CCD1D2D53AE03D215768B9`。
- 完整报告 SHA-256：
  `56D61350EF31D52EF3AA36838CC3C0E187E5FA128A4874300A5821A39FA2DEF0`。

浏览器拟合、接缝门禁、复制和重解析已通过；CK3 Apply/Copy 与 framebuffer 对照仍为 pending。

```bat
cd coat_of_arms_editer_of_ck3
pnpm exec playwright test e2e/reference-hunter-fit.spec.ts
```

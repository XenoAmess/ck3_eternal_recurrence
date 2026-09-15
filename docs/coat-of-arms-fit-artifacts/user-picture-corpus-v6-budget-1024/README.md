# user-picture-corpus-v6-budget-1024

本目录冻结用户提供的 `pictures.zip` 全部 7 张图片在相同 1,024 绘制实例预算下的浏览器回归结果。
每个子目录都包含完整 CK3 代码、规范 230 px 预览、拟合报告截图、右侧编辑器预览截图和机器可读
`report.json`；输入原图及其 SHA-256 由
`coat_of_arms_editer_of_ck3/e2e/fixtures/pictures/cases.json` 固定。

算法为 `ck3-coa-browser-fit-v6-budget-exhaustive-edge`。相对 v5，它移除了边缘修复只能尝试 8 个新增实例的
隐藏截止条件，改为持续保留严格改善项，直到用户预算耗尽或完整一轮没有改善。两处网页预览均引用同一个
canonical data URL，因此本目录只能证明浏览器内上下预览一致，不能代替 CK3 framebuffer 对照。

| 用例 | 实际实例 | 总损失 | 边缘损失 | 相对改善 | 代码 bytes / 行 | 相对 v5 |
|---|---:|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.018757 | 0.039032 | 58.73% | 403,155 / 14,343 | 总损失、边缘均改善 |
| picture-02 | 580 | 0.035329 | 0.064976 | 41.67% | 232,336 / 8,127 | 自然无改善，保持一致 |
| picture-03 | 1,024 | 0.021254 | 0.044994 | 64.22% | 403,604 / 14,343 | 总损失、边缘均改善 |
| picture-04 | 1,024 | 0.052426 | 0.096459 | 60.02% | 401,598 / 14,343 | 总损失、边缘均改善 |
| picture-05 | 881 | 0.057423 | 0.100367 | 74.56% | 347,408 / 12,341 | 自然无改善，保持一致 |
| picture-06 | 1,024 | 0.008202 | 0.017361 | 92.15% | 399,357 / 14,343 | 总损失、边缘均改善 |
| picture-07 | 956 | 0.053918 | 0.090944 | 64.30% | 378,300 / 13,391 | 自然无改善，保持一致 |

所有比较都使用 `alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1`、96 px 搜索平面、
96/192/256 px 多尺度重评、相同 surface mask 与 exact 1.19.0.6 asset pack。v5 数值在每个 receipt 的
`v5Budget1024Baseline` 中冻结；数值噪声容差为 `1e-12`。7/7 均通过 serialize → parse 精确闭环和
96/230/512 px 零内部背景泄漏。原生 Apply/Copy 和像素对照仍为 pending。

复现：

```bat
cd coat_of_arms_editer_of_ck3
set COA_CORPUS_BUDGET=1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --reporter=line
```

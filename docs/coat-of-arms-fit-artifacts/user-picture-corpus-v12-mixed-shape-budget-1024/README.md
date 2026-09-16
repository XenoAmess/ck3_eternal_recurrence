# User picture corpus v12 — iterative mixed native-shape refinement

Status: **7/7 browser gates passed; changed picture-05/07 native revalidation pending**.

Source corpus: `pictures.zip`, 6,240,071 bytes,
SHA-256 `0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`。
全部 7 个归档成员均运行 1,024 绘制实例预算，没有抽样。

v12 在 v11 高分辨率混合候选之后增加迭代原生形状替换：

- descriptor shortlist 保留最强语义匹配，同时为原版 `ce_block_02`、`ce_billet`、`ce_circle`、
  `ce_lozenge`、`ce_triangle_mask` 预留真实渲染比较位置，覆盖矩形、圆、菱形和楔形基础族；
- 替换 pass 数随用户预算对数增长，受剩余绘制实例预算约束，不是新的产品总层数上限；
- 每个 pass 必须在总损失不退化时严格改善边缘损失；第一次无改善立即自然停止，不为满足素材比例
  塞入无贡献图层；
- 替换完成后才进入 256px 局部块修复，因此形状层与高分块竞争同一用户预算。

| 用例 | 实例 | 总损失 | 边缘损失 | v11→v12 | 形状 pass / 接受 | 接受的原生形状 |
|---|---:|---:|---:|---|---:|---|
| picture-01 | 1,024 | 0.018757 | 0.039032 | 代码逐字节相同 | 0 / 0 | — |
| picture-02 | 640 | 0.033979 | 0.063220 | 代码逐字节相同 | 1 / 0 | —；648 候选后自然停止 |
| picture-03 | 1,024 | 0.021254 | 0.044994 | 代码逐字节相同 | 0 / 0 | — |
| picture-04 | 1,024 | 0.052426 | 0.096459 | 代码逐字节相同 | 0 / 0 | — |
| picture-05 | 917 | 0.052549 | 0.094820 | 总损失改善 0.84%，边缘改善 1.12% | 4 / 4 | `ce_billet`×2、`ce_letter_j`、`ce_letter_i` |
| picture-06 | 1,024 | 0.008202 | 0.017361 | 代码逐字节相同 | 0 / 0 | — |
| picture-07 | 986 | 0.049541 | 0.085786 | 总损失改善 0.13%，边缘改善 0.50% | 2 / 1 | `ce_circle` |

picture-05/07 在 192px 与 256px 的 edge/total 也均不退化；例如 picture-05 的 256px edge 从
0.069470 降至 0.068814，picture-07 从 0.056032 降至 0.055704。两例绘制实例数与 v11 相同，
说明收益来自局部原生形状替换和预算重新分配，不是单纯增加层数。picture-01/02/03/04/06 的
`coat_of_arms.txt` 已通过二进制比较，与 v11 完全一致。

每个用例保存完整 CK3 代码、canonical 230px PNG、拟合报告截图、编辑器预览截图和
`report.json`。报告中的 `nativeShapeRefinement` 记录请求/完成 pass、实际评估数、可用基础形状族、
接受纹理和停止原因。网页两处预览继续使用同一个 data URL、相同盾形投影，复制后解析/序列化和
实例计数均为 7/7。当前原生结论只可由代码未变的 5 例继承；picture-05/07 必须经过新的结构化
MCP Apply/Copy/framebuffer 后才能晋级。

验证：

```bat
cd coat_of_arms_editer_of_ck3
pnpm exec vitest run src/domain/imageFitter.test.ts --reporter=verbose
pnpm test
pnpm build
pnpm verify:production-boundary
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs\coat-of-arms-fit-artifacts\user-picture-corpus-v12-mixed-shape-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1
```

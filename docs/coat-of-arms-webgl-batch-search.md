# CK3 家徽编辑器 WebGL2 批量搜索证据

状态：`WP4 in_progress / background candidate GPU batch + reduction passed`

日期：2026-09-16（Asia/Shanghai）

合同：`webgl2-texture-array-reduction-float-v1`

## 已实现能力

浏览器拟合 Worker 会为当前 96×96 目标创建独立 WebGL2 context，并把同一轮背景候选作为 `sampler2DArray` 上传。第一个 fragment pass
在一张按候选纵向排列的 float atlas 中并行计算 color、横向 edge 和纵向 edge contribution；后续 2×2 reduction passes 在 GPU 上把
每个候选的矩形分别归约到一个 RGBA32F texel，CPU 只回读每候选一个 texel。

GPU 数值不被无条件信任。CPU reference 仍对每个候选执行完整
`alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1` 评分；只有所有 color/edge/total 指标最大绝对差不超过预先固定的 `2e-6`，且整个
候选稳定排序与 CPU 完全一致时，GPU 排序才进入背景候选选择。任一条件失败均 fail closed，改用 CPU 排序并在 result receipt 中记录原因。

当前 GPU 覆盖背景候选排序、每个语义素材的粗搜索胜者晋级，以及局部优化后候选排序。每个 transform 的 CPU renderer/reference score
仍保留，完整的语义 transform population 和逐块残差绘制尚未由 GPU 直接渲染；因此这证明 GPU 已实际参与多段批量候选搜索，不证明整个
拟合已经 GPU 化，也不把本项标成 WP4 全部完成。

## 上下文丢失与降级

`WebGlBatchScorer` 每次评分前后检查 context，纹理/FBO/着色器或 readback 失败也进入有界失败状态：

- `context_lost` → 当前 run 使用 CPU reference 完成，不丢模型或 checkpoint；
- `runtime_error` / 扩展不可用 → 当前 run 使用 CPU reference；
- CPU/GPU 数值或稳定排序不一致 → `reference_mismatch_fallback`；
- 下一次 run 会创建新 Worker 和新 context，因此不复用已经丢失的 GPU 状态。

浏览器用 `WEBGL_lose_context` 真实触发丢失后，后续 batch 调用返回 `null` 且状态为 `context_lost`；DOM-less 单元门禁另用该状态证明拟合器
仍选择正确的 CPU 候选。当前恢复粒度是“当前 run 无损降级、下一 run 重建 context”，不是同一 run 内重建 GPU context 后继续使用 GPU。

## 实测

本机 Microsoft Edge headless、Vite 开发服务器：

- 4 个 16×12 RGBA 候选的 GPU/CPU color、edge、total 最大绝对差小于 `2e-6`；
- `WEBGL_lose_context` 后 batch scorer fail closed；
- 真实拟合压力的 128 / 1,024 / 10,000 三个预算均报告 `searchBackend=webgl2-batch+cpu-reference`；
- 每个压力 run 的合成 asset pack 有 1 个 pattern、6 种背景调色候选，单批处理 6 个候选；GPU/CPU 最大绝对差
  `2.5092759509126594e-8`，排序一致；
- hunter 1024 真实素材 run 共执行 6 个 GPU batch、排序 354 个背景/语义晋级/local 候选，最大绝对差
  `6.102908300942289e-8`，CPU 稳定排序完全一致；
- 10,000 预算仍自然收敛到 1,824 个严格改善实例，总损失 `0.19578464753140656`、边缘损失
  `0.26330842040763747`，96/230/512 px 接缝门禁全部零泄漏；
- 10,000 run 耗时 13,409 ms，仍低于预先冻结的 180 秒门禁。

## 复现命令

在 `coat_of_arms_editer_of_ck3/` 中执行：

```text
pnpm exec vitest run src/domain/imageFitter.test.ts --reporter=verbose
pnpm exec playwright test e2e/webgl-batch-scorer.spec.ts --reporter=line
pnpm exec playwright test e2e/fit-budget-stress.spec.ts --reporter=line
pnpm test
pnpm build
```

后续仍需让 GPU 直接处理完整语义 transform population 与大规模 tile 候选，补充真实 GPU/浏览器进程内存证据，并在更多取消阶段验证
资源及时释放。

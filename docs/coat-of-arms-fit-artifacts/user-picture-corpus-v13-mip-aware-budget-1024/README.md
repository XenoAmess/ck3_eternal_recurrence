# User picture corpus v13 — DDS mip-aware renderer

Status: **7/7 browser gates passed; CK3 native revalidation pending**.

Source corpus: `pictures.zip`, 6,240,071 bytes,
SHA-256 `0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`。
全部 7 个案例均使用用户预算 1,024，不抽样、不静默 clamp。

## 修复内容与原生依据

v12 同会话 A/B 证明 picture-05 的浏览器微小形状收益进入 CK3 后反向退化。进一步检查原版素材和
shader 后定位到缺失的 mip 维度：

- 原版 DDS 自带完整 mip 链。例如 `ce_billet.dds` 是 128×128 DXT5，文件为 22,000 bytes；这正好
  包含 header、顶层和 64/32/16/8/4/2/1 的压缩 mip 数据。旧网页解码器只读取顶层。
- exact 1.19.0.6 的 `game/gfx/FX/coat_of_arms/coat_of_arms.fxh` 明确为 MaskMap 配置
  `MagFilter=Linear`、`MinFilter=Linear`、`MipFilter=Linear`、U/V `Wrap`；pattern/emblem shader
  通过 `PdxTex2D` 采样。这说明缩小后的原生元素不会始终读取顶层。
- v13 解码 DXT1、DXT5 和 BGRA8 的完整声明 mip 链；renderer 根据全表面尺寸或 emblem 仿射导数
  计算 LOD，在相邻 mip 间三线性采样，并继续保持原生 clockwise rotation、descending depth、
  surface mask 和 Wrap 合同。Worker 克隆也完整保留 mip。
- 原生形状替换新增 1% 双门禁：总损失和边缘损失都必须相对改善至少 1%。r15 中已证伪的
  picture-05 浏览器收益为总损失 0.84%、边缘 1.12%，现在被拒绝；v13 picture-07 的约
  3.08% / 2.68% 实质收益保留。

## 七图结果

这是 renderer v4 新合同，不能把下列数字与 v11/v12 的顶层-only renderer 数字直接当作同口径比较。

| 用例 | 实例 | 总损失 | 边缘损失 | bytes / 行 | 最终输出中的非块语义 |
|---|---:|---:|---:|---:|---|
| picture-01 | 1,024 | 0.017103 | 0.036077 | 403,676 / 14,343 | — |
| picture-02 | 586 | 0.033150 | 0.061314 | 232,315 / 8,211 | 既有 semantic seed |
| picture-03 | 1,024 | 0.019422 | 0.041974 | 403,410 / 14,343 | 最终 winner 不含新增形状 |
| picture-04 | 1,024 | 0.046932 | 0.087176 | 401,670 / 14,343 | — |
| picture-05 | 904 | 0.044505 | 0.083329 | 355,216 / 12,663 | billet/字母假收益已消失 |
| picture-06 | 1,024 | 0.006149 | 0.012750 | 399,366 / 14,343 | — |
| picture-07 | 987 | 0.047678 | 0.081570 | 388,482 / 13,825 | `ce_pot.dds`、`ce_desdichado.dds` |

picture-03 的形状 lane 曾接受 `ce_grain` 和两个 `ce_triangle_mask`，但最终仍由无新增形状的
`native-edge-refined` 候选胜出，导出不会为了“多素材”保留较差候选。picture-05 完整评估 648 个
形状候选后以 `no_improvement` 停止。picture-07 的 `ce_desdichado` 使 96px hybrid 从
`0.052811 / 0.086795` 降至 `0.051184 / 0.084468`，192/256px 也同时不退化，随后再进行 24 层
高分辨率修复。

两处网页预览继续共享同一 canonical PNG、盾形比例和 clip-path；7/7 的完整复制、重新解析、实例/
层/块计数一致。优化采样器后，picture-05 确定性复跑的代码与 PNG 均逐字节相同；1% 门禁后的
picture-07 也逐字节相同。完整七图运行耗时 13.8 分钟，性能仍需在 WP4 继续优化，不能把正确性
修复后的额外 CPU 成本隐瞒为已完成性能目标。

验证：

```bat
cd coat_of_arms_editer_of_ck3
pnpm exec vitest run src/domain/dds.test.ts src/domain/renderer.test.ts src/domain/imageFitter.test.ts --reporter=verbose
pnpm test
pnpm build
pnpm verify:production-boundary
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs\coat-of-arms-fit-artifacts\user-picture-corpus-v13-mip-aware-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1 --reporter=line
```

每个 `picture-*` 目录保存完整代码、canonical PNG、拟合报告截图、编辑器预览截图和 JSON 收据。
本目录与实现一起提交；原生结论必须由新的 MCP Apply/Copy/framebuffer 运行产生，不能继承 r14。

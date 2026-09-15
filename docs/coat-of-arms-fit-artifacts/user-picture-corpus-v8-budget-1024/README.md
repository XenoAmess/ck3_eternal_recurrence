# user-picture-corpus-v8-budget-1024

本目录冻结 `pictures.zip` 全部 7 张输入在 CK3 原生 depth 降序语义修复后的 1,024 预算浏览器结果。
它取代 v7 作为原生验收输入，但保留 v7 作为发现 depth 方向缺陷时的历史证据。

输入压缩包为 6,240,071 bytes，SHA-256
`0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`。评分合同仍为
`alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1`；renderer 合同升级为
`cpu-rgba8-bilinear-clamp-pixel-center-native-clockwise-depth-descending-v3`。

| 用例 | 实际实例 | 总损失 | 边缘损失 | 相对改善 | 代码 bytes / 行 |
|---|---:|---:|---:|---:|---:|
| picture-01 | 1,024 | 0.018757 | 0.039032 | 58.73% | 403,155 / 14,343 |
| picture-02 | 580 | 0.035329 | 0.064976 | 41.67% | 232,336 / 8,127 |
| picture-03 | 1,024 | 0.021254 | 0.044994 | 64.22% | 403,604 / 14,343 |
| picture-04 | 1,024 | 0.052426 | 0.096459 | 60.02% | 401,598 / 14,343 |
| picture-05 | 881 | 0.057423 | 0.100367 | 74.56% | 347,410 / 12,341 |
| picture-06 | 1,024 | 0.008202 | 0.017361 | 92.15% | 399,357 / 14,343 |
| picture-07 | 956 | 0.053918 | 0.090944 | 64.30% | 378,300 / 13,391 |

v8 与 v7 的七张 canonical preview 逐字节相同；代码内容改变为 CK3 原生 depth 表示。例如
picture-07 的 956 个实例由 `1,2,...,956` 反编码为 `956,955,...,1`。因此浏览器拟合质量没有回退，
但网页和 CK3 现在能按同一层叠顺序解释导出代码。

七例均通过：拟合预览与编辑预览同一 data URL、完整 Copy、重新解析实例计数一致、serialize/parse
精确闭环。当前晋级为浏览器基线；原生 Apply/Copy/framebuffer 结果写入后继 `v8-native-*` 目录。

复现：

```bat
cd coat_of_arms_editer_of_ck3
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v8-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --workers=1
```

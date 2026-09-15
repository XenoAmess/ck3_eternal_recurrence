# user-picture-corpus-v7-budget-1024

本目录冻结 `pictures.zip` 全部 7 张输入在 CK3 原生顺时针屏幕旋转语义修复后的 1,024 预算浏览器结果。
它取代 v6 作为后续原生验收输入，但不覆盖 v6：v6 是发现 renderer 角度方向缺陷时的历史基线。

输入身份仍由 `coat_of_arms_editer_of_ck3/e2e/fixtures/pictures/cases.json` 固定；压缩包为
6,240,071 bytes，SHA-256
`0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`。评分合同仍为
`alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1`，renderer 合同升级为
`cpu-rgba8-bilinear-clamp-pixel-center-native-clockwise-v2`。

| 用例 | 实际实例 | 总损失 | 边缘损失 | 相对改善 | 代码 bytes / 行 |
|---|---:|---:|---:|---:|---:|
| picture-01 | 1,024 | 0.018757 | 0.039032 | 58.73% | 403,155 / 14,343 |
| picture-02 | 580 | 0.035329 | 0.064976 | 41.67% | 232,336 / 8,127 |
| picture-03 | 1,024 | 0.021254 | 0.044994 | 64.22% | 403,604 / 14,343 |
| picture-04 | 1,024 | 0.052426 | 0.096459 | 60.02% | 401,598 / 14,343 |
| picture-05 | 881 | 0.057423 | 0.100367 | 74.56% | 347,410 / 12,341 |
| picture-06 | 1,024 | 0.008202 | 0.017361 | 92.15% | 399,357 / 14,343 |
| picture-07 | 956 | 0.053918 | 0.090944 | 64.30% | 378,300 / 13,391 |

七例均通过：拟合预览与编辑预览同一 data URL、完整 Copy、重新解析实例计数一致、serialize/parse
精确闭环。picture-02 的首个语义元素由 v6 的 `223.375°` 变为 `136.625°`，其余参数及浏览器质量
不变；这是同一视觉方向在 CK3 顺时针角度合同下的正确序列化结果。picture-07 同样重新拟合角度。

本目录当前只晋级为浏览器基线。必须由 fixed-calibration framebuffer MCP 把这批新代码逐例 Apply
到 CK3 后，才能声明浏览器/游戏像素差异已修复。

复现：

```bat
cd coat_of_arms_editer_of_ck3
set COA_CORPUS_BUDGET=1024&& set COA_CORPUS_ARTIFACT_ROOT=docs/coat-of-arms-fit-artifacts/user-picture-corpus-v7-budget-1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --reporter=line
```

# CK3 家徽编辑器：用户图片回归集与预览偏差排查

## 本轮结论（2026-09-16）

`pictures.zip` 中的 7 张图片已全部纳入可追溯回归集，不做抽样。原始压缩包大小为
6,240,071 bytes，SHA-256 为
`0D6C529035333E22E34758D1128A713218D877831206FF60E11990CD362C575F`。每张图片的文件名、尺寸、字节数与
SHA-256 保存在
`coat_of_arms_editer_of_ck3/e2e/fixtures/pictures/cases.json`。

已稳定复现并修复一个独立缺陷：拟合报告下方的预览和右侧结构化编辑器预览原本来自两条不同渲染链。

- 下方预览按拟合分辨率单独渲染；小预算时只有 `56×56`，且漏掉了原生盾面
  `coa_mask_texture.dds` 与命名色。
- 右侧预览按 `230×230` 的 shader 模型渲染，包含盾面 mask 和命名色；CSS 还把它拉伸并裁成盾形。
- 因此同一份代码在页面内都会显示成两幅不同的图。修复后两处强制引用同一个 canonical
  data URL，并使用相同的盾形比例、拉伸和 clip-path。
- 拟合 Worker、WebGL 交叉评分与精确剪枝 Worker 也改为使用和右侧/原生目标一致的
  surface-mask 与命名色合同，不再优化一幅最终不会显示的“裸正方形”。

最小失败证据使用 `picture-01`和预算 1：旧链的下方图像为 56×56 PNG，右侧为
230×230 PNG，字节不一致；修复后同一用例通过。完整 7 图串行回归为 `7 passed
(2.9m)`，并逐图断言两处 data URL 字节一致、展示几何一致、`surfaceMaskApplied=true`。

## 1024 预算浏览器质量基线

下表是 7 张图用相同的 1024 绘制实例预算逐一运行的实测数据。总损失、边缘损失与相对改善只是
`alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1` 合同下的浏览器比较，不代表 CK3
像素已验。

| 用例 | 原图 | 实际实例 | 总损失 | 边缘损失 | 相对改善 | 代码 bytes / 行 |
|---|---|---:|---:|---:|---:|---:|
| picture-01 | `718c….jpg` | 726 | 0.026529 | 0.052951 | 41.63% | 286,960 / 10,171 |
| picture-02 | `a124….jpg` | 580 | 0.035329 | 0.064976 | 41.67% | 232,336 / 8,127 |
| picture-03 | `baiqi2.png` | 877 | 0.027418 | 0.055756 | 53.84% | 346,485 / 12,285 |
| picture-04 | `BV1bt421G7qL.png` | 913 | 0.055554 | 0.106272 | 57.63% | 363,063 / 12,789 |
| picture-05 | `BV1oe411i7oF.png` | 881 | 0.057423 | 0.100367 | 74.56% | 347,408 / 12,341 |
| picture-06 | `Cache_5d2e1902d7c282d2.png` | 722 | 0.018526 | 0.035506 | 82.28% | 282,025 / 10,115 |
| picture-07 | `人类化头像.png` | 956 | 0.053918 | 0.090944 | 64.30% | 378,300 / 13,391 |

这组数据证明用户反馈的第一类问题不能解释为“只是上下预览不一致”。`picture-01`和
`picture-02` 在 1024 预算下仍只有约 42% 相对改善；`picture-04/05/07` 的绝对边缘损失也明显偏高。
目前实现虽会在 96/192/256 上重评候选，但主要块画搜索和局部边缘修复仍发生在 96×96
平面，复杂人脸的眼睛、头发边界和细线被量化成明显方块。这是下一质量修复包的已量化基线，
不得把“能识别大致轮廓”冒充成与原图高保真。

## 验收分级和剩余工作

| 检查 | 当前状态 | 当前证据能支持的结论 |
|---|---|---|
| 原图→浏览器拟合 | 已逐图量化 | 7 图均完成 1024 预算，但其中多图质量仍不可接受 |
| 下方预览→右侧预览 | 通过 | 7/7 字节源和展示几何一致 |
| 完整复制→重新解析 | 通过 | 7/7 代码完整，实例计数一致，serialize/parse 精确闭环 |
| CK3 Apply/Copy | 待 MCP 逐图验收 | 尚不能宣称 7 图均被原生 parser 接收 |
| CK3 空间像素→右侧预览 | 受限 | 现有 MCP 只有语义路由和源码 Apply/Copy，无 framebuffer/空间像素摘要；需先补 MCP，不使用 OCR/坐标鼠标链替代 |

下一个可执行工作包是：在新的共同合同下实现高分辨率局部替换/边缘细化，用这 7 图逐图做
改动前后消融；同时为原生开发验收增加有界、只读的 CoA framebuffer/空间摘要 MCP。

## 复现命令

```bat
cd coat_of_arms_editer_of_ck3
pnpm exec playwright test e2e/user-picture-preview-consistency.spec.ts --reporter=line
set COA_CORPUS_BUDGET=1024&& pnpm exec playwright test e2e/user-picture-quality-corpus.spec.ts --reporter=line
pnpm test
pnpm build
```

质量套件把每张图的完整 CK3 代码、canonical 230px PNG、拟合报告截图、右侧预览截图和
JSON receipt 写入
`coat_of_arms_editer_of_ck3/test-results/user-picture-quality-corpus/budget-<N>/<case>/`。该目录是本地运行产物；
正式晋级的原生对照会另存到 append-only docs artifact，不覆盖浏览器基线。

# xenoamess hunter v4：1024 预算无缝浏览器基准

状态：**浏览器接缝修复通过；CK3 Apply/Copy 与原生像素对照待 WP1。**

实现与冻结 artifact 的提交：`d01f3d4e`。`report.json` 同时保留生成时基线 commit 和完整工作区补丁 SHA-256，便于逐字节追溯。

这是 `xenoamess-hunter-v3` 的不可覆盖后继。输入仍是用户提供 ZIP 中唯一的
`xenoamess_hunter_4096_no_shade.svg`，浏览器栅格输入、exact CK3 1.19.0.6 静态素材包和 96×96
评分合同均未改变。v4 只修复四叉树 paint tile 的输出覆盖几何、稳定 tie-break、导出门禁和证据完整性；没有启动或连接 CK3，
也没有使用 Java、后端、OCR 或前台桌面。

## 原缺陷可复现性

回归夹具使用高饱和底色、完全不透明测试画笔、相邻 1/4 与 1/2 混合尺寸四叉树块；只统计画面内部 nominal 公共边界带，
并以相同 surface mask 的无缝 nominal 构图作为参考。像素被判为泄漏须同时满足：相对参考最大通道差大于 2，且实际像素到
底色的平方距离至少比参考小 4。画面外边界不参与。

恢复旧 `[0.96, 1, 1.04]` 逻辑后，夹具稳定得到：

| Surface mask | 96px | 230px | 512px |
| --- | ---: | ---: | ---: |
| 关闭 | 186 / max 225 / peak 47 | 1,806 / max 225 / peak 228 | 5,112 / max 225 / peak 510 |
| 开启 | 186 / max 225 / peak 47 | 1,806 / max 225 / peak 228 | 5,112 / max 225 / peak 510 |

单元格依次为 `backgroundLeakPixels / maximumLeakAmount / max(rowPeak, columnPeak)`。mask 开关结果相同，证明规则网格来自
实例几何缩小，不是 surface wear；`ce_block_02.dds` 顶层 mip 本身完全不透明。

修复后候选只允许 nominal `1.00` 或覆盖更大的 `1.04`。CPU reference 的硬几何裁切按像素中心采样，因此 `1.00` 是该合同下
最小可证明无缝的 footprint；`1.04` 只有在总损失真实下降时才会入选。损失在 `1e-12` 内平分时，先选择覆盖安全，再选择较小
安全面积，最后才使用稳定键。96/230/512 的几何 post-check 任一出现泄漏都会拒绝导出。

修复后同一夹具在 mask 开/关及 96/230/512 六个观测点全部为 `0 / 0 / 0`。这证明门禁既能抓住旧缺陷，也能验证修复。

## 输入、合同与结果

- 原始 SVG SHA-256：`FA93CF19A687C0681E6D35AEFD6837B6279722B27470E63D6B0F3E99F4A5E8DC`
- 1024×1024 目标 PNG SHA-256：`53BBDB2FB3B8252475A12098BAC4E1B0A5BBC4765CB6896B4397923EE54D8AC8`
- 素材包：`ck3-1.19.0.6-base-complete-42p-1578e-8aux`
- 素材 manifest SHA-256：`AD7F0A911A2B4F002E923FEAB13716566D9A7B61447E9092504826FE6498FE91`
- 算法：`ck3-coa-browser-fit-v4-coverage-safe`
- 评分：`alpha-weighted-srgb8-mse62-luma-gradient-l1-38-v1`
- Renderer：`cpu-rgba8-bilinear-clamp-pixel-center-v1`
- 搜索平面：96×96；surface mask 关闭；随机种子不适用；候选比较数值容差 `1e-12`
- 用户预算：1,024 个实际绘制实例；停止原因：没有继续改善的候选

| 字段 | v3 共同合同重评 | v4 | 门禁 |
| --- | ---: | ---: | --- |
| 总损失 | 0.025898240475696027 | 0.025898240475696027 | 不劣化，通过 |
| 颜色损失 | 0.015389746153544555 | 0.015389746153544555 | 记录项 |
| 边缘损失 | 0.043043678580258954 | 0.043043678580258954 | 不劣化，通过 |
| 相对背景改善 | — | 86.771978337903% | 高于 80%，通过 |

历史文档只冻结到五位小数（`0.02590` / `0.04304`），因此 v4 E2E 另外把 v3 完整代码在同一新声明的评分合同下重新解析、
重新渲染并取得上述原始浮点数，再以 `1e-12` 比较。v3/v4 在 96×96 下完全相同并不代表高分辨率几何相同：两者
`fitted-flat-96.png` 的 SHA-256 相同，而 230px v4 已不再出现 v3 的规则底色网格。

| 计数 | 值 |
| --- | ---: |
| 用户预算 | 1,024 绘制实例 |
| 实际绘制实例 | 1,000 |
| 编辑器逻辑图层 | 1,000 |
| `colored_emblem` 块 | 1,000 |
| `instance` 数 | 1,000 |
| CK3 代码 | 380,862 UTF-8 bytes / 14,006 行 |
| 损失序列 | 背景 + 1,000 次接受；1,001 项严格递减 |
| 评估构图 | 2,300 |

精确 CRLF 复制载荷由 Playwright 在 `navigator.clipboard.writeText` 边界捕获，而不是从 DOM `textContent` 回读；随后执行
parse → serialize 精确字节比较。解析错误为 0，模型、元数据、源码正则计数完全一致，没有截断，也没有凭空补入 `mask`。

## Artifact 与 SHA-256

- [输入 PNG](target.png)：`53BBDB2FB3B8252475A12098BAC4E1B0A5BBC4765CB6896B4397923EE54D8AC8`
- [96×96 无材质拟合平面](fitted-flat-96.png)：`27551BC48DD82BCCB93E25DDC68F03A836E356C582B54D702E1EC64F509339EA`
- [230×230 shader 预览](fitted-shader-preview-230.png)：`58015D2ADB0BB54D8DB6E0F869663692C2473BCF02CF801CE7DA2D3511ED8F8B`
- [完整拟合报告截图](fit-report.png)：`638A42E9DD552ADE90A105F4AE339AF996DCBBD657170BC19718B0DADBDA6B75`
- [独立预览面板截图](preview-panel.png)：`4572E89A43A2B50639E0CA3FAD06E9ADF1E2D23619549FB04836005B071C8514`
- [精确 CRLF CK3 代码](coat_of_arms.txt)：`C4648E2C98D3503252D9A9A298B4A39E27A8F4C7269944E607F34F86B3C60571`
- [机器可读报告](report.json)：`ECC88D47E5D12CE866DA6E06174ED24073B30F29C8D699324CA45B5773449FE2`

`report.json` 记录输入、源码工作区补丁、asset pack receipt、配置、原始浮点指标、共同合同 v3/v4 对照、计数、严格下降摘要、
接缝指标和证据分级。报告自身哈希仅列在本文中，避免自引用。

## 验证与证据边界

在 `coat_of_arms_editer_of_ck3/` 执行：

```text
pnpm exec vitest run src/domain/parser.test.ts src/domain/imageFitter.test.ts
pnpm build
pnpm exec playwright test e2e/reference-hunter-fit.spec.ts
pnpm test
```

本版本已证明：浏览器回归通过；完整浏览器复制边界、parse/serialize 和计数传输通过。它尚未证明 380,862-byte 载荷能被 CK3
原生 UI 接受，也尚未完成 CK3 Copy 回读或 framebuffer 空间像素对照。那些状态明确保留为 `pending-wp1`，不得把本结果称作
“游戏内已验证无缝”。

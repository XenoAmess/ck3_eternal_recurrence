# xenoamess hunter：1024 层上限拟合证据

这是 2026-09-15 用户提供的 `xenoamess_hunter_4096_no_shade.zip` 的可复现质量门禁。ZIP 内唯一文件为
`xenoamess_hunter_4096_no_shade.svg`；仓库保留该 SVG，并使用 headless Chromium 确定性栅格化为 1024×1024 PNG 后交给正式
纯浏览器流程。没有启动或连接 CK3，没有调用 MCP、Java、OCR 或前台桌面。

## 输入与参数

- 原始 SVG SHA-256：`FA93CF19A687C0681E6D35AEFD6837B6279722B27470E63D6B0F3E99F4A5E8DC`
- 目标 PNG SHA-256：`53BBDB2FB3B8252475A12098BAC4E1B0A5BBC4765CB6896B4397923EE54D8AC8`
- 素材包：CK3 `1.19.0.6` exact base pack，42 pattern / 1,577 个可生成 registered emblem
- 算法：`ck3-coa-browser-fit-v3-shape-beam`
- 用户参数：最大改善图层数 `1024`
- 大预算搜索平面：`96×96`
- 重建路径：从最佳纯色背景开始，重复使用原生 `ce_block_02.dds`，以自适应四叉树叶片覆盖目标；每个候选经浏览器
  CK3 shader 翻译正向渲染，只有总损失严格下降才写入结果。

## 结果

| 字段 | 值 |
|---|---:|
| 实际保留图层 | 1,000 / 1,024 |
| 停止原因 | 剩余候选不能继续降低损失 |
| 评估构图 | 3,324 |
| 总损失 | 0.02590 |
| 颜色损失 | 0.01539 |
| 边缘损失 | 0.04304 |
| 相对背景改善 | 86.77% |
| WebGL2 RGBA8 交叉分 | 0.01536 |
| CK3 代码 | 379,666 bytes / 14,006 行 / 1,000 个 `colored_emblem` 块 |

1,000 并非硬截断或序列化遗漏：`provenance.layerLosses` 含背景加 1,000 次接受后的损失，自动回归逐项断言严格递减；其余候选
没有改善，因此没有为了凑满 1,024 而输出。代码超过 128 KiB，但该数值只是开发期 MCP 桥传输合同，不是已证明的 CK3 原生
剪贴板上限；网页继续允许复制，并显示证据边界警告。

## Artifact

- [目标 PNG](target.png)
- [96×96 无盾面材质拟合平面](fitted-flat-96.png)
- [230×230 shader/surface-mask 预览](fitted-shader-preview-230.png)
- [页面目标、参数、进度、双图与指标截图](fit-report.png)
- [生成的 CK3 代码](coat_of_arms.txt)
- [Playwright 文本报告](report.json)

关键 SHA-256：无材质拟合图
`27551BC48DD82BCCB93E25DDC68F03A836E356C582B54D702E1EC64F509339EA`；shader 预览
`5B1F5FA0FD2CF0C33A9A303D204A37FE72FE6CC4FFBF486F91CF911AFA1B9103`；CK3 代码
`15622775E549AF970EF29A3017FD72335589DC763607023A6A089923B4768A46`。

正式 E2E `reference-hunter-fit.spec.ts` 固定使用这张图和 1,024 参数，并要求至少 900 个严格改善层、总损失低于 0.04、相对改善
高于 80%、序列化块数与实际层数一致，同时保存上述运行 artifact。

# xenoamess-hunter-v6-compressed

本目录是 [`xenoamess-hunter-v6-edge-refined`](../xenoamess-hunter-v6-edge-refined/README.md) 的仅结构压缩投影。
只合并绘制顺序中安全相邻且 texture/colors/mask 完全相同的块，不改变 1,008 个实例的次序或参数。

- `colored_emblem` 块：1,008 → 299（减少 709，70.34%）。
- 绘制实例：1,008 → 1,008。
- UTF-8 bytes：383,865 → 263,603（减少 31.33%）。
- 96/230/512 px 逐 RGBA byte 差异均为零；serialize → parse 精确闭环通过。
- 输出 SHA-256：`2593605D696EFCBCEB58576D5105A4DF7C61B636A2F11969FEADBBFF0318401B`。
- 报告 SHA-256：`0B7D8CD5391CC735A183ADDCFFCB6FD2C1724B4B711886E86D9CE258C440E5D7`。

复现：`pnpm exec playwright test e2e/reference-hunter-v6-compression.spec.ts`。

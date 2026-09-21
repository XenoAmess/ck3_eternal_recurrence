# v15 质量首选候选 CK3 原生补验 r20

状态：`visual-passed / strict-source-normalization-observed`（2026-09-21）。

本次补验取 v15 七张图各自的 `candidate-01`，在 Steam 离线、CK3 `1.19.0.6`、结构化 MCP、无 OCR/键盘/鼠标/固定坐标条件下执行 Apply、原生 framebuffer 对照、Copy、再 Apply 和第二次 framebuffer 对照。目标图沿用 v14/v15 同一套 `canonical-preview-230.png`。

结果：

- 浏览器目标 → 首次 CK3 原生像素：7 / 7 通过。
- CK3 Copy → 再 Apply 原生像素：7 / 7 通过。
- 实例数、逻辑层数、colored-emblem block 数：7 / 7 保持。
- 首次 Apply 的严格语义序列：4 / 7 通过；picture-02/04/07 仅 `rotations` 不逐值相等，原因是 CK3 对小数旋转值做规范化。规范化后的 Copy → 再 Apply 为 7 / 7 严格通过。
- framebuffer 标定最大重投影误差为 0 px，低于 2.5 px 门限。
- 首次原生对照最坏值：MAE 0.038297、color MSE 0.008643、edge loss 0.124055、8×8 最坏空间 MAE 0.209689，均分别低于 0.1 / 0.03 / 0.16 / 0.25。
- Copy → 再 Apply 最坏值：MAE 0.0000633、color MSE 0.000000248、edge loss 0.000322、8×8 最坏空间 MAE 0.000846，均分别低于 0.01 / 0.001 / 0.02 / 0.03。
- Steam 保持离线；独占 launch/state lock 已释放；CK3 进程树与 watchdog 均消失；`cleanup_proven=true`。

`summary.json` 是可审阅压缩报告，SHA-256 为 `D56A42669CA9FB46367001D804B052BC3BD4A2D7D665E92F326124354E09C133`。原始 21,337,000-byte 报告 SHA-256 为 `399E5CFBBFF57F057CA1E7A4ECF2F3D5904379F18025C5D26258034BE3F9553E`，因内含重复源码和 base64 PNG 而按仓库规则不提交；14 张哈希绑定原生裁剪图与压缩报告永久入库。

本次补验证明历史 v15 首选在 CK3 中视觉可用且 Copy 后稳定；它不替代当前 Delta-Q v9 的独立原生证据，也不把 CK3 的旋转正规化误报成像素质量失败。

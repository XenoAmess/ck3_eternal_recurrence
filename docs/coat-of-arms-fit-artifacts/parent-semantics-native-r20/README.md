# CK3 `parent` 剪贴板预览矩阵（R20，探索性）

R20 首次用 reference-free framebuffer MCP 取得七个 parent/literal case，Apply、原生 Copy、capture 和受管清理均通过。它发现：

- 有效 `parent=k_england` 与显式写出的 England definition 明显不同；
- 有效 parent、缺失 parent 与根颜色 override 之间只出现 1 个 8-bit 级别的微小差异；
- 显式 child 会产生明显变化。

但 R20 在运行前没有登记“独立捕获量化噪声”的数值门限，所以 `summary.json` 只保存原始像素指标，正式
`parent_not_materialized_gate` 为 `null`。不得把 R20 单独写成正式通过结论。

R21 在启动前冻结门限并重跑同一矩阵，已取代 R20 作为正式原生证据：
[`parent-semantics-native-r21`](../parent-semantics-native-r21/README.md)。R20 文件作为前驱过程证据永久保留，不原地改写成 R21。

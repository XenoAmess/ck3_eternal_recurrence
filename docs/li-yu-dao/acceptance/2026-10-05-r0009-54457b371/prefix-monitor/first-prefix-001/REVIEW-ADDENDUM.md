# 首个 R9 日志前缀的分类补记

本次固定大小复制发生于 2026-10-05 UTC 05:54:03.208173–05:54:03.290549（北京时间 13:54:03）。`raw-prefix/error.log` 的 138556 字节 SHA-256 为 `0a9b5cfb2628d42b9b334e6adb0777640f6614f2f376ff66d64a0c6d6483fb50`。复制前后 path 与打开文件 handle 的各自元信息均稳定，原始日志末行完整；这只约束这次复制，不代表实时日志此后冻结。

原始严格分类保留为 576 条已识别 case fixture unused 和 2 条待审 fixture；没有覆写 `CLASSIFICATION.json`。逐条审阅后，另两条也均为 `lyd_im_adopted` 被设置但未使用的 fixture 诊断：

- 原始 line 115，字节 `[27354,27584)`，13:50:58，group SHA `4e86f129350e827f63a6ff891a37686861a8fe0c5dbe0682e40d6464833deb65`。
- 原始 line 404，字节 `[96632,96862)`，13:51:57，group SHA `6aaceec49f40be2f33e4e5c9dcd83950b002e4538bc95c33574b2f3bf1e24df3`。

因此，这个已保存前缀的 578 条 `[E]` 全部属于上述 fixture unused 诊断；C2 产品错误、`source_signed` 或 scratch 读取错误均为 0。没有据此确认正式交互、任意后续回调或最终整份日志通过。16 份 raw prefix 的 SHA 和复制元信息见 `INDEX.json` 与 `REPORT.json`。

观察者只读日志，没有操作游戏、main 或 pipe。后续等待 ROOT 指定回调消息后再建立第二个独立前缀；不会自动轮询。

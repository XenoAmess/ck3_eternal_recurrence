# R0011 实际永久入库追加记录

2026-10-06，ROOT 在 R0012 严格关闭后完成一次全局收集和永久导入。原 [REPORT.md](REPORT.md)保留作者截止时的原文；该报告中的收集器未执行、最终再冷载未执行属于其历史截止状态。

实际导入绑定 [INDEX.json](INDEX.json)：356,782 字节，SHA-256 `85aa58f2a6de0e5177bcd7986a9dc190f6ffc1fb20b88245c26b5b7b8a3fdd81`。2,180 个原始引用对应 1,665 个内容对象，原件、存储件和解码件均完成 SHA 与无损核验。约 90 MB 存档、DLL、EXE 和导出包本体继续外置，永久记录保存来源及精确哈希。

实际 ROOT 导入回执为 `C:/workspace/ck3_lyd_runtime_20261004/r11-root-global-import-receipt-after-r12-20261006-001/RECEIPT.json`；状态 `ACTUAL_ROOT_APPEND_IMPORT_COMPLETE_NOT_GREEN`，不授予额外实机信用。

[R0012 独立报告](../2026-10-06-r0012-632f0a57a/REPORT.md)追加最终吸收后的真实冷重载 58 项通过，不修改 R0011 原 SDK97 的 UNKNOWN claim。I3b、C3、I4 及一期整体仍未完成。

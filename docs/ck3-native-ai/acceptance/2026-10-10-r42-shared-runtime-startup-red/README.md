# R42 永久原件入口

主报告：[R42 shared runtime startup RED](../../2026-10-10-r42-shared-runtime-startup-red.md)。

- `FACTS.actual.json`：从原始回执提取的实际结果和信用边界。
- `INDEX.json`：ZIP 的全部 617 成员、来源路径、bytes/SHA 与外置 seed pin。
- `RAW-EVIDENCE.zip`：原件逐字节归档，7,314,363 字节，SHA-256 `3db4babbf20345ed58d636794b19e39e1be7229f1f5c4566bd96d75372240bbf`。
- `VALIDATION.actual.json`：成员、CRC、原件 SHA、目录计数、命令及脚本派生的实际核验结果。
- `package_evidence.py`：仅归档现成原件；`--output` 必须为新目录。

本场 startup RED、业务未执行。独立观察句柄证明 CK3 exit 1；不是原 CreateProcess 句柄、typed normal exit 0 或产品合格证据。原 `cleanup_ok=false/session.report=null` 不改。seed 正文未读取/打包；Source05 与 CI 的既有包只回链，不重复复制。

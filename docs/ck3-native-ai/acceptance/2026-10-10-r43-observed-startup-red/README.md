# R43 原件入口

主报告：[R43 observed startup RED](../../2026-10-10-r43-observed-startup-red.md)。

- `FACTS.actual.json` 保留实际 startup、采样、缓存勘正、CI 及闭场边界。
- `INDEX.json` 列出全部 506 成员、来源与 bytes/SHA，seed 只 pin。
- `RAW-EVIDENCE.zip` 为原始字节归档：11,849,698 字节，SHA-256 `a42370b4d2e6a14751aab1fb1df783da766d32059e30115681a24fb404fa6d0e`。
- `VALIDATION.actual.json` 记录本次成员、CRC、原件 SHA、目录计数和命令 pin 核验；CI 嵌套 logs 的既有一次核验只复用。
- `package_evidence.py --output <fresh-directory>` 只归档现成文件，不采样或运行游戏。

600 秒 startup RED、native0、steps0。最后活动样本止于573.100秒；约28.857秒后独立观察句柄得到CK3 exit1，不是原CreateProcess句柄或typed normal0。原cleanupfalse/sessionnull、缓存初稿错误与勘正均保留。无业务通过信用。

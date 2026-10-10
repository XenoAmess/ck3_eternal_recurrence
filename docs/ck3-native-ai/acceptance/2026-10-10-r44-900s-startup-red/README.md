# R44 原始证据

本目录保存900秒startup RED及实际闭场的紧凑永久证据。主报告为 [R44](../../2026-10-10-r44-900s-startup-red.md)。

- RAW-EVIDENCE.zip：13275410B，SHA `89ffffabe830f499174a9667d767277b60e4b31da04af2c69e8354967f637337`，594原件；ZIP成员与外置源对应关系见 INDEX.json。
- FACTS.actual.json 保存原 native report、两个 cutoff/最终采样摘要、frozen input比较、关闭/释放信用与限制。
- VALIDATION.actual.json 是本次一次归档字节/CRC/来源核验，不是业务PASS。
- package_evidence.py 复用 R43 producer，读取已结束原件并写新输出；不会启动 CK3/SDK/屏幕/进程或改旧记录。

seed91,711,686B仅既有pin+长度，正文未读/重hash；大STATE/sourceZIP/cache未复制。cleanupfalse/session.report null、独立 CK3exit1/非typednormal0原样保留。原 expected4339与实际 event4340分别记录。

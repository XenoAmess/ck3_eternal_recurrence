# R0047 空事务对照与闭场确认缺失

完整编号 `bf-202609141645-5434332d4d--li-yu-dao--R0047`；[实际报告](../../2026-10-10-r47-startup-control.md)。八步与空事务保存断言通过，正式I3b/C3/I4和whole product不授信用。原public run2/verify2、正常退出确认缺失不追认；独立原CK3句柄exit0、host0及资源闭场分列。

`RAW-EVIDENCE.zip` 1,110,002 B，SHA-256 `76357b7711a55d6172ad5524faa6339ea286b10901a5310f351212140811056f`。162条逻辑引用、133个按SHA去重的压缩对象，原选定正文16,940,416 B。一次producer验证全部object长度/SHA及ZIP CRC通过；导入只核输出pins，不重放业务或再次展开检查。

`INDEX.json`映射原路径到ZIP内`objects/<sha256>`；`FACTS.actual.json`分列case、原进程、keeper/CAS及晚审阅事实。还原时按INDEX选定对象并核其原长度和SHA。PNG、原存档、frozen argv、大native-wire、源码/缓存/native索引正文不重复入包，保留必要原pins；未逐一展开全部外部文件清单，不能当作全量原件备份。`COMPACT-SUMMARY.actual.json`是已完成只读提取，不再次读取SAVE正文。

首次archive003候选因native-wire超过8MiB失败；后继004对象验证完成后因外部pin展开超过1MiB失败，原部分包仍在本机有限期保留。最终005明确排除大wire、原stdout保留在压缩对象内但不重复展开其中的逐文件库存，实际单次exit0。没有提高8MiB单件、32MiB总正文或1MiB索引上限。

另附原预留核销、有限清理复核和可移植manual-review五项测试实际命令回执。本包及外部原件均遵守[通用存储策略](../../../storage-retention-policy.md)，引用不承诺永久本机可用；TTL到期复核不改写本轮事实。

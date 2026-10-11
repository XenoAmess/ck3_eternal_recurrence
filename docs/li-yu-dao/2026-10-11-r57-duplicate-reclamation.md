# R57 重复输入实际回收（2026-10-11）

ROOT 在行政闭场后串行完成精确回收：**3,744 件、513,620,896B 逻辑大小**。其中四份重复 SAVE 为366,678,829B，3,740件输入cache副本为146,942,067B。allocation API汇总为522,037,408B；不能据此声称磁盘free变化由本次动作独占造成。

001已准入，但metadata规划漏了继承的R0056路径，plan/serial均实际1。它在任何apply前停止，2026-10-11 04:02:25 UTC零删除闭账，回收信用为0；原失败、partial及命令回执保留。002只纠正路径，独立新attempt未改写001：admit0，serial0（04:09:18–04:10:43 UTC），close0（04:11:24–04:11:25 UTC）。

删除对象是已由现存原件承接的profile restore/last_save/autosave/xar_checkpoint及输入cache重复副本。0240 seed、R57 initial-school-cooldown-checkpoint、R54 immutable seed、独有输入、native及故障诊断保留；本次没有删除最后恢复来源。原路径和文件身份仍由外置NATIVE-PLAN及逐文件原台账提供，本包不复制SAVE、cache、PE/native或五份大detail/result。

002 canonical event保持原字节；独立CLAIM只随实际CLOSED提交一次513,620,896B，不重复消费旧事件。48MiB预约已结束，future0；保守项目carry为135,561,175,567B。结束预约不等于释放48MiB磁盘文件。闭账fresh free为619,256,213,504B，free变化独占归因为UNKNOWN。

旧prepared validator为 **RESTORE_REQUIRED**；原manifest和历史结论保留，但旧payload重放前须先恢复。原cache复核仍为2026-10-17T13:06:29.278808Z，quota复核仍为2026-10-12T05:19:51.814083Z，未续TTL。详细ledger按30日、摘要按180日有限保留，无自动删除或续期。

本包同时保全f9798edadc5e31f759a7e6d633233d1cf1147001与2c9eeb1885fe56ca74b6ba7d9e91fd39a3c060b4的Official/Linear双SUCCESS小报告。CI只授对应源码检查结果；本次回收不授启动、正常GUI退出、C3或正式业务信用。第一期仍75%估计／NOT_GREEN。

精确小原件与外置stdout/细账来源映射见[证据索引](acceptance/2026-10-11-r57-duplicate-reclamation/INDEX.actual.json)。此文为已发生清理的入库候选；Source16路径计划和以后的发布HEAD不在此预断。

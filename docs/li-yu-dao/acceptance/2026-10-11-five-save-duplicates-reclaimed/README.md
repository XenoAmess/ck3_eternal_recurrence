# 五份已闭场 SAVE 重复副本实际回收

ROOT 于 2026-10-11 06:21 CST 执行一次，原命令 exit0。先持有 3 个保留源与 5 个目标，逐个核验完整 SHA/身份（共读 733,357,860 B），全部匹配后才删除；5 个目标均实际缺失。逻辑回收 **458,348,713 B**，API 分配量之和 **458,362,880 B**。

精确删除集合：CASE3/4/5 的 `state/profile/save games/restored_campaign.ck3`；CASE4/5 的同目录 `xar_checkpoint.ck3`。这五个旧副本现已不可读，历史路径与 SHA 保留在 [原回执](evidence/RESULT.original.json)。前者由原 R10 0240 保留基线恢复；后者分别由 R53/R54 各自保全的 `initial-school-cooldown-checkpoint.ck3` 恢复，不能当成原基线。

删除期间三个保留原件均持有可读句柄并核完整 SHA；本归档不重开或重验存档。所有 shadercache、autosave、last_save、唯一实际 SAVE、失败 JSON 以及当前 Source13/Cbr3/Source14/009 均保留。ROOT 只解除五个可重建副本的用途保护，7 日保护继续覆盖必要最小失败集；所有原期限不续。

卷 free 从 619,429,654,528 B 到 619,888,009,216 B，差 458,354,688 B；并发变化不能独占归因于清理。本次不得再计入旧 R52 shadercache 已删 146,942,031 B，不把预约释放计成物理删除。下一准入可只扣减本次逻辑量一次，仍须重新核容量与其他预约。

一期仍 75% / NOT_GREEN；无业务重验或新增 I3b/C3/I4 信用。详见 [索引](INDEX.actual.json)与[原命令](evidence/COMMAND.original.json)。源 plan/executor 留外置精确 ref，不复制大输入。详细回执 2026-11-09 复核，compact 原截止 2027-04-08；归档不续期。

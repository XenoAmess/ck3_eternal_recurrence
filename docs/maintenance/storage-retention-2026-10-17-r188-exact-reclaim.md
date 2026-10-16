# R188 准备期精确回收实际结果（本地 2026-10-17）

`machine_id: desktop-3fevhd2-1c74096080`；通用策略 **1.0.0**。实际删除发生于 **2026-10-16T18:08:29.179012Z** 前，日期标题按北京时间。本记录只证明该来源机器；不能外推其他机器的占用、原件可用性或保护状态。

Root 逐项审阅绝对构建根分组及精确 ZIP a02 后，采纳有限期的 source/index 保护，并授权最多 1,000 叶。实际 **1,000/1,000 删除，0 留置/失败**：

| lane | 叶数 | logical（B） | 单硬链接 allocation（B） |
| --- | ---: | ---: | ---: |
| 8 个旧构建根的 993 OBJ + 6 项目生成 LIB | 999 | 470,905,783 | 472,879,104 |
| 已到期可重建 Superman process CAS ZIP | 1 | 1,169,783,806 | 1,169,784,832 |
| **合计 C** | **1,000** | **1,640,689,589** | **1,642,663,936** |

**D credit = 0**。此前 E01 exact7 的 D 5,629,001,728 B 与 R184 已回收项目均未重算。本批 allocation 是真正已删叶的实测分配量，不能把并发 free 变化全部归因于清理。新保存的 index 占 335,872 B allocation；仅扣该新增 keeper 的净量为 1,642,328,064 B，其他小回执另计。以最新 free/used 作为预算时，不再重复减已包含的历史 credit。

## 范围、来源与执行守卫

[8 个绝对根的分组](evidence/storage-retention-2026-10-17-r188-exact-reclaim/NATIVE999-GROUPS.readonly-a01.json)、[999 叶原计划](evidence/storage-retention-2026-10-17-r188-exact-reclaim/NATIVE-EXACT-PLAN.readonly.json.gz)、[一叶 ZIP 原计划](evidence/storage-retention-2026-10-17-r188-exact-reclaim/ZIP-ONE.plan.readonly-a02.json)保持原字节。a26/a27 只清冻结 subset：a26 3 LIB，不补第 4 项；保留全部 EXE/DLL/source/CMake/Ninja 和关键历史回执。Root 已用 R186/a29 实际正常存档、退出 0 结果解除旧中间对象原字节 fallback 用途；不声称自然满 14 天。

ZIP 是 48 小时到期的可重建 process archive；原 working ZIP 早已缺失，**不是两份现存 ZIP 去重**。没有重新哈希或复制 1.17 GB ZIP。只从其受保护读取句柄抽取 335,729 B `index.json`，独立 keeper SHA 为 `e0803f56c58fb6267fd1e0f08353293acd3f28289f20b63410f809e36b512ac1`；Win32 FileID **[3061637496, 1125899908743803]**。keeper 的原机精确路径、1074 项 source 索引、保留 final/media/manifest/packager 来源及期限都在原计划和 Root 采纳回执中。

先落 [Root 采纳](evidence/storage-retention-2026-10-17-r188-exact-reclaim/ROOT-ADOPTION.actual-a01.json)；fresh RestartManager 与旧 root producer 检查未发现消费、没有 shutdown/restart 调用。源 1,074 叶、index、final/manifest/recipes 等 **1,129 个**保留句柄全程阻止写/删，执行前后身份一致。1074 项只复核当前文件身份/大小/时间和保护 digest，不重新全文 SHA；小型 recipe/index/manifest 有内容 SHA 检查。

所有 target 仅通过同一独占 `DELETE|READ_ATTRIBUTES` handle 比对冻结 volume/FileID、size、FILETIME、link=1 和 allocation，随后逐叶 disposition、关闭并确认原路径不存在。没有递归删根、补选未审项或按回调 ACK 计 credit；没有大 payload body hash。a29、R188 现场、R186 normal save、Steam/helpers、active capacity 均未变；screen/SDK/TaskBus/安全设置零操作。

保留 source/index 的 owner 为 Root，保护截止仍是 **2026-10-17T17:56:09.645216Z**，没有自动续期；小 index 作为 record 的复核时间仍为 **2027-04-14T17:59:44.610089Z**。重建可得到新的派生 archive，不保证历史 ZIP 编码逐字节相同；旧对象标记 `deleted_unavailable`，历史 manifest 不改写、不制造同名替代。跨机只能复用方法和知识，不能假定原机 keeper 随 Git 同步。

## 实际结果与读回

[实际总回执](evidence/storage-retention-2026-10-17-r188-exact-reclaim/ROOT-DELIVERY.actual-a01.json)记录 C free：执行前 28,495,585,280 B，执行后 **30,138,322,944 B**；D free 当时 **52,566,605,824 B**。这些只是有时间绑定的历史快照，不产生新容量准入或配额，也不复用已过期的 07:45 授权窗口。

[独立读回](evidence/storage-retention-2026-10-17-r188-exact-reclaim/INDEPENDENT-READBACK.actual-a01.json)再次确认 1,000 路径不存在、1,000 FileID 唯一，index keeper 当前身份和小 SHA 不变；其中新鲜 free 数值以其 UTC 为准。[逐叶 availability](evidence/storage-retention-2026-10-17-r188-exact-reclaim/ITEMS.actual-a01.jsonl.gz)包含所有精确历史路径、FileID、kind、logical/allocation 与状态，不提交原 payload 或全盘库存。

`automatic_gc: false`；这次是 Root 审查后的专用执行，不是每日 04:00 只读巡检自动删除。未触发或修改 Scheduler。主 HEAD 在实际执行前后都是 `d05b0c780b615faa714fdf0535403bb2e6941faf`；本便携候选只写外置目录，未 apply 主仓。精简 record 按策略 180 天复核，详细 ledger 默认 30 天归纳，记录包装不延长原件和保护寿命。

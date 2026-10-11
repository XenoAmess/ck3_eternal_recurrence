# R59 / CASE10：74 个历史文件用途退役

2026-10-11，本机按已发布存储策略完成 R59 / CASE10 两个明确历史 scope 的用途退役：两批原命令均0，共删除 **74 文件 / 183869349 logical B**，allocation API 汇总183998696 B。这是用途结束的独有文件退役，**不承诺重建**，不冒充重复副本资格。原27份SAVE退役信用不在本轮重删或重扣。

原失败全部保留：首次 admit1，002恢复0；plan0；原 apply1 因 phase 判定误拒而 deleted0/credit0。随后按明确 CASE10、R59 两批执行，各0；finish0 另写 recovery aggregate/credit/link，原零删除 aggregate/credit 未覆盖。首次 close1 因计量输入含嵌套目录被拒，002纠正后0，原48MiB预约于 **11:31:14.393423 UTC** 完成闭账。单次事件 `lyd-r59-case10-purpose-retirement-exact-reclamation-20261011-001` 与唯一 claim 绑定，恢复未新增预约或重用旧信用。

闭账原件载明 future reservation0、other reservation0、known retained521370 B；carry134697538883→134513669534 B，本轮实际信用只扣183869349 B一次，旧信用再次扣减0。闭账 free620062707712 B为独立读数，不将并发物理空间变化独占归因于本轮删除；logical和allocation API也不等同实际独占可释放量。

三个 SHA 未知的 SAVE 被保留；所有 cache、seed、Source17、native、原0240均不在本轮删除范围。原逐叶PLAN85048 B、detail ledger、存档/native正文不复制入库，仅由原 aggregate/link 的精确ref指向外置原件。原失败和恢复分别保留在[小证据索引](acceptance/2026-10-11-r59-case10-purpose-retirement/INDEX.actual.json)，raw保字节。

详细回执 review期限为2026-11-10T11:12:32.213687Z，摘要期限2027-04-09T11:12:32.213687Z；原cache/源码TTL与quota review不续期。closed没有授权自动删除其他scope，也不产生业务信用。

源码 `a4ae3c7509bfaec015ad38ce76c1e173c7eea524` 的 [Official Runner CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38135431053) 与 [Linear history](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38135431063) 均 attempt1 / SUCCESS，原78080 FAILURE继续保留；这里只引用现成元数据，未重查、下载日志或重跑。CI不外推新native/CK3业务。Phase I **75%仅估计，NOT_GREEN**；本次仅容量退役和知识保全。

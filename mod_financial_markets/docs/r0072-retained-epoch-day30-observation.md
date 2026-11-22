# R0072：E6累计D30观察缺一条，原续行案PARTIAL

2026-11-23（北京时间；原作业UTC为2026-11-22），machine_id: `4-8e1c2f1861`，CK3 1.21.0／build26622941。实际来源 `db315f6abef0a6fc195148efc90ee4d6f403f484`，scene22i／`market-evolution-continuation21`。沿R71 D14最新物理档保留E6，属于R64自然分支；没有新开世界、回滚R64、ARM／新epoch、重新emit或业务注资。

## 已保存事实

| 范围 | 实际结果及边界 |
| --- | --- |
| D0冷载与阶段 | 23279条完整金融／news投影与R71 D14全等，missing／added／changed均0；E6 observer150995293、epoch6、原基准金融289及原15条记录逐项保留。D0 Root阶段实际接受，非业务或35日通过。 |
| 第二份SAVE | 本地D16／原累计D30，raw53151696→53152080，新增16自然日／384ticks。每档8次完整解析成功；实际共2SAVE，授权最多3份不等于已存3份。D35及第三档未执行。 |
| 严格观察失败 | 30条记录／应31，daily_samples29／应30；305后下一条观察记录为307，缺金融306的记录，producer gap／allocation标记被报告存在。30条实际issues、continuity=false、35日标志false；原15条前缀仍与R71完全相同。 |
| 金融与图端点 | 金融端点303→319为＋16，与观察缺一条并存。跨日Whole23279→21061，missing4204／added1986／changed7981全部留存；这是跨日差异，不是D0冷载不相等，也未逐项归因或授守恒／回收正确。 |
| 计数与覆盖 | D30登记139、活跃136、pending0、期货计数134只是已读计数，不证明paired容量、交割、退款成本或新发行资格。原局及早期已通过业务保持各自范围。 |

这次只确认观察记录存在缺口。金融端点＋16既不能补造中间见证，也不能单独证明每次业务日结均完成；同样，缺306记录尚不能定位到产品timer、daily业务或observer hook的具体原因。根因仍由独立源码诊断处理，不能预写某项调度修复通过。

## 负阶段、原件和正常退出

Root在16:12:23 UTC按现有公开响应格式发表第一项assertion=false、其余两项true，明确不接受“累计30天已有31条连续记录”。Generic据原严格要求拒绝，保留 `Original product GUI/semantic requirements incomplete`，未继续剩余5天。原负phase notes一处写成“31个issues”，这是内部计数笔误；实际facts数组len为30，以原967180字节报告为准，原响应／notes／False断言均不改写。

START原退出2／1212.9410241秒，public run2／1209.1411938秒、verify2／0.5352885秒，整案PARTIAL、case／boundary／product均false。这是实机观察条件未满足，不是解析或软件回归失败；pipeline D0原0／156.1676554秒、D16原0／152.1477221秒只证明其读取流程完成，不授业务／连续样本通过，也不作为游戏日性能指标。

Game5272正常退出、retainedOS／Host／Job／keeper／allocator均为原终态0，cleanup／threadfinished已证；keeper末序16217，CAS16217→16218 done、resources为空。正常退出自动保存仍未单独核实；资源正常释放不改run2／verify2或原R71 GAP。

## 来源与后继边界

本场当前READY与Host Python后继绑定已经实际消费成功：沿原Q49／e672 Native编译来源和同DLL，没有新Native或Java编译。上一软件记录中的“待绑定”是当时切点；本场实际来源绑定不等于金融业务通过，也不重复计640／loc25／NoGame115。

唯一已保存前进来源为本场D30档：222144536字节，SHA-256 `10f1745054ebb847b6b8d61a51512cff4398b8a1115fef4ff6e5c6c589601112`。原gap和失败事实保持；当前诊断必需原件按存储策略限期保护，删除派生资产不改写原结果；先定位真实回调原因，再用明确的新前进合同选择后继，不回滚、不重ARM、不回放旧SAVE，不以再跑5天修复历史缺口。21日续行／35日观察、每日金融覆盖、容量／395日性能、20剧情、全游戏送达、完整Mod及Workshop首发均未通过；无总比例结论。

[两档、30条issues、负phase与正常释放原件索引](../../docs/maintenance/evidence/2026-11-23-financial-markets-r0072-retained-epoch-day30.json)。

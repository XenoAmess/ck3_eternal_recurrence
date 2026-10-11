# R56：71日观测后事件边界拒绝与实际闭场

本机一期仍为 **75% / NOT_GREEN**。R56 使用 Source15/O15 与原0240存档完成71个自然日的合格观测，期间修派确认按钮始终禁用。下一步 `case-natural-day-0074` 出现活动事件，普通逐日入口拒绝继续；没有到期、最终SAVE、冷重载或完整I4通过。

完整小原件见[索引](acceptance/2026-10-11-i4-natural-r56/INDEX.actual.json)。原native报告13,335,772B、SHA `68f55842797645a61e9bdb2035f648b2bfe2d3aab19d2c8c6cc496e4527321a9`外置保留，不把大报告、SAVE、缓存或截图复制入库。

## 实际失败

[精确失败字段](acceptance/2026-10-11-i4-natural-r56/failure-frame.actual.json)的32个暂停读取谓词只有第9项失败：`active_event != None`，而本次普通推进未准入事件实例。同一PID/owner、paused、map_ready、mailbox ready/failure/date等其余31项均满足。它属于严格事件边界拒绝；不能归因为此前的pending-ready缺陷或仅凭历史 `stress_points` 诊断推断原因。

末次合格日期53146416；被拒场景日期53146440不计为第72个合格观测。0074的queue exit0只证明一次提交；原host wait1、受管CK3 exit1、公共run/verify均2。原始失败不改写。ROOT首次读终态报告后，因摘要缺少具体谓词，另授权一次精确有界诊断读取；两次实际读取的用途与SHA均记录，未为状态轮询重复读取大body。

## 实际闭场与容量

游戏与host在ROOT正常退出复核前已退出，故保留[明确阴性回执](acceptance/2026-10-11-i4-natural-r56/normal-quit-negative.actual.json)，没有伪造GUI退出或OS0/native0。ROOT于01:38:35Z直接审阅新的Steam原始画面，底栏显示“离线模式”；窗口实际位移及新像素收据在[最终复核](acceptance/2026-10-11-i4-natural-r56/final-offline-root-review.actual.json)。显示恢复、STOP、原keeper/allocator实际等待均0，随后CAS **4713→4714**释放。

预约013于01:43:22Z实际闭账，未来写入预留0。限定新增保留978,200,491B，加闭账输出上界1MiB后979,249,067B，保守项目carry为136,188,544,282B；闭账时卷空闲618,657,980,416B。此处物理删除0B，没有再次扣四项已消费清理信用，也没有续期缓存、source、native或原配额。原close因精确graphics receipt超过1MiB失败；后继只允许该文件一次≤2MiB读取、按字节校验Python producer，并计入两次close命令。失败与成功原件均保留。

## 并行结果与下一门槛

新增 `tools/c3_common_g4_observation.py` 只验证公共G4真实查询结果与冻结DTO绑定。原Source15合成合同8项及新便携入口1项实际通过，生产qualifier未改；默认测试metadata明确synthetic，正式C3仍须B4/B5及同场新Title的真实查询与SAVE联结，没有实机信用。

I4公共冷重载候选已完成8项离线合同检查；独立审阅发现真实公共wrapper argv尚未覆盖，最小修正继续，不能用R56失败世界准备冷载。B4原生EH独立fixture已修正栈对齐与主异常判定，等待独立192MiB准入后构建和Windows实际异常流程。Source12–14及R56重复输入回收仅到只读候选/计划，未冒充已删除。

当前固定HEAD `c44f94397b52b23845bba50921afcf6fe8025844` 的[官方CI](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38099634211/job/114352700779)及[线性历史检查](https://github.com/XenoAmess/ck3_eternal_recurrence/actions/runs/38099634202/job/114352700723)均实际success；这不授予业务通过。现场释放后已fetch/rebase更新主线，没有merge提交或force push。

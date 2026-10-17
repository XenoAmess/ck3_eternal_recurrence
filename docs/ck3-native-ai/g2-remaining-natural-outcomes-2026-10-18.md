# G2剩余两项：Sway终局与自然继承

2026-10-18。`machine_id: xenoamess-full-tower-eb9d2c1186`；本次离线观察开始于
2026-10-17T19:01:26Z，来源、源码pin与验证见[小型证据](evidence/g2-remaining-natural-outcomes-2026-10-18.json)。
G2仍为 **6/8**，M6、M7均未完成。当前罗贝尔战役继续推进及录制优先，本包没有操作Game、SDK、MCP、Steam、桌面或录制。

## M6：已补公共源码的真实receipt身份接缝

当前公共完整规划器已经具有普通Sway调度；冻结SDK48尚无此调度器和Service adapter。
P50实际启动参数的小回执包含七个Sway权限开关，因此不能归因为缺少开关。
仅等待当前旧执行源不会自动补上普通Start路径。P49已验证但未启用的五叶组合仍是未来必要SDK维护的输入，
本包没有将它热装到当前SDK，也不要求中断有效自动游玩。

本次把该候选中尚未进入公共源码的两个formal-consumer接缝采用到
[sway_formal_consumer.py](../../ck3_autonomous_player/src/xar_autoplayer/sway_formal_consumer.py)：

- 原版1.20.0.4的applied receipt含原action及完整SchemeID，却不序列化actor/target。
  在精确build、EXE、action、完整ID/generation和前后capture/date匹配后，从已持久化原动作投影这两个身份；
  原始receipt保持原样。后续实例观察与消费可以取得原身份。
- 真实Start后，独立active read必须找到同完整ID、generation及target的唯一行，且晚于receipt。
  保存该原始行与独立查询来源；另一个实例即使同target，也只保留pending，不产生Start成功信用或重发。

公共[严格分类器](../../tools/g2_saved_campaign/sway_start_typed_classifier_v1.py)复用原P44已验的纯函数，
接收当前场actor/episode/PID及完整Start链，只授`Sway Start primitive`；终局、收益、游戏日均为false。
当前运行的canonical classifier没有被替换。未来SDK合批也须同步采用已验证的完整普通接线及外层分类入口，
不能只复制此leaf或改变权限便声称已部署。

新增[三项便携组合](../../ck3_autonomous_player/tests/unit/test_sway_actual4_start_observation.py)
使用当前公共全规划器、实际query/action transport、formal ledger、实例观察及following consumer，
Native回包与OS边界全部为synthetic。3项及3个子例通过，2.68秒。
覆盖真实`.4`序列化字段缺actor/target后的身份链、一次Start/后续消费/重新创建Service不重发、
独立实例不符保留pending，以及分类输入漂移拒绝。原68项与P49三项历史组合未重复执行。
这不是CK3冷载、原生Start或吞吐验收。

真正剩余的M6观察按既有[原版来源树及终态合同](sway-beneficial-terminal-followup-12004.md)进行：
保留当前场原action/actor/target/fullID/generation；自然推进后独立读同实例终止事实与具名修正收益；
由下一次实际普通玩法消费并保存原记录。状态1可证明`terminated_unattributed`；行消失、总好感、阶段成功、
Start ACK或同值正修正均不能推出有用终局或新增收益。阶段收益可以与原实例继续并存。
不新增穷尽所有终态原因的前置门槛，也不以手动Stop制造成功。

## M7：自然结果观察沿原普通继承通道

已存在公共[异步owner adapter](../../tools/g2_saved_campaign/m7_ordinary_successor_async_queue.py)、
[纯原版无pact资格](research/sdk37-verified-vanilla-lifecycle/README.md)及本场私有自动handoff。
本次离线核对P50准备源仍由既有队列在刚结算的actor/episode边界调用handoff，
保留已完成Continue时不重发，继承modal的typed Close与独立clear、successor SAVE、goal及逐title reconciliation。
源码header里的候选描述不是现场调用证明；本次没有自然继承回执。

下一批直接在普通运行中观察，不另开继承专用游戏：

1. 在前任仍活时保留最后完整succession expectation及campaign goal；已有观察随正常帧更新。
2. 自然actor/episode改变时，使用原结算AUTO与同Game出生代，不重发该AUTO。
   对比实际后继及全部前任title；保存`successor_match`、`title_distribution_match`和`matched`。
3. 原队列在必要时执行一次typed modal Close并独立验证clear；原Continue已应用而持盘失败时保留真实失败，不重发。
   将真实successor SAVE配对纳入原owner状态后，继续后继普通玩法。
4. 留存之后正常玩法的goal消费与后继配对。未来本来必要的cold维护，再验证同goal、有效旧动作回执及零重发；
   不为本离线包抢占运行槽或专门重启。

当前30年窗口内未自然发生目标时记`evidence_not_observed`，继续普通战役；不强制死亡或手选继承人。
已有N42后继物理载入/goal小证据保留其历史场次身份，不能转记为当前1066干净局的继承成绩。
其他政府/种子的业务资格仍是M7更广缺口；本包不把当前自然继承子证据等同整项完成。

## 首次30年手动MCP保存与永久保留

当前公共MCP为`ck3_save_checkpoint(expected_revision=<fresh revision>)`；只接受revision，
原生固定文件名是`xar_checkpoint.ck3`，没有用户命名参数。Driver等待真实物化并返回date、history、size和SHA。

到首次30年实际目标时，owner先停后续自动SAVE，取得fresh SEM后显式调用这个MCP一次。
真实物化成功后保护该物化文件，停止后续自动SAVE；沿本场交接要求，等Game实际退出后再
把该次真实文件保存为唯一命名的独立副本，
核对MCP SHA与保全文件SHA、记录目标日期/actor/episode/机器及原SAVE回执。
这份副本按用户2026-10-18明确“以后不要删除”指令永久保护，覆盖此单一资产的默认到期规则；
普通滚动checkpoint、Driver、原片不因此全部永久保留。
新命名保全不会伪造游戏内存在命名接口，预先复制旧SAVE也不满足该次手动MCP保存。

Python/闭场JSON与已验源接缝不新增Paradox脚本语义，`open_kaishek: not-applicable`。
本包没有读取活跃Driver/SAVE或大媒体，没有编译、启动、热装、删除或新增容量预留。
小型派生记录按通用策略48小时复核；最终永久SAVE是用户明确指定的后续独立资产，尚未生成。

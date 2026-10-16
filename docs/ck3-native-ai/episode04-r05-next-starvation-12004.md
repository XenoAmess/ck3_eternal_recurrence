# Episode 04 R05：下一次自然低库存、零库存与实际供给扣兵

本页是下一场执行卡，**没有新增饥饿实机正例**。它将既有原生结算来源、当前公共查询 profile 和 keyed physical consumer 接成最小自然实验；不新增 native hook、SDK 入口或虚构查询参数。R05 仍未闭环，不能由本页提高研究或镜头百分比。

离线审阅时间 **2026-10-16 09:54:40 UTC**；`machine_id: desktop-3fevhd2-1c74096080`，由 `tools/ck3_live_run_id.py machine` 当次读回。Git HEAD 为 `20c7319b6964c80fa419540cf4e30852feff4810`；工作区已有其他并行任务改动，本任务只新增本页。目标来源身份为 CK3 **1.20.0.4 / Steam25734779 / EXE SHA-256 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`**，复用既有研究 pin；本任务没有读取游戏 EXE、连接进程/SDK/桌面、构建或运行旧 fixture。机器 ID、安装和新场资格不能由本页外推到其他机器。

## 当前缺口与新增的源码关联

[R182 实机摘要](episode04-r182-march-and-county-p-12004.md)报告 Army18 两端供给 raw `30000000`，即 300 供给；不是低于10的候选。[R183](episode04-r183-window-capture-12004.md)新增三次自然日回执和截断录像，没有新增供给数值或物理扣兵资格。因此继续在该高库存基线上等待几个游戏日，不能被称为一次有效的饥饿实验。

本页新增的是以下**可复用源码关联**，没有新取原生指令事实：

| 当次核对的仓库源码 | 与下一场采样直接相关的事实 |
| --- | --- |
| [公共 MCP 实际签名](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py#L3042) | `ck3_query_army_strengths` 默认 `profile="ordinary_core_v1"`，其说明明确省略 retained phase journals；必须显式用 `observed_history_full_v1` 读取 R05 日志。现有 `army_ids`、`expected_revision` 足够，不另造 future-date 或 drain 参数。 |
| [军力 collector](../../ck3_autonomous_player/native_bridge/src/ck3_12002_army.cpp#L1038) | 当前 stock 从 CArmy `+0x180` 直接读取；capacity、attrition fraction、monthly-named rate 分别取原有 getter。getter 是当前观测，不能代替下一次 writer 当场 stock。 |
| [parent context 捕获](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_supply_parent_join_context.hpp#L43) | writer 使用实际 invocation receiver 再读 `+0x124/+0x10/+0x180`，核身份后复制 `stock_at_writer_entry_raw`；不是借用 callback entry/return 库存。此功能宏在 header 缺省为0，不能只因源码在仓库就声称运行构建已启用。 |
| [callback journal](../../ck3_autonomous_player/native_bridge/include/xar_bridge/army_actual_supply_callback_observations_v1.hpp#L14) / [writer journal](../../ck3_autonomous_player/native_bridge/include/xar_bridge/army_actual_loss_writer_observations_v1.hpp#L19) | 两个全局环各为512条。每 exact 日采样只是降低覆盖风险；仍须逐环检查自己的 fence、oldest/latest、overwrite/failure，不保证一天内不会覆盖。 |
| [keyed join](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_actual_supply_parent_join_summary.py#L8) / [来源阶段分类](../../ck3_autonomous_player/src/xar_autoplayer/bridge/army_periodic_loss_component_12004.py#L10) | join 按真实 token/thread/depth/双 FullID/date 关联，物理数从 unique slots 复算。join 的 `strict_below_ten_supply_physical_debit_soldiers` 当前**只合计供给 preferred**；完整 supply residual 要另外按真实 parent/callsite/flags 分类并分列，不能拿 preferred 小计冒充整军全部供给损耗。 |

portable 链接均指仓库内文件；外置大原件只由对应实机摘要定位，本页不搬运巨型导出。旧文档的 `SOURCE_NOTRUN`、默认OFF和外置候选状态保持历史事实；新场必须核实际 hello/build/字段和完整 parent 样本，不能由旧文档单句判断当前是否已部署。

## stock、状态、预算与物理扣兵分四列

1. **库存**：signed int64 / Q100000。当前 getter、callback before/after、writer 当场 stock 分列保存；不能用其中一个倒填另一个。
2. **状态**：[既有 R05 来源](episode04-starvation-loss-12004.md)证明按 `trunc0(stockRaw/100000)` 后的 signed32，依实际 loaded levels 原顺序选档。普通原版表 `[60,10,0] / [0,0,5000]` 下，非负 raw `<1000000` 才是低于10；exact10不是正例。必须保存当次 loaded 表和实际 commander/fleet suppression。
3. **预算**：一次 updater 成功后才读更新后的 stock，按合格兵数与有效分量计算整数 supply budget。原版5% base、无修正的普通域中，19名合格兵预算可为0，20名才可为1；避免选择人数过少或有效分量为0的候选。getter fraction、request 和 conditional budget 仍不等于已经扣兵。
4. **实际写入**：只认完整同实例 unique physical slots 的 `SUM(before.current-after.current)>0`，并与原生合计一致。cache、Army 总数净变、界面百分比和写入 ACK 不填该列。兵力因补员上升也不抹去已经单独记录的供给扣兵，但净变化必须另报。

[零库存来源](episode04-zero-supply-loss-source-12004.md)已闭合：stock0加负 rate floor回0仍可 AL=true；这里没有“0时不扣”或“0多一档”的特殊分支。预算读取更新后库存。因此自然从正库存跨到0的**同一次 callback**就可能产生 stock-at-writer=0 和 physical debit；不必人为等待另一个所谓零库存月份。若当场没有 writer，仍不能单凭 stock0→0判定是 updater拒绝、整数预算0或其它抑制。

## 结算机会与观察天数

[当前 callback 来源](army-current-callback-supply-risk-12004.md)闭合 daily dispatcher `2A9A570`：它选 `uint32(GameState+9C)%30` 的实际 pointer bucket，按原存储顺序逐 occurrence 调 `24E3410`。这不是“每月1日扣5%”；重复 pointer 也不能预先乘成固定多次扣兵。

[next-date 来源](army-next-admitted-supply-tick-input-12004.md)及[当前 builder](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_source_derived_next_daily_supply_frame.hpp#L56)给出下一日的 low32 date `+24` 和 `trunc0(signed32(nextRaw-43800000)/24)` 的 native D；[all30 reader](../../ck3_autonomous_player/native_bridge/include/xar_bridge/ck3_12004_future_daily_supply_schedule.hpp#L25)保留当次30个桶的原匹配位置。下一机会只能作为该冻结桶的条件计划，逐日必须读回实际 date/D/桶和 callback。

| 观察条件 | 至少需要看到什么；时间预算如何定 |
| --- | --- |
| T0 已是低库存，下一真实选桶含该 Army 且 admission 允许 | 最早 **1个 exact+24 日窗**就可能得到正例；必须确实保留 callback 和 writer。1天未见不能作阴性结论。 |
| T0 是正低库存，当前负 rate 足以一次归零 | 以一次真实 callback 为第一目标；若实际更新后归零并出现供给 physical debit，可同窗完成低→0→扣兵链。至少一个前端点、一个后端点和该次 writer，不能只拍后端0。 |
| 冻结桶中只有某一 phase 匹配，实际正常 D 每天递增1且桶/身份稳定 | 从下一个自然日开始 **30个逐日窗**覆盖一轮 phase。30是调度机会的完整普查预算，不是成功更新、饥饿或正例的保证；达到更早的真实正例即可停止。 |
| T0 库存较高，负 rate 暂固定 | 只可算成功更新数的条件量，不直接换成日期。令 `a=-rateRaw>0`：到 raw<1000000 为 `max(0,floor((S0-1000000)/a)+1)` 次，到0为 `ceil(S0/a)` 次；每次后重读 rate/capacity/context。即使按30天一轮估算，也没有实际桶稳定/admission保证。 |
| grace未过、combat/gathering/retreat门拒绝、rate≥0、桶变化、无实际 parent/physical 捕获 | **没有一个有限观察天数能保证 R05 正例**。及时停止该 lane，保留具名阻断原因；不能用盲等30/60天替代找合适自然候选。 |

当前最省时的选择是找已自然处于低库存、下一次真实负补给更新可归零的军队，而不是从R182的300补给开始耗尽。先用普通 profile 对实际可用军队做一次小范围当前状态筛选，再只对选中1支军队读取 full history；不导出全世界/全战役全历史。若当前 actor/军队没有自然候选，保存该事实并选择已有合法正常低库存 checkpoint 或后续自然战局；禁止 console/内存改 stock、调用 updater制造样本、复制别军库存或将旧场数据拼成同场跨阈值。

## Root 可执行的最小 lane

以下是下一场已授权实机内的顺序，本文没有执行它。

1. **开场检查**：按[统一存储策略](../storage-retention-policy.md)核身份、路径/容量、deadline与收尾余量；核当次 Steam 离线、实际 EXE/build、actor/episode/PID/generation和新鲜 paused snapshot。实际运行构建须有供给 callback/writer/parent capture；没有 leaf 时保留缺失并正常闭场，不能靠 query打开编译期开关。录像计划必须短于剩余期限并预留 finish/save/退出时间。
2. **挑1支自然候选**：同一正常战役中确认完整 Army/CArmy FullID、roster顺序和physical slot身份；优先静止、无战斗/集结/撤退/渡海抑制、无需抵达新县，且非负 stock<10、真实负 rate、有效供给分量>0、合格兵数足够的军队。若需先正常移动到耗补给处，抵达和稳定后另立T0；移动窗不计作单一饥饿窗。围城可另分 supply/siege primitive，但优先无围城/劫掠的清晰镜头。
3. **保存T0与独立 fences**：读 fresh revision，调用现有 `ck3_query_army_strengths(army_ids=[<真实FullID>], expected_revision=<新revision>, profile="observed_history_full_v1")`。保全原始返回与SHA，记录各 journal 自己的 latest sequence，不比较两个日志 sequence 的大小。保存 loaded表、clock/grace、all30桶、当前/conditional风险、roster、physical current/max、补员/战斗/移动等观测。`ordinary_core_v1` 不承担这一步的历史证据职责。
4. **小段推进并逐日取证**：录制前先直接审阅当次客户区原始采样帧；以正常 exact-day 通道推进 **1天**并实际读回 paused/date+24/overshoot0，随后对同一军队再取 full history。每个请求用新ID，结果未知不重投动作。立即保全新 callback/writer/refill/arrival等相关事件；核实际D/phase和 before/after stock。不要等30天末尾才读512条环。
5. **离线逐窗消费**：用 `join_actual_supply_parent_writer_observations_v1` 和真实 build/fences关联；检查 token/thread/depth/FullID/日期、callback完整、capture flags、physical coverage/aliases/合计和各环连续性。再用 `classify_actual_loss_component_12004`将供给 preferred、供给 residual、siege/raid、county分别列账。原始row保持原样。分析可与下一日自然推进并行，Root仍独占实机/SDK。
6. **及时收束**：任一可信正例出现即暂停保存正常 checkpoint、完成录像、正常退出和释放现场。达到本轮窗口/容量/墙钟上限而没有样本则同样闭场，记录“未取得正例”及具体阻断项；不能延长到错过配额期限。缺失token、同日重组/身份变化、日志gap/覆盖、物理capture不完整时停止该证据链，重新建立新T0，不回写旧RED。

陌生事件按项目指令先留原生事件/实例/实际选项，再选择首显示项并验后验；如其改变Army/补给/兵员或停顿观察窗，则保存并将该窗标混合。事件离线补齐与下一轮并行，不要求逐条重启游戏。

## 何时算成功，何时只能说“看到了0”

**最小严格供给扣兵正例**：同场同身份的真实自然 callback，与至少一个 source-confirmed supply writer 通过 copied invocation key严格关联；writer当场 `0<=stockRaw<1000000`，当次loaded表和有效分量支持低库存来源，complete unique physical debit>0，各环连续且capture完整。只授该具体供给调用的扣兵，不宣称整个Army净少的人都由它造成。

**本轮完整零库存链**还要保留先前正低库存端点、同次真实 callback 的 before/after归零、writer当场 `stock_at_writer_entry_raw==0` 和对应physical debit>0。一个从库存0开始的正例能证明“零库存仍实际供给扣兵”，不能伪装拍到“正库存耗尽”的过程。只取得 stock0、低状态/getter、预算、request、callback无writer或Army净人数下降时，分别授其实际观察层，R05仍pending。

preferred-only正例已足以证明某个真实供给扣兵 primitive；完整军队饥饿总额还需覆盖所有供给 preferred/residual及其他同窗变化，不能因 consumer目前小计方便而忽略 residual。若另一个角色/场景先取得正例，可复用该机制证据；不能替代视频中指定角色、William故事或ABC基线所需的身份/情境证据。

本页新增SDK/桌面/EXE读取、native build、游戏日、原片与R05正例均为 **0**。唯一新文件为小型portable执行卡，按统一策略复核，不设置永久保护；完成实机后应追加新场证据引用，保留本次离线计划的时间边界。

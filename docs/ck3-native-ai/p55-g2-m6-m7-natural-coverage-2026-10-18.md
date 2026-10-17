# P55：M6/M7 自然结果的覆盖与下一局采集

2026-10-18。`machine_id: xenoamess-full-tower-eb9d2c1186`；离线整理于
2026-10-17T21:21Z 开始，源码观察基线 `cf75d38a5055e2dc0f1fb40a7159c041dd61e525`。
[便携证据](evidence/p55-g2-m6-m7-natural-coverage-2026-10-18.json)保存精确来源 SHA、
字段合同、外置工具来源和复核边界。**G2 保持6/8，M6/M7均为 in_progress。**
本次只沉淀文档；没有新运行、动作、自然终局或分数。

## M6：Start、阶段收益和有用自然终局分别计量

复用[原生终态与普通后续消费合同](sway-beneficial-terminal-followup-12004.md)及
[既有普通 Start 接线](g2-remaining-natural-outcomes-2026-10-18.md)。M6 的 d0a 外置包
已准备 closed-AUTO 审计，source-only/synthetic 资格不能算本机自然游玩通过。
SDK02/host02 的六 consumer 源审 `dacb044c…5d9b` 和七个 private flags
证明源接线/权限准备，不能证明发生过 Start、同实例读取、终局或新增收益。

当前普通调度使用原生顺序的 direct landed vassal，检查后轮转。
意见≤50是新 Start 的我方门槛，仍受当前 empty-slot、完整 CanSend/legal 和原动作身份约束；
不是自然终局门槛，也没有证明该目标是最高派系价值目标。收益先限定为真实选中封臣关系的具名改善；
离开派系、增加税收或救下战争等战略结果须另有实际来源。

可提交复核的自然有用终局包必须串起：

1. 正常 AUTO 的真实 `.4` Start 回执，以及独立唯一匹配的 action/actor/target/full SchemeID/generation；pending 不重发。
2. 原实例仍 active 时的较早具名 baseline；随后同身份的 `scheme_sway_opinion` 新增正增量。
3. 后来的独立 retained terminal，且没有该实例的 typed Stop；`terminated_unattributed` 保留原因未知。
4. 实际后续普通 AUTO 对原 material 和 terminal 的消费，包含归档 `previous_interventions`。

Start ACK、总好感、首次看到就存在的正修正、同值刷新、phase success、行消失或存储复用都不能补齐这条链。
阶段收益可能与继续 active 的原实例并存。后来的同值 material 刷新可能清除最新
`incremental_named_gain_observed`，所以应保留较早实际 gain 的独立来源，按原 action/fullID/generation
去重，不能只看最终 ledger。审计只输出 `evidence_packet_ready`，最终业务结论仍由原证据复核。

**当前 ordinary war hold 可能使整个 Sway 生命周期长期没有调度机会。**
[scheduler](../../ck3_autonomous_player/src/xar_autoplayer/ordinary_sway_schedule_v1.py)和
[Service adapter](../../ck3_autonomous_player/src/xar_autoplayer/bridge/ordinary_sway_service_v1.py)
均要求 baseline `selected_step == life-advance`；本次源审中 ordinary lifecycle helper 的调用点
是 adapter 的 `observe_applied` 分支。战争 sentinel/驻留 hold、route-contact advance 并非这个 step。
因此即使已 Start，也可能迟迟没有首次 baseline 或月度 lifecycle read。
这是源码所示的调度饥饿风险，本包没有量出当前实机的饥饿时长，也没有修好该调度。

下一局每个已结束 batch 分别统计：普通 life-advance 机会数、war/route 时钟数、optional job、
Root frontier 缺失、合法 no-op/cooldown、原动作 pending、严格 Start、具名增量、terminal 和 following 消费。
零机会、未到期、缺来源与 native failure 分开；不要从零 Start 推断 flags 不存在。
不抢战争优先级或手动 Start/Stop 制造资格窗口。原 host02 owner 未放行三个私有只读 route，
首选仍是普通 AUTO 内部 Service 生产的回执；必要 future owner COW 的精确 route/参数保存在便携 JSON，
不绕过 owner，也不把路由扩展设为继续普通游玩的门槛。

## M7：一次真实继承与 broad coverage 的边界

[权威 requirements](../autonomous-agent-progress/g2-requirements-v1.json)将 M3 定义为自然死亡前预测、
核对分配并由真实继承人继续；M7要求多个 rulers/seeds/governments，以及 checkpoint/继承后的同一高层意图。
旧索引 natural0 已被后来的真实回执补充，不能继续当当前事实；定义和6/8分母不变。

本机[当前 clean campaign 实际小证据](evidence/p50r1-natural-successor-actual-2026-10-18.json)
记录19:27Z的31254→40695。原 AUTO361 没有重放；364零MCP重消费，365结算原动作，
逻辑 Continue368、原生 modal Close372 的独立 clear、SAVE374、SEM375 和普通 FULL376 分别有来源。
campaign/origin31254保留，current40695、progress1，后继普通 plan 已消费原 goal，且有真实将领任命。
婚姻 pending、行军 submitted 不扩大为婚配、到达或战胜。

2230/2231/2262三 title 全部匹配同一继承人，other-heir/without-heir/additional 均为空。
持久 expectation 已旧3121游戏日；较新逐 title 补证仍距死亡322日，紧前 primary-heir 补证距死亡7日，
不能拼成死亡前 fresh 全 title。原 AUTO361 推进7日，Close372 的 life-advance 又推进7日，分列为两个实际推进。
SAVE374 的范围是 `WRITE_REPLACE_RETURNED_NOT_FSYNC`；此证据没有证明后继精确配对的真实 Game 冷恢复。
SDK-only 轮换不等同新 Game 载入存档。

| 覆盖项 | 当前及历史证据的精确边界 |
| --- | --- |
| 同一继承人 | 本场真实一次，深度1；不等于多代长期意图完成。 |
| 分封 | 本次没有；项目另有31254→40526的历史 goal，保留 other-heir2262及后续普通 plan。两份历史小记录无机器身份，记 `machine_id: unknown`，不追认为本场或本机新成绩。 |
| 无首继承人/分配不符 | 源码已有 `no_primary_heir`、`unexpected_successor`、`title_distribution_mismatch`；本次未触发。无活新 played actor 的 Game Over 不满足 successor reconciliation，不能硬做成功 handoff。 |
| other-heir/additional | 合法分封不自动算败战失地；other-heir title 不在继任人名下，不证明其实际新 holder。additional title 是信息项。 |
| 独立/改宗主 | 可记录真实 realm 变化；不属于 M7 新增必测死亡变体。主动授独立 AUTO193不能计自然继承。 |
| 政府/种子 | 真正广度缺口。旧 .3 Robert/Murchad均为 core_landed；Clan/Tribal旧 bootstrap失败不授玩法成绩。 |

政府识别表的 feudal/clan 是 `core_landed`，tribal 是 `core_tribal`；其余有 unsupported 或实现待补状态。
18个识别键不代表18个可玩政府或强制全通矩阵。必须同时保留实际 government_key/family、同帧 actor/build
及正式政策消费/结果；metadata `core_supported`/ready 不能代替业务资格。
当前继承小证据没有 government DTO，本包不从姓名或旧 goal 推断政府。

## 下一1066局：正常流程产生证据，批后离线归一化

下一局按用户顺序在当前影片完成后启动1066罗贝尔。重复封建罗贝尔可以提供新初始 lineage 的自然连续性，
不会自动增加 government family。独立 seed 以真实初始 checkpoint/RNG 或 initial-state 来源为依据；
新标题、SDK、PID或同存档 reload不能自动算新 seed。不为补广度改动用户指定开局。

每批关闭后将原 owner 已完成清单的显式 source path/bytes/SHA 交给离线消费者，与下一批推进并行。
只采新增/变化的 goal、episode、expectation 来源帧与年龄、原动作状态和后验，不复制完整 history。
自然转换按 machine+campaign+old/new episode 去重，不能按回执文件数累计次数。
复用既有 owner 的一次结算、逐 title reconciliation、必要 modal Close、独立 clear、正常 successor SAVE
和后来普通 goal 消费；缺字段记未知，不新增 stop-gate、强制死亡或手选继承人。

以后正常维护确有 Game 冷启动时，再用既有
[goal extractor](../../tools/extract_g2_goal_continuity.py)和
[owner cold extractor](../../tools/extract_g2_owner_cold_evidence.py)，保留旧进程实际退出、
精确 checkpoint 配对、真实新 PID+birth、同 episode/goal、零动作重放及后来普通 plan。
现有新 M7 normalizer 仅做显式小 JSON pin/pointer 投影；实际24706B证据已离线运行一次，得到继承与后续 goal两条观察，
不新增继承或 M7分数。外置 audit/normalizer 的 exact source ref 在 JSON 内，当前只合入文档。

便携 JSON 内嵌 M6/M7 的 manifest 形状、字段列表和未知状态规则；来源单件上限256KiB。
过大 AUTO 若没有现成小投影，就保留来源 pin 与 `oversized_source/not_observed`，不读巨大正文、活跃 Driver/SAVE或媒体。
缺自然终态时报告已有阶段证据与 terminal_not_observed；冷恢复、独立种子或政府未闭也各自保持未完成。
本次仅离线证据整理，没有新 Paradox 语义或CK3验收，`open_kaishek: not-applicable`。

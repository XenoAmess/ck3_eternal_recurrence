# 战役时钟吞吐：等价等待与真实边界

当前阶段目标为**每实际游戏日不超过1秒**，后继目标0.5秒；1066.9.15至1096.9.15共10950日，分别对应182分30秒、91分15秒。分母必须取实际日期差，零日查询、规划与持久化全部计入端到端墙钟，不用调用ACK或请求天数冲抵。

| 路径 | 当前来源与可复用证据 | 结论和可施工边界 |
| --- | --- | --- |
| 普通generic clock | `_execute_life_advance`先依局面选原horizon/速度，战争结果窗口可把原horizon夹到8日；新campaign transport单次Arm至月界/终点 | 已是多日一批，没有每游戏日新增MCP。不能为吞吐删掉战争/事件输入或放宽原horizon。 |
| exact-day风险观察 | [既有实测](exact-clock-observation-timing-v1.md)：相同机器P27的22日平均5.2906秒/日，21日用speed1；原版speed1本身2秒/日 | 是2026-10-16历史，不代表当前dc4b采用或性能。其原speed/风险资格继续有效，不扩route/contact speed5。 |
| battle、route、objective | 现有native sentinel在daily callback判断watch、scope与date并暂停；普通wrapper等待public change | 月界与终点已沿同一次Arm夹断。scope、watch、A/B和native源未变；不能把高风险逐日观察擅自变成长窗。 |
| 普通Sway | `ordinary_sway_schedule_v1`依原已观察frontier/actor/lifecycle限频；optional query后内部fresh replan再dispatch | 没有固定sleep。查询可以改变source revision，不能直接复用旧plan。空frontier的本地no-operation仍重规划，须有同帧plan来源证明后才能单独优化，当前未改。 |
| Driver等待 | `_wait_for_life_advance_snapshot`调用condition/public-change等待；NamedPipe server空闲poll为0.01秒 | 已有profile未把长等待归因到固定poll；不能凭理论删掉真实状态等待或称其为主瓶颈。 |
| 零日候选/查询 | P12小摘要 `tools/g2_saved_campaign/fixtures/p12_actual_timing_baseline.json`：63日571.60秒，其中life推进93.65秒，declarable139.30秒、派系63.53秒，另有多笔entry forecasts | 该历史摘要无machine_id，必须标`machine_id: unknown`。只说明该来源样本非clock独占；不能作为当前硬件或当前算法吞吐。候选/序列化由独立owner施工。 |

本包已经实现一个等价削减：`campaign_deadline_transport_v1`收到绑定的paused starting frame，如果实际`speed`已经等于原策略选择，就不再发同值`set-speed-N`，也不为该setter再次取同帧semantic snapshot。它保留原生Arm独立的speed、generation、date、mode、scope和pause校验。回执单列`speed_configuration.status=already_observed`及原snapshot/native revision/date，不把它装成一次accepted命令；真实actions只保留实际发出的Arm、resume、Status。起始速度不同仍走原setter与读回，所有月界、事件、终点和失败清理保持。

[软件比较回执](evidence/campaign-clock-same-speed-performance-2026-10-19.json)绑定`machine_id: xenoamess-full-tower-eb9d2c1186`，登记时间`2026-10-19T03:21:28.269860Z`。固定baseline `f5d26108` 与candidate在**相同输入**上运行实际Driver→primitive executor→Protocol fake wire：原4个native命令缩为3个，5个游戏日、目标raw、原speed5、scope与完整关键返回语义相同。7项定向测试通过，包含native Arm却报告speed4时禁止resume的负例；不同起始速度仍提交setter，旧exact-day helper未修改。

这不是Game/Native实测，也不证明已经达到1秒/日。当前冻结运行源未热改。下一批实际冻结采用后，由runtime owner从既有compact response与timing记录端到端秒/实际日、零日轮占比、各步骤p50/p95/总墙钟、回包字节与Driver增长；不新增只为benchmark的现场RPC。实际Arm/Status及月样本到达才授该批游戏日信用，实际墙钟变化才授性能收益。

后继实际AUTO74暴露了优先级更高的30秒事件盲等，[独立小回执](evidence/campaign-clock-native-event-wait-2026-10-19.json)绑定同一机器和已闭合原件。该AUTO耗30.314162秒，只从raw53144520推进至53144568（2日）；普通原生事件instance1已存在，sentinel仍armed/generation2/ticks2/trigger_flags0，最终Python才发pause-map并合法cancel。普通8日AUTO50只耗3.000531秒，不能把两条不同局面当作严格A/B；完整FULL11的61.535486秒/10日仍计为6.15355秒/日。

真实源码缺陷在新date-only等待谓词：它只接纳paused或`_life_advance_new_modal_hint`，而后者**明确在active_event/pending interaction存在时返回None**。因此普通native事件已发布但paused尚false时仍会等到timeout。修复改用原generic的`_life_advance_progressed`并传实际cap horizon，完整保留普通事件、交互、terminal、war/threat、modal及日期边界；不增加查询、不改public revision、不重resume，也不把2日写成请求的8日。停止后仍独立读Status，对原armed generation合法cancel，事件交后续原策略处理。

同输入实际Driver→Protocol软件复现将timeout缩为0.15秒：旧0.162654秒、新0.001488秒，**6条原生命令顺序完全相同**，2日/event/paused/target/progress/cancel关键语义相同，均一次resume，事件未被选择。9项定向测试通过，含“只有不足horizon的日期进展、没有合法事件/其他原边界时不得冒充早停”的负例。登记时间`2026-10-19T03:39:25.957740Z`；这证明去掉了可复现的无效等待，实际新tuple的收益仍由下一冻结后的原始compact/timing验证，未追认当前freeze已经采用。raw-only诊断hint不改变public revision的另一类等待未在本包扩大施工，不将理论分支作为当前新局继续的门禁。

后继真实AUTO147暴露了上段修复过宽的日期分支：目标日先发布，原生每日回调的暂停状态稍后发布，Python在两次发布之间再次提交`pause-map`，收到`CK3 map state is unavailable`拒绝。原生Arm/Status仍独立证明raw53145048→53145240、8日、generation6、date_deadline、零过冲、实际原生暂停；拒绝ACK保留，不能把它改写成成功。[源审及同输入回执](evidence/campaign-clock-target-pause-publication-2026-10-19.json)绑定实际采用的src03/063531c4，未把当前工作树当成现场源码。

最窄后继修复只让**目标日之前**的原有事件等合法边界触发Python暂停；到达目标日后继续等待同一次Arm所属原生回调发布暂停。相同实际Driver→Protocol软件输入重现旧4命令中的暂停拒绝，新3命令为Arm、resume、Status，完整原生clock证明及关键结果相同、仅一次resume，未增加RPC。10项定向测试通过；AUTO74提前事件、无合法边界不冒充早停、错speed拒绝和月界/终点用例保留。`machine_id: xenoamess-full-tower-eb9d2c1186`，登记时间`2026-10-19T04:22:52.179124Z`。这是后继源码资格，未热改冻结SDK、未重放147、未声称已取得对应实机修复结果或达到1秒/日。

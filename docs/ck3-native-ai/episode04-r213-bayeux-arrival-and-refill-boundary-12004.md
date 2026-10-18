# R213：普通战役 typed Move 到达 Bayeux 与补员观测边界

`machine_id: desktop-3fevhd2-1c74096080`；实际场次 source `3661e495bc45490238992d3f2850e75558566922`，public run `desktop-3fevhd2-1c74096080--vanilla--R0208`；本次知识补录时间 `2026-10-18T17:55:54.730191+00:00`。机器安装、原生资格、路径与权限不能由此外推到另一机器。

普通 `native_campaign` 不需要伪造 one-life episode。R212 的 typed Move 在空 episode 守卫被提交前拒绝；另一 generic literal 又被 `action_steps` 准入拒绝，两者均没有原生 Move。共享修复 `3661e495` 保留原始空值或既有 episode，并绑定 PID、连接代数、本机玩家、当前在世 actor、暂停日期和自有非战斗军队。one-life 仍要求非空 episode；原生目的地合法性、能力与路线后验继续执行。见[历史拒绝与修复来源](episode04-r212-native-campaign-typed-move-refusal-12004.md)。

R213 真正经公共 typed `ck3_move_army` 提交一次；原生路线与独立日步后验最终确认 **43 天后到达 province 2170（Bayeux）**，日期 `53148408`。可复用的调用方式是先取本次 fresh snapshot 与合法 preview，再提交一次 typed 请求，消费 route/目标后验；不能把未广告的 generic literal 当成备用入口，也不能重放结果未知的动作。

[场次消费者](evidence/episode04-r213-bayeux-arrival-12004/monitor-terminal.actual.json)与[县行军终态](evidence/episode04-r213-bayeux-arrival-12004/county.actual.json)记录到达、OFFclear 与 Save。到达是这次行军的实测结果，不等于县进入条件 P/OR 的正例，也不自动关闭 R04 研究。

后继 R06 a01 保留真实 RED；a02 另推进恰好一天，终态为 `ONE_EXACT_DAY_NO_RETAINED_CORE_UNKNOWN`。它保留 OFFclear/Save，但没有 retained core 因果载体，不能把“未观测 ADD”写成“实际没有补员”，不能拼接独立 journal 授予共同 token。详见[一天终态](evidence/episode04-r213-bayeux-arrival-12004/r06a02.actual.json)及下面的精确小源索引。

正常闭场分列：[normal-close](evidence/episode04-r213-bayeux-arrival-12004/normal_close.actual.json)、[retained OS0](evidence/episode04-r213-bayeux-arrival-12004/retained_exit.actual.json)、[原 host Popen0](evidence/episode04-r213-bayeux-arrival-12004/host_exit.actual.json)，最后 Root 原 allocator wait0、keeper STOP 后 CAS **6714** 释放。a06 是 CAS 前原件，其未评估标记保留；[Root 后续释放补记](evidence/episode04-r213-bayeux-arrival-12004/root-release-adoption.actual.json)独立追加。R212 的 host1 来自失败 history，不能改写为0，见[原因原件](evidence/episode04-r212-typed-move-refusal-12004/host-exit-reason.actual.json)。

视频只给实际覆盖范围：R213 第一段约1499秒在到达之前结束；后段约106秒没有推进新日，不包含 R06 a02 的后继日。技术解码、样帧与唯一 Finish 不能替代全片1×、continuous clean 或正式镜头签核；到达证据来自 typed/独立查询，不能倒填片内 arrival。R212 两段45.433秒及73.3秒只显示静态 ArmyWindow，没有行军成绩。

R211 新中文口播/TTS/27秒渲染是独立编辑输入与实际媒体引用，继续区分原生供给扣337、另围城/劫掠67、画面净404，受控预置库存0不称自然耗尽。见[可移植 TTS 源输入](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r211-r05-tts-candidate-a01/README.md)及[精确源索引](evidence/episode04-r213-bayeux-arrival-12004/source-index.json)。原69 cue/旧电影不改。

午夜按 `2026-10-18T16:00:00Z`（CST10月19日00:00）划线：R211 27秒交付23:59:56属于旧周；R213到达、媒体、回收与R06一日属于新周开场。旧日报/周报里的后续事实只作晚补记录，不计入旧周完成。

研究 **10/14**、业务 **7/11**、正式动态 **0/11**、ABC **0/3** 均不因本次行军或技术片自动增加。下一场需新 source/runtime/capacity/机器绑定，再消费完整共享查询和 retained core；来源机器路径仅作原始出处，跨机从仓库内小原件与 Git 来源重建绑定。

## 精确后继边界与下次入口

`machine_id: desktop-3fevhd2-1c74096080`；2026-10-18T17:57:43.295294+00:00。[一天原件](evidence/episode04-r213-bayeux-arrival-12004/R213-REFILL-ONE-DAY.actual-a01.json)选Regi2602/slot1，正q1、positiontrue、stored fraction4020/1e5，但实际prepare/ADD未观测；[物理投影](evidence/episode04-r213-bayeux-arrival-12004/R213-PHYSICAL-NET.actual-a01.json)37个唯一槽位6674→6674、净0、68→68，不把净0当gross ADD0。实际core child为null，保持unknown而非虚构记录。下次须在exactday后OFF前保存真实sampling状态，再由共同token/retained payload消费资格；[源码一次观测卡](episode04-friendly-refill-one-shot-12004.md)不替代本场缺失载体。

[移动边界分析](evidence/episode04-r213-bayeux-arrival-12004/MOVEMENT-PROGRESS.actual-a01.json)、[首海边界](evidence/episode04-r213-bayeux-arrival-12004/MOVEMENT-FIRST-SEA-EDGE.actual-a02.json)、[现金只读](episode04-r213-current-cash-readonly-12004.md)、[R211实际27秒渲染](../../promo/ck3_native_war_ai/episode-04-march-logistics/review02/r211-r05-render-27s-a01/README.md)均有仓库内小原件。第二段媒体只有budget-constrained probe/两JPEG小QA，不能冒称完整canonical三PNG审阅或formal签核。

最后正常Save原DTO的episode/lifecycle字段为null；[下一场normal-S0 proposal](evidence/episode04-r213-bayeux-arrival-12004/normal-S0-promotion-not-activated.candidate.json)只是候选，旧public checkpoint_source的one-life硬约束尚未适配，不能填假EP来通过准备。公共入口应薄适配真实ordinary normal DTO，不能另起并行管线。

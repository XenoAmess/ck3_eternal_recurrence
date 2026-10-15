# 1.20.0.4：R0175 锁定首段 Halt 实际后果

R12 已有同一受管会话的实际后果：普通 Move 形成 `[1036,8653,1034,1033]`，进度原始值96666严格大于实际加载阈值50000；同日 Halt 后路线仅剩 `[1036]`，首段进度保留；两天后实际到达原首段省份1036，次日仍为空路线。目标字段当时不可观察，保持 unknown，没有据此补造“目标已清空”。

来源机器为 `desktop-3fevhd2-1c74096080`，观察会话 `desktop-3fevhd2-1c74096080--vanilla--R0175`，PID16512/create134365577928096099、connection generation1、actor31254、Army full ID18、episode `native-31254-13a1253fe701`。源码为 `dcda9fde1afa1effb75d46fe99bba4bcd9aeabcb`；闭场观察时间2026-10-15T18:07:27.175576+00:00，来源是便携原件中的 `CLOSED.actual-a01.json` 和原 R12 final report。观察资格只属于该机器与当次会话。

[便携验收](acceptance/2026-10-16-episode04-r12-r0175/README.md) 保留六个关键完整查询、417对原请求/响应及全部31代实际时钟、暂停 snapshot、Arm/Resume/status、失败与只读恢复。总自然时间32天；第30代用了两天并因军队位置/路线变化提前停止，不能改写成31次严格单日采样。其余33个完整查询未归档；媒体、save和DLL原件不在便携包内。原媒体 decode 与六张样本审阅结果仅随 JSON 报告保留，连续 clean 与最终 human approval 均仍为 false。

## 两个实际 publication race 的通用处理

一次已触发停止后，readonly status 可发布较新的公开 revision。后续 strength 查询应先取新的 paused snapshot 并绑定其 revision，同时核对原停止日期、Army所有者/控制、Province、完整路线及非战斗/非撤退状态。发生明确 readonly revision admission refusal 时，保留原失败、原 Arm/Resume 和暂停记录；只补只读状态/快照查询，不能重发推进动作。结果未知的动作仍保持 onceclaim。

另一次 Resume 后，最早轮询仍可能读到开始日期的 paused publication。必须同时读到日期确实前进和 paused，才进入完成检查；单独 paused 不足以证明停止。只读 sentinel status 使用 `expected_revision=None`；这不解除随后强度查询的 fresh revision 绑定，也不授权动作使用未知 revision。

[watched_stop.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/watched_stop.py) 提供这些纯检查与 status 参数。便携 [replay.py](../../promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/replay.py) 已消费真实恢复输入，调用现有 `verify.frame/r12` 与源 SHA 固定的四个生产 clock validator 定义/原因表；无 Windows Driver bootstrap、SDK 或游戏动作。现有 runtime caller 没有在本交付中改线。

离线结果见 [REPLAY.actual-a01.json](acceptance/2026-10-16-episode04-r12-r0175/REPLAY.actual-a01.json)：全部981个原件成员字节校验通过，六个完整关键帧与31代时钟重放通过；四个实际输入变体分别拒绝精确 pin 变化、snapshot/query revision错配、stop generation变化及日期未前进的暂停帧。该重放不产生新的实机事实。

核心卡为4/14（28.6%），business为2/11（18.2%），不能合并分母或外推 R13、拆合军、补员、零供给扣兵和军事维护费归因。a07的11个源码包与本场dcda/a06事实保持独立。存储仍计既有active32MiB中的metadata17MiB，本lane上限12MiB；复核/保护截止2026-10-16T07:45:01.597Z，不延长。

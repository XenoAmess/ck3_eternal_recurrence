# CASE-C：既有战争路线续行的首次接战观察结果

**结果：这次独立窗口没有观测到实际接战。** R0005 的同一 War4 从 `date_raw53144784` 前进到 `53145504`，共30游戏日；第30日出现待处理人物互动，观察器按预定停止条件暂停。保存的68次正式快照中，同战双方没有任何公开军队的 `in_combat=true`；因此没有触发正式 actual-contact、battle-control、battle-transition 查询，也没有绑定 CombatID。这个有限窗口不能证明短暂接战从未发生，更不能推出原生 AI 拒绝交战。

本结果对应独立的[结果合同](research-plans/war-film-case-c-result-20260923-r1/plan.json)、[结果图](research-plans/war-film-case-c-result-20260923-r1/graph.md)和[逐项来源摘要](research-plans/war-film-case-c-result-20260923-r1/readback.json)。执行依据仍是先前检查过的 [CASE-C r2 准备计划](research-plans/war-film-case-c-20260923-r2/plan.json)；其待填字段和未知边保持历史原样。结果文件只读既有请求与响应，未执行新实机命令。

| 绑定 | 实际读数 |
| --- | --- |
| 游戏与会话 | CK3 1.19.0.6；EXE SHA-256 `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`；`desktop-3fevhd2-1c74096080--vanilla--R0005` |
| 进程与身份 | PID32356、connection generation1、episode `native-29829-fcaa3906d404`、玩家 CharacterID29829 |
| 战争 | WarID4，玩家为攻击方，主要对手31549；这是 CASE-W 中玩家宣战后的战争，不是 AI 自然宣战样本 |
| 起止 | `date_raw53144784 → 53145504`，30游戏日；观察器墙钟37.105秒；原始日期观测31个 |
| 样本 | 68个正式 snapshot 响应，31个不同日期；全数核对 actor29829、War4、对手31549、无本战公开军队 `in_combat` 标志 |
| 停止帧 | `snapshot_id=native:79`、public revision80、`paused=true`、War4仍 active、`player_relative_war_score=0` |
| 停止触发 | `pending_character_interaction.instance_id=16777352`，`sender_character_id=32522`，`auto_accept_notification=false`；`active_event=null` |

操作记录 `c004/c006/c071` 只有 `set-speed-2`、`resume-map`、`pause-map` 三个已接受步骤。沿用 CASE-W 已经提交的玩家路线，没有在本窗口新发宣战、招兵、移动、分合军、撤退或和平命令，也没有替玩家处理待互动。`c070` 在日期53145504读到待互动、尚未暂停；`c071` 提交暂停，`c072` 在同一日期确认 `paused=true`，`c073` 回读War4仍active。以上是在同一正式会话中的先后状态，不把 command ACK 当作状态已改变的唯一证据。

起点 day19 存档为 `case-c-r1/pre-contact.ck3`，49,683,960 bytes，SHA-256 `74d43b27bb9e13ed6431e3cbb7f38982b3af6622dd6a445e17fa1dc668a9d789`。结果摘要为每个原始快照响应保存路径、字节数、SHA-256、日期、revision和当天 `in_combat` 读数，也绑定实际录像、服务延长及原始失败收据。原件根目录是 `D:/workspace/ck3_war_film_research_20260923/`。抽样间隔不是引擎的同步断点；这份结果只能说**已取到的样本没有接战信号**。

## 录像与来源状态

`case-c-r1-recording/gameplay.mkv` 已完整写出：1,928,022,579 bytes，SHA-256 `5cd5daf6ab08e6ddfd07d5a7d5105b70d4d4e0e0953d7c05079dfccf2249bb76`。录制与probe退出码均为0，probe报告H.264、2560×1440、471.902秒；现场监控记录前台始终是CK3。录像长于37.105秒的日期推进，因为观察器暂停后录制继续等待到独立停止标记。原回执明确 `clean_span_review=pending`、`native_ai_causality_proven=false`；不能把整段录像称为连续战斗画面或已审合格镜头，也不能把快照自动映射到某一视频帧。

R0005 的**原始 capture-session RED 独立保留**：`capture-live-live-r5/hot-failure-state.json` 在21:50:53Z记录 checkpoint actor/date 与来源收据不符，当时 `played_character=null`。之后的已加载地图 HUD 和 CASE-W/CASE-C 正式读回说明后续时刻可继续做有边界的研究，但不追改原失败为 GREEN。CASE-W 里 `w006` 的存档 inspector typed unavailable 也是另一项未通过的工具读回；实际已保存的文件及其hash另有独立收据，不借本 CASE-C 声称该 inspector 通过。

CASE-C 开始前，同一服务 owner 于22:10:27Z延长恢复服务预算1800秒，收据 `capture-live-live-r5/service-extension-r1.json` 记录旧 monotonic 截止 `1220530.7981535`、新截止 `1222330.7981535`，累计恢复预算3600秒，延长动作提交原生游戏命令数0。原准备文档里的22:20:54Z是**延长前**的预计到期时间；从收据推算新预计到期约22:50:54Z，不能把原时刻说成实际服务退出。CASE-C 在延长后的服务时限内遇待互动停止，且只用了计划120日/600秒上限的一部分。结果不宣称CK3进程在停止标记时退出。

本窗口实际未进入可选的单战自然结算子窗口。要展示一次完整的接战、战斗控制或终局，需要另立有界案例，取得实际 CombatID、双方正式 unit/side 与同一 C 的终局读回；仅有路线、接近时间或这份零接战窗口都不够。待互动内容及其与战争的关系也未在本次结果中求证。

结果合同的离线结构/文件完整性检查为 `plan-consistent`：5条已枚举边中3条标为本次正式读回支持、2条保持未知；1项有界结果案例 observed、2项接战/终局案例 not-applicable。该检查不复核游戏语义，不是人工1×观片或影片签核；记录在[check.json](research-plans/war-film-case-c-result-20260923-r1/check.json)。

## 媒体封装复核

独立媒体封装在 `D:/workspace/ck3_war_film_research_20260923/case-c-bundle-r2/` 完成，`report.json` 为 `260660` bytes、SHA-256 `f8bbe7eadab0548833c30442c5d46299f1657b03ffd27a379b6cc81363468263`。报告状态为 `adapter-validated-passive-wartime-evidence`；它对原始录像、时间线、证据索引、73次正式调用、68个快照、checkpoint 和停止条件做了文件及来源核验。录像前有2次只读准备调用，录像内有71次调用；两阶段的 UTC 与 monotonic 时钟均按各自边界校验。原始录像的哈希仍为 `5cd5daf6ab08e6ddfd07d5a7d5105b70d4d4e0e0953d7c05079dfccf2249bb76`。

封装报告明确保留 `actual_combat_id_bound=false`、`native_battle_result_proven=false`、`frame_synchronous_query_proven=false`、`native_ai_causality_verified=false`、`human_1x_review_performed=false` 和 `signoff_granted=false`。按 PTS 抽取并目视查看的若干画面确实是 CK3 地图/HUD，但不能把快照时间强行配到特定帧，也不能把完整录像时长说成不间断行军。第一次封装尝试 `case-c-bundle-r1/` 因把录像前准备调用误判为录像内调用而失败，失败 attempt 原样保留；修复工具后在新的 `r2` 目录重新封装，没有改写原始调用、录像或失败收据。

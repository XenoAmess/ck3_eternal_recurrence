# CASE-C：既有战争路线上的首次实际接战

2026-09-23；**prepared / 本准备包零实机操作**。CASE-W 已在 day19 停止；本计划是新窗口，
不修改 W 的预算或结论。不追加宣战、招兵、移动、分合军、战斗/撤退命令，也不替玩家选择剧情。
继续既有玩家路线与 NPC 自身行为，观察一个实际 CombatID；必要时只观察这一场自然结算。

当前冻结入口是 [r2 plan](research-plans/war-film-case-c-20260923-r2/plan.json)、
[check --for-observation](research-plans/war-film-case-c-20260923-r2/plan-check.json)、
[同源图](research-plans/war-film-case-c-20260923-r2/graph.md)。
[baseline](research-plans/war-film-case-c-20260923-r2/baseline.json)保存旧 W 实值和新 checkpoint 绑定；
[window](research-plans/war-film-case-c-20260923-r2/sampling-window.json)是实际执行边界，
[source contract](research-plans/war-film-case-c-20260923-r2/source-contract.json)复用现有 API。
r1 是 checkpoint 到达及可选结算授权之前的准备草稿，原样保留；**执行使用 r2**。
检查通过只说明声明与文件绑定一致，不能称为已见到 CASE-C 接战。

## 真实起点与时限

新窗口仍由 root 唯一控制 R0005/PID32356/generation1，episode `native-29829-fcaa3906d404`。
day19 存档已经保存并由本准备器只读核对：

- `D:/workspace/ck3_war_film_research_20260923/case-w-r1/end-state.ck3`
- `49,683,960` bytes；SHA-256 `74d43b27bb9e13ed6431e3cbb7f38982b3af6622dd6a445e17fa1dc668a9d789`
- 对应 `end-checkpoint.json`，后置 `native:45 / public46 / native45 / date_raw53144784`。

每次实际调用仍从 fresh snapshot 获取 R，不能直接重放 public46。
旧 w131 的 W4：玩家29829、主要对手31549；玩家 U18 在2624，既有路线终点2638。
敌方完整 public IDs 为 `16777221 / 16777231 / 22 / 27 / 28`，该帧均 `in_combat=false`；
它们只是起点记录，后续每帧遍历当前 W4 的 allied/enemy rows，不只盯住这六支旧军。
w130 的 U22 最后 stored arrival为53146416，按现有 raw-hour 一日24的合同距起点68日；
这只是该路线时间线，**不是接战 ETA 或接战保证**。公开终点、narrow move target和每段route字段各自保留。

硬上限取先到者：**120 游戏日、600 秒墙钟、当前服务的可用剩余时间**。
起点53144784，因此120日上限为53147664；墙钟从首次 CASE-C resume 提交前的 monotonic mark 开始，
其后暂停、取样和查询耗时都计入。最后五游戏日或最后30秒改用 speed1，
在 day119 或 wall570s 主动请求暂停，为调用延迟留余量。
准备时 root 报告 R0005 服务原预计22:20:54Z到期；这条是准备阶段的时间前提，实际执行前的延长和最终停止记录见文末附记。
采样和命令延迟并非引擎同步闸门；如实际超限，保存真实值并记异常，不能把它改成预算内。

## 精确操作顺序

以下是调用说明，R/U/P/C必须换成正式返回的当前类型和值，不是预排请求模板。
R始终为public revision；U始终为full public CUnit，不能换用native CArmy。
准备器不向请求目录写入任何游戏请求，root只通过自己的正式 MCP 入口执行。

1. `ck3_get_capabilities()` → `ck3_get_bridge_diagnostics()` → `ck3_take_snapshot()` → `ck3_get_war_state()`。
   核对同run/PID/generation/episode、actor29829、date53144784、paused/map-ready、W4和对手31549。
   capabilities须新鲜广告speed1/2、pause/resume与接触/control/transition工具。
   checkpoint已完成，不必为了本计划重复存档。若起始已经in_combat，记“窗口开始前已存在”，不声称捕获了其发生。
2. 用最新R调用 `ck3_execute_step(step="set-speed-2", expected_revision=R)`，再snapshot刷新R，
   `ck3_execute_step(step="resume-map", expected_revision=R)`。允许改speed1；不调用其他自动planner。
3. 运行中串行 `ck3_take_snapshot()`，通常相邻取样不超过2墙钟秒；同地/邻接或接近已有到达时间时，
   speed1且约0.5秒取样。实际延迟单列。每帧检查全部当前W4 allied/enemy U的 `in_combat`，
   同时检查事件、pending interaction、身份、战争、日期与墙钟；不在运行时调用要求暂停的narrow查询。
4. 任一同W4 U的 `in_combat=true`，立即用最新R调用
   `ck3_execute_step(step="pause-map", expected_revision=R)`，然后snapshot确认真正暂停。
   取该U当前正式 `current_province_id` 为P，不把历史目标2638强行填成战斗地点。
5. 同一暂停状态依次：
   `ck3_query_actual_contact_scope(subject_army_id=U, target_province_id=P, expected_revision=R)`；
   `ck3_query_battle_control_snapshot_v1(subject_army_id=U, expected_revision=R)`；
   从实际返回取得C后 `ck3_query_battle_transition_v1(combat_id=C, expected_revision=R)`。
   每次保存返回的snapshot/public/native revision、date、阶段、C和ordered sides；有publication变化先fresh snapshot。
6. 至少一个当前W4 allied U和一个enemy U须出现在实际战斗的**相反side**，同full C且owner一致。
   同war单位可能正在另一场战争中战斗；单凭其 `in_combat` 不足以把C归给W4。
   `hypothetical`、`contact_if_now`、ETA或in_combat flag都不能替代实际C。
   第一次触发后最多两轮暂停读回；typed unavailable/identity_pending仍无法闭合就留下部分证据并停止，不推进日期等待“变绿”。
7. 三项正式读回闭合后，先保持暂停并保全请求、响应、首末帧、raw/timeline绑定。
   至此首次接战段即可停止成功；若进入以下可选子窗口，必须沿用这个C和同一整体预算。

revision失配不盲目重放写命令，先读实际状态。已有事件/待交互时暂停后停止，不选答案；
身份变更、连接失效、W4消失/终止/主要对手改变也停止。服务退出后不自行恢复或重启本attempt。

## 可选：只观察这一场自然结算

已保全暂停C证据后，可以只用speed1/2、resume/pause观察同一C；不下战斗、撤退、重新接近或和平指令。
单战额外最多30游戏日，日期截止为 `min(53147664, contact_date_raw+30*24)`，
原600秒/服务时限不重置。先保存同W4的 `player_relative_war_score`，以后只比较同W4。

同C终局、原subject退出战斗或C消失时立即暂停，调用：

```text
ck3_query_battle_terminal_transition_v1(prior_combat_id=C, subject_public_cunit_id=原绑定U, expected_revision=R)
ck3_query_battle_control_snapshot_v1(subject_army_id=当前仍存在的原U, expected_revision=R)
ck3_take_snapshot()
ck3_get_war_state()
```

`after_terminal_sequence`仅可填既有正式返回的游标，没有就省略。原U删除时不能猜一个successor替换；
须靠terminal journal的原C/原U/deletion或明确successor关系和当前状态闭合。
结束后的control可能不再有active combat，保留其真实typed结果；该结果或C消失本身都不是终局证明。
拿不到对应terminal/控制后置证据只写“不完整”，不追第二场。
war总分变化仅为同war前后读回；其他占领或战斗可能同时影响，不能仅凭时间相邻归因于这场C。

整个窗口没有实际C，只写“本窗口未观测到接战”；轮询间隙可能漏过短接触。
本包不证明完整AI评分、自然宣战、撤退策略或每帧同步。
原始素材预定 `case-c-r1` 与 `case-c-r1-recording`，准备包不启动recorder。
战时日历前进的素材不能使用暂停地图producer的同日期关联合同冒充同一暂停状态。

## 执行附记：服务期限与来源失败（2026-09-23）

这份 runbook 的上文是事前合同，r1/r2计划也保持原样。实际开始 CASE-C 前，唯一 owner 在 **2026-09-22T22:10:27.394459Z** 对同一个仍运行的 R0005 服务延长了1800秒；`capture-live-live-r5/service-extension-dispatch-r1.json` 与 `service-extension-r1.json` 分别保存调度和实际执行收据。monotonic截止从 `1220530.7981535` 变为 `1222330.7981535`，累计恢复服务预算3600秒；延长时没有提交原生游戏命令。因此上文旧预计22:20:54Z不是 CASE-C 执行时的截止，新的预计约22:50:54Z。这个服务期限变化不增加 CASE-C 自身的120游戏日/600秒预算，也不重开 CASE-W。

R0005 最初在 `capture-live-live-r5/hot-failure-state.json` 记录的 checkpoint身份核对 RED 仍为单独来源失败，不能由后来的正常HUD与正式读回倒改。CASE-W `w006` 存档 inspector typed unavailable 也保留其原结果。CASE-C 实际从独立日19 checkpoint开始，30游戏日后因待处理人物互动而停止；实测细节见[独立结果](war-film-case-c-result-2026-09-23.md)。没有实际 CombatID，故没有执行接战三连查询或可选结算。

## 复现准备

[离线准备器](../../tools/war_film_case_c_prepare.py)只读既有收据、存档和API源码，不重跑静态EXE研究。
新输出路径必须不存在：

```text
py tools/war_film_case_c_prepare.py --output-dir D:/workspace/ck3_war_film_research_20260923/case-c-plan-reproduce-NEW
py tools/native_research_plan.py check D:/workspace/ck3_war_film_research_20260923/case-c-plan-reproduce-NEW/plan.json --for-observation
```

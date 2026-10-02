# R0321 H3911：168 小时首路点与双守军的正式证据门

状态：**同帧只读输入 GREEN；发令、日期推进与进攻均 RED**。本页在独立 worktree 只读核对接收端 attempt4、现有策略和 CK3 1.19.0.6 原生研究；没有启动游戏或改变行动门。H3911 是 R0271 之后的独立帧，不能回填 R0271 turn 36 的证据。

## 已经证明的范围

接收端 `attempt-4-h3911-readonly-no-launch/live-h3911-readonly-v1` 的 `read-only-result.json`、`contact-payload.json`、`preview-payload.json`、`strength-payload.json`、`v3-source-comparison.json` 和 `independent-audit.json` 绑定同一次暂停读取：`native:3`，公开/native revision `4/3`，raw `53219928`，episode `native-29829-2bc2d599f7f9`，War `16777231`。原始存档 SHA-256 为 `5EFB3B3CF3EE7368C6C12D4C984B4A0366AA8A971409165016E3DC24725A4746`；接收端独立审计 SHA-256 为 `2DDA136A9FD52FEC33BDAFED8ABF429D6C65BB43248197D8C8234001A987D094`。来源 v3 摘录 SHA-256 `865EA7B7AC1B4A680E2BE3A1D84012C67CF9550474075E4A917EFE043CCCDD51` 与接收端新查询的**语义载荷**相等；两次查询的 snapshot/revision 不相等，不能混为同一帧。

| 事实 | 该帧读数 | 证明上限 |
| --- | --- | --- |
| 我军 | Army `83886367`，省 `2610`，2333 人 | 当前兵力，不是 44 日后的战力。 |
| 目标守军 | Army `[50331920,83886484]`，均在 `2629`，分别 1423、311 人 | 当前目标分区恰为两军；当前场外敌军为空，不保证未来名单。 |
| 路线 | `2614→2618→2624→2631→2630→2629`；首点 ETA raw `53220096`，目标 ETA raw `53220984` | 首点距今 **168 raw 小时/7 日**，终点距今 1056 raw 小时/44 日；ETA 是当前条件投影。 |
| 接触 | 全两敌军 `[53219928,53219952]`、`one_day_contact_free=true`、`conflicts=[]` | 仅前 **24 raw 小时**；首点前还有 144 小时未经证明。 |
| 战斗输入 | v3 目标 `2629`、入口 `2630`、攻 `[83886367]`、守 `[50331920,83886484]`，`actual_route_dependency=false` | 当前假想固定接战输入；`planner_usable=false`，无未来接战集合证明。 |

`_siege_forecast_participant_partition` 对当前两守军已返回 `available`。来源 attempt4 的旧 provisional 检查因 `one_defender_only=false` 失败；#512（`6b70f7520`）的新代码可为完整有序双守军做 `multi_defender_research_only` 试算，固定 `planner_usable=false`，并未补出正式生产者。#514（`e70f0a802`）的 compact MCP 读口只解决大历史传输；它没有改变原生含义。#507（`f7e78a1a9`）的安全首跳补丁只把短路点 **只读查询**移到现金门前，不降低发令或推进门，且尚须与 #512 集成审查。

## 两个不同许可

**A. 只向首路点发令。**在当前帧另取 `preview-move-army-83886367-to-2614`，要求原生路线精确为 `[2614]`；另取 `query-route-contact-horizon-v1-83886367-to-2614-h-2-50331920-83886484`，要求同 snapshot/revision/native revision/date/episode/connection generation、完整敌军 ID 和逐敌当前省份与全路查询一致，且精确 `[date,date+24]` 无接触。随后同帧核唯一可控军、无未处理事件/活动战斗、typed move、战时现金与本动作费用上界。现金的待付、即时费用、最低储备、有限期未来成本必须为有来源的数值，不能把 `null` 当零。所有门通过后也只可提交 `move-army-83886367-to-2614`，并立即读取接受后的原生路线/状态；发令本身不消耗七日安全证明。H3911 尚无短路线回执与现金报价，因此 A 当前 RED。

**B. 沿已提交路线最多推进一天。**先以动作后新暂停帧确认同一 Army/War、仍朝 `2614` 行进、没有撤退/战斗/待处理事项；重新查询该帧所有当前非撤退敌军和全部可控我军的 contact horizon，覆盖下一次最多 24 raw 小时的全军安全。只在正式规划器选出对应 `advance-route-contact-horizon-v1`、现金/维护风险仍有界时推进一次；推进后读回日期和路线，并丢弃旧帧许可。按当前 ETA 至少要重新作七个一日决策，实际 ETA 可能变化；任何敌军改路、范围变化、预报冲突、路线中断或额外我军无证明都停住。**当前帧没有能一次证明 168 小时无接敌的原生读数**；要预先保证整周，只能另造并验证覆盖 CK3 AI 改令、行动顺序和动态接触的原生确定性 oracle，现有 `arrival_date_raws` 不是这种 oracle。

这一分层与 [R0284 远期单跳](r0284-distant-single-hop-contact-2026-09-28.md) 的实测边界一致：一次 `move-army` 可以在原日期生效，后态仍在起点；后续日期信用必须按新帧逐日取得。当前 H3911 没有 A/B 的动作回执，不得把 R0284 的成功挪用。

## 双守军正式接战所需的独立闭环

最终靠近 `2629` 时必须在**当时**重新证明攻守两侧有序 Army/CArmy/CUnit、司令、当前 Province、目标内外所有敌军、native 接战选择/side、当前路线与时序。目标省当前两守军的 v3 输入不能排除未来增援、退出、撤退或双方属性改变；最终接战前只读重新查询，还需在真实 contact/join/phase 边界以原生 entry 与 selected CombatID 回读校验。现有 [未来增援输入边界](future-reinforcement-trial-input-boundary-2026-09-27.md)说明 route 的 Province ETA 不能提前绑定未来 CombatID。

合格 `combat_entry_eu_v1` producer 的最小证据包必须同时包括：

1. **原版逐日转移 parity。**对真实双守军战斗采两侧有序团/骑士、current/soft/hard、逐侧出伤与承伤、反制、战宽、优势、司令更替、入列/离列、胜负/追击/撤退及 RNG/phase 边界；逐 tick 对原版与纯函数找首个差异。H3911 当前 local-shell 硬伤候选为攻军承伤 36%、守军承伤 45%，研究模型仍默认两侧 30%；[硬伤诊断](r0321-hard-conversion-source-audit-2026-09-29.md)已证明这个首帧差异，尚未用真实 CCombat 和后续 ledger 闭合。
2. **加载内容与事件回流。**绑定实际 playset 来源、13 行 phase AST/evaluator、原生效果抽样和人物伤亡/失能后的当日及次日战力反馈。v3 的 132 项输入可观察，不等于 `loaded_playset_verified`、`ast_evaluator_ready`、`original_trace_ready`；H3911 三位均 false。
3. **独立校准。**事先冻结训练/留出存档 lineage 与风险阈值，核胜/负/未决、p90 硬伤、灭队、指挥官/骑士灾难尾部。重复同一存档的模拟样本或多段录像不构成独立原版结果。合格产物需保存输入、版本、实验种子、样本数、原版 holdout 对照及校准误差。
4. **同帧三行动效用。**将 `attack`、`avoid`、`wait_reinforce` 的战争目标、现金/兵员、角色生命、围城时钟与退出价值绑定到同一 encounter identity；通过冻结的 `combat-entry-eu-v1` 94 路径、显式 action components、概率与尾部硬门。`COMBAT_ENTRY_EU_ACTIVATION_ENABLED` 仍是单独门；填一个漂亮胜率或把 `planner_usable` 改 true 都不能替代它。

目前接收端 `qualified_forecast.status=producer_unavailable`、`formal_eu_activation_enabled=false`、`selected_step=null`。若始终无法校准双守军模型，安全结果可以是停下、重新选独立安全路线或经 H2743 合格退出决策，不能借研究 trial 直接攻入 `2629`。

## 可机器检查的拒绝样本

现有聚焦测试 `test_combat_provisional_defense_canary.py` 已断言双守军仅 `multi_defender_research_only` 且 `planner_usable=false`，并验证 R0271 短路点查询、冲突及敌军位置不一致时 fail closed；#507 的现金门测试另涵盖空值拒绝。新增同义测试会重复当前实现，故本页不新增测试。接收端若做下一次 **只读** H3911 查询，可把 `{short_preview,short_contact,full_contact,frame_identity}` 保存为新 attempt，再以现有聚焦测试的字段门作离线负例；这些证据完成前不选择 move。真正的七日闭环只能由每日新帧逐次验证。

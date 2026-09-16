# G2-M2 自然事件缺口与下一次实机门

状态：`static-ready / natural production loop pending`。工作包
`G2-M2-NATURAL-EVENT-GAP` 基于 `origin/master@38a56db8eaa1e12e0856803e861c463710869a92`，只读核对
CK3 `1.19.0.6 (Scribe)`、EXE SHA-256
`2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86` 的原版定义及现有生产资产。
本包没有启动 CK3，也没有使用屏幕、控制台、事件强制触发或 fixture。

## 结论

没有发现可在离线阶段确定修复的生产代码缺口。两个事件所需的 exact current-event query、registry recommendation、
typed option action、同角色压力 material comparator、旧 event-instance advance 检查和正式多 turn owner 均已存在。
剩余缺口是两次不同自然场景的完整 production artifact；因此本包不新增 private capability，也不改变任何默认开关。

| 链路 | `tgp_travel_events.0030` | `death_management.1007` |
| --- | --- | --- |
| 自然出现 | R555 在普通 product 路径到达真实 modal；无 console/fixture/坐标输入，但未完成选择 | R374 在普通 campaign 到达真实 modal |
| 正式 query | R555 冻结 player root、`travel_plan`、`poem_province`、两个 native option | R374 冻结 player root、`new_memory`、distinct `dead_character`、`deceased_character_stress`、唯一 native option |
| 正式 recommendation | 当前 registry/strategy 已 static-ready；R555 发生时尚未完成现行 recommendation → utility 链 | 当前 registry/strategy 已 static-ready；R374 的历史唯一选择不能补写为现行 campaign-utility recommendation |
| action | R555 未提交选择 | R374 已有 authored1/native0、instance `1046 -> null` 的历史 action/advance |
| material result | 未取得同角色 `stress_points` 严格下降 | R374 时 snapshot 尚无压力字段；没有同角色严格上升证据 |
| 下一正式 turn | 未取得 | 历史上随后继续清理其它事件，但没有与现行 recommendation/material result 绑定的下一 turn artifact 和 durable checkpoint |

R555 与 R374 都是有价值的自然 modal/局部生命周期证据，不能单独关闭 G2-M2。R665–R670 是旧 R555
checkpoint 路线上的 harness RED；旧 timeline 已退出重试队列。R374 的 park/driver snapshot 明确没有 durable checkpoint。

## `tgp_travel_events.0030` 自然触发判据

原版调用链为：code 触发的 `on_travel_plan_movement`（每次旅行进入省份）→ `travel_event_tombola` →
`travel_events_on_action` → weight-100 的 `.0030`。前两层为随机门；不能把“当前满足 event trigger”解释成必然出现。

候选场景必须同时满足：

1. TGP DLC trigger 为真，玩家政府为 `celestial_government`；标准封建 campaign 不可能自然命中。
2. 玩家是正在旅行的成年在世统治者，至少持有伯爵级头衔；不在军队、不被囚禁、不 incapable、无致命传染病，且不在 task-contract/gone-adventuring 或 pilgrimage event chain 中。
3. 当前地点是存在 county 的陆地省份；附近至少一个存在 county 的 special-building province，距离满足
   `squared_distance_monstrous`。
4. `.0030` 的十年 cooldown 已清除；事件由正常日期推进和旅行省份移动出现，没有 console、force/simulate trigger、
   事件 fixture 或人工事件注入。
5. 为取得 material evidence，选择前同帧玩家 `stress_points > 0`。压力为零仍可安全关闭事件，但只能得到
   `verified_no_change`，不能关闭本 material 门。

自然 modal 的严格投影仍须是 player root、两个 saved scope（`travel_plan: travel_plan`、
`poem_province: province`）及两个 shown/enabled native option。正式 recommendation 必须选择 authored2/native1；
它只施加 authored `medium_stress_impact_loss`（base `-30`），避免 authored1/native0 的五日延误与随机 duel。
运行期精确 delta 受人物 stress-impact 修正影响，不要求恰好 `-30`。

来源：`travel_on_actions.txt:1-19,715-951,995-1028`，SHA-256
`7E433A0D6969E09CFED1D9DC50FB5276D944354024D6D2E045B314355F41040C`；
`tgp_travel_events.txt:311-496`，SHA-256
`42B8B1E56C029054FBC4E0B3964511A980D9B5053C47BFF980CD3F5F3924DB37`；
`00_available_for_events_triggers.txt:131-145`，SHA-256
`5566A89A7D93BFB80DCF5A2F065BE0F058BE13E0B84470D1182B82D8D6384A44`；
`00_travel_triggers.txt:1-5`，SHA-256
`80AF79A434BEE49FD25BF793D37F93131FDF39CEAF496E6BCFDB270AEFD469EE`。

## `death_management.1007` 自然触发判据

原版 `on_death` 排队 hidden `.0001`。`.0001` 只把“其 `player_heir` 等于死者”的在世头衔持有者加入
`title_holder_list`，随后延迟触发 `.0002`；`.0002` 先分派配偶、囚犯、软禁和战死等更高优先级分支，普通继承人分支
还要求收件人是死者的近亲或扩展亲属。`.1007` 打开时 ROOT 必须已经有替代 `player_heir`。

下一次可被**当前严格策略**直接消费的场景应进一步收窄为：

1. 在世玩家统治者的当前 `player_heir` 死亡，且死亡发生前玩家仍是其继承头衔持有者。
2. 死者是玩家的 close family。原版 `.1007` 允许 extended family，但 `on_death` 只为 close family 创建
   `relative_died` 的 `new_memory`；仅扩展亲属可能产生当前合同明确拒绝的 missing-`new_memory` 新 shape。
3. 死者不走 dungeon、own-dungeon、house-arrest 或 battle-death 优先分支；没有 killer/known-killer scope，
   从而匹配 R374 的严格三-scope shape。
4. 事件打开时玩家仍有另一位 `player_heir`；选择前同帧 `stress_points` 必须允许实际增加。若到达压力上限或修正使
   结果不变，只能记录 `verified_no_change`，不能关闭 material 门。
5. 事件来自正常 campaign 的死亡/on_death 链；force event、模拟死亡、fixture 或控制台触发只能作为局部开发证据。

正式 recommendation 必须是 sole legal route authored1/native0。它对 ROOT 施加
`minor_stress_impact_gain`（authored base `+20`）；`deceased_character_stress` 不被 `.1007` 读取，`after` 仅显示 tooltip。
运行期精确 delta 同样不要求恰好 `+20`。

来源：`death.txt:966-984,2156-2162`，SHA-256
`F9D596E05A84C42E7370B63874B5172CECB574190541AD67606C68C387F5A041`；
`death_management_events.txt:5-13,94-100,340-364,527-706,1949-2057`，SHA-256
`31591A2F2D3A61E65853CC43B9BEF4B001FEB75EA1502861D2FB9AC054AB1FB7`；
`00_stress_values.txt:25-34`，SHA-256
`104A7EF94EE9DA1092F23AEB2FD9DC971B08C695415F3B7EBFB628F381D26395`。

## 可执行的 bounded natural 观察清单

两个场景分开执行；不要让标准封建死亡长局承担天朝旅行事件。每个场景优先复用本来就要继续的 production campaign。
普通 campaign slice 使用既有上限：最多 `40` 个正式 turn、`7200` 秒墙钟、readiness `300` 秒；已有相邻 checkpoint 时
可缩为最多 `6` turn、`1200` 秒、readiness `300` 秒。上限到达而目标未出现时记
`evidence_not_observed`，保存合法 tail checkpoint 后结束，不算 RED，也不算 GREEN。

每个场景依次保存以下证据：

1. **冻结输入**：agent/native/MCP commit，DLL/injector/EXE 哈希，DLC/mod/load order，save 与 driver-state 哈希，
   profile、played CharacterID、起始日期、turn/墙钟边界；证明只有一个 CK3 实例。
2. **自然 provenance**：目标 modal 前的 command history 只含正常 production query/action/date progress；没有 force/simulate、
   console、fixture、OCR 或坐标输入。只从目标 modal 开始录证而无法说明其来源时，最多记局部 modal 证据。
3. **同帧 query**：`ck3_query_current_event_window_context_v1` 返回 exact key、正 event instance、player root、上述严格
   saved scopes 与 shown/enabled native option；保存同帧玩家 CharacterID 和 pre-stress。
4. **正式 recommendation**：生产 `choose_one_life_turn`/`ck3_auto_turn` 消费同一 context；registry decision 为
   `recommended`，native index 分别为 `.0030 -> 1`、`.1007 -> 0`，并发布对应 campaign utility。
5. **唯一 action**：带 exact instance/revision 只提交一次 typed event option；ACK 本身不算结果。
6. **独立 material frame**：同一 CharacterID、旧 instance 已消失、revision/snapshot 前进；`.0030` 要求
   `post_stress < pre_stress`，`.1007` 要求 `post_stress > pre_stress`。相等仅关闭生命周期，不关闭 G2-M2 material 门；
   反向变化、缺字段或 CharacterID drift 为 RED。
7. **下一正式 turn**：再执行恰好一个正常 `native_auto_run` turn。其 before frame 不得含旧 instance，history 中该 instance
   的 select 仍恰好一次，planner 必须消费当前新状态并选择一个合法新 step，不能重复旧 option。保存该 turn 的独立报告。
8. **durable handoff**：在下一 turn 后保存 paired game/driver checkpoint；报告明确关联 natural provenance、query、
   recommendation、action、material result 与 next-turn command identity。若 cold restore 属于当轮既定验收，再从该 checkpoint
   启动新进程确认旧 instance 不重投；它不是这两个 material 门的替代品。

若 `.1007` 出现 killer/known-killer、missing `new_memory` 或其它 scope shape，保留真实 paused RED 并为该 shape 单独做
exact-build review；不要因“唯一选项”绕过合同。若 `.0030` 出现在 forced/feudal 场景，只可验证局部 query/action/comparator，
不得称自然 G2-M2 证据。

## 离线验证

聚焦 registry、policy、material comparator 与 auto-run event lifecycle 在 normal 和 `python -O` 下均为
`19 passed, 77 deselected`。由于本包未改 native 代码、ABI、MCP 注册或开关，没有新增 native 双模式构建面。

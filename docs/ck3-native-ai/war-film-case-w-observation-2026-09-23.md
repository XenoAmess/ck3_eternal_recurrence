# CASE-W：操作者宣战后的原生 NPC 战时反应观测

2026-09-23；**prepared / 未执行**。本包只读取既有 R0004 收据和原版静态文件，
没有连接、启动、恢复或操作 CK3。R0004 服务已按原预算结束；本单用于唯一 owner
今后分配的新正式 run，不能继续使用旧 PID、revision 或请求目录。

目标是一条有界连续案例：**操作者按当前合法 token 宣战 → 同一战争中的 NPC 军队出现/集结 →
原生已提交路线及随后进展**。必要且来得及时才补一个真实接战。
影片应明确“这场战争由我们发起，之后观察对方原生 AI 的反应”；不称自然 AI 宣战，
也不解释未暴露的完整目标评分、战斗胜率或撤退策略。

## 冻结输入与不能复用的旧值

[计划](research-plans/war-film-case-w-20260923-r1/plan.json)、
[观测前检查](research-plans/war-film-case-w-20260923-r1/plan-check.json)、
[同源图](research-plans/war-film-case-w-20260923-r1/graph.md)、
[历史基线](research-plans/war-film-case-w-20260923-r1/baseline.json)、
[工具合同](research-plans/war-film-case-w-20260923-r1/source-contract.json)及
[采样窗口](research-plans/war-film-case-w-20260923-r1/sampling-window.json)共同保存本次准备。
`check --for-observation` 只检查文件绑定与采样声明，不证明 runtime 已就绪，不授予启动权限。
图中的一条 live 边只表示历史 CASE-R 基线，**CASE-W 新行为 live 边为零**。

| 项目 | R0004 归档实值 | 新 CASE-W 的使用方式 |
|---|---|---|
| 玩家 / 目标 / effective target | `29829 / 31549 / 31549` | 恢复后重新读回；不匹配即停，不猜新映射。 |
| 对方身份 | 独立伯爵；primary title ID `2111`；首都省份 `2638`；top liege 为自身 | 依据当次 `005-campaign-root.json`；不使用旧 run 的人名。 |
| 合法行 | `31549-40--1`；`minor_religious_war`；target titles `[2111]` | 仅作检索目标；必须在新 run 成功枚举的当前行中再次存在。 |
| 原生战略 power | 我方 `3786000000`，对方 `1334000000`；native ratio `35235`，Q100000 | `010-assessment-two.json` 的历史输入，不当作新战争实时值或胜率。 |
| 旧帧 | `native:5`，public `6`，native `5`，date_raw `53144328` | 不作为新请求的 `expected_revision`。 |
| day-zero 存档 | `50502569` bytes，SHA-256 `a450f37ff62ea0375b9ae2f6549aa5a14baa9940fc57fa6f97f912f1c76447f8` | 新 run 的 seed/恢复输入；保留原件，恢复成功要另外读回。 |

存档路径：`D:/workspace/ck3_war_film_research_20260923/robert-input-case-r1/day-zero.ck3`。
其 bytes/hash 与 `003-checkpoint.json` 一致，是原始 `SAV0101` 二进制存档。
本包没有二进制角色解码结果，不能把历史脚本 `20829` 的人名直接赋给 runtime `31549`。
原版省份 `2638` 对应 `b_syracusa` 可静态核对，但本片人物暂称“这位独立伯爵”。
`006-declarable.json` 是超时记录；历史合法行来自已恢复结果后的 `011-case-end-snapshot.json`，
不得把 006 改称成功枚举。

## 操作前置

1. root 通过已有正式 run/profile 恢复流程分配新 run，记录实际 seed 的 bytes/hash、恢复收据、
   DLL/EXE 身份、PID、connection generation、episode、HUD 和 map-ready 后置。
   若改为新开局，明确记为新案例，不称恢复了该 checkpoint。
2. `ck3_restore_checkpoint(expected_revision=R)` 确实存在，但只恢复 server 已绑定的 checkpoint，
   **没有文件路径参数**，且会重启 native session。它不是向已终止 R0004 发请求的入口，
   也不能凭本单给它传入任意 seed 路径。正式恢复由新 owner 的启动配置完成。
3. 后续串行使用该 owner 的正式 MCP；本包不另开 server、不接管单实例管道。
   先确认本次 capabilities 广告所需查询及 `pause-map / resume-map / set-speed-1 / set-speed-2`。
4. 开启新的 CASE-W raw/timeline，逐条保存完整 request/response、UTC 和 monotonic mark。
   保存新 pre-declaration checkpoint 到独立归档路径，验证已 materialize；不覆盖 day-zero 原件。

## 精确 MCP 顺序与参数

下表 `R/D/Q/W/U/P/C` 是说明变量，**不是可以原样发送的字符串**。
`R` 每次取最新 snapshot 的 public `revision`；`D` 为当前合法行的字符串 token；
`Q` 为真实 pending request ID；`W/U/C` 为当前正式返回的完整 WarID/public CUnitID/CombatID；
`P` 为本次真实省份 ID。动作之后先读回后置，再决定下一调用；ACK 不等于完成。

| 顺序 | 正式调用 | 必须保留的后置或停止条件 |
|---|---|---|
| 1 | `ck3_get_capabilities()` → `ck3_get_bridge_diagnostics()` → `ck3_take_snapshot()` | 新 run/PID/generation/episode、exact build、actor、日期、paused/map-ready；失配即停。 |
| 2 | 如未暂停：`ck3_execute_step(step="pause-map", expected_revision=R)` → `ck3_take_snapshot()` | 真实 `paused=true`；再以新 R 调 `ck3_query_campaign_root_context_v1(expected_revision=R)`，核对 actor/目标的当前身份。 |
| 3 | `ck3_save_checkpoint(expected_revision=R)` → `ck3_inspect_save_artifacts_v1()` → `ck3_take_snapshot()` | 存档已落盘并 hash 归档；最后快照作为 S0，避免跨 checkpoint publication 复用 R。 |
| 4 | `ck3_get_war_state()` → `ck3_query_declarable_wars(expected_revision=R)` | 保存前置战争/军队范围；成功结果中重新选择精确 `minor_religious_war` 行 D。不能只读未经成功查询的缓存空数组。 |
| 4a | 仅原请求确实留下 Q 时：`ck3_collect_declarable_wars_result_v1(request_id=Q, expected_revision=R)` | 只收原请求，不重发枚举；`pending` 可在暂停的同绑定下最多收取三次、累计60秒；`stale/rejected/unavailable` 即停。无 Q 不猜。 |
| 5 | `ck3_query_war_entry_assessments(target_character_ids=[31549], expected_revision=R)` | 仅一个目标；ready 且本次 actor/target/effective target 如预期。新值可与历史值不同；不同不强行改回。 |
| 6 | `ck3_declare_war(declaration_id=D, expected_revision=R)`，**最多一次提交** → `ck3_take_snapshot()` → `ck3_get_war_state()` | 绑定新增 W、主要攻守方、CB/目标和当前双方 armies。超时先做一次真实状态核对；未证明 W 就停止，不盲目重试。 |
| 7 | 对 W 的真实 NPC U：`ck3_query_army_strengths(army_ids=[U], expected_revision=R)`；可用时 `ck3_query_battle_reinforcement_assignment_v1(selected_public_cunit_id=U, expected_revision=R)` | U 来自 W 的 enemy army rows；核对 owner、不可由玩家控制、native AI membership。`subject_not_ai_managed` 等 typed unavailable 原样留存。 |
| 8 | `ck3_execute_step(step="set-speed-1", expected_revision=R)` → snapshot → `ck3_execute_step(step="resume-map", expected_revision=新R)` | 暂停前后都刷新真实快照；游戏运行时只取快照观察日期。开始时一日一停，之后最多三日一停，可用已广告 speed2；接近接战用 speed1。 |
| 9 | 当前 snapshot → `ck3_execute_step(step="pause-map", expected_revision=最新R)` → snapshot → `ck3_get_war_state()` → 重做顺序7 | 比较同 W/U 的当前省份、已提交路线与后续进展；记录实际日期，不按猜测的 raw-date 步长推进。达到主要证据或上限即停。 |
| 10（可选） | `ck3_query_actual_contact_scope(subject_army_id=U, target_province_id=P, expected_revision=R)` | P 从真实当前位置/目标/接触范围取得；保留返回的阶段和双方顺序。`hypothetical`/present-time projection 不能叫实际接战。 |
| 11（仅实际接战） | `ck3_query_battle_control_snapshot_v1(subject_army_id=U, expected_revision=R)` → `ck3_query_battle_transition_v1(combat_id=C, expected_revision=R)` | C 必须来自实际 contact/control。绑定 W/U/双方与同一个 C 后停止；不追加第二场战斗、终战或撤退实验。 |

所有带 R 的读查询要核对返回的 queried/public/native revision、snapshot、日期及暂停状态。
查询导致 publication 或帧已漂移时，保存原返回，刷新后只补必要的新读请求，不能跨帧拼装“同帧”。
正在运行时乐观 revision 失配也先重读实际状态；若无法建立一次可靠暂停，就保留失败并停止取材。
不调用 `ck3_auto_turn`、`ck3_plan_turn` 或 `life-advance` 来替代这个明确窗口。

若需要我方军队作为接近对象，root 可在窗口内显式记录一次
`ck3_raise_troops_default(expected_revision=R)`，随后读回我方真实军队。
必要时仅一次 `ck3_move_army(army_id=我方当前U, target_province_id=本次P, expected_revision=R)`，
并核对原生接受及真实路线。二者都是操作者干预，不是被观测的 NPC 决策。
不得向 NPC 下达移动、招兵、传送、战争结果或隐含 planner 指令。

无参数请求的真实 envelope 例子：

```json
{"action":"mcp","tool":"ck3_take_snapshot","arguments":{}}
```

带参数请求按上表填入真实 JSON 类型，串行等待返回；不要把整表预先排入请求目录。

## 能证明的最小节点与停止点

| 节点 | 最小现场证据 | 不足时应怎样描述 |
|---|---|---|
| 新战争 | 一次显式宣战的 request/response；前后快照中的新 W；双方/目标一致 | 单有动作 ACK 不叫宣战完成。 |
| NPC 军队出现/集结 | 新战争后的暂停帧中，W 下 U/owner/位置/兵力的连续返回；有正式集结状态时另存该字段 | **第一次出现在 published scope 不足以证明新招兵**。可能是既存军队刚纳入 war scope；没有明确状态/有效前后证据时只写“首次观测到军队”。 |
| 原生路线与进展 | 同 W、同完整 U 的 `route_province_ids`，以及后续当前省份改变或相应原生时间线进展；可配 narrow reinforcement route/ETA | 只见军旗移动、路径 preview、路线不为空或 ETA 减少不足以说明完整选目标策略。改道/停军如实记录。 |
| 单次实际接战（可选） | 实际 contact/control 的 C 和双方，transition 的同 C；U 的同 W 归属 | 预测接触、候选 CombatID、`contact_if_now` 均不是已经加入战斗。 |

路线工具实际字段来自
[battle_reinforcement_assignment_contract.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/battle_reinforcement_assignment_contract.py)
L18–92：`route.current_province_id / move_target_province_id / route_province_ids / arrival_date_raws /
assignment_eta_date_raw`，以及 `route_alignment` 和 typed unavailable。
这个查询要求 AI membership；未获得 ready 路线时，可保留 war-army 已发布路线和跨帧位置证据，
不可编造 ETA 或把它称为已经完成 requesting→assigned→join 实验。
军队拆分/合并或 ID 消失时，仅有明确 successor 证据才沿用同一链；否则停止该链并记身份中断。

主要停止点是同 W 下一个 NPC U 的出现/集结记录、已提交路线和后续进展。
硬上限取先到者：**30 个实际游戏日、12 个暂停采样轮、12 分钟观测墙钟**。
墙钟从首次宣战提交开始；启动/恢复/合法性枚举另行记录，不计作 NPC 反应时间。
如果影片确实需要且已有路线能在剩余预算内接触，可以进入唯一可选延伸：
总计不超过 **45 游戏日、16 轮、15 分钟**，第一次真实 CombatID 绑定完成就停。
不会为了成功无限加天数、追逐第二场或另找新目标。

身份/连接变化、目标战争消失或主要对手改变、关键读回持续 unavailable、
意外事件要求无关干预、达到上限，也都停止。结果未出现只能写“本窗口未观测到”，
不能写“AI 不会招兵/移动/接战”。若宣战前对方军队不可见，空数组不能充当全军为零的证明。

每一节点至少关联：checkpoint bytes/SHA、run/PID/generation/episode、UTC/monotonic、
snapshot/public/native revision、实际日期、W/U/owner、必要的 P/C、raw 录像 SHA 和 timeline mark。
执行结束另建结果包，不修改本准备包；每条未知边只按实际新证据更新到新的结果计划。

## 复现准备包

[准备器](../../tools/war_film_case_w_prepare.py)只读本地归档和静态源码，默认拒绝已有输出目录。
以下命令应使用新的输出目录；原冻结 r1 不覆盖：

```text
py tools/war_film_case_w_prepare.py --output-dir D:/workspace/ck3_war_film_research_20260923/case-w-reproduce-r2
py tools/native_research_plan.py check D:/workspace/ck3_war_film_research_20260923/case-w-reproduce-r2/plan.json --for-observation
```

正式 API 名称和参数核对自
[mcp_server.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)
L1288–1367、L1401–1596；声明结果收取的同绑定规则见
[native_driver.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py) L8242–8350。
本包不修改 MCP schema、旧专题或共享路线图，也没有新实机结论。

# Robert 1066 原版局：现有 MCP 取材操作单

2026-09-23；状态：**prepared / 未执行**。本单基于现有正式入口与已归档实证编写，
不把正在准备的 R0004 填成成功案例。不预置任何 actor、WarID、ArmyID、CombatID 或省份 ID。
执行由当前唯一 CK3 owner 完成；本包没有启动、附加、查询游戏或修改 native 代码。

本单中的 **CASE-R** 另由[暂停观测计划](research/war-film-robert-readback-plan-20260923.json)、
[check 收据](research/war-film-robert-readback-check-20260923.json)与
[同源图](research/war-film-robert-readback-graph-20260923.md)绑定。
该计划仅覆盖当前 Robert 的玩家合法候选与单目标 war-entry 原生读回，不覆盖下文战争延伸，
也不把 `check --for-observation` 称为实机完成或额外启动授权。

## 优先拍哪条连续案例

先拍 **“Robert 当前能对谁宣战 → 两个目标的原生战略军力估值 → 回到同一暂停地图”**。
这是一个当前玩家视角、原生查询值的连续案例，服务 W1 输入与 W3 数值解释，
不承诺捕获自然 AI 宣战或整场战争。

选择依据是[Robert day-zero readback](robert-day0-war-opportunity-readback-2026-09-23.md)：
该文第 20–30 行记录 R0140 在旧 Robert 普通 `xar_off` 存档同一暂停帧完成合法性与三次军力查询，
有多个合法目标、不同有效防守方与不同军力比。**历史目标数、ID、比值、日期均不可填入本次表格**。
其第 18–19 行还明确：未经主动 declaration query 的空 `declarable_wars` 不证明没有合法战争。
本次先真实查询，最多评估四个当前候选目标，取得两个有区别的结果即可停止；不扩大成全世界枚举。

预计可用画面约 60–120 秒，实际采集耗时取决于查询与 UI 可见性，不能预先承诺完成。
拍摄前须同时确认 HUD 已显示和正式 StartGame/campaign-root 后置成功；
[R0003](war-film-startgame-post-ready-pump-2026-09-23.md) 的“载入100%”画面不能替代该条件。

## 版本、绑定和请求方式

- 固定 CK3 `1.19.0.6`，EXE SHA-256
  `2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86`。
  MCP server 版本为 `0.1.0`；各查询仍有独立 v1/v3 合同，不能把 server 版本当作查询 schema 版本。
- 先调用 `ck3_get_capabilities()` 和 `ck3_get_bridge_diagnostics()`，保存本次真实返回，
  核对 exact-build、所需 advertised capability、PID 与 connection generation；记录当前 DLL/injector 来源收据。
  代码注册了工具不等于当前加载 DLL 一定提供它。
- `ck3_take_snapshot()` 得到 `snapshot_id`、**public `revision`**、`native_revision`、日期、
  玩家与暂停状态。下文 `R` 一律取 public `revision`；不要把 `native_revision` 填入 `expected_revision`。
  所有写明 `expected_revision` 的取材调用都显式传本次 R，即使 API 允许省略。
- 原生细项查询要求暂停并通过自己的同帧检查；例如 war-entry 在查询结束复核 snapshot ID、
  public/native revision、episode 及 target scope。读回 revision 漂移时保留失败，刷新快照后另记一次新查询；
  不修改历史收据，也不自动重发宣战、移动或和平动作。
- 每个 ID 从当前正式返回绑定。`player_armies[].army_id`、
  `active_wars[].allied_armies[].army_id` 与 `enemy_armies[].army_id` 是 public CUnit ID 来源；
  不把 `native_carmy_id` 填进要求 public CUnit 的参数。CombatID 从 actual-contact/battle 返回取得。
- 使用现有同 owner 的 [interactive/recovery 请求入口](war-film-capture-hot-service-2026-09-23.md)，
  串行等待每个正式 MCP response，再依该返回填写下一请求；本单不另开 MCP server 或接管管道。

无 ID 请求可直接使用该入口已有 envelope：

```json
{"action":"mcp","tool":"ck3_take_snapshot","arguments":{}}
```

下表的 `R/T/U/C/W/P/E` 是人工绑定变量说明，不是可以原样发送的字符串或猜测 ID。
对应值必须以正式工具 schema 要求的整数/list/string 类型写入 `arguments`。

## 已存在的正式只读工具

工具注册来自 [mcp_server.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py)：
能力/诊断/快照 L1288–1324，战争与军队 L1401–1586，campaign-root L1589–1596，
撤退预览 L2457–2468，战斗输入/战争评估/和平 L2493–2570。

| 精确工具名 | 参数与版本 | 能得到的证据与范围 |
|---|---|---|
| `ck3_get_capabilities` | 无参数 | 当前 backend、steps、native capabilities；不是动作成功收据。 |
| `ck3_get_bridge_diagnostics` | 无参数 | 当前连接、PID/generation、heartbeat/mailbox；不是地图或角色真值。 |
| `ck3_take_snapshot` | 无参数 | 最新缓存语义帧及诊断；被动读取，不负责刷新 declaration/和平查询，也不主动推动游戏。 |
| `ck3_query_campaign_root_context_v1` | `expected_revision=R`，v1 | 当前玩家、头衔、首都、领主、政体与规则 token；用于把本次人物和地图绑定。 |
| `ck3_get_war_state` | 无参数 | 当前 active wars、玩家军队、已缓存查询切片及 revision；不能把其中未查询的空数组当作否定结果。 |
| `ck3_query_declarable_wars` | `expected_revision=R`；现有合法宣战枚举入口 | 当前玩家 final-legal 声明行及精确 `declaration_id`；不是 AI 原始候选分数、90%过滤、Top5 或抽签结果。 |
| `ck3_query_war_entry_assessments` | `target_character_ids=[T]`, `expected_revision=R`；wire v1，**严格一目标/请求** | 当前合法候选或 active-war primary opponent 的 effective target、双方 base/network/total power、原生 ratio 与 provenance；同目标多个 CB 共享评估，不是 CB-specific 成本。 |
| `ck3_query_army_strengths` | `army_ids=[U,...]`, `expected_revision=R`；v1 | 当前 published player/war scope 中军队的 current/max soldiers 与 AI base power；不能变成胜率。 |
| `ck3_query_actual_contact_scope` | `subject_army_id=U`, `target_province_id=P`, `expected_revision=R`；v1 | 接触前假设或接触后实际 Combat/双方绑定；必须保留返回的阶段语义和 native side order。 |
| `ck3_query_combat_simulation_inputs_v3` | `target_province_id=P`, `attacker_entry_province_id=E`, `attacker_army_ids=[...]`, `defender_army_ids=[...]`, `expected_revision=R`；v3 | 当前同一战争双方的显式 encounter phase/regiment 等输入；required readiness 与 unavailable 原样保存。不是原生 `0x19186E0` 的完整 AI ratio，更不是预测胜率。 |
| `ck3_query_battle_control_snapshot_v1` | **MCP 参数名** `subject_army_id=U`, `expected_revision=R`；v1 | full public CUnit 的 active Combat、所属 side、retreat gates/资格；不证明原生 AI 有意选择撤退。 |
| `ck3_query_battle_transition_v1` | `combat_id=C`, `expected_revision=R`；v1 | phase、winner、ordered sides 等当前战斗状态。C 必须来自实际返回，不能拿战争 ID 代替。 |
| `ck3_query_battle_terminal_transition_v1` | `prior_combat_id=C`, `subject_public_cunit_id=U`, `expected_revision=R`, 可选 `after_terminal_sequence`；v1 | journal 支持的终局、删除、subject 与 successor 状态。可选 sequence 只沿用前一返回的游标，不杜撰。查询不是 journal 之外全部历史的补录器。 |
| `ck3_query_battle_reinforcement_assignment_v1` | `selected_public_cunit_id=U`, `expected_revision=R`；v1 | **native AI-managed** CUnit 的 coordinator、parent/subunit stored order、asking/assigned、assignment target、route/ETA、present-time contact 投影。玩家可控军没有该 membership 时返回不足，不能替代 AI 实例。 |
| `ck3_preview_active_combat_retreat_v1` | `selected_public_cunit_id=U`, `target_province_id=P`, `expected_revision=R`；v1 | 具体当前撤退候选的合法性和短时 token；只是显式预览，不证明 AI 策略 caller。 |
| `ck3_query_war_termination_options` | `war_id=W`, `expected_revision=R`；现有 options 合同 | surrender/white_peace/victory 的原生构造、validator、available、recipient response/可观测 acceptance，及支持的战争分数分解；不是 AI 主动提议日程。 |
| `ck3_query_outbound_war_white_peace_status` | `war_id=W`, `expected_revision=R`；v1 | **当前玩家作为发送方**的精确 pending 白和收据；不能充当任意 AI proposer 的全局日志。 |
| `ck3_query_war_termination_terms` | `war_id=W`, `expected_revision=R`；当前公开 v1 | `claim_cb_claim_disposition` 窄切片：claimant、目标、claim 状态与三种结果方向；非 claim CB 的 typed unsupported 不是零成本，不能外推完整金钱/停战/俘虏账单。 |

`ck3_query_combat_simulation_inputs`（无 `_v3`）也有注册，但本单优先使用 v3；旧入口接受同形参数，
不能把两种输出混成同一证据版本。当前 public MCP 没有独立完整 CAIWarCoordinator 调度/目标评分表、
normal/desperate mode、主动撤退选择或主动白和 scheduler 查询。
reinforcement 查询中的 coordinator/target 是已实现的局部只读投影，不是这些缺失观测的替代品。

代码依据：

- [service.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/service.py) L11230–11347：
  单目标 scope、public revision 入参、native revision 结果绑定及查询后同帧检查；
  [war_entry_contract.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/war_entry_contract.py) L15–74：
  v1 capability、exact EXE、Q100000 与 15 个原生输出字段。
- service L10463–10570：reinforcement 的 paused/native revision 与字段合同；
  [援军专题](battle-reinforcement-and-join.md) L496–514：具体 coordinator/signal/assignment/route 字段；
  L539–548 的旧 live 有 asking、无 assigned，不能据此称普通完整求援链已经取到。
- service L10967–11035 与 [combat_contract.py](../../ck3_autonomous_player/src/xar_autoplayer/bridge/combat_contract.py)
  L359–415：v3 两组军队必须来自当前 published scope、异侧并共享一场 active war，不能自由拼全地图两支军队。
- [war-termination.md](war-termination.md) L986–994：公开 terms v1 的明确窄范围；
  L1054–1063 有旧 Robert claim CB 同帧 options/terms 实证，未提交终战动作。

## W1–W7 各自能拍到什么

| 工作包 | 现有工具可证明 | 本单不能宣称已证明 |
|---|---|---|
| W1 宣战 | 玩家本帧合法声明、effective defender、原生战略 power 输入；操作后可另读真实 WarID。 | 自然 AI 的预算完整输入、候选原始分、90%/Top5/加权抽选、该次 AI 为何开战。 |
| W2 目标 | 当前军队路线；AI reinforcement 的已存 assignment、coordinator/parent membership。 | 所有 campaign 目标候选、优先级竞争、预算/重算 timer、最终目标提交 caller。 |
| W3 接近与接战 | Army strength、explicit contact 双方/顺序、v3 phase inputs；战后实际 phase 可对照。 | 完整 AI 战斗估值、normal/desperate 触发的本次 producer、胜率。战略 target/actor ratio 与局部战斗 ratio 不能混用。 |
| W4 求援/增援 | 有真实 AI subject 时观察 asking/assigned、目标、对齐路线与 ETA、实际 join 后 CombatID。 | 只见 bit=true 就声称亲眼见到阈值转换；没有同 subject 历史状态不能实证滞回。普通求援不能外推 PLAYER_SUPPORT 专用政策。 |
| W5 战中撤退 | 当前资格、显式预览 token、控制动作及其后果，terminal/离场状态。 | 普通 AI 主动撤退意愿与真实 caller；玩家命令或继承/战后清理不能冒充。 |
| W6 战斗结果 | 同 Combat 的 phase/winner/终局与同 War 的已发布 score/breakdown 前后值。 | 仅用总分差还原单场贡献；其他战斗/占领可同时变化。现有工具没有本次败方八桶完整 producer 读回，不能声称逐桶实机复算。 |
| W7 和平 | 本帧 options legality、recipient 是否会接受、可观测 acceptance、claim terms、当前玩家 outbound pending。 | AI 自然主动提案的 scheduler/随机竞争；我方 `offer_white_peace` 只能证明操作者提议后的 native 处理。 |

W6 八桶来源已静态闭合，见[八桶研究](war-film-battle-score-denominator-2026-09-23.md) L5–20；
该页明确无新实机。以上限制是当前已有工具的边界，不否认静态结论。

## CASE-R：同一暂停帧的两目标估值对照

观测窗口只读，不推进游戏日期，不触发自动 planner。存档动作在窗口开始前单独记录。
以下动作均是**待执行操作**：

1. owner 确认 HUD 和 StartGame 独立后置，另起 HUD 之后的原始录像，保存本次纯原版 enabled-mods/版本来源。
   用 capability、diagnostics、snapshot 和 campaign-root 返回建立本次人物/日期/版本绑定。
   actor 只来自本次 `played_character` 与 campaign-root 一致读回，不从本文或旧 R0140 复制。
   先以最新 public revision 调 `ck3_save_checkpoint(expected_revision=R)`，保存正式返回并验证存档已 materialize；
   可用 `ck3_inspect_save_artifacts_v1()` 读取当前 server 绑定 profile 下的存档证据。
   存档成功后重新取快照作为 S0，避免把 checkpoint 引起的 publication 变化混进只读比较。
   HUD 后新录像与启动全程 `raw-desktop.mkv` 使用不同文件及 timeline；后者只作 debug 过程保全。
2. 记录 S0 全快照，令 R=S0.revision。调用 `ck3_query_declarable_wars(expected_revision=R)`，
   保存真实返回及后快照 S1。无查询成功结果时，停止候选解释；查询成功为空时只讲本帧此入口没有合法行。
3. 从成功返回的当前行取得不同 target CharacterID。每个请求只带一个：
   `ck3_query_war_entry_assessments(target_character_ids=[T], expected_revision=R)`。
   查询前后核对 queried snapshot/public/native revision、actor、date、target 与 readiness。
4. 最多四个目标，优先保留两个 effective target 或原生 ratio 有区别的实际结果。
   若两个原始目标解析为同一个 effective defender，保留这个现象并解释“宣战对象与实际防守方可能不同”；
   不为了画面不同伪造对照。没有第二个有效目标就拍单例，不能称全候选排序或最强/最弱。
5. 在画面/旁表只展示 native 返回的 actor/target base、network、total 与 actual ratio。
   Q100000 只做显示单位换算，ratio 直接展示原生 `actual_power_ratio_raw`；
   不自行从士兵数合成，不称作胜率，也不把军力优势等同合法成本可付或决定开战。
6. 收 S2 与结束 mark。S0/S1/各 query/S2 的暂停、日期、角色及 revision 全部匹配时，
   才标为同一帧两目标对照。若发生新 publication，保留各段各自绑定并重取未完成的只读段；
   不跨帧剪成一个排序池。回到同一地图画面结束，不把此案例称为自然 AI 决策重现。

可用旁白边界：“这些是原生程序对当前目标返回的合法性和军力值；这次是我们主动读取它们。
原生 AI 还要经历候选评分与选择，不能从这张比较表直接推断它会宣谁。”

## 当前局已有战争时的有限延伸

若 `ck3_get_war_state()` 真实返回 active war，再为同一 W 建立独立段落，不为接续而假定 Robert 已在战争中：

1. 从本帧 allied/enemy/public-army rows 选真实 U，读取 strengths、actual-contact；
   v3 的 P/E/双方 ordered IDs 必须来自 exact contact/route 证据，不凭地理或军旗猜 side。
2. 已存在 active Combat 才读 battle-control/transition。对 `controllable=false` 且实际具有 AI membership 的 U，
   可读 reinforcement；无 membership、无 asking、无 assignment 各自按 typed 返回记录，不能为拍成功反复扩大天数。
3. owner 另行决定自然时间推进时，记录每次显式操作及新 snapshot；
   下一暂停点继续同 C/U/W，终局后读 terminal journal、War options/score。
   同 War 分数变化与同 Combat 结果要各有绑定，不把相邻画面等同唯一因果。
4. 和平先只读 options；非 claim CB 的 terms unsupported 原样保留。
   如日后明确执行和平动作，完整保留发送/收件人 response/war disappearance，另标“操作者发起”。

可用的**写入**工具确实存在，但不属于 CASE-R：`ck3_declare_war(declaration_id, expected_revision)`、
`ck3_raise_troops_default(expected_revision)`、`ck3_move_army(army_id, target_province_id, expected_revision)`、
`ck3_offer_white_peace(war_id, expected_revision)`、`ck3_surrender_war(war_id, expected_revision)`。
必须只用新查询返回的 token/ID 及其原生合法性；响应 ACK 仍要后置读回。
时间/暂停使用已注册 `ck3_execute_step(step, expected_revision)`，step 从本次 advertised action steps 选取，
不在本文编造单独的 pause/resume MCP 工具名。

## 留档与执行后填写

本单不预填完成状态。执行后另存：完整 run-ID、profile/source hash、DLL/EXE 身份，
每次 request/response、首末 snapshot、query sequence、ID 来源、实际日期、
raw 录像/截图 hash、timeline/marks、可用 clean span 与失败段理由。
原始画面、机制数值、操作者动作分别写明来源。只有实际取得且审看的段落才进入影片，
不能以工具注册、历史 live、prepared 操作单或空 marks 宣告本次取材完成。

已有 `capture-preparation-r1/open-kaishek.json` 的 syntax-only 预验作为前置记录复用，未重复运行；
其 parser 只覆盖设置/规则/教程文件，不覆盖本次 native evaluator。当前 R0004 的真实分配/预检来源是
`capture-live-live-r4c/live-run-identity.json` 与 `preflight.json`；这些来源不预言 HUD 或查询会成功。

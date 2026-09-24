# 第 1 集候选主案：西西里同一战斗逐日回读

状态：2026-09-24 新增原版实机证据；**整场胜率与模拟器 fidelity gate 仍未通过**。本页只记录一场实际发生的战斗，不把它的一次输赢转换为概率。

## 身份与原始材料

- 游戏：纯原版 CK3 `1.19.0.6`，EXE SHA-256 `2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86`；Steam 离线模式，独立 profile。
- 原始战争存档：SHA-256 `74D43B27BB9E13ED6431E3CBB7F38982B3AF6622DD6A445E17FA1DC668A9D789`，由原生 `save-checkpoint` 回执绑定。新会话只复制该存档，没有复制旧 driver history。
- 接战时刻不可变存档：`D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-002\contact-combat-16777218-raw53146248.ck3`，SHA-256 `45CCE7E9A7E505C878F661333DE30D6B459DA638259A9E99990A226CE564245F`；同目录 `ck3-output/interactive-requests-responses/065-save-contact.json` 是原生保存回执。
- 逐日原始请求和完整响应位于同目录 `ck3-output/interactive-requests*/`；离线逐项核验索引是 `original-battle-r1-verified.json`。该索引绑定 31 天 `snapshot/control/transition/advance` 响应及终局响应的 SHA-256，不代替原始 JSON。
- 两段连续桌面录像分别为 `gameplay-precontact-r1.mkv`（900 秒，SHA-256 `E3B39A2AF11307AB32EEDB5E2E464E60C8B228D1B79B39F1A7AD546BB75AD3AC`）和 `gameplay-precontact-r2.mkv`（900 秒，SHA-256 `0E7699911B05EC54ACC852C6FCB31CB77E32D1DE5BCA8BA2A6FD054C3903589F`）；均为原始 1024×768/30fps 桌面采集，ffprobe 可读。镜头采用前须再次按原片 PTS 与游戏日期裁出 clean span，不能把整段 15 分钟都称为有效实机画面。

## 原版观察

同一战争 `WarID=4`、同一战斗 `CombatID=16777218`、省份 `2633`。`raw53146248` 接战时，原版 UI 显示玩家一侧 1288、敌方 330；原生兵团 `current_fighting_raw` 合计分别为 `128800000` 与 `33000000`（Q100000），身份与人数一致。战斗 side0 是敌方进攻者，side1 是玩家防守者；初始最终战宽为 728。

从接战到结果，连续 31 个战斗日的原生暂停回读日期严格每次增加 24 raw，无缺口，所有回读仍指向该 CombatID。第 1–3 天是 maneuver，第 4 天进入 main，第 28 天进入 pursuit；第 32 天 `raw53146992` 的被动终局 journal 确认 `normal_result`，winner 为 side0。玩家军队 18 脱离旧 CombatID 并处于 retreating 状态，旧战斗对象已从活动存储移除，战斗结果对象仍可解析。

| 战斗日 | 敌方 side0 当日新增军队 | 当日参战敌军总数 |
| ---: | --- | ---: |
| 1 | `16777221` | 1 |
| 2 | `16777231`、`27` | 3 |
| 12 | `22` | 4 |
| 22 | `28` | 5 |

第 32 天的原版终局回读记载 battle warscore：`WarID=4`，玩家作为战争进攻方的分数增量为 `-5000000` Q100000，即 -50；随后的战争快照总战分为 -50。**战斗 side0 的“进攻者”和战争进攻方不是同一个身份**，不能把 `winner_raw=0` 误读成玩家赢。

逐兵团 `current_fighting_raw` 与 control 的 `derived_current_fighting_raw` 一致。部分主阶段日的 side-level `stored_current_fighting_raw` 与逐兵团当前合计不同，control 明确给出 `stored_current_matches_derived=false`；剪辑展示日末人数时应使用标明来源的逐兵团合计，不把 side-level 暂存值混作同一时点人数。这个现象尚需原版 transition 时序对拍解释。

## 独立回放的阶段追踪与边界

第二次独立会话 `D:\workspace\ck3_native_war_ai_promo_work\episode01-full-edge-attempt-004` 从上述不可变接战存档启动，使用单独构建的研究 bridge（DLL SHA-256 `EB643577E0DE6214582A667B3C6C52DB712CA75E46374BECB9DB5C36204F67E7`），在第 4–27 日分别保存不可变日初 checkpoint、执行恰好一天并保全 `experimental-combat-phase-event-trace-managed-v1` 的 BEGIN/FINISH 回执。24 次追踪中 19 次给出七边界的 `bounded_trace_available`；第 11、21 日发生增援加入，第 15、16 日及第 27 日发生人员/阶段边界变化，5 次严格保留为 `trace_unavailable`。**所有 24 次的 `full_mutable_transition_bundle_complete` 与 `original_trace_ready` 都是 false**；19 次 bounded 只证明该桥声明的有界采集条件，不证明完整 phase effect 或模拟器对拍。

回放阶段事件账本在第 5、7、9、15、16、19 日各新增一条，其中第 15 日账本写入 `knight_killed_by_enemy`。第 5 日的 `knight_wounded_by_enemy` 账本指向角色 `36303`，第 6 日追踪里其 prowess 从 8 降到 6；原版脚本该分支还包含受伤、对手威望/勇武机会和可能的称号荣耀。当前桥没有完整读取伤势 trait、威望、延迟事件和回调写集，因此只能把它标成**事件与后续状态相关的候选回流**，不能单凭账本或 prowess 变化宣布全部效果已复刻。第 15 日的“阵亡”账本也不能代替人物死亡状态及脱离参战名单的闭环证明。

更关键的是，独立回放的日初数值只在第 4、5 日与第一条原始时间线吻合，第 6 日起分叉。例如第 6 日原案 side0 当前兵力为 `186071277`，回放为 `185282077`（Q100000）；第 27 日分别为 `457629639` 与 `457549708`。**同一个存档与 CombatID 不足以证明同一条随机轨迹。** 回放事件镜头必须标为“同存档独立回放”，不能剪成第一条战斗的直接下一日，更不能用它校准第一条原案的逐日残差。两条时间线的逐日值、响应 SHA、事件及 `replay_matches_original_day` 已投影到智能体包内的[共用原版案例数据](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_original_case.json)，文件 SHA-256 `62C70CED2E4E1E355A986C9220F05F59441EE26F14C0EE412D537383413DBF9F`；投影脚本为[project_native_battle_case.py](../../ck3_autonomous_player/tools/project_native_battle_case.py)。该案例文件明确 `planner_usable=false`、`calibrated_win_probability_available=false`，由智能体和宣传片共用同一读取器与身份门禁。

另有在梅西纳战场居中、战斗面板打开后录得的追击到终局原版实机片段 `gameplay-messina-pursuit-to-terminal.mkv`（100 秒，1024×768/30fps，SHA-256 `359BE5CF17D7D838E9A4E1049B0E85CBE5BF9ACF9668B0E43EF467AB4F68D27F`），位于 attempt-004；相应第 28–32 日回读索引 `terminal-replay-d28-d32.jsonl` SHA-256 `B4F8C8D4E2827650E4401E9FBAB34DE62558641A424382A4C460FEDBD261E160`。它属于独立回放，虽同样正常败退、战分 -50，仍须在片中和第一条原始轨迹区分。

### 共用伤亡内核的条件对拍

将独立回放第 4–26 日各自**原版当日已观测出伤**送入游玩智能体的 `apply_main_phase_casualties`，再按 regiment ID 与下一日原版 `current_fighting_raw` 比较。这是原版出伤给定条件下的兵团伤亡内核检验，不是从战前输入独立预测出伤。完整逐日残差与三份回执 SHA 位于[共用对拍报告](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_main_tick_parity.json)，文件 SHA-256 `CE1B40AB72126C905D4B73411FBFB44141A1AA251D6A108575CDA32B019E7497`；重建工具为[compare_native_main_tick_receipts.py](../../ck3_autonomous_player/tools/compare_native_main_tick_receipts.py)。

| 归类 | 源日 | 结果与解释边界 |
| --- | --- | --- |
| 双方主阶段参战兵团当前兵力逐项零差 | 4、5、6、8、10、12、13、16、19、20、22、23、24、25、26（15 天） | 其中第 16 日阶段追踪本身是 RED，严格同时满足稳定参战者和 bounded trace 的只有 14 天。 |
| 个别兵团微小残差 | 7、9、14、17、18 | 每日最多两条，单条最大绝对残差 `181` Q100000；尚不能归零，也不能任意归因于事件或舍入。 |
| 增援改变输入集合 | 11、21 | 第 12、22 日敌军新增军队；若沿用日初旧参战者向量，敌侧大量兵团失配。 |
| 人员/兵团离场 | 15 | `knight_killed_by_enemy` 账本出现，原先 regiment `180` 在次日输入中缺失；完整角色 effect 与离场顺序仍未闭合。 |

这份对拍报告被智能体包持有，并可由视频从同一证据板引用。它支持“给定原版当天出伤和稳定参战名单时，现有伤亡内核多日逐兵团对拍”的窄结论；**不支持**完整出伤生成、事件反馈、增援预测、追击终局或整场胜率。模型决策门禁仍必须逐项等待这些缺口关闭。

### 同接战存档的三次原生回放

2026-09-24 在独立 profile 中进行了有界重复性实验，原始请求、响应、脚本、失败回执、两次原生 restore 生命周期与 session 清理证明保存在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-native-repeatability-attempt-007`。最初脚本在第 32 天错误查询已经移除的活动战斗，收到 RED；修正脚本改查被动终局 journal，保留这条失败记录，没有覆盖此前素材。输入仍是接战日 `raw53146248`、同一 `CombatID=16777218`；本次原生固定 checkpoint 的 SHA-256 为 `ABC37ED58E0ED008C1D627F38E6BA138F728438DDC16F50041576E5368399EDD`。第 1 次是保存检查点后的同会话继续，第 2、3 次才分别从这份**相同 bytes** 的检查点重启原版进程。

三次均连续回读 31 个战斗日，第 28 天进入追击，第 32 天正常结算；原生终局 `winner_raw=0`，玩家位于 side1，三次都是玩家败退并造成战争进攻方 -50 战分。三条**逐兵团当前兵力合计**轨迹两两在第 6 天首次分叉；第 6 天敌方合计分别为 `183703672`、`185282077`、`183966739` Q100000。原生 side-level 暂存兵力与逐兵团合计在这些帧并不总一致，因此对照板不用暂存值冒充战斗人数。绑定原始回执 SHA、逐兵团合计和每次终局的[共用回放数据](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_repeatability.json) SHA-256 为 `5E2D4B1AEE3BD6D64AC48111CD7ED1D8F48B8827D9FEBAB3F04505F3F2C1EF9C`；[只读投影工具](../../ck3_autonomous_player/tools/project_native_battle_repeatability.py)会核对源响应与检查点 bytes。视频的[片用对照板](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/repeatability-board.json)与智能体都经 `native_battle_case.py` 读取同一份数据。

### 阶段事件账本与实际回流的时点

对 attempt-004 的 24 份原始阶段回执再次按 SHA 核验，并把六次战报新增条目的 fire 前后人物核心字段、骑士称号荣耀以及下一次逐日回读分别投影到[共用阶段事件观察](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_phase_event_observations.json)（SHA-256 `94831B16AE56BC050833D7BEE9064170D118F77700DE672A0977E68F47C98AAE`）。[投影工具](../../ck3_autonomous_player/tools/project_native_phase_event_observations.py)拒绝源回执 hash 变化、非追加账本或跨 side 条目；智能体的案例读取器也强制 `complete_effect_feedback_proven=false`、`planner_usable=false`。

六次条目在第 5、7、9、15、16、19 日各一条；每一次对应的 fire 前后，**已捕获的人物核心字段与称号字段没有变化**。这只排除这些字段在该捕获区间内可见的即时改写，不能排除未捕获 trait、资源、脚本变量、回调或稍后的改写。第 5 日条目称 `knight_wounded_by_enemy`，目标角色 36303 在 fire 前后勇武均为 8，下一源日 schedule 前仍为 8、fire 前已为 6；第 15 日 `knight_killed_by_enemy` 的目标 36673 在 fire 后仍未见死亡标记，下一源日 fire 前已有死亡标记且兵团链接改变。第 15、16 日整体 trace 是 `trace_unavailable`，这里只引用零错误、身份与日期相符的局部 fire 成对记录，不提升整日 readiness。

因此战报追加时刻**不等于**效果写集全部生效时刻。跨两次日初/阶段回读的变化与对应条目有时间关联，但还不能单独证明因果、精确回调边界或完整 effect；任何模拟器若在 fire 记录追加时立刻把伤/死效果写入状态，仍需和原版后续读取点对拍。片中可以展示“战报先出现，后续状态再变”的该案实证，不得解说为完整事件模型已经确认。

这些结果证明“同一接战检查点可产生不同的原版逐日数值轨迹”，也证明三条被观察到的轨迹都输了；**不证明回放之间是独立随机抽样，更不等于这场战斗的胜率为 0%**。样本只有一个初始局面、两个真正的重启回放，没有覆盖不同战斗条件；event effect、增援策略与模拟器预测残差也未闭合。数据合同明确 `independent_random_draws_proven=false`、`calibrated_win_probability_available=false`、`planner_usable=false`，不得把 3/3 败退作为自动进攻的概率输入或作为正片百分比。

## 仍未满足的正片与智能体门槛

本案例足以展示“开局 1288 对 330，增援改变了整场战斗并最终败退”的原版观察，也新增了原版事件账本和可用实机追击画面；它**不足以给出原版条件胜率**。下一步须在同一条随机时间线闭合 event effect 写集、增援/脱离/撤退与终局，逐日对拍模拟器，并用不同条件、独立种子的原版战例做概率校准。当前 [`combat-entry-eu-v1`](../../ck3_autonomous_player/src/xar_autoplayer/simulation/combat_decision_contract.py) 计算器和[游玩策略入口](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py)已能接收同一试验向量；没有合格 forecast producer 时保持自动进攻关闭，不能将研究包络的胜率用于实机进攻。第 1 集[导演案](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/director-plan.md)的出片门禁不变。

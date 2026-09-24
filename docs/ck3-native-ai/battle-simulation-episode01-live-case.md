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

### 主阶段出伤缩放的 46 项条件零差

[共用出伤对拍](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_main_outgoing_conditional_parity.json) SHA-256 `E31C81A6C7A65A65704C942DFC1C470C6C30EA41FB8CD769334E8D79CCF41727`，由[只读重算工具](../../ck3_autonomous_player/tools/compare_native_main_outgoing_damage.py)核对第 4–26 日的 control/phase 原始回执 SHA，将智能体 `outgoing_damage_raw` 应用于双方 46 个实测值，**46/46 零差**。每项输入包含原版反制后攻击力、有效优势、战宽及参战人数。优势取同日期 side1 schedule 返回后的有效记录；第 16 日首条记录的捕获标志非零，但该下一条同日期记录为 0，没有借用失败记录。人数取当前有效兵力，不能沿用阶段记录中的上一日缓存；第 11、21 日须计入已观察到的增援，前者还须使用入场后更新的战宽。

进一步从 exact-build stock `common/province_terrain/00_province_terrain.txt`（SHA-256 `922A5B8BA73007B18E95F1CCFCDBE075A03F5DE61CBF8FF8F66698BEDBB3BE3C`）核到战场省份 `2633=forest`，`common/terrain_types/00_terrains.txt`（SHA-256 `39D79AD120BF85B49D6EE8D96FE4D94EDBBABC190A41662DBA8ECA8DE0ACE64E`）给森林战宽系数 `0.9`。智能体新增 `update_combat_width`，用双方当前参战人数、既有 base 战宽历史与该系数逐日更新：第 4 日 `1645/1480`，第 11 日已观察到的增援使之升至 `2467/2220`，第 21 日再增援时 base 仍保留 `2467`。新的[宽度自主复算 + 出伤条件对拍 v2](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_main_outgoing_conditional_parity_v2.json) SHA-256 `967FD94030A39A7408C33D281E814E01C0F1E412B7797F61449F90FAA58F8F00`，23/23 日战宽与原版相等，双方出伤仍 46/46 零差；v1 保留原样。

这闭合的是**已观察到入场时点和参战人数下的战宽公式、以及给定原版反制后攻击力和优势时的主阶段出伤缩放公式**。它没有重建反制后攻击力、优势生成、增援策略或宽度更新被调用的动态时点。第 11、15、16、21 日完整阶段 trace 的 RED 不因局部公式零差而变绿；原案与独立回放仍严格分开。视频[同源出伤板 v2](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/outgoing-damage-board-v2.json)由智能体读取器生成，[v1](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/outgoing-damage-board.json)保留为过程资产；整场胜率和 `planner_usable` 均未开放。

### 两次自然增援的到达日伤亡

第 11、21 源日的完整 phase trace 因增援导致 side 身份变化而为 `trace_unavailable`，但前一日冻结存档、移动快照和下一日的首次有效阶段记录可以独立配对。[共用增援日投影](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_join_day_casualties.json) SHA-256 `C51A17070A66729C00B1BB1ADB40821CB61CAC1F7DF11155CE25FE0C5152EA72` 核对了所有源 bytes：ArmyID `22` 到达第 12 日，其 12 个参战兵团的入场前存档当前人数合计 2560，到达日阶段回读为 2521.99061，软/硬伤亡分别为 26.03650/11.97289；另 1 个未参战骑士兵团没有战斗伤亡。ArmyID `28` 到达第 22 日，其 5 个参战兵团从 1058 到 1049.99308，软/硬伤亡为 5.48476/2.52216。17 个参战兵团逐项满足“入场前存档当前数 = 阶段起始数”和“起始数 − 到达日当前数 = 软伤亡 + 硬伤亡”，每项伤亡均大于零。两次移动前 `in_combat=false`、目标梅西纳；一步日期推进后 `in_combat=true`，同 CombatID。

因此至少这两次自然加入在**到达的同一日推进中已经受伤**。这比仅见“下一日参战名单增加”更强，但还不能推出所有地图接触情形的 manager 全局调用顺序；两次到达源日整条 trace 的 RED 保持原状，也不能将独立回放拼接到首条原案。片用摘要为[同源增援板 v3](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/join-day-board-v3.json)；智能体模拟器应允许入场当天伤亡，实际调度仍须通过其他时序夹具对拍。

进一步把原版实测出伤和这两次已观察到的入场名单送入智能体现有的 `apply_main_phase_casualties`，得到了[初次条件对拍](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_join_day_kernel_parity.json)：第 12 日新增兵团 12/12 精确，整侧 37/38 精确，原有兵团 `220` 的 `current_raw` 残差为 `+214`（Q100000）；第 22 日新增兵团 5/5、整侧 42/42 精确。第 11 日原版有效阶段记录证明，兵团 `220` 在 side0 schedule 前的有效韧性已从较早快照的 `7400000` 变为 `3700000`。用这份**原版调度前韧性**作为条件输入后，[第二次条件对拍](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_join_day_kernel_parity_v2.json)分别为第 12 日 38/38、第 22 日 42/42 精确。模拟器尚未自主计算该韧性刷新、增援策略或每日出伤；两天源 trace RED 保留，整场胜率仍不可用。

### 反制后攻击力 R14：同日输入与阶段回执配对

第三条**独立回放** `D:\workspace\ck3_native_war_ai_promo_work\episode01-paired-counter-trace-attempt-010` 从 attempt-004 的第 4 日不可变存档启动；第 4–26 日逐日先保存 checkpoint，再在**同一暂停日期与同一进程**读取原版 v3 的兵团类别、反制目标和双方 owner 修正，然后推进一天，读取原生阶段追踪的反制后攻击力 R14。原始 v3、BEGIN/FINISH、存档和逐日 journal 均保存在该 attempt。[只读重建工具](../../tools/project_native_paired_counter_parity.py)逐个核对存档及两类回执 SHA，并调用智能体内核重算；[共用报告](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_paired_counter_r14_parity.json) SHA-256 `18B9BC086BAFB4423262EF01BE00B71D19CBA461A4483795E514C710992E7358`，片用[反制板 v1](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/counter-r14-board-v1.json)由智能体的同一读取器生成。

v3 的 `current_soldiers` 是军队现存人数口径；战斗继续后，直接以它计算 R14 会把暂时退出当前交战的软伤亡兵员也算进去。第 5 日即能观察到高估。智能体因此新增 `post_counter_attack_from_fighting_entries_raw`，要求传入阶段边界的逐兵团 `current_fighting_raw`（Q100000）和当时**已刷新**的有效攻击属性，再按当前双方类别兵力重算反制系数；缺少完整属性表或兵团身份不合时拒绝计算。第 5 日的[原版配对回归夹具](../../ck3_autonomous_player/tests/fixtures/combat/episode01_messina_paired_day05_r14.json)与单元测试验证了两种人数口径的差异。

| 配对回放源日 | R14 条件对拍 | 限制 |
| --- | ---: | --- |
| 4–10、12–20、22–26 | 42/42 双方零差 | 给定原版当日参战人数、已刷新攻击属性与日初参战名单；第 26 日整条阶段 trace 仍是 RED，只使用捕获标志为 0 的局部边界。 |
| 11 | 0/2 | 当日军队 22 插入后才计算 R14；v3 与局部阶段记录仍是增援前名单，整条 trace `trace_unavailable`。 |
| 21 | 1/2 | 当日军队 28 插入；玩家侧零差，敌侧旧名单少了新军的攻击量，整条 trace `trace_unavailable`。 |

因此 23 日共 **43/46 个局部 R14 数值零差**，但它是“原版当前战斗状态给定时”的内核验证。第 11、21 日还需把入场兵团与反制时点接入同一来源；人物伤势导致的属性刷新仍由原版边界提供，优势的日内生成、事件完整效果、后续胜败与概率校准也未自主生成。新回放第 6 日数值与 attempt-004 不同，不能把两条时间线混剪或混用于逐日残差。报告维持 `forecast_ready=false`、`planner_usable=false`。

### 同接战存档的三次原生回放

2026-09-24 在独立 profile 中进行了有界重复性实验，原始请求、响应、脚本、失败回执、两次原生 restore 生命周期与 session 清理证明保存在 `D:\workspace\ck3_native_war_ai_promo_work\episode01-native-repeatability-attempt-007`。最初脚本在第 32 天错误查询已经移除的活动战斗，收到 RED；修正脚本改查被动终局 journal，保留这条失败记录，没有覆盖此前素材。输入仍是接战日 `raw53146248`、同一 `CombatID=16777218`；本次原生固定 checkpoint 的 SHA-256 为 `ABC37ED58E0ED008C1D627F38E6BA138F728438DDC16F50041576E5368399EDD`。第 1 次是保存检查点后的同会话继续，第 2、3 次才分别从这份**相同 bytes** 的检查点重启原版进程。

三次均连续回读 31 个战斗日，第 28 天进入追击，第 32 天正常结算；原生终局 `winner_raw=0`，玩家位于 side1，三次都是玩家败退并造成战争进攻方 -50 战分。三条**逐兵团当前兵力合计**轨迹两两在第 6 天首次分叉；第 6 天敌方合计分别为 `183703672`、`185282077`、`183966739` Q100000。原生 side-level 暂存兵力与逐兵团合计在这些帧并不总一致，因此对照板不用暂存值冒充战斗人数。绑定原始回执 SHA、逐兵团合计和每次终局的[共用回放数据](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_repeatability.json) SHA-256 为 `5E2D4B1AEE3BD6D64AC48111CD7ED1D8F48B8827D9FEBAB3F04505F3F2C1EF9C`；[只读投影工具](../../ck3_autonomous_player/tools/project_native_battle_repeatability.py)会核对源响应与检查点 bytes。视频的[片用对照板](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/repeatability-board.json)与智能体都经 `native_battle_case.py` 读取同一份数据。

### 阶段事件账本与实际回流的时点

对 attempt-004 的 24 份原始阶段回执再次按 SHA 核验，并把六次战报新增条目的 fire 前后人物核心字段、骑士称号荣耀以及下一次逐日回读分别投影到[共用阶段事件观察](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_phase_event_observations.json)（SHA-256 `94831B16AE56BC050833D7BEE9064170D118F77700DE672A0977E68F47C98AAE`）。[投影工具](../../ck3_autonomous_player/tools/project_native_phase_event_observations.py)拒绝源回执 hash 变化、非追加账本或跨 side 条目；智能体的案例读取器也强制 `complete_effect_feedback_proven=false`、`planner_usable=false`。

六次条目在第 5、7、9、15、16、19 日各一条；每一次对应的 fire 前后，**已捕获的人物核心字段与称号字段没有变化**。这只排除这些字段在该捕获区间内可见的即时改写，不能排除未捕获 trait、资源、脚本变量、回调或稍后的改写。第 5 日条目称 `knight_wounded_by_enemy`，目标角色 36303 在 fire 前后勇武均为 8，下一源日 schedule 前仍为 8、fire 前已为 6；第 15 日 `knight_killed_by_enemy` 的目标 36673 在 fire 后仍未见死亡标记，下一源日 fire 前已有死亡标记且兵团链接改变。第 15、16 日整体 trace 是 `trace_unavailable`，这里只引用零错误、身份与日期相符的局部 fire 成对记录，不提升整日 readiness。

原始回放还保留了事件前、后的同战斗存档。使用 [Rakaly CLI](https://github.com/rakaly/cli) `v0.8.19`（官方 Windows zip SHA-256 `343E2C33869B1EC82E4AB018D1BB6936CC68B63146F99F426939F4D76106710D`；解码 exe SHA-256 `E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D`）在外置 attempt-008 只读解码六次事件前后的 11 份已冻结 `.ck3`，各次命令均退出 0。[共用存档回流投影](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_phase_event_save_feedback.json)（SHA-256 `42C495789167F27F330D40FE657CEE359C02AF5FF217DFCB16E9A2971ECAC130`）逐一绑定原始存档 SHA、解码文本 SHA、`traits_lookup`、CharacterID 和事件回执。第 5 日事件前存档中 36303 没有伤势；与事件 `native_date_raw=53146368` **同日期**的第 6 日初存档已有 `wounded_1`，但当时原生 core 回读勇武仍为 8，到再下一个 fire 入口才读到 6。第 15 日事件前存档中 36673 存活；与事件 `native_date_raw=53146608` **同日期**的第 16 日初存档已有 `dead_data`，日期 `1066.12.19`、死因 `death_battle`、击杀者 32716，与战报右侧人物相符。

六条账本中五次为 `knight_wounded_by_enemy`，五名目标在各自同日期后续存档都新增 `wounded_1`；第 15 日另一次为上述击杀。右侧对手的同日存档变化如下，威望指可回读的货币数值；累计威望在前后都存在时也与货币增量相同，第 16 日对手缺字段，不作累计威望断言。

| 源日 | 目标状态 | 对手 CharacterID | 威望货币增量 | 基础勇武增量 | 累计威望 |
| ---: | --- | ---: | ---: | ---: | --- |
| 5 | `wounded_1` | 34867 | +75 | +1 | +75 |
| 7 | `wounded_1` | 54140 | +37.5 | +1 | +37.5 |
| 9 | `wounded_1` | 34867 | +37.5 | 0 | +37.5 |
| 15 | `death_battle` | 32716 | +300 | +1 | +300 |
| 16 | `wounded_1` | 54144 | +75 | +1 | 存档字段缺失，未断言 |
| 19 | `wounded_1` | 35124 | +75 | 0 | +75 |

第 9 日受伤目标 `54144` 的 RegimentID `220` 又提供了[后续兵团属性回流链](../../ck3_autonomous_player/src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_messina_phase_event_regiment_feedback.json)：同日后续存档新增 `wounded_1`；第 9 日 fire 前、第 10 日 schedule 前、第 10 日 fire 前、第 11 日 schedule 前，人物勇武 `4/4/2/2`，对应兵团有效韧性 `7400000/7400000/7400000/3700000`。更早 control 快照沿用旧韧性，造成第 11 日条件伤亡对拍的 `+214` 残差；送入原版 schedule 前韧性后精确。这个时序是同一独立回放的观察，不证明受伤条目是数值变化的唯一原因，也不把第 11 日整体 RED trace 提升为 GREEN。

原版 `00_knight_phase_events.txt` 的相应分支调用 `add_prestige` 与 `knight_increase_prowess_chance_effect`；这些存档数值与调用相容，未逐指令证明唯一因果。勇武增量并非每次都出现，模拟器不能把这个机会效果硬编码成固定 +1。

所以“条目出现后，伤势/死亡到下一游戏日才生效”这个说法过宽：**同日期存档已保存伤势 trait 和死亡状态**。当前实证只定位到“fire 局部 core 读数未变，但同日期后续存档状态已变；勇武缓存的可见下降更晚”；它捕获了六次对手威望与基础勇武的存档变化，但没有定位完整 effect 回调、荣誉/脚本变量等全部写集或排除同日其他因果。模拟器必须分别对拍 trait/死亡状态和其对下一次战斗数值输入的刷新时点；本片仍不能报整场胜率。

这些结果证明“同一接战检查点可产生不同的原版逐日数值轨迹”，也证明三条被观察到的轨迹都输了；**不证明回放之间是独立随机抽样，更不等于这场战斗的胜率为 0%**。样本只有一个初始局面、两个真正的重启回放，没有覆盖不同战斗条件；event effect、增援策略与模拟器预测残差也未闭合。数据合同明确 `independent_random_draws_proven=false`、`calibrated_win_probability_available=false`、`planner_usable=false`，不得把 3/3 败退作为自动进攻的概率输入或作为正片百分比。

## 仍未满足的正片与智能体门槛

本案例足以展示“开局 1288 对 330，增援改变了整场战斗并最终败退”的原版观察，也新增了原版事件账本和可用实机追击画面；它**不足以给出原版条件胜率**。下一步须在同一条随机时间线闭合 event effect 写集、增援/脱离/撤退与终局，逐日对拍模拟器，并用不同条件、独立种子的原版战例做概率校准。当前 [`combat-entry-eu-v1`](../../ck3_autonomous_player/src/xar_autoplayer/simulation/combat_decision_contract.py) 计算器和[游玩策略入口](../../ck3_autonomous_player/src/xar_autoplayer/strategy.py)已能接收同一试验向量；没有合格 forecast producer 时保持自动进攻关闭，不能将研究包络的胜率用于实机进攻。第 1 集[导演案](../../promo/ck3_native_war_ai/episode-01-battle-win-probability/director-plan.md)的出片门禁不变。

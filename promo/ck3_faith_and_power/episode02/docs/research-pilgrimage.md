# 信仰引擎二期 R4：普通朝圣的来源、决策与施工状态

2026-10-20 后续接入：[游玩智能体研究入口](../../../../docs/ck3-native-ai/faith-and-power-episode02-agent-reference-12004.md)汇合本页静态知识、当前接口和后续实机边界。本文原始“当前／尚未实现”以各段记载时刻为准；新增接口与场次不追认早期资格，普通 auto 尚未自动消费本研究。

普通朝圣可以组织成约七分钟的一条决策链：同一笔预算，近处合法圣地能否解决这次目标，远处目的地多出的收益是否值得额外费用、风险与离境时间。源码已经支持这条讲解；**当前尚缺完整规划器总费、一次合法出发和抵达—阶段结束—归返的实机闭环。** 现有有限只读候选只解决当前玩家主办朝圣活动的身份，不包含开窗、付费、推进或奖励验收。

本文来源观察为 `machine_id: 4-8e1c2f1861`，使用 `tools/ck3_live_run_id.py machine` 于本轮重新读回；关键实际资源于 `2026-10-19T19:54:22Z` 前后复核。研究基线为 Root 冻结的 `17f7fb69cdae7fd67afdd385f5b1e922d17e2a0c`。Root 于 `2026-10-19T18:54:20.430481+00:00` 报告同机安装为 Steam build `25734779`、rawVersion `1.20.0.4`，EXE SHA-256 为 `98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518`。这项安装态观察不是运行时绑定、新鲜 Steam 离线图或朝圣业务通过。

本轮仅写本文；没有修改业务源码、执行 Git、编译、操作屏幕/游戏或准备存档。下述候选状态截至各自交付时刻；Root 后续应用与资格应追加独立证据，不能凭本文追认。

## 1. 当前 1.20.0.4 来源绑定

游戏相对路径均以本机实际安装根 `C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game` 为基准；行号从 1 起。以下文件在本轮逐个重新读回 SHA，与原研究审计相符；只绑定这些实际字节，不宣称全安装纯净性或其他机器同版文件相同。原研究审计为外置 `episode02/capture-b1-a01/research/pilgrimage/SOURCE-AUDIT.json`，SHA-256 `5d50c7867c978ddce34234e93d49548212a36ee1e68ff69d38141f1919a2148c`。

| 编号 | 实际游戏文件 | SHA-256 |
| --- | --- | --- |
| G1 | `common/activities/activity_types/pilgrimage.txt` | `24153043485b035cb0477de7306649027cb68c039e4a9d903776eddd870d8b9f` |
| G2 | `common/scripted_effects/00_pilgrimage_effects.txt` | `4374f9917e58a98e7b51ece5848d3540534f39fe60152f48342a79c3b2dc6f80` |
| G3 | `common/script_values/50_pilgrimage_values.txt` | `643414d0d4fe87118f42cea52ded3e3f1cca326894bdba944679e7595cbbf0c9` |
| G4 | `common/script_values/00_activity_values.txt` | `0b5c2da145cf0d2311aba8525c7decfc865d0539b81acdf3974ed74a68b37c92` |
| G5 | `common/script_values/pam_values.txt` | `458d1bd882e8854005e3158339fca343177cff13eac7f83cb5877a8a37171965` |
| G6 | `events/activities/pilgrimage_activity/pilgrimage_events.txt` | `900959b36dfc121bb0e785733723ea7e70e3931e7377a16206ba98eba555be06` |
| G7 | `common/on_action/travel_on_actions.txt` | `cd40f30a9280ea9ba656b59005201550f3991afd646fd686d7474657b1b1ff70` |
| G8 | `common/on_action/activities/pilgrimage_on_actions.txt` | `fdf71f074882f94eb3df497a1ddb2cb9a95fb13e973aebf25d4c3569729ee354` |
| G9 | `gui/window_activity_list.gui` | `3750766862563fb413847848641ae16856f618feed4c9906c2be84472419fd3d` |
| G10 | `gui/window_activity_planner.gui` | `2f18263ad5be79bfc10c9bc33fd1ccff1e41a0be2bafc7d19e4f9cf0b58feb54` |

下文 N 编号指仓库生产来源，路径根为 `ck3_autonomous_player/native_bridge/`。这些是 `17f7fb…` 的来源绑定；Root 合入后需重新固定新源码和 DLL，不能把旧 SHA 当新构建资格。

| 编号 | 仓库相对文件与相关行 | SHA-256 |
| --- | --- | --- |
| N1 | `src/activity_hosted_identity_v1.cpp:254–285,335–439` | `cce4156f7b8261f38ebab0075be518f46b45d0b4237e29f663c4ca0cdf576978` |
| N2 | `src/ck3_12004_religion_context_addons.cpp:118–186` | `e0ba99a34214b07efb832136af60f75cd80c3f9a9f24a2856a5735ca99bb6dc4` |
| N3 | `src/activity_cost_slot12_passive_v1.cpp:48–65,176–191,245–255` | `868ef7fd1405cbace04f95ef7f83ce1c9313b514e177999f69378aadae0f6979` |
| N4 | `src/activity_stage5_feast_full_cost_v1.cpp:61–85,105–124,135–141` | `daab791aa7ad27071e965e9c6853d1727f4da96cb3999b7e37530b2088d75ae7` |
| N5 | `include/xar_bridge/ck3_12004_activity_migration_v1.hpp:1–120` | `7526087fa26afa86a3c1c2230da3453d9281af74ecf9020f94e947631c16f97d` |
| N6 | `src/ck3_12002_feast_planner_native.cpp:106–203,235–263,285–328,347–438` | `f7b31076456c220ec12d30cfcd69da21dd2088477592015b254690372d026452` |
| N7 | `src/activity_feast_stage5_start_v1.cpp:210–267` | `41ad0af352f6ad4d6237eac1cad159e7e24771c1bf163730e2ea185173138205` |
| N8 | `src/ck3_12003_activity_phase_dates.cpp:27–56` | `d328adad17534d7eb25a53a383b93b03808d97624909e8f2f13944fdf0e607e5` |

## 2. 可以直接复用的普通朝圣结论

### 先核人物当前礼仪与实际选项

G1:37–129 的规划条件包括当前可用成年人、活动未冷却、**当前 Rite** 未禁止朝圣、当前 Faith 存在圣地等条件；最终还应读取原生 CanPlan。目的地受 G1:220–298 约束：五年内相同目的地记忆会阻挡；非冒险者不能去自己的首都；特定摄政离境限制另加。Hajj 在特殊类型为 `pilgrimage_type_hajj` 时只允许麦加（G1:256–265）。这些地点条件不能由“它是本信仰圣地”替代。

G1:1392–1456 对虔诚与世俗类型的判断可以明确写成：

- `pilgrimage_type_pious` 默认候选：当前 Rite **不要求** `mandatory_hajj`，**或** 人物已有 `hajjaj`。
- 若当前 Rite 要求 `mandatory_hajj`，pious 和 worldly 的合法性都要求人物已有 `hajjaj`；否则该项不额外阻挡。
- 默认表达式、AI 权重与当前实际选中项是不同观测；CanPlan、CanSelect 和 Stage5 CanStart 也不能互相替代。

因此本章不能用未完成朝觐的阿拔斯角色强行做普通 pious 朝圣。应优先核 D1 基督教独立实验臂，或选择本来已有 `hajjaj`、实际符合原版条件的角色。不能添删特质、修改礼仪或绕过条件来凑镜头。

`special_type` 的 pious/worldly/Hajj 与忠诚、规模等配置栏是不同选项。首个最小实验只做真实默认为 pious 的合法配置；若人物默认或实际选中不匹配，先保留拒绝和真实起点，不据默认名称猜选中了什么。

### 普通奖励分在抵达、阶段结束与归返

| 时点 | producer → caller → consumer | 可以讲到的结论与最低后态 |
| --- | --- | --- |
| 抵达并激活阶段 | G1:2380–2409，host 分支先解除 `promised_pilgrimage_to_clergy_modifier`，非 Hajj 安排三个月后推进阶段；G1:2459–2489 分流 obligatory、Hajj 与普通抵达事件 | 三个月是普通目的地停留安排，不能叫全程三个月。解除朝圣承诺与获得特质应分开读回。抵达分支不同，不能保证每次显示同一个事件。 |
| 一般抵达事件选项 | G1:2486–2488 → `pilgrimage_arrival_events`；例如 G6:9059–9104 的 `pilgrimage.4001`，option 的 G6:9099–9100 调用 `give_pilgrim_trait_or_xp_effect` 与抵达压力效果 | 要保存实际事件实例/定义与选择前后 trait/XP、压力和资源。只见地图位置已到不能宣称这些选项效果都已到账。 |
| 普通阶段结束 | G1:2544–2579 的 `on_end` → G2:1301 起归档表现 → 触发 `pilgrimage.7000` → G2:55–91 的 completed log；普通分支 G2:73–85 调用 G2:1136 起 `give_pilgrimage_reward_effect` | 普通主奖励在这个真实 effect 链执行。G1:2906–2907 也明确指出结论/奖励在 phase `on_end`。G2 顶部仍有旧 `on_complete` 注释，解释应服从实际调用者。 |
| 结论窗口 | G6:15091–15093，7000 普通 a 选项使用 `show_as_tooltip = { pilgrimage_completed_log_entry_effect = yes }` | 同名 effect 在此仅展示 tooltip，不能算又发了一次主奖励。其他特殊选项仍按自身效果另核，不能把整个事件都说成无效果。 |
| 活动完成、记忆与冷却 | G1:2906 起 `on_complete` 设置后续归返变量/记忆；G1:3075–3091 给完成记忆补目的地和五年 holy-site cooldown | 保存完成记忆与冷却后态；不能拿奖励窗口出现代替活动全部生命周期完成。 |
| 归返 | G7:1466–1475 的旅行完成 `first_valid` 先尝试 9010、再 9001；9001 自身 trigger 在 G6:15187–15197，后续包含旅行生活方式检查与清理 | 不保证每趟都显示 9001；9001 也不是同一笔主虔诚在回家时统一再发。归返地点/旅行状态与活动终态分别确认。 |

主虔诚结算 G2:516–627 有严格顺序：距离档基础 → 忠诚设置倍率 → pious 表现倍率 → 特质/规模等追加值 → 特定朴素礼仪倍率 → 普通圣地条件的 `×0.5` → 邦联最终倍率。G2:610–619 检查的是本 Faith 在目的县存在 `is_eminent = no` 的圣地；同县多个圣地的关系不能省略，也不能把 `×0.5` 套到所有独立额外奖励。G2:1301–1335 的 pious/Hajj 表现为 `>=75`、`[50,75)`、`[25,50)` 与其余四档。

精神满足度走 G2:1167–1168 → G2:1191–1206 → G5:2177–2178：当前 Rite 有 mandatory pilgrimage 教义 **或** mandatory hajj 教义，声明变化为 `+10`；否则 `+5`。这是源码声明值，当前封顶、背景事件和实际净变化仍需读回。可花虔诚、奉献经验、满足度、trait/XP 不是一个数；奉献经验应使用原始 `current_devotion_total_raw` 前后值，不能拿等级跳变代替总增量。

本章不必先复原完整 Hajj 事件链、全部朝圣分支或多次王朝传承矩阵。先用一次普通合法短途行程，把以上时点讲清楚。

## 3. Full cost：优先消费原版规划器的实际报价

G1:865–900 的活动基础费分币种：Gold 分支是“没有 treasury **或** 非 theocracy”，Treasury 分支是“theocracy **且** 有 treasury”；另有特定头衔折扣。G3:286–441 继续按时代、承诺/修正、传承、家族、法令、居所与当前 Rite 等动态条件计算；独立 `if` 可以叠加，`else_if` 不可以。G4:772–810 的基础费还受头衔等级、部落和 AI 难度影响。G1:2133–2136 起只有一条 predefined 普通目的地 phase，阶段费用另有距离档；活动选项和旅行设置还需纳入当前配置。

所以 `default_activity_quote`、活动列表 `GetCostDescription`（G9:402）、`ui_predicted_cost` 只能按其实际合同称活动费/预测价，不能更名为当前总旅费。费用距离档与奖励距离档也不能因为都有“长短”就合成一组阈值。

原版窗口的实际消费者很明确：G10:1801–1803 与 2182–2184 为 `ActivityPlanner.AccessCostBreakdown`；最终按钮在 G10:1819–1824 与 2191–2195 使用 `ProgressPlanningStage`、`CanProgressPlanningStage` 及其理由 tooltip。

当前可复用调用链是：

1. N2:118–186 已有 actual .4 朝圣 CanPlan、地点候选、默认活动配置/活动费和出程路线绑定；它没有因此获得最终规划器全旅费资格。
2. 既有 native planner 正常 refresh → passive slot12 observer 留同一 actor/owner/stage/frame/configuration fingerprint 的样本 → Stage5 Gold/FullCost 按真实资源名读取 → typed serializer/Python 消费。N5 已有实际 .4 的 refresh `0x11BA6B0`、正常 slot12 return `0x11B5B3F` 与 named GetCost `0x310ADF0` 映射。
3. **尚缺朝圣有限分支。** N3:48–65、176–191 的 type 检查固定 `activity_feast`；N4:61–85 按宴会四资源键读值，不能由此保证朝圣全部旅行成本已覆盖。改配置后旧 fingerprint 必须立即失效，缺正常 refresh 的成本应为不可用，不能写成 0；也不能主动调用更新冒充被动观察。

最短施工应在这条同源 producer/caller/consumer 加固定 `activity_pilgrimage` 合同，保留原 Feast 合同，证明所读总额含当前活动与旅行设置、资源名映射和实际分项。先比较同一人物两个目的地，固定相同类型、活动/旅行选项、随从和服务。每处目的地分别等正常更新，再记录真实报价、路线/危险/时间、原生最终许可及理由。全程预估与实扣成本应分列：途中事件和月收入会改变钱包，长时间前后钱包差不能直接称成交费。

不必为了首版先建 headless 全旅行服务、任意选项编辑器或提前返程 ETA。N8 的旧 .3 phase-date reader 只承认旧 EXE，并把 Activity `+408` 的低 32 位当 progress date；当前 .4 身份合同保留的是单位未知 completion QWORD。不能只换 SHA，不能相减算天数，也不能拿它当 ETA。

## 4. 已有有限只读候选与最短施工顺序

外置候选基址为本机 `C:/workspace/ck3-faith-and-power-20261017/episode02/capture-b1-a01/research/pilgrimage/`。材料属于该机器当前工作包输入；路径与历史通过都不外推到其他机器。

| 材料 | 截止交付状态与边界 |
| --- | --- |
| `native-work-package-a01.md`、`.sources.json` | 完整施工说明与 21 个源 pin，观察时间 `2026-10-19T19:22:32.177279+00:00`；施工说明 SHA `eacb497658e30c6c274e296d13835ab51f79d0165cb9d15b9929a620ef3686da`，source index SHA `64f38fe48d4cfd6dd063ffd58044b87ec54e8c0bb148f84a3ec5aa7cc41a545f`。 |
| `patch-candidate-a01/` | 六文件候选；patch SHA `0e8cba7f7de27c24834779709b56e611aad50b1d586cf704ba782a0655760f19`。新增 `ck3_query_player_pilgrimage_activities_v1(expected_revision)`、typed native step/serializer、Python strict leaf、Driver 薄转发与 readonly MCP 注册；没有新 callee/RVA/hook。状态为 authored，未编译、未实机。 |
| a01 `INDEPENDENT-REVIEW.md/.json` | 原始独立源码审查为 HOLD_APPLY，仅 R1：既有 focused router test 缺新 serializer spy，可能从 archive 拉入同时包含旧 executor/serializer 的真实 transport TU，破坏 spy 链接隔离。没有运行构建，不能声称实际见过某个 LNK 错误。历史 HOLD 保留。 |
| `patch-candidate-a02/` | 仅一个既有 router test 的增量修正，`2026-10-19T19:39:55.812645+00:00` authored。patch SHA `9e37abb2e28db8e9a12697d8172d95319cb0e140ef6d70e8b2c776447cc96e32`，test SHA `27e60b69e0617dc20d19e8cd7026b0a2a707e07ed06d19908491fe27ebf5f2b8`。新增 serializer spy、.4 只读正例、七项 dispatch 前拒绝；源 pin 与九个 diff hunk 内存重建相符。未编译/执行，不自动把 a01 审查改为 PASS。 |

只读叶直接使用 N1:335–439 的泛型 `ReadActivityHostedIdentityV1`，它本来枚举当前玩家主办的全部类型；N1:254–285 的单目标 reader 和后续 Feast 消费者才固定宴会。候选在既有 owner-thread executor 的旧 mode 分支前调用泛型 reader，随后只保留真实 `activity_pilgrimage`。它不走 `CapturePost`、余额、Feast 客人、outcome 或 Start，避免无关的宴会世界状态要求。

回执保留 full Activity ID/host/type、revision/date、独立 completed/invalidated 观测和 raw completion stamp；stamp 单位未知，观测为零保留 `0`，未知保留 `null`。当前 .4 泛型 reader 对 terminal bytes 缺失/非法会整体 RED，不能许诺一定返回局部 unknown。空列表合法，但 `absence_is_completion=false`；活动从当前 hosted 列表消失也不证明成功完成。没有原生指针出库。

候选仍共用现有 `XAR_CK3_ENABLE_G2_ACTIVITY_FEAST_STAGE5_START_PRIVATE_V1` 编译 gate；它没有自动启用 gate，也没有新增写工具。Python 需显式 query flag 或 case 声明；旧 DLL 不会因为新 Python 名字而具备该能力。a02 沿现有合成 .2 mailbox fixture，仅给真实 router 提供 exact .4 descriptor；这验证的是路由/spy 设计，不能当 .4 原生执行环境或 reader/serializer 资格。

建议按以下最短顺序滚动交付：

1. **身份 A：** Root 独立审阅并应用 a01+a02，冷构建/运行既有 focused target `xar_ck3_12002_activity_feast_router_test`。不要把真实 transport TU 硬加进 spy target。随后做真实泛型 reader → 新 native serializer → strict Python leaf → 已注册 MCP 的生产接缝资格，覆盖非空/空集合、非目标类型过滤、完整 generation、stamp unknown/observed-zero、exact build 与 stale frame 拒绝；再取目标机暂停实读。手写 JSON shape 通过不能替代这条链。
2. **规划器 B：** 有限朝圣 opener → 真实 pious 默认/CanProgress → 原版一次确认 → 一条 predefined row 的 CanSelect/Select → Stage5 总费与理由。N6 已有 selected option `0x11B64A0`、CanProgress/final `0x11B8650`、Progress `0x11B8CB0`、CanSelect `0x11B6F30`、Select `0x11B6C60` 来源；其旧 Feast 读取器固定两条 row，不能只改字符串套给朝圣。
3. **单次出发 C：** 朝圣自己的 final/完整预算/保留金/持久 intent/无 pending 合同，沿 N7 的 actual .4 commit `0x11B8D70` 一次提交。保留现有 Feast guest-route 合同，不放松它冒充朝圣。ACK 只记 pending，独立看到一个新 full ID+host+type 与同日实际扣费才进入 created；未知结果只 reconcile，不再提交。
4. **生命周期 D：** 只增加本章必需的 trait/XP、资源/奉献经验/满足度与事件前后态，按抵达、phase end、活动完成、归返分别取证。无需先穷尽全部活动系统。

## 5. D1 资格待核与最小实验

D1 来源脚本为同机外置 `episode01/revision-v6-20261019/resume-20261019/capture-d1-a05/materialize_d1_static_p17_a01.py:27–30`，本轮重读 SHA 为 `5f60baf973c44f8765b5798154b8cac7604844a66b819bfcd1eabe1ec78f871e`。它指向：

`C:/workspace/ck3-faith-and-power-20261017/episode01/runtime/v5-crossreligion-d1-retry-a02/state/profile/save games/xar_checkpoint.ck3`

来源脚本保存的历史 pin 为 `68,958,787 B`、SHA `62d18fe254d658356671269f194319a316729394da6f38b32da0d503bae1cd58`、actor `31254`、date_raw `53144328`。本轮只重新确认文件存在与大小相符，**没有读/哈希存档 body**；历史 pin 不能写成本轮 body 校验。历史同机 Faith13/Religion8/Rite0 及“罗贝尔”称呼也不是新场当前资格。

新场先核机器/EXE/加载来源/DLL、新鲜 Steam 离线图、独占屏幕与有效容量；再读人物身份、当前 Rite 的 mandatory_hajj/forbidden 条件、pilgrim/hajjaj、成年/旅行/军队状态、钱包、冷却、DLC、实际选项与原生许可。D1 不合法则保存真实理由，换本来合法的独立人物并重新交代起点。

最小实验只比较两个真实目的地，最终做一趟合法普通短途朝圣。可用一个实际首都/冷却拒绝讲边界，无需全拒绝矩阵。关键状态依次为：

| 状态 | 必需观测与失败出口 |
| --- | --- |
| 起点/规划 | 当前人物与 Rite、旧 hosted IDs、实际 pious、真实目的地 row、同设置两处总报价/路线、原生最终许可；成本/资格缺失则 HOLD，不写 0。 |
| intent/出发 | 先持久化 prestate/预算与意图，commit 一次；ACK 与新活动/扣费分开。unknown 不重提；只见新 ID 而实扣不明记 `created_debit_unresolved`。 |
| 抵达 | 保存实际事件实例/定义/显示选项与帧，以及原生选择前后的承诺、trait/XP、压力和资源；不以位置变化代替全部到达收益。 |
| 阶段结束 | 归档表现档、7000 及 piety/devotion/满足度/trait 后态；tooltip 不重复计收入，跨日变化保留月收入和其他事件干扰。 |
| 完成/归返 | 分别确认 full ID 的真实终态、完成记忆/冷却、当前地点/旅行状态；9001 未出现不补造，列表空不判 completed。 |

陌生事件依根规则当场保存实例/定义 ID、双方、帧和显示选项，经原生第一显示项续行，独立读回结果；每批后并行补来源绑定规则。没有原生通道时保留真实失败，不能用 OCR/鼠标替代游戏动作或把 ACK 当已生效。

这条路线可按“目标 → 资格 → 两地预算 → 一次出发 → 抵达 → 阶段收益 → 归返后重新评价”连贯讲解。台词中的具体成交价、实际用时、收益净值和人物结论仍留待实测，不用暂停快照或源码定值填成已拍成功。

## 6. 本轮自审与材料时效

本轮重新匹配原 SOURCE-AUDIT 的 12/12 个实际游戏资源 SHA，窄读了上述条件、费用、GUI 与奖励调用链；D1 仅来源脚本 SHA 和存档 stat；候选只复述其精确交付/审查状态。没有将 .3、其他机器或安装态资格外推到当前 .4 业务。

本文为小型可复用来源说明，新增上限 128 KiB；按 [通用存储策略](../../../../docs/storage-retention-policy.md) 与其 JSON 参数管理。外置候选与审计仍是活跃 R4 合入输入，原工作包复核点为 `2026-10-26T19:02:10.097469+00:00`；合入或否决后复核是否已被更小的仓库来源与回执替代，不因外置历史材料或失败 attempt 自动永久保留，也不据本文删除资产。源码 pin 可长期作为知识引用，但本机文件可读取性、版本、费用、人物条件和运行资格有时效，后续执行须重新观测。

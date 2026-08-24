# CK3 1.19.0.6 原生战争闭环契约

本页定义 `native-headless` 的战争状态、命令和最小决策闭环。该路径只走注入 DLL 的 named pipe；CK3 窗口最小化时仍可运行，也不会回落到 OCR、键鼠或窗口聚焦。

## 2026-08-24 动态目标与军队运行态

- `game.state.war-objectives` 发布 `targeted_title_ids` 和按目标头衔 de jure 层级解析出的
  `war_objective_province_ids`：男爵领目标取自身省，伯爵领目标取首府男爵领省，公国/王国目标递归发布全部
  de jure 伯爵领首府省。planner 严格按“全部 exact 目标 → legacy
  `enemy_primary_default_raise_province_id` fallback”轮转，不按省份数字混排。默认集结省不是 war goal。
- 军队运行态使用 `army_state` / `army_state_code`：`combat=2`、`sieging=3`、
  `retreating=6`、`moving=7`。`combat` 只允许有界接触推进，`sieging` 推进围城，
  `retreating` 先按 30 游戏日正常期限等待；超过期限后仍以有界 `life-advance`
  等 CK3 释放军队，不能在暂停地图上以 `selected_step=null` 自锁。
- 每个 `life-advance` 结果持久保存 `war_progress_before/after`，只含日期、战争分数、
  exact/fallback 目标和双方军队 ID、当前省、兵力、移动目标及运行态。若选定战争中
  玩家军队在目标省从明确的 `sieging` 变为非围城，且分数上升或战争消失，则该目标
  记为已完成并轮转到下一个目标；仅离开围城而未涨分不会误判。全部围城目标完成后，
  planner 恢复选择安全的可见敌军；无敌军时只做有界推进并等待战争状态改变。legacy 快照以此将同省接触限制为
  14 日或两次 probe；一次明显败退（分数下降至少 20）使对应敌军/省进入 90 日冷却。
- `move_deferred` 不再每 turn 重试：同一目标按 7/14/30 游戏日退避。已接受且仍在
  `moving` 的 exact 目标继续 `life-advance`，不重复提交 move；若 exact 运行态已回到
  `regular`/`sieging` 等非行军状态且原生路线为空，旧 move intent 立即失效。

以上状态均来自最小化 CK3 的 native snapshot/command history，不需要 OCR 或恢复窗口。

## Snapshot

顶层 `active_wars` 是数组；每场战争包含：

- `war_id`
- `player_side`: `attacker` 或 `defender`
- `primary_opponent_character_id`: 玩家对侧的 primary war leader；完整 `CharacterID` 已按 generation 重新解析，过渡帧无法解析时为 `null`
- `player_is_primary_war_leader`: 玩家是否正是本方 primary war leader；它是 `enforce-demands` 的必要前提
- `targeted_title_ids`: 该场战争 `CCasusBelli.targeted_titles` 的完整 `TitleID` 数组
- `war_objective_province_ids`: 每个目标头衔按原生 de jure 子头衔顺序展开并稳定去重的可围城目标省。男爵领取自身省；伯爵领取 `+0x240` 首个 de jure 男爵领的省；公国、王国及更高层级递归到全部 de jure 伯爵领并取各自首府。每场战争最多解析 4096 个 generation 匹配的头衔，递归深度最多 8；任一目标的层级出现失效 ID、非法 tier、无首府或越界数组时，该目标的整组省份不发布，但保留 `targeted_title_ids` 和其他可完整解析的目标
- `enemy_primary_default_raise_province_id`: 对方 primary 角色的原生默认集结省；无法解析时为 `null`。它不是解码出的 war goal、首都或真实行军目标；planner 只把它用作明确 fallback，或在进攻方已取得正战争分后的稳定围城启发式锚点
- `player_relative_war_score`: 相对玩家视角的整数战争分
- `allied_armies` / `enemy_armies`: 当前能从原生对象读取的军队数组

顶层 `player_armies` 保留玩家仍在场的可控军队。它不能只从 `active_wars` 临时推导：战争结束后的下一帧必须还能看见残留军队，planner 才能发出解散命令。

军队 canonical 字段为：

- `army_id`, `owner_character_id`
- `soldiers`: 非负整数；当前构建若尚未稳定解析兵力偏移，允许为 `null`
- `current_province_id`: 军队正在生成或销毁、原生对象暂时无省份时允许为 `null`
- `route_province_ids`: CK3 原生“剩余路线”数组，严格保持引擎顺序和重复项；不人为补入 `current_province_id`。每项都必须经当前省份表解析，整条最多 4096 项；任一非法项或越界容器都原子发布 `[]`，绝不发布部分前缀。完整数组只在 paused snapshot 读取；running snapshot 固定为 `[]`，此时表示“未做完整读取”，不能解释成“没有路线”
- `move_target_province_id`: 原生路线最后一个 `SUnitPathProvinceInfo` 的省份；无有效路线时为 `null`
- `move_target_observable`: 仅当 DLL 成功解析了非空原生路线末项时为 `true`；running snapshot 仍保留旧版单次末项读取，不遍历中间项
- `army_state_code` / `army_state`: `1 regular`、`2 combat`、`3 sieging`、`4 embarked`、`5 gathering`、`6 retreating`、`7 moving`、`8 raiding`、`9 bartering`
- `in_combat`: `CUnit` 关联的 `CArmy+0x128` 是否解析到 generation 匹配且存活的 `CCombat`；不是“与敌军同省”的推断
- `retreating`: `CUnit+0x170 > 0` 的直接投影
- `controllable`

Python 会拒绝类型错误的 ID、阵营、分数和数组，同时把早期 fixture 的 `soldier_count` 输入别名统一投影为 `soldiers`；MCP 输出永远使用 canonical 名称。`route_province_ids` 是 additive 字段，但 Python 的 army normalizer 必须显式复制并校验它；仅依赖 `**state` 不会保留军队对象内部的未知键。

## Capability 与具体 step

DLL hello 广告：

- `game.state.war-primary-opponent`
- `game.state.war-objectives`
- `game.state.army-routes`
- `game.command.preview-move-army-N-to-N`
- `game.command.raise-troops-default`
- `game.command.move-army-N-to-N`
- `game.command.disband-army-N`
- `game.command.enforce-demands-N`
- `game.command.query-declarable-wars`
- `game.command.declare-war-N`

Python 根据当前 snapshot 展开为：

- `raise-troops-default`: 有活动战争且没有可控军队时才出现
- `move-army-<army_id>-to-<province_id>`: 可控玩家军队与可见敌军当前省的有效组合；存在 exact `war-primary-opponent` capability 时，也始终展开有效的 `enemy_primary_default_raise_province_id`，即使敌军仍可见
- `disband-army-<army_id>`: 每支当前可控玩家军队各一个
- `enforce-demands-<war_id>`: 每场当前活动战争各一个；planner 只在玩家视角战争分达到 100 时选择
- `query-declarable-wars`: 无活动战争时显式运行一次 CK3 原生 CB evaluator；该查询可能遍历很多角色，绝不放进 250ms heartbeat
- `declare-war-<declaration_id>`: 只从最新查询结果展开。`declaration_id` 是本代运行时的
  `target-cb-index-configuration-index` opaque choice，不是跨版本的 CB ID

占位模板本身不会暴露给 planner。若军队已在目标省或已经以该省为目标，相同 move step 不再广告，避免提交无状态变化的重复命令。

`preview-move-army-<army_id>-to-<province_id>` 只在地图已暂停时运行 CK3 原生路线规划器。成功结果为
`route_preview={status:"available",army_id,origin_province_id,target_province_id,route_province_ids}`；同省目标返回空路线且不调用 A*。它复用 move 的 mode/character/army gates，但只构造、复制并析构 caller-owned 临时路径，既不绑定/调用 apply RVA `0x2248450`，也不进入 command queue。worker-thread 静态审计确认规划调用只写 per-call scratch、未见 world/global/TLS 写；由于引擎没有为 world graph 获取读锁，unpaused 调用明确返回 `requires_paused`。

## 命令后置条件

- raise：等待 snapshot 出现新的可控军队；否则命令超时并返回失败。
- preview move：纯查询，成功只返回完整原生路线，不改变 CK3 revision 或军队状态；Python driver 会把只读结果记录进 `native_command_history`，供下一 turn 的同日期、同起点 freshness 判定使用。任一 ProvinceID 无法解析、路线超过 4096 项或 native builder 失败时整次请求失败，不返回部分路线。
- move：若 DLL 能观察 `move_target_province_id`，等待该军队的目标变为指定省或军队到达；若当前构建不能观察该字段，则以 native `command_result` 的 `accepted/submitted` 为提交成功，返回 `move_submitted`，随后由 `life-advance` 推动行军。
- disband：等待目标军队从顶层 `player_armies` 消失。
- declare：DLL 缓存查询得到的完整 choice；提交时按 target/CB 重新枚举，并要求 claimant、目标 title、configuration 与缓存完全相同。
  Python 等待 `active_wars` 增长；若原生命令已入队但战争尚未投影，返回 `declaration_submitted`，下一 turn 先推进时间而不重复宣战。
- enforce：只允许当前玩家是该战争的 primary war leader；native builder、validator 与 command queue 接受后，Python 等待目标 war 消失。

2026-08-23 实机验证使用 exact-build DLL 与 `native-headless`，在 CK3 窗口 `IsIconic=true` 时显式查询并提交
`declare-war-29097-11-0`。提交后并非只收到 command ack：下一份 native snapshot 实际新增
`war_id=16777290`、`player_side=attacker`、`player_relative_war_score=0`；CK3 进程继续响应且窗口仍保持最小化。
该路径未调用 OCR、截图、键鼠或视觉 fallback。

同一存档中的战争 `16777290` 给出 `targeted_title_ids=[2388]`：目标为
`d_spoleto`，其 `capital=2389`（`c_spoleto`），该郡首府男爵领为
`2390`（`b_spoleto`），最终省份为 `2585`。对手默认集结省 `2543`
属于 `b_firenze`；它确实由敌方持有且可围城，但不是该战争的目标省。
旧投影只返回目标头衔的单个首都省；exact 1.19.0.6 的新投影改走完整 de jure 子树，因此公国/王国战争不再被压缩成一个围城点。

2026-08-24 的后续实机回放补齐了移动与解散。旧 bridge 从 AI/controller 调用点抄入了
`command kind=2` 与 queue flags `7`；这会在玩家军队的控制权校验处被拒绝。连续推进约 49 个游戏日、
更换目标省以及尝试停止集结都不能修复该问题，且运行时字段明确显示军队并未处于集结状态。玩家地图路径实际使用
`kind=1`、queue flags `0x0E`。改为该路径后，窗口保持 `IsIconic=true` 时
`move-army-83886341-to-2586` 返回 `move_submitted`；随后约 35 个游戏日内，同一军队的当前省从
`2619` 变为 `2606`，证明发生了真实行军而非仅收到 command ack。

同日的后续最小化实机验证覆盖了跨 driver 重启的移动意图。driver 从持久历史读回旧的、已经
`accepted/submitted` 的 move 后，planner 选择 `life-advance`，没有再次提交同一 move。第一次推进将原始日期
`53168688` 推到 `53168784`（4 个游戏日），军队从省 `2619` 移到 `2618`；继续推进 7 个游戏日后到达
`2615`，再推进 6 个游戏日后到达 `2609`。新 DLL 在同一局发布的战争字段为
`primary_opponent_character_id=36108`、`player_is_primary_war_leader=true`、
`enemy_primary_default_raise_province_id=2543`。可见敌军目标仍为 `2591` 时没有重复 move；该敌军实际移动到
`2602` 后，planner 才进行一次重定向并得到新的 `move_submitted`。每个 turn 结束时游戏都重新暂停，且 CK3
窗口始终为 `IsIconic=true`；全程没有 OCR、截图、键鼠或窗口恢复。

同一最小化实机战争随后暴露了纯追击策略的实际价值问题：首战令战争分从 `0` 升至 `24`，但其后约 80 个游戏日
持续追逐移动敌军时战争分保持 `24`。继续追逐约 70 日后分数才升至 `41` 并保存 checkpoint，说明追击偶尔能再次
接战，但会长期被移动目标牵引。Python planner 因此只在玩家为进攻方、本方 primary war leader 且战争分已经大于
零时，把 `enemy_primary_default_raise_province_id` 固定为围城启发式锚点；若玩家军与任一可见敌军同省，则仍优先
原地推进战斗。该策略改动目前由离线 Python 契约测试覆盖，不把默认集结省宣称为已解码的真实 war goal。

已提交的 move intent 保留 90 个游戏日，覆盖真实跨省行军所需时间；intent 未过期且所跟踪目标未改变时，
planner 必须推进时间而不是重复下令。战争中的单次 `life-advance` 最多推进 30 个游戏日，提前停止只依据玩家/
盟军军队位置与战术状态、战争分、战争集合或待处理事件这些会改变下一步决策的信号；敌军逐日移动不单独造成一次推进提前
结束。驻地或围城军队没有活动路线时，driver 另外监控“非撤退敌军首次把当前省作为所在省、移动目标或已发布路线节点”这一关系；
关系首次出现便立即暂停，不等满 30 日，也不把无关的敌军逐省移动当作进展。追击模式下，推进结束后的新决策点若发现所跟踪敌军已经换省，才提交一次新的追击目标；围城模式下目标
保持为稳定锚点，敌军在异省移动不会造成重定向。两种模式共用相同的 90 日 move intent 与 advance 去重。

解散命令同样必须使用玩家路径：公开 ArmyID 只负责解析 `CArmy`，command payload 使用
`CArmy+0x178` 的内部 target ID，并先调用原生 validator，再以 `kind=1` / flags `0x0E` 入队。
同一最小化实机回放中，`disband-army-83886341` 返回 `war_action.status=disbanded`，下一份
snapshot 的 `player_armies` 已为空；该成功路径用于战争结束后的残军清理，不能推广成战时重置军队。

同局后续 checkpoint 的 `date_raw=53174208`、玩家战争分 `41`，军队 `83886341` 位于省 `2598` 且为
`sieging`。推进 30 游戏日后仍未进入 `combat`；战时尝试 `disband-army-83886341` 被原生 validator 以
`CK3 army is not player-controllable` 拒绝，军队状态未变，因此不得采用“战时解散再重拉”的自动策略。
向 exact 目标 `2585` 围城推进 60 日后，两支敌军的原生 route 都锁定 `2585`；仅在 `2585` 与 legacy
fallback `2543` 两点间轮转会同时受堵。公国/王国目标发布全部 de jure 伯爵领首府，正是为了给 planner
提供更多安全围城点，而不是继续在这两个已被封锁的点上试探。

同一 `date_raw=53174208` checkpoint 的定向恢复又复现了另一类实际失败：目标省 `2585` 本身没有敌军，
但玩家军队从 `2568` 提交到 `2585` 的原生路线经过敌军当前省 `2581`，推进仅 1 游戏日就进入 2v1
`combat`。因此“目标省安全”不等于“路线安全”；planner 提交 move 前必须审阅玩家候选路线的每个
`route_province_ids` 条目，而不能只比较双方终点。硬冲突包括：非撤退敌军当前省位于玩家路线、敌军 move target
位于玩家路线、双方下一跳相同、双方剩余路线共享任一未来省，以及双方以相反方向使用同一条边。共享省会记录
双方各自的 1-based hop；当前没有每段地形/速度 ETA，不能仅凭 hop 差声称必然错峰。一般追击允许“被追击敌军
恰在路线最后一项”这一种终点命中，但中途相遇、共同下一跳、未来共享省和其他敌军仍会阻断。该字段发布的是 CK3 已计算的剩余路线，不包含 bridge
猜测或最短路重建。

路线安全是全局时间推进门槛，不是“最强军队”局部提示。每次战争中的 `life-advance` 前，planner 会在
paused snapshot 审计全部可控军队的活动路线，威胁集合取全部 active wars 的非撤退敌军；任一完整路线
不可读或不安全，就不能推进所有军队。实际不安全的军队会优先改道；旧路线仍存在时，本轮只允许纯
`preview-move-*` 或真正的 `move-army-*` 替换命令，替代目标已在当前省、preview/move deferred、retry
backoff 都不能成为继续推进旧危险路线的理由。`game.command.preview-move-army-N-to-N` 只解决提交前查询，
自动 exact routing 还必须同时广告 `game.state.army-routes`，否则明确返回 unsupported，避免未来 partial
adapter 在提交后失去持续审计能力。

没有活动路线的驻地军队也不是自动安全。paused 决策帧会针对该军当前省单独检查所有非撤退敌军的
`current_province_id`、`move_target_province_id` 和完整 `route_province_ids`；敌军正在汇聚到当前围城点时，
planner 先预览下一个 exact 目标，全部 exact 目标无解则保持暂停，不能继续围城推进。该检查只保护当前驻地，
不会把敌军路线上的任意远端交叉省加入通用目标黑名单。

同一实机现场在玩家到达 `2604` 后给出了更强的完整路线反例：玩家回到 `2585` 的预览为
`[2603,2595,2598,2599,2587,2585]`，敌军 `357` 从 `2597` 去 `2604` 的剩余路线为
`[2596,2595,2603,2604]`。双方在 `2603` / `2595` 共享未来省，并在 `2603→2595` 与
`2595→2603` 形成反向共边，因此不得提交。到 `2596`、`2600` 的候选也共享 `2603/2595`；
到 `2568` 的候选 `[8759,2602,2591,2589,2579,2574,2572,2568]` 则与两支敌军当时的完整路线无交集。

以上移动、解散与围城观测全程没有恢复窗口，也没有调用 OCR、截图或键鼠。

这些具体战争 step 即使运行在显式 `hybrid-fallback` 配置中也只允许 native 后端执行；native 未广告时不会转发到视觉后端。

## 一步 planner

事件和待回复角色互动仍优先处理。其后每次 `ck3_auto_turn` 只执行一个战争动作：

1. baseline checkpoint 完成且当前无战争/残军时，显式 `query-declarable-wars`；优先 county holy war、county conquest、claim，随后按单 title 与稳定 runtime ID 排序，提交一个 `declare-war-*`。
2. 任一活动战争达到玩家视角 100 分：先执行 `enforce-demands-<war_id>`，确认该 war 从 snapshot 消失，不再无意义推进时间。
3. 有活动战争、无可控军队：`raise-troops-default`。
4. 玩家是进攻方、本方 primary war leader 且存在 exact `war_objective_province_ids`：从战争刚开始的 0 分起就按 DLL 的 DFS 顺序围攻 exact 目标；Python 只做稳定去重，不按 ProvinceID 重排。paused 状态先预览完整原生路线，再按上面的硬冲突审计；不安全则预览下一个未完成 exact 目标，所有 exact 路线都不安全时保持暂停，绝不偷用 legacy fallback。
5. 没有 exact 目标时，战争分为 0、玩家是防守方或不是本方 primary war leader：选择兵力最大的可见敌军，令最强可控军队追击其当前省；兵力未知时按最小 `army_id` 稳定选择。仅 legacy fallback 可用时，仍要求进攻方已经取得正分，才把 `enemy_primary_default_raise_province_id` 当作围城启发式锚点；它绝不是解码出的 war goal。
6. 军队已经在目标省、已观察到向目标省移动，或 90 个游戏日内已有相同的 accepted/submitted move intent：只有全部可控活动路线的 fresh passive audit 都安全，才执行一次最多 30 个游戏日的 `life-advance`，不重复提交 move。running snapshot 先暂停再读完整路线；敌情变化后每次推进前重新审计，不把上一次 preview 当永久通行证。
7. 战争消失但玩家军队仍在场：逐支执行 `disband-army-<army_id>`。

Typed MCP 工具为 `ck3_get_war_state`、`ck3_query_declarable_wars`、`ck3_declare_war`、`ck3_raise_troops_default`、`ck3_move_army`、`ck3_enforce_demands` 和 `ck3_disband_army`。通用 `ck3_plan_turn` / `ck3_auto_turn` 使用同一份状态和 step，不另建旁路策略。纯 native 缺少任何 capability 时明确返回 unsupported；Python 不会回落到最小化窗口的视觉点击。

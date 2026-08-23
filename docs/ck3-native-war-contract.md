# CK3 1.19.0.6 原生战争闭环契约

本页定义 `native-headless` 的战争状态、命令和最小决策闭环。该路径只走注入 DLL 的 named pipe；CK3 窗口最小化时仍可运行，也不会回落到 OCR、键鼠或窗口聚焦。

## Snapshot

顶层 `active_wars` 是数组；每场战争包含：

- `war_id`
- `player_side`: `attacker` 或 `defender`
- `primary_opponent_character_id`: 玩家对侧的 primary war leader；完整 `CharacterID` 已按 generation 重新解析，过渡帧无法解析时为 `null`
- `player_is_primary_war_leader`: 玩家是否正是本方 primary war leader；它是 `enforce-demands` 的必要前提
- `enemy_primary_default_raise_province_id`: 对方 primary 角色的原生默认集结省；无法解析时为 `null`。该字段只是敌军省份不可见时的明确 fallback，不冒充 war goal、首都或真实行军目标
- `player_relative_war_score`: 相对玩家视角的整数战争分
- `allied_armies` / `enemy_armies`: 当前能从原生对象读取的军队数组

顶层 `player_armies` 保留玩家仍在场的可控军队。它不能只从 `active_wars` 临时推导：战争结束后的下一帧必须还能看见残留军队，planner 才能发出解散命令。

军队 canonical 字段为：

- `army_id`, `owner_character_id`
- `soldiers`: 非负整数；当前构建若尚未稳定解析兵力偏移，允许为 `null`
- `current_province_id`: 军队正在生成或销毁、原生对象暂时无省份时允许为 `null`
- `move_target_province_id`: 目标偏移尚未稳定时允许为 `null`
- `move_target_observable`: DLL 是否真实发布了目标字段
- `controllable`

Python 会拒绝类型错误的 ID、阵营、分数和数组，同时把早期 fixture 的 `soldier_count` 输入别名统一投影为 `soldiers`；MCP 输出永远使用 canonical 名称。

## Capability 与具体 step

DLL hello 广告：

- `game.state.war-primary-opponent`
- `game.command.raise-troops-default`
- `game.command.move-army-N-to-N`
- `game.command.disband-army-N`
- `game.command.enforce-demands-N`
- `game.command.query-declarable-wars`
- `game.command.declare-war-N`

Python 根据当前 snapshot 展开为：

- `raise-troops-default`: 有活动战争且没有可控军队时才出现
- `move-army-<army_id>-to-<province_id>`: 可控玩家军队与可见敌军当前省的有效组合
- `disband-army-<army_id>`: 每支当前可控玩家军队各一个
- `enforce-demands-<war_id>`: 每场当前活动战争各一个；planner 只在玩家视角战争分达到 100 时选择
- `query-declarable-wars`: 无活动战争时显式运行一次 CK3 原生 CB evaluator；该查询可能遍历很多角色，绝不放进 250ms heartbeat
- `declare-war-<declaration_id>`: 只从最新查询结果展开。`declaration_id` 是本代运行时的
  `target-cb-index-configuration-index` opaque choice，不是跨版本的 CB ID

占位模板本身不会暴露给 planner。若军队已在目标省或已经以该省为目标，相同 move step 不再广告，避免提交无状态变化的重复命令。

## 命令后置条件

- raise：等待 snapshot 出现新的可控军队；否则命令超时并返回失败。
- move：若 DLL 能观察 `move_target_province_id`，等待该军队的目标变为指定省或军队到达；若当前构建不能观察该字段，则以 native `command_result` 的 `accepted/submitted` 为提交成功，返回 `move_submitted`，随后由 `life-advance` 推动行军。
- disband：等待目标军队从顶层 `player_armies` 消失。
- declare：DLL 缓存查询得到的完整 choice；提交时按 target/CB 重新枚举，并要求 claimant、目标 title、configuration 与缓存完全相同。
  Python 等待 `active_wars` 增长；若原生命令已入队但战争尚未投影，返回 `declaration_submitted`，下一 turn 先推进时间而不重复宣战。
- enforce：只允许当前玩家是该战争的 primary war leader；native builder、validator 与 command queue 接受后，Python 等待目标 war 消失。

2026-08-23 实机验证使用 exact-build DLL 与 `native-headless`，在 CK3 窗口 `IsIconic=true` 时显式查询并提交
`declare-war-29097-11-0`。提交后并非只收到 command ack：下一份 native snapshot 实际新增
`war_id=16777290`、`player_side=attacker`、`player_relative_war_score=0`；CK3 进程继续响应且窗口仍保持最小化。
该路径未调用 OCR、截图、键鼠或视觉 fallback。

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

已提交的 move intent 保留 90 个游戏日，覆盖真实跨省行军所需时间；intent 未过期且所跟踪目标未改变时，
planner 必须推进时间而不是重复下令。战争中的单次 `life-advance` 最多推进 30 个游戏日，提前停止只依据玩家/
盟军军队位置、战争分、战争集合或待处理事件这些会改变下一步决策的信号；敌军逐日移动不单独造成一次推进提前
结束。推进结束后的新决策点若发现所跟踪敌军已经换省，才提交一次新的追击目标。

解散命令同样必须使用玩家路径：公开 ArmyID 只负责解析 `CArmy`，command payload 使用
`CArmy+0x178` 的内部 target ID，并先调用原生 validator，再以 `kind=1` / flags `0x0E` 入队。
同一最小化实机回放中，`disband-army-83886341` 返回 `war_action.status=disbanded`，下一份
snapshot 的 `player_armies` 已为空。以上两条路径全程没有恢复窗口，也没有调用 OCR、截图或键鼠。

这些具体战争 step 即使运行在显式 `hybrid-fallback` 配置中也只允许 native 后端执行；native 未广告时不会转发到视觉后端。

## 一步 planner

事件和待回复角色互动仍优先处理。其后每次 `ck3_auto_turn` 只执行一个战争动作：

1. baseline checkpoint 完成且当前无战争/残军时，显式 `query-declarable-wars`；优先 county holy war、county conquest、claim，随后按单 title 与稳定 runtime ID 排序，提交一个 `declare-war-*`。
2. 任一活动战争达到玩家视角 100 分：先执行 `enforce-demands-<war_id>`，确认该 war 从 snapshot 消失，不再无意义推进时间。
3. 有活动战争、无可控军队：`raise-troops-default`。
4. 有可控军队和敌军省份：选择兵力最大的敌军，令最强可控军队追击其当前省。兵力未知时按最小 `army_id` 稳定选择，不阻塞闭环。敌军省份暂不可见时可以使用 `enemy_primary_default_raise_province_id` 维持行动，但该 fallback 只是对方 primary 角色的默认集结省，绝不是 war goal。
5. 军队已经在目标省、已观察到向目标省移动，或 90 个游戏日内已有相同的 accepted/submitted move intent：执行一次最多 30 个游戏日的 `life-advance`，不重复提交 move。推进只因玩家/盟军军队位置、战争分、战争集合或待处理事件改变而提前结束；若下一决策点发现所跟踪敌军已经换省，再重定向一次。
6. 战争消失但玩家军队仍在场：逐支执行 `disband-army-<army_id>`。

Typed MCP 工具为 `ck3_get_war_state`、`ck3_query_declarable_wars`、`ck3_declare_war`、`ck3_raise_troops_default`、`ck3_move_army`、`ck3_enforce_demands` 和 `ck3_disband_army`。通用 `ck3_plan_turn` / `ck3_auto_turn` 使用同一份状态和 step，不另建旁路策略。纯 native 缺少任何 capability 时明确返回 unsupported；Python 不会回落到最小化窗口的视觉点击。

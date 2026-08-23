# CK3 1.19.0.6 原生战争闭环契约

本页定义 `native-headless` 的战争状态、命令和最小决策闭环。该路径只走注入 DLL 的 named pipe；CK3 窗口最小化时仍可运行，也不会回落到 OCR、键鼠或窗口聚焦。

## Snapshot

顶层 `active_wars` 是数组；每场战争包含：

- `war_id`
- `player_side`: `attacker` 或 `defender`
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

- `game.command.raise-troops-default`
- `game.command.move-army-N-to-N`
- `game.command.disband-army-N`

Python 根据当前 snapshot 展开为：

- `raise-troops-default`: 有活动战争且没有可控军队时才出现
- `move-army-<army_id>-to-<province_id>`: 可控玩家军队与可见敌军当前省的有效组合
- `disband-army-<army_id>`: 每支当前可控玩家军队各一个

占位模板本身不会暴露给 planner。若军队已在目标省或已经以该省为目标，相同 move step 不再广告，避免提交无状态变化的重复命令。

## 命令后置条件

- raise：等待 snapshot 出现新的可控军队；否则命令超时并返回失败。
- move：若 DLL 能观察 `move_target_province_id`，等待该军队的目标变为指定省或军队到达；若当前构建不能观察该字段，则以 native `command_result` 的 `accepted/submitted` 为提交成功，返回 `move_submitted`，随后由 `life-advance` 推动行军。
- disband：等待目标军队从顶层 `player_armies` 消失。

这些具体战争 step 即使运行在显式 `hybrid-fallback` 配置中也只允许 native 后端执行；native 未广告时不会转发到视觉后端。

## 一步 planner

事件和待回复角色互动仍优先处理。其后每次 `ck3_auto_turn` 只执行一个战争动作：

1. 有活动战争、无可控军队：`raise-troops-default`。
2. 有可控军队和敌军省份：选择兵力最大的敌军，令最强可控军队追击其当前省。兵力未知时按最小 `army_id` 稳定选择，不阻塞闭环。
3. 军队已经在目标省或已经向目标省移动：执行一次有界 `life-advance`。
4. 战争消失但玩家军队仍在场：逐支执行 `disband-army-<army_id>`。

Typed MCP 工具为 `ck3_get_war_state`、`ck3_raise_troops_default`、`ck3_move_army` 和 `ck3_disband_army`。通用 `ck3_plan_turn` / `ck3_auto_turn` 使用同一份状态和 step，不另建旁路策略。

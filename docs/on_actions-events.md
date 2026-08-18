# on_action 与事件实测笔记

## on_action 的覆盖/合并行为（关键）

mod 文件里重新定义同名 on_action 时，**字段级冲突取最后加载者**（mod 晚于游戏本体）：

- 你写了 `effect = {...}` → 原版同名 on_action 的 effect **被覆盖消失**（`jomini_onaction.cpp: There is more than one 'effect' defined using most recent`），原版开局逻辑会被你炸掉。
- 无侵入扩展模式（本项目采用）：

```
on_game_start_after_lobby = {
	on_actions = { xar_on_game_start }   # 只加 on_actions 条目，不碰 effect/events
}

xar_on_game_start = {                   # 自定义钩子 on_action
	effect = { ... }
}
```

## 开局钩子选择

- `on_game_start`：空 scope，此时**玩家/游戏规则还不可靠**。
- `on_game_start_after_lobby`：官方注释明确"需要知道玩家是谁、规则是什么时用这个"。本项目实测：前者里 `every_player`/`has_game_rule` 静默失败，换后者正常。

## effect 与事件的并发陷阱（`_on_actions.info` 明写）

on_action 的 effect 与它触发的事件**并发执行，不是先后**：

> Effects run here create a separate chain than events the on_action fires, so you can for example not manipulate values in the effect, and then reliably access those in an event that was fired at the same time.

后果：effect 里算好的变量，同 on_action 立刻 `trigger_event` 的事件**读不到**（本项目开局分数显示 0 的元凶）。

对策（本项目用第二个）：
1. 计算挪进事件的 `immediate`（事件显示前执行）
2. `trigger_event = { id = xxx days = 1 }` 延迟触发，隔天后值必然已写好

## 延迟事件的 root 失效

`trigger_event = { days = 1 }` 到点时会重新校验 root 有效性——on_death 里 root 是"将死角色"，一天后已死亡 → 事件被丢弃，静默不发生。

对策：把延迟事件触发到存活 scope，如 `player_heir ?= { trigger_event = {...} }`。

另注意官方说明：带 delay 的事件"在 on_action 执行时和延迟到期时都要有效才触发"。

### 无继承人结算兜底

- 有 `player_heir` 时仍把 `xar.1001` 延迟 1 日发给继承人，避开死亡 root 失效。
- 无 `player_heir` 时没有可供延迟承载的存活角色，只能在 `on_death` 的将死 root 上同步 `trigger_event = xar.1001`；代码用 `XAR: no player heir; synchronous settlement fallback` 标记该分支。
- 2026-08-18 CK3 1.19.0.6 实测：链路改为 `on_death -> xar.1000` 计分提交 -> `xar.1003` 写位/分流 -> `xar.1002` 玩家变量快照。无继承人不再打开会被遮住的 `xar.1001`，而由生成器向原生继承窗注入结算 widget；八项数值、无“继续扮演”、退出确认和返回主菜单均有真实像素证据，run `xar_accept_fmq_wxxc`，0 `xar` errors。

## 死亡钩子

`on_death`：root = 将死角色（"about to die but not dead yet"），属性/金钱/宗族均可读；`scope:killer` 可能有。它对所有角色死亡触发（含 AI），自己的 limit 要写得廉价快速（先查 flag）。

## 杂项

- 事件必须有 `theme`（common/event_themes），否则报 `Theme missing in event`。选项块内**没有** `after = {}`（那是别的游戏的语法），顺序逻辑直接在 option 内用 `if`。
- `Event xxx is orphaned`：事件没被任何东西引用时的提示，仅警告。
- 控制台 `die` 可直接测死亡链；`event xar.0001` 手动触发事件。

# 脚本基础语法

## 文件与编码

- 所有脚本文件必须 **UTF-8 with BOM**（缺 BOM 仅警告 `should be in utf8-bom encoding`，仍尝试加载；但 yml 缺 BOM 直接不加载）
- 注释用 `#`；块结构 `key = { ... }`；赋值 `key = value`
- 同名数据库条目跨文件：多数类型后者覆盖前者；on_action 字段级"最后加载者赢"（见 ../on_actions-events.md）

## scope（作用域）

- 脚本在 scope 上求值：character、title、province、dynasty、dynasty_house、faith、culture……
- 换 scope：`root`、`scope:xxx`（事件目标）、直接链接如 `dynasty = { ... }`、`house = { ... }`、`player_heir ?= { ... }`（`?=` 表示可不存在）
- 迭代器：`every_dynasty_member = { limit = {...} ... }`——注意迭代器的 scope 要求（`every_dynasty_member` 必须在 dynasty scope 里用，角色下先 `dynasty = {}`）

## trigger / effect / script value

- trigger：条件（`has_game_rule = x`、`global_var:a >= 25`、`is_ai = no`），可嵌套 `AND/OR/NOT`
- effect：动作（`set_global_variable`、`add_diplomacy_skill = 1`、`trigger_event`、`if = { limit = {...} ... }`），分支 `else_if = {...}` / `else = {...}`
- script value（`common/script_values/`）：可计算的数值，支持 `add/subtract/multiply/divide/floor/round/ceiling` 和 `if = { limit add }`
- scripted_effect / scripted_trigger：复用块，调用 `xxx = yes`

## 事件骨架

```
namespace = xar

xar.0001 = {
	type = character_event
	theme = stewardship            # 必填，common/event_themes 里的键
	title = xar.0001.title
	desc = xar.0001.desc

	immediate = { ... }            # 触发时执行

	option = {
		name = xar.0001.option_a   # loc key
		trigger = { ... }          # 选项可用条件
		# 直接写 effect；没有 after 字段
	}
}
```

## 游戏规则

```
xar_enabled = {
	categories = { game_modes }
	default = xar_on
	xar_on = {}
	xar_off = {}
}
```

判定：`has_game_rule = xar_on`（选项键）。loc 键有固定前缀：`rule_<规则id>`、`setting_<选项id>`、`setting_<选项id>_desc`。

## 常用 effect 速查（本项目用过）

| 目的 | 写法 |
|---|---|
| 设全局变量 | `set_global_variable = { name = x value = 1 }` / 布尔 `set_global_variable = x` |
| 改全局变量 | `change_global_variable = { name = x add = -25 }` |
| 删全局变量 | `remove_global_variable = x` |
| 加属性 | `add_diplomacy_skill = 1`（ martial/stewardship/intrigue/learning/prowess 同理） |
| 角色标记 | `add_character_flag = xa_enabled` |
| 触发事件 | `trigger_event = { id = xar.0001 days = 1 }` |
| 触发 on_action | `trigger_event = { on_action = xxx }` |
| 遍历玩家 | `every_player = { ... }` |
| 日志标记 | `debug_log = "XAR: xxx"` |
| 存显示用值 | `save_scope_value_as = { name = x value = global_var:y }` |

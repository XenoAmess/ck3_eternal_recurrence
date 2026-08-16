# 变量与 script value 实测笔记

## 变量类型

- `var:x` — scope 内变量（角色/省份等），随存档
- `global_var:x` — 全局变量，**随存档**（不是跨存档！跨存档见 cross-save-persistence.md）
- flag 变量：`set_global_variable = xxx`（无值，存布尔）；带值：`set_global_variable = { name = xxx value = 1 }`

## global_var 的读取上下文差异（实测踩坑）

`global_var:x` 在不同字段里的解析行为**不一致**：

| 上下文 | 写法 | 结果 |
|---|---|---|
| trigger 比较 | `global_var:xa_run_score >= 25` | ✅ 正常 |
| script value 的 add 字段 | `add = global_var:x` | ✅ 正常（原版 fp2 有先例） |
| `set_global_variable` 的 value 字段（块内） | `value = { value = global_var:x }` | ✅ 正常 |
| **`save_temporary_scope_value_as` 的 value 字段** | `value = global_var:x` 或块形式 | ❌ **被当作 scope 链接解析**：`Event target link 'global_var' returned an unset scope` |
| **`save_scope_value_as` 的 value 字段** | `value = global_var:x` | ✅ 正常（原版 ep3_frankokratia 有先例） |

结论：要在事件文本里显示全局变量，用 `save_scope_value_as`（临时版既解析错误、生命周期也不够）。事件 loc 里显示：`[TopScope.GetValue('保存名')]`（`|+0` 格式带符号）。

## script value

- 定义目录是 `common/script_values`（**不是** scripted_values——放错目录不加载，引用处报 `Cannot read as a script value`，定义处无报错）
- 数学：`add/subtract/multiply/divide`，`floor = yes` / `ceiling = yes` / `round = yes`
- 角色属性直接是值：`diplomacy/martial/stewardship/intrigue/learning/prowess`；还有 `gold/prestige/piety`
- 引用另一个 script value：直接用名字 `value = tiny_gold_max_value_static`（script_values 文件内确认可用）
- `every_dynasty_member`/`every_house_member` 可以在 script value 里用（原版 tgp 有先例），但注意 scope：这俩是 dynasty/dynasty_house scope 的迭代器，角色 scope 下要用 `dynasty = { every_dynasty_member = {...} }` 包一层

## set/change 语义

- `change_global_variable = { name = x add = -25 }`：支持负数，支持 script value 块（`add = { value = gold divide = 10 floor = yes }`）
- 变量未设置时读取：trigger 里按 0 处理并告警；`value = global_var:x` 读取会报 `Failed to fetch variable ... not being set`。需要兜底就先 `if = { limit = { NOT = { has_global_variable = x } } set... }`
- `remove_global_variable = x` 删除

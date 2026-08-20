# CK3 GUI 系统实测笔记

## 顶层窗口的实例化：scripted_widgets 注册

自定义顶层 `window = {}` 写在 gui 文件里**不会自动实例化**——必须在 `gui/scripted_widgets/*.txt` 注册：

```
gui/xar_meta.gui = xar_meta_window
```

格式：每行 `文件路径 = 窗口名`。未注册的窗口：不渲染、state 不求值、**且无任何报错**（本项目最大的隐性坑，浪费了大量排查时间）。

## 动画 state（trigger_when / on_start）

```
state = {
	name = "xxx"
	trigger_when = "[<数据表达式>]"   # 条件由假转真时进入该 state
	on_start = "[<数据表达式>]"       # 进入时执行一次
	duration = 0.5                   # 可选；带时长的 state 会退出并可在条件保持时重入（可用于重试）
	delay = 0.5                      # 可选；延迟进入
}
```

- 原型用途是动画驱动（见 frontend_bookmarks.gui），POD 将其用作自动触发器。
- **求值时机**：实测注册的、可见的窗口上会求值；`GetPlayer.Custom(...)` 结果变化时能触发重入。
- **副作用能力**：`on_start` 里 `GetScriptedGui('x').Execute(...)` 有效（写游戏状态成功）；但 `Tutorial.OnClickTransition(...)` 无效——推测这类"按钮动作"函数只响应真实用户点击路径。

## 数据上下文作用域（重要）

GUI 数据函数并非全局可用，很多上下文由代码只注入到特定窗口：

- `Tutorial.*`（GetStepText/HasTransition/OnClickTransition/...）**只在 tutorial_window 本体有值**。其它任何窗口（含同 layer）里全空、不报错。调试面板实测：StepText/StepName 全空，按钮调用无效。
- `GetPlayer`、`GetVariableSystem`、`GetScriptedGui`、`Localize`、`ExecuteConsoleCommand` 等在常规窗口可用。
- 结论：要动教程窗口的东西，就 override `gui/window_tutorial.gui` 本体（mod 同路径文件整体覆盖），不要试图在外部窗口遥控。
- 2026-08-18 CK3 1.19.0.6 实测：`SuccessionEventWindow.*` 的可见性 getter 在注册的外部窗口可求值，但其文字 getter、鼠标输入和 `GoToMenu` action 不具备完整上下文。无继承人结算因此由 `tools/gen_no_heir_gui.py` 把 `xar_no_heir_settlement_widget` 注入原生 `window_succession_event.gui`；只有原生窗口内的按钮能可靠打开退出确认。
- 原生窗口被 `.gitignore` 排除，clean checkout 不能把本机游戏文件当校验 fixture。跟踪投影可先移除唯一注入并恢复原版正文，再用 CK3 1.19.0.6 canonical text SHA-256 `322971347711308a51bcb16e3c34a7bd9eae5e7938243699ec8fe3691d8c7406` 固定其语义；该摘要基于移除 UTF-8 BOM、把换行规范化为 LF 后的 UTF-8 正文。随后重新注入并逐字比对投影；本机存在原版源时再追加两份正文完全相等的强校验。该可逆契约由 `tools/test_gen_no_heir_gui.py` 覆盖，不需要提交第二份 Paradox 原版 fixture。
- 死亡后的自定义数值用 `GetPlayer.MakeScope.Var(...).GetValue` 可读；直接从 `SuccessionEventWindow.GetDeadCharacter.MakeScope` 读取会显示空白。写值必须在可见窗口初始化前经过隐藏事件提交边界。

## scripted_gui 执行链

```
common/scripted_guis/x.txt:
xxx_gui = {
	scope = character
	is_shown = { ... }    # 显示条件（界面上下文）
	effect = { ... }      # 执行效果（游戏状态脚本！可 set_global_variable 等）
}
```

GUI 侧：`datacontext = "[GetScriptedGui('xxx_gui')]"` 然后 `onclick = "[ScriptedGui.Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"`，或在 state 的 `on_start` 里链式 `GetScriptedGui('xxx_gui').Execute( GuiScope... )`。

这是把"界面侧条件"（含 interface trigger 的结果）**写回游戏状态**的正规通道。

## 决议原生分组与标题图标

CK3 1.19.0.6 的原生决议面板通过 `DecisionsView.GetDecisionGroupItems` 自动消费
`common/decision_group_types/*.txt`。新增命名空间分组并在决议中写
`decision_group_type = xar_eternal_recurrence` 即可得到独立折叠区，不需要覆盖
`gui/window_decisions.gui`。分组 `sort_order` 越高越靠前，`gui_tags = { big_button }`
会把组内行高从 45 提到 55；工具型分组不要设置 `important_decision_group = yes`，否则会默认产生重要决议提醒。

分组没有原生 `icon =` 字段。兼容做法是在普通 additive GUI 文件中注册 `texticon`，再把
`@xar_decision_group_icon!` 放进九语言的 `decision_group_type_xar_eternal_recurrence` 文本。
图标会出现在原生折叠箭头之后；若要放在箭头前或只给列表行加独立图标，才需要高冲突的原生窗口覆盖。
本项目复用 `glassfire_trait.dds` 作为 25×25 分组前缀。该机制由 1.19.0.6 原版 schema/GUI
及 Princes of Darkness 1.19.0.6 的 `POD_decision_group_types.txt`、`POD_texticons.gui` 交叉确认；
PoD 的完整 `window_decisions.gui` 覆盖与 shader 注入并非分组所需，不应照搬。

决议的 `picture.reference` 同时服务列表右侧淡化图和 550×220 详情图。原版惯例是
1100×440 DXT1；列表会水平镜像图片，因此素材不得包含自然语言文字或有方向意义的标记。

## 杂项

- `layer`：教程窗口在 `tutorial` 层；自定义窗口常用 `middle`。
- 窗口不可见化：不加 `Window_Background` 即无可见内容；`alwaystransparent = yes` 让点击穿透。窗口移出屏幕会被裁剪且 state 可能停止求值（不推荐）。
- 事件/调试按钮：`visible = "[InDebugMode]"`。
- 界面调试：`Gui.Debug`（debug 模式工具栏）、`gui_warnings.log`、error.log 里的 `pdx_data_factory` 错误会指出表达式解析失败位置。

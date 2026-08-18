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

## 杂项

- `layer`：教程窗口在 `tutorial` 层；自定义窗口常用 `middle`。
- 窗口不可见化：不加 `Window_Background` 即无可见内容；`alwaystransparent = yes` 让点击穿透。窗口移出屏幕会被裁剪且 state 可能停止求值（不推荐）。
- 事件/调试按钮：`visible = "[InDebugMode]"`。
- 界面调试：`Gui.Debug`（debug 模式工具栏）、`gui_warnings.log`、error.log 里的 `pdx_data_factory` 错误会指出表达式解析失败位置。

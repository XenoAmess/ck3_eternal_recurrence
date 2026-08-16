# GUI 脚本语法

## 数据表达式（datacontext）

属性值里 `"[...]"` 包裹的表达式，如：

```
visible = "[And( GetPlayer.IsValid, Not( IsPauseMenuShown ) )]"
text = "[Tutorial.GetStepText]"
onclick = "[GetScriptedGui('x_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
```

- 逻辑：`And/Or/Not`；比较：`EqualTo_string(a, b)`（POD 用例）
- 取 loc：`Localize('key')`；自定义本地化：`GetPlayer.Custom('custom_loc_id')`
- 作用域构建：`GuiScope.SetRoot( GetPlayer.MakeScope ).AddScope('name', X.MakeScope ).End`
- **数据上下文有作用域**：`Tutorial.*` 只在 tutorial_window 本体有值（详见 ../gui-system.md）

## 窗口骨架

```
window = {
	name = "xxx_window"
	size = { 600 300 }
	layer = middle
	visible = "[GetPlayer.IsValid]"
	using = Window_Background          # 背景样式（不写则无可见内容）

	state = { name = _show using = Animation_FadeIn_Quick }
	state = { name = _hide using = Animation_FadeOut_Quick }

	vbox = { ...子控件... }
}
```

**顶层窗口必须在 `gui/scripted_widgets/*.txt` 注册才实例化**：

```
gui/xar_meta.gui = xar_meta_window
```

## 动画 state 用作自动触发器

```
state = {
	name = "my_trigger"
	trigger_when = "[EqualTo_string( GetPlayer.Custom('xxx'), Localize('yyy') )]"
	on_start = "[GetScriptedGui('zzz_gui').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
	duration = 0.5     # 带时长可重入（重试）
	delay = 0.5        # 延迟进入
}
```

条件假→真时执行一次 on_start。有效：`GetScriptedGui().Execute`（可写游戏状态）。无效：`Tutorial.OnClickTransition` 这类按钮动作函数。

## mod 覆盖原版 gui

同相对路径的 gui 文件**整体覆盖**（如 mod 里放 `gui/window_tutorial.gui` 即替换原版）。代价：游戏更新后需同步。局部增改可以用 types 扩展（`types X { type y = window { ... } }` 合并）——但实测加 state 到既有 type 的效果未验证成功，稳妥用整体覆盖。

## 调试

- 解析错误：`error.log` 里 `pdx_data_factory.cpp`（函数找不到）/ `pdx_gui_factory.cpp`（行号）
- 实时查看数据表达式值：注册临时可见窗口 + `text = "[表达式]"`
- 游戏内工具：debug 模式的 `Gui.Debug`、GUI Editor

# 教程课程系统（tutorial lessons）

本项目的跨存档存储载体。参考：`_tutorial_lesson.info` / `_tutorial_lesson_chains.info`（游戏内官方文档注释）。

## 链（chain）

```
reactive_advice = {
	trigger = { is_gamestate_tutorial_active = no }
}
```

- `chain = reactive_advice` 是"反应式建议"链（游戏过程中触发的提示），**完成状态全局存 tutorial.txt**
- `save_progress_in_gamestate = yes` 的链（新手引导）进度存在**存档里**——方向相反，勿混
- 字段：`trigger`（链启动条件）、`delay`（秒）
- 一条链一次只激活一个课程（串行队列）

## 课程

```
my_lesson = {
	chain = reactive_advice
	delay = 0                        # 触发后延迟秒数
	start_automatically = yes        # 默认 yes；no 则需 start_tutorial_lesson effect
	shown_in_encyclopedia = no       # 默认 yes

	trigger = { ... }                # 课程启动条件（游戏状态 trigger）

	step_name = {                    # step，可多个
		text = "loc_key"
		delay = X                    # step 窗口显示延迟
		animation = center           # 窗口位置动画（center/far_right/...，教程窗口类型的 state 名）
		gui_tag = X                  # 激活时设置 gui tag，GUI 可用 IsTutorialTagOpen('X') 检测

		gui_transition = {           # 按钮 transition：玩家点击才前进
			button_id = "next"
			button_text = "tutorial_lesson_button_complete"
			target = lesson_finish
			enabled = { ... }        # 可选：条件满足才亮按钮（next 键的条件文本会作为指引显示）
		}

		trigger_transition = {       # **触发 transition：条件满足自动前进，无需点击**
			trigger = { always = yes }
			target = lesson_finish   # lesson_finish 完成 / lesson_abort 中止 / 其它 step 名
			button_id = "next"       # 可选：显示个禁用按钮作提示
		}

		interface_effect = { ... }   # 任何课程可用（关界面、移镜头等界面动作）
		effect = { ... }             # 仅 save_progress_in_gamestate 链可用游戏逻辑 effect
	}
}
```

## 完成与存储

- 完成 → 引擎写入 `tutorial.txt` 的 `completed_lessons`（**全局、跨存档**）
- 读取：`is_tutorial_lesson_completed = <课程id>`——**interface trigger**，只能用于 customizable_localization / GUI
- 相关 trigger：`is_tutorial_lesson_chain_completed`、`is_tutorial_lesson_active`、`is_tutorial_lesson_step_completed`
- 控制台：`tutorial.enable` / `tutorial.disable` / `tutorial.reset`（全清，含原版！）/ `tutorial.debugwindow`（调试窗口，含 per-lesson Complete/Reset，debug 上下文，mod 用不了）

## 本项目用法要点

- 静默自动完成：`trigger_transition = { target = lesson_finish trigger = { always = yes } }`，弹窗一闪即逝
- 课程名/step 名的 loc 会显示在弹窗标题/正文；哨兵文本勿带方括号
- 大量课程并发触发时按链串行逐个完成

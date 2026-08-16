# 跨存档全局存储（局外存档）

CK3 脚本没有任何官方跨存档 API。本文档记录本项目验证过的唯一双向方案及其完整架构。

## 通道排查结论（Workshop 纯 mod 范围内）

| 通道 | 全局文件 | 脚本可写 | 脚本可读 | 结论 |
|---|---|---|---|---|
| **教程课程 `tutorial.txt`** | ✅ | ✅（课程完成） | ✅（interface trigger） | **唯一双向方案** |
| 成就 `common/achievements` | 解锁状态在 Steam/GDK 后端 | ❌ | ❌ | mod 无法注册成就 ID；改校验和后成就禁用 |
| 游戏规则预设 `player/game_rules/presets.txt` | ✅ | ❌ | ❌ | 仅玩家手动保存；无 `set_game_rule` effect |
| 捏人存档 `rulers/*.ck3ruler` | ✅ | ❌ | ❌ | 仅捏人界面写 |
| `debug_log`/`error.log`/控制台 dump 命令 | ✅ logs/ | ✅ 只写 | ❌ | 单向导出，需外部程序，不算纯 mod |
| `pdx_settings.txt`/launcher sqlite/pops_filestorage | ✅ | ❌ | ❌ | 引擎/PDX SDK 内部 |

二进制逆向通道（DLL 注入、存档改写）违反纯 mod 约束，不采用。

## 存储介质

`Documents\Paradox Interactive\Crusader Kings III\tutorial.txt`：

```
last_lesson_chain="reactive_advice"
completed_lessons={
	reactive_advice_army_automation
	...
}
```

`completed_lessons` 由引擎全局维护：跨存档、跨重启持久。每个已完成课程 ID = 一个**只增位**（完成不可逆；`tutorial.reset` 控制台命令会全清，含原版课程——注意风险）。

## 写入路径（游戏内 → 全局）

1. 脚本 `set_global_variable = xar_hs_ge_<t>`（存档内变量）
2. 定义教程课程，`trigger = { has_global_variable = xar_hs_ge_<t> }`，`chain = reactive_advice`，`delay = 0`，`shown_in_encyclopedia = no`
3. 课程 step 内用 **`trigger_transition`** 自动完成——这是关键发现：

```
xar_hs_ge_<t> = {
	chain = reactive_advice
	delay = 0
	shown_in_encyclopedia = no
	trigger = { has_global_variable = xar_hs_ge_<t> }
	xar_hs_ge_step_<t> = {
		text = "xar_silent_step"
		trigger_transition = {
			target = lesson_finish
			trigger = { always = yes }
		}
	}
}
```

> `trigger_transition` = 条件满足时自动前进（`_tutorial_lesson.info` 官方字段），弹窗一闪即完成，玩家零操作。**不要**试图从 GUI 外部点击（`Tutorial.OnClickTransition` 从动画 state 调用无效，且 `Tutorial` 上下文只在 tutorial_window 本体存在——这些都是实测排除掉的弯路）。

注意：教程链一次只激活一个课程，多个位同时置位时会串行逐个完成（很快，但仍是队列）。已完成的课程不会重复触发。

## 读取路径（全局 → 游戏状态）

`is_tutorial_lesson_completed` 是 **interface trigger**，游戏状态脚本（事件/effect/script value/on_action）里禁用，只能在 customizable_localization 和 GUI 里用。因此读取必须走三层桥（POD 模式）：

```
customizable_localization（interface trigger 合法）
  → GUI state 的 trigger_when 比对 Custom() 文本
  → on_start 执行 GetScriptedGui('x').Execute(GuiScope.SetRoot(GetPlayer.MakeScope).End)
  → scripted_gui 的 effect 里 set_global_variable（写入存档内变量）
```

之后存档内脚本随意使用该变量。

### 关键细节

- 自定义顶层窗口**必须**在 `gui/scripted_widgets/*.txt` 注册才会实例化（`gui/xar_meta.gui = xar_meta_window`），否则 state 永不求值（无报错！）
- `GetScriptedGui('x').Execute(...)` 在 1.19 可用；POD 代码里的 `PlayerGuiExecute` 在此版本不存在
- 游戏语言非英语时，customizable_localization 引用的 loc key 必须在**当前语言**的 yml 里定义，否则 parse 时报 Missing loc key（英文回退对这条校验不生效）
- 多人：各玩家本地 tutorial.txt 独立；GUI 触发的 `set_global_variable` 在 MP 有潜在不同步风险（本项目单机定位）

## 编码方案：分层阈值

位只增 → 只能存单调数据。纪录用阈值序列编码：`xar_hs_ge_<t>` 完成 ⟺ 纪录 ≥ t。

七层首尾相接（粒度, 槽数）：`(1,100) (5,100) (10,100) (50,100) (100,100) (500,100) (1000,100)`，共 700 位，上限 167,600。

**写入只完成一个位**：降序 `else_if` 链，完成「≤ 分数的最大阈值」对应的那一位。纪录必落在阈值上，语义与全量置位完全等价，但每次破纪录最多 1 个弹窗。位已完成的场合课程不重触发 = 0 弹窗。

**读取用降序 first_valid**（位可能稀疏，不能用"顶位相邻检测"）：

```
xar_record_level = {
	type = character
	text = { trigger = { is_tutorial_lesson_completed = xar_hs_ge_166600 } localization_key = xar_rec_166600 }
	...降序...
	text = { localization_key = xar_rec_0 }
}
```

customizable_localization 的 text 块按序取第一个 trigger 成立的。GUI 侧每个等级一个 state，比对 `GetPlayer.Custom('xar_record_level')` 与 `Localize('xar_rec_<t>')`（各级 key 内容必须互不相同），命中即执行对应 scripted_gui 写入纪录值。

**扩展上限**：生成器 `TIERS` 列表追加层即可，旧位永久保留。

## 我们的使用模式（纪录 → 开局副本）

- `xa_global_record_imported`：GUI 桥实时维护的全局纪录（存档内镜像）
- `xa_local_points`：开局时由钩子置 `xa_shop_pending`，导入执行时拷贝纪录为**本局可花费副本**；消费只扣副本，不动全局
- 死亡：on_death → 算分 → 破纪录则先置位（通知先弹）→ 结算事件延迟 1 天显示

## 已知限制

- 需开启教程设置（reactive advice），否则写入侧不触发（读取不受影响）
- `tutorial.reset` 控制台命令会清空全部位（含原版课程）；手动删 tutorial.txt 同理
- 位容量有限；纪录精度 = 所在层的粒度（本项目购买粒度 25/点，低分区 1 分粒度，购买力无损）

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

七层首尾相接（粒度, 槽数）：`(1,100) (5,100) (10,100) (50,100) (100,100) (500,100) (1000,100)`，共 700 位，上限 166,600。

真实本局分数保存在 `xa_run_score`，它不直接参与纪录比较。生成的 `xar_quantize_record_candidate_effect` 用降序 `else_if` 链把它量化为 `xa_record_candidate`：取「≤ 真实分数的最大现有阈值」，达到或超过 166,600 时固定为 166,600。

**写入只完成一个位**：只有 `xa_record_candidate > xa_global_record_imported` 时才算破纪录，生成的 writer 再按 candidate 等值分支完成对应 lesson。真实分数在同一阈值区间内增长不会反复报新纪录。首次达到上限会写入并正常反馈；历史位阶已经是上限后，任何更高真实分数都不会再写入或报新纪录。

**读取用降序 first_valid**（位可能稀疏，不能用"顶位相邻检测"）：

```
xar_record_level = {
	type = character
	text = { trigger = { is_tutorial_lesson_completed = xar_hs_ge_166600 } localization_key = xar_rec_166600 }
	...降序...
	text = { localization_key = xar_rec_0 }
}
```

customizable_localization 的 text 块按序取第一个 trigger 成立的。GUI 侧每个等级一个 state，比对 `GetPlayer.Custom('xar_record_level')` 与 `Localize('xar_rec_<t>')`（各级 key 内容必须互不相同），命中即执行对应 scripted_gui 写入纪录值。所有旧 `xar_hs_ge_<t>` lesson ID 原样保留，因此历史纪录继续兼容。

**扩展上限**：生成器 `TIERS` 列表追加层即可，旧位永久保留。

## 我们的使用模式（余烬位阶 → 开局副本）

- `xa_run_score`：本局死亡结算的真实分数，可含小数。
- `xa_record_candidate`：真实分数向下映射得到的量化候选余烬位阶，最高为 166,600。
- `xa_global_record_imported`：从历史 lesson 位汇总出的量化历史位阶（存档内镜像）。
- `xa_local_points`：导入 ready 后从历史位阶复制的**本局可花费副本**；消费只扣副本，不动历史位阶。
- 死亡：on_death → 两条继承路径调用同一手写 wrapper → 算真实分数并同步提交一次纪录信号与 native settlement → candidate 严格高于历史位阶才置位 → `xar.1003/1001/1002` 后续只做 UI。agent 的 serial/ready 字段与外部 `tutorial.txt` 落盘边界见 [ck3-native-settlement-contract.md](ck3-native-settlement-contract.md)。

### 显式导入协议

1. `xar_on_game_start` 对玩家初始化 `xa_import_requested=1`、`xa_import_ready=0`、`xa_import_consumed=0`，不直接打开契约或商店。
2. GUI state 同时要求「最高 lesson 位匹配」和 request 信号；无论窗口先实例化还是 on_action 先执行，只有 request 从 0 变 1 后才会运行 importer。
3. importer 在 request guard 内幂等写入 `xa_global_record_imported`，随后执行 `requested=0 -> ready=1`。
4. `xar_consume_import_effect` 仅接受 `ready=1 && consumed=0`，先准确复制 `xa_local_points`，再执行 `ready=0 -> consumed=1` 并启动契约或 selftest。

因此 GUI 与 on_action 的先后顺序不会造成零值抢跑，重复 Execute 也不会重复打开流程；契约和商店只能在导入 ready 且点数已复制后出现。

### 两进程实证

2026-08-18 在 CK3 1.19.0.6 使用 `tools/run_acceptance.py --scenario persistence-restart` 实测：进程 A 从空 XAR 位开始，死亡结算后把 `xar_hs_ge_405` 写入 `tutorial.txt`；确认文件稳定后强制结束 A 的完整进程树，位阶与 SHA-256 均未变化。进程 B 启动前不调用任何纪录预置逻辑，并断言 handoff SHA-256 原样保留；新进程日志随后出现 `import state fired k=405`、`import consumed` 及三项 import PASS。两进程 XAR error 均为 0，证明写入、完全重启和读取链成立。具体分数随角色随机状态变化，验收以“A 写出的非零量化位阶等于 B 导入位阶”为准。

### 首世分流与只读账簿

- 正常 `xar_on` 导入完成且 `xa_global_record_imported=0` 时，契约接受选项跳转 `xar.0010` 首世说明，不打开 0 点商店；确认后直接进入 `xar.0004` 祝福流程。
- acceptance 的生产 UI 路径以 `xa_full_ui_test_active` 优先分流，仍向 `xa_local_points` 注入 200 并打开真实 `xar.0001` 商店，因此不会被首世逻辑短路。
- 原生 `xar_ledger_decision` 仅对 `xa_enabled && is_ai=no` 显示和生效。账簿事件调用生成的 `xar_prepare_ledger_effect`，把只读即时分数投影为当前候选位阶、下一位阶和差值。
- 该投影与死亡量化共用 `gen_highscore.py` 的 `THRESHOLDS`；扩展 `TIERS` 后会同步生成新的下一位阶邻接关系。达到最高阈值时 next 固定为 cap、gap 为 0，并显示明确上限文案。
- `xa_ledger_*` 只承载当前事件的临时展示快照，关闭事件即清除；它不设置 `xar_hs_ge_*`、不改 `xa_global_record_imported` / `xa_record_candidate` / `xa_run_score`，也不改变任何玩家资源。

## 已知限制

- 需开启教程设置（reactive advice）才能完成新 lesson 并把新位阶写入 `tutorial.txt`。禁用教程时，已完成 lesson 的接口读取和导入仍可工作，但本次及后续新纪录无法落盘。
- `tutorial.reset` 控制台命令会清空全部位（含原版课程）；手动删 tutorial.txt 同理
- 位容量有限；跨存档对象是余烬位阶/量化纪录，不是精确最高分。精度等于所在层的粒度，当前上限 166,600。

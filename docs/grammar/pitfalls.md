# 踩坑合集（按错误信息索引）

本项目实测踩过的坑。遇到报错先在这里检索关键词。

## 加载/解析期

| 错误信息 | 原因 | 解法 |
|---|---|---|
| `should be in utf8-bom encoding`（lexer.cpp，txt/gui） | 文件无 BOM | 加 UTF-8 BOM（警告级，建议都加） |
| `Missing UTF8 BOM`（yml） | yml 无 BOM | **必须加**，否则整个文件不加载 |
| `Cannot read [xxx] as a script value` / `Failed to find a valid event target link 'xxx'` | script value 定义放错目录 | 目录是 `common/script_values`，不是 `scripted_values` |
| `Theme missing in event` | 事件没写 `theme` | 加 `theme = <common/event_themes 里的键>` |
| `Unknown effect: after` | 事件 option 里写了 `after` | CK3 option 没有 after 字段；逻辑直接写在 option 里 |
| `Missing loc key 'x' for custom localization` | 当前语言的 yml 里没有该键 | custom loc 的键不吃英文回退，**每种在用语言的 yml 都要有** |
| `Unknown anchor 'topleft'` | 锚点写法 | 用 `top\|left` 这类合法组合 |
| `Variable 'x' is used but is never set` | 有引用无写入（删残留代码没删干净） | 清理孤儿引用 |
| `gui/xxx.gui: 文件 should be in utf8-bom`（scripted_widgets 等） | 同上 BOM | 加 BOM |

## on_action / 事件流程

| 现象 | 原因 | 解法 |
|---|---|---|
| 原版开局逻辑失效（`There is more than one 'effect' defined`） | on_action 同名字段**覆盖不合并** | 只加 `on_actions = { 自定义钩子 }` 条目 |
| 开局钩子里玩家/规则拿不到 | `on_game_start` 时机太早 | 用 `on_game_start_after_lobby` |
| effect 里设的值，同 on_action 触发的事件读到旧值 | effect 与事件**并发**执行 | 计算进事件 immediate，或事件延迟 1 天 |
| 延迟事件没触发 | root 到点时失效（on_death 的角色已死） | 触发到存活 scope（如 `player_heir`） |

## 变量

| 现象 | 原因 | 解法 |
|---|---|---|
| `Event target link 'global_var' returned an unset scope`（save_temporary_scope_value_as） | 该字段把 `global_var:` 当 scope 链接解析 | 改用 `save_scope_value_as` |
| 事件 desc 里显示 0 | 保存用了 `save_temporary_scope_value_as`（生命周期不够）或上一条 | `save_scope_value_as` + `[TopScope.GetValue('名')]` |
| `Failed to fetch variable ... not being set` | 读了从未设置的变量 | 先 `if NOT has_global_variable` 兜底设默认 |
| `Wrong scope for effect: character, expected dynasty` | 迭代器 scope 不对 | `every_dynasty_member` 需在 dynasty scope：角色下先 `dynasty = {}` |

## 教程课程 / 全局存储

| 现象 | 原因 | 解法 |
|---|---|---|
| `Reading an interface trigger 'is_tutorial_lesson_completed' in forbidden area` | interface trigger 用在游戏状态脚本 | 只能在 customizable_localization / GUI 里用，读取走三层桥（见 ../cross-save-persistence.md） |
| 自定义窗口 state 永不触发，无报错 | 窗口没在 `gui/scripted_widgets/` 注册 | 注册：`gui/x.gui = window_name` |
| `Tutorial.GetStepText` 等在自定义窗口为空 | Tutorial 上下文只在 tutorial_window 本体 | 别遥控；也不要从外面点——课程内用 `trigger_transition` 自动完成 |
| state 里 `Tutorial.OnClickTransition` 点了没反应 | 按钮动作函数不响应非用户点击路径 | 放弃模拟点击，用课程自带 `trigger_transition` |
| 哨兵文本显示成 `ERROR:[XXX]` | loc 内容含方括号被当命令解析 | 标记文本不要带 `[]` |
| `Unknown effect: add_influence` | 影响力没有 add_influence | 用 `change_influence = 100`（add_gold/prestige/piety 才有 add_ 形） |
| `Failed parsing data statement 'PauseMenu.ExitGame'` | GUI 数据上下文按窗口注入（同 Tutorial 一类）；且该函数要参数 | 原签名 `PauseMenu.ExitGame( '(bool)yes' )`；即便写对，从自定义窗口 state 调用也无效。回主菜单/观察者模式走 `ExecuteConsoleCommand('observe')` 之类 |
| 同名 character modifier 重复购买不生效 | add_character_modifier 同名不叠加 | 用一系列不同名修正逐个发放（见 modifiers/xar_modifiers.txt 的 50 层寿命） |
| 事件选项太多溢出 | option_grid 不支持滚动 | 分页（页变量 + 翻页选项 + 重触发事件） |
| 免费宗教改革无 effect | 改革走信仰窗口 GUI | 发 `faith_creation_piety_cost_mult = -1` 修正让费用归零 |
| `has_global_variable` 门控初始化导致首帧读到 none | 引擎加载时静态注册所有被引用的全局变量名：检查为 true 但值仍是 none，初始化被跳过 | 一次性初始化放到只执行一次的上游（如开局事件选项里），不要用存在性检查做幂等 |
| 窗口移出屏幕后 state 停求值 | 离屏被裁剪 | 隐身用"无背景+点击穿透"，不要移出屏幕 |
| `Unknown effect: add_renown`（1.19） | 没有 renown effect | 宗族威望：`dynasty ?= { add_dynasty_prestige = 150 }` |
| `add_gold effect [ Negative value in: {}. {} ]`（运行期） | `add_gold` 运行期拒绝负值（字面值/值块都不行）；`remove_gold` 和（无目标的）`pay_gold` 均**未注册为 effect**（effect_localization 里的条目是死 loc） | 1.19 没有合规的一次性扣金币手段。改设计：用 `monthly_income = -1` 这类角色 modifier（祝福诅咒池诅咒 0 即如此） |
| `mother trigger [ Failed context switch ]` / `father trigger ...`（运行期刷屏） | 触发器里 `father = {}`/`mother = {}` 链对**不存在/未知**的亲属报运行期错误，且 `OR` 不短路（每分支都求值）——`every_dynasty_member` 循环里一行链 × 全宗族 = 错误风暴 | 后代统计改为从死者 `every_child` 逐层向下遍历（effect 的上下文切换对空链安静），5 代展开 + 临时 flag 去重 + 事后清 flag。见 xar_effects.txt 的 `xar_desc_node_l1..l5` |
| `player_heir` 在 `on_game_start_after_lobby` 里是空 | 继承人在开局钩子时点尚未指派 | 要在死后于继承人身上跑逻辑：从结算事件（root=继承人）里嵌套触发检查器 |
| 结算事件窗打开后时间永远不走 | 事件窗（至少 character_event 结算窗）**硬暂停**游戏（底栏 tooltip「因轮回终结事件暂停」）；开局也默认暂停、死亡弹继承窗强制暂停 | 依赖日 tick 的逻辑必须在该窗打开前完成，或嵌套立即执行（`trigger_event = x.x` 无 days = 同链同步执行） |
| 开局 GUI 桥偶尔迟迟不触发 | scripted GUI 桥（xar_meta）的求值 tick 会被模态窗（继承/结算）饿死 | 自测类链路：先轮询等桥交付（自重排的隐藏事件 days=1），再做不可逆动作（如自杀） |
| `Unrecognized loc key xar_..._slot_x`（CEventOptionDesc，**加载期**）；补同名 yml 后三个选项全显示 fallback | 事件选项 `name` 不能直接消费 custom-loc resolver；同名静态 yml key 不会被 resolver 覆盖，反而会遮蔽动态值 | 事件改用普通 wrapper key，yml 内容写 `[SCOPE.Custom('xar_..._slot_x')]`；resolver key 本身禁止出现在 yml。`tools/validate_loc.py` 同时校验 wrapper 精确内容和同名遮蔽（2026-08-18 简中实机 OCR 验证） |
| 事件切换后 OCR 读到上一事件并误点 | `debug_log` 在事件 `immediate` 执行时写出，早于新模态窗口完成像素替换；日志 marker 只能证明脚本已开始，不能证明 UI 已稳定 | marker 后继续 OCR 等待新事件标题出现，再读选项；截图前把鼠标移出选项区，避免 debug tooltip 被识别成选项行（2026-08-18 实测） |
| 事件 immediate 里 `has_game_rule` 表现存疑 | 未查明（该行无日志可判定真假） | 换用全局旗标：`has_global_variable`（任何上下文都可靠） |

## 事件背景图 / 纹理

| 现象 | 原因 | 解法 |
|---|---|---|
| `environment reference empty` / `ambience reference empty`（event_background_database.cpp） | `common/event_backgrounds` 的定义缺字段 | 两个都必须填：`environment = "environment_standard"` + `ambience = "event:/SFX/..."` |
| 自定义事件场景图不显示/黑 | 纹理格式 | 必须 DDS；事件场景规格 **1592×848 DXT1**（原版 alley.dds 实测），Pillow 可写（`save(pixel_format="DXT1")`），路径放 `gfx/interface/illustrations/event_scenes/`，事件里 `override_background = { reference = <背景键> }` |
| character_event 窗口右半边空着 | 窗口类型固定布局：左文本列 + 右立绘区，无立绘角色就空 | 把人物合成进背景图右半（tools/compose_avatar.py）；或改用 `type = letter_event` 窄窗（信纸风，无大图背景） |
| 事件窗口尺寸想改 | window 类型由事件 type 决定，theme 只管图标/标题底/音效/默认背景 | 不想覆盖全局 GUI 就别动；用构图迁就窗口 |

## 调试技巧速查

- 解析验证：启动到主菜单 → 读 `error.log`
- 链路断点：每环节 `debug_log = "XAR: ..."` → 读 `debug.log`
- 全局存储验证：直接看 `tutorial.txt`
- 死亡链测试：控制台 `die`；事件测试：`event <id>`

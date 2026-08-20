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
| `Variable 'x' is set but is never used` | 生成器写入了没有任何游戏状态读取者的变量；只在 localization 中用也不算读取 | 删除无用写入，或让机制在状态脚本中实际消费；不要白名单忽略 |
| `Variable 'x' is set but is never used`，但变量已用于 `debug_log` 本地化 | localization 读取明确不计作状态脚本消费；开发采样 wire 因此会为每个 character variable 报错 | 在输出后用一个临时 global 逐个读取 `var:x`，最后删除临时 global。2026-08-19 长期平衡摇测实测 |
| `Unknown trigger: title_tier`（`every_held_title` 内） | 进入 title scope 后，层级 trigger 名是 `tier`，不是 `title_tier` | 写 `limit = { tier >= tier_county }`；角色 scope 才使用 `highest_held_title_tier`。2026-08-19 加载期实测 |
| `Unknown trigger: every_in_list` | `every_in_list` 是 effect 迭代器，不能放在 scripted trigger 中；即使同名列表语法可在 effect 使用，trigger 解析器也不会注册它 | 要求列表每项都满足条件时使用 `any_in_list = { variable = <list> count = all ... }`。2026-08-20 CK3 1.19.0.6 付费廷臣加载期实测 |
| `You should not set a size on a container! Containers resize to contain all of their children.` | dynamic list/grid 的 `item.container` 是自动包裹容器；每个实例给它写 `size` 都会重复报一条 GUI error | 删除外层 `container.size`，把尺寸留给内部按钮或 widget。2026-08-20 CK3 1.19.0.6 动态 trait 目录实测 |
| 动态文化列表生成了正确数量的按钮行，但文化名称全部为空且无 GUI 报错 | heritage 标题仍可见，容易让 OCR/人工误以为文化目录已完成；本例并非 loc 缺失，直接改成 `[CultureTemplate.GetName]` 或原版 wrapper 仍为空，实际是子项内容没有按原版嵌套结构取得可用布局 | 代表文化 scope 先取 `Scope.Culture.GetHeritage`，再以 `CulturePillar.GetCulturesWithPillar` 建子列表；子 item 用 `Culture.GetTemplate`。按钮内容必须保留独立缩进 `hbox`，其中以 `[Culture.GetNameNoTooltip]` 渲染名称并在末尾放 `expand = {}`；选择 scope 用 `Culture.MakeScope`。2026-08-20 CK3 1.19.0.6 `xar_courtier_creator_postreview22_20260820` 实测 |
| 动态 Faith 行可见且 tooltip 正常，但点击后 scripted GUI 完全没有执行 | 把原版 `Button_Select_Faith` 模板直接搬到非 ruler-designer 窗口会携带不适用的交互状态；此外，GUI saved scope 的目录成员判断不适合作为行按钮的前置门禁，内容子层还可能吞掉自动化点击 | 外层使用普通 `button_standard_hover`，在父层以 `Scope.Faith` 切换上下文，内容 `hbox` 设 `alwaystransparent = yes`；选择 effect 只校验玩家访问和 `scope:faith` 存在，最终配置/购买仍负责目录成员校验。自动化先用 OCR 定位行，再点击实测有效的行内空白并等待 effect marker，不把“发出点击”当成功。2026-08-20 CK3 1.19.0.6 `xar_courtier_creator_postreview22_20260820` 实测 |
| `gfx/interface/icons/traits/_stars_N.dds: failed to read trait level star texture` | trait 的 `track` 有 N 个 entry 时，引擎按 `TRAIT_OVERLAY_LEVEL_STARS` 自动请求 `_stars_N.dds`；CK3 1.19.0.6 原版只提供 0–5，十级 trait hover 会每帧刷缺图错误 | mod 必须补同路径的 `_stars_10.dds`。本项目由 `tools/compose_trait_stars.py` 程序化生成并做逐字节静态 parity；验收把 `failed to read trait level star texture` 视为项目错误，即使该日志行不含 `xar`。2026-08-21 【琉焰之视】hover 实测。 |
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
| `Data error in loc string`，hidden event 的 `debug_log = <loc_key>` 中 `ROOT.Var` / `ROOT.Char.MakeScope.Var` 全部渲染为空 | 原版可行样例是在可见 character event 的 option 中求值；hidden event `immediate` 的 debug-log 本地化没有等价数据上下文，多跨一层事件也无效 | 不用动态 localization 传遥测。用 script value 对生产 global 做 `abs/floor/divide/modulo 2`，再以静态 bit marker 在 BEGIN/END 间编码，外部 runner 还原。2026-08-19 长期平衡摇测实测 |
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
| 进入观察者后 `Object of type 'character' is not valid for '<custom loc>'` 每帧刷屏 | 顶层 GUI 在 `GetPlayer` 失效后仍调用 `GetPlayer.Custom(...)`；`And(GetPlayer.IsValid, ...)` **不短路** | 父窗口仅用 `visible = "[GetPlayer.IsValid]"`，把 custom-localization 求值放到其受保护子树；需要驱动另一顶层 modal 时，由父窗口 state 写 `GetVariableSystem` 旗标，modal 只读该旗标。2026-08-18 实机复现；2026-08-21 铁人终局首次回归以 45 条同类错误再次验证 |
| 首次打开随机池时大量 `Failed to fetch variable ... due to not being set`，但 effect 第一行明明初始化了变量 | 事件 tooltip/description 会预求值后续 `if`/`random_list.trigger`，早于同一 effect 的实际执行 | 在触发抽池事件之前的上一个事件/effect 中创建全部槽位变量；抽池内部初始化只负责重置。2026-08-18 首世生产链实测 |
| `Unknown effect: add_influence` | 影响力没有 add_influence | 用 `change_influence = 100`（add_gold/prestige/piety 才有 add_ 形） |
| `Failed parsing data statement 'PauseMenu.ExitGame'` | GUI 数据上下文按窗口注入（同 Tutorial 一类）；且该函数要参数 | 原签名 `PauseMenu.ExitGame( '(bool)yes' )`；即便写对，从自定义窗口 state 调用也无效。非铁人终局可走 `ExecuteConsoleCommand('observe')`；铁人模式禁止控制台命令，必须分支到注册 modal，以 `OnPause` 保持暂停、`OnPauseMenu` 打开原生菜单，再让玩家走原生自动保存/退出。`OnPause` 是 toggle，只能在 `Not( IsGamePaused )` 时调用。2026-08-21 CK3 1.19.0.6 非 debug 实测。 |
| 同名 character modifier 重复购买不生效 | add_character_modifier 同名不叠加 | 用一系列不同名修正逐个发放（见 modifiers/xar_modifiers.txt 的 50 层寿命） |
| 事件选项太多溢出 | option_grid 不支持滚动 | 分页（页变量 + 翻页选项 + 重触发事件） |
| 免费宗教改革无 effect | 改革走信仰窗口 GUI | 发 `faith_creation_piety_cost_mult = -1` 修正让费用归零 |
| `has_global_variable` 门控初始化导致首帧读到 none | 引擎加载时静态注册所有被引用的全局变量名：检查为 true 但值仍是 none，初始化被跳过 | 一次性初始化放到只执行一次的上游（如开局事件选项里），不要用存在性检查做幂等 |
| custom localization / GUI 每帧刷 `Failed to fetch variable ... not being set` | 可见性桥用数值比较读取尚未赋值的全局变量；custom loc 会高频重复求值，把一次错误放大成错误风暴 | 布尔信号改用 `has_character_flag` 等无未初始化值的 trigger；不要在首帧可求值的 GUI/custom loc 中数值读取未设全局变量（2026-08-18 实测） |
| 窗口移出屏幕后 state 停求值 | 离屏被裁剪 | 隐身用"无背景+点击穿透"，不要移出屏幕 |
| `Unknown effect: add_renown`（1.19） | 没有 renown effect | 宗族威望：`dynasty ?= { add_dynasty_prestige = 150 }` |
| `add_gold effect [ Negative value in: {}. {} ]`（运行期） | `add_gold` 运行期拒绝负值（字面值/值块都不行）；`remove_gold` 和（无目标的）`pay_gold` 均**未注册为 effect**（effect_localization 里的条目是死 loc） | 1.19 没有合规的一次性扣金币手段。改设计：用 `monthly_income = -1` 这类角色 modifier（祝福诅咒池诅咒 0 即如此） |
| `create_character effect [ Cannot specify both location and employer ]` | 同一个 `create_character` 同时写了 `location = ...` 与 `employer = ...`；2026-08-20 CK3 1.19.0.6 PostValidate 实测 | 创建受雇廷臣时只写 `employer = root`，让雇主关系决定归属；不要再并列指定 location。原版 `ep3_laamp_decision_events.txt:22389-22407` 同样只用 employer |
| 只选一项相反特质时配置仍被判无效 | 多子条件 `NOT = { A B }` 会要求两个子条件都不成立，不等价于“禁止 A 与 B 同时成立”；2026-08-20 CK3 1.19.0.6 付费廷臣实机验收复现 | 用 `NAND = { A B }` 表达“不可同时成立” |
| `Script system error! (while building tooltip/description)` + `Failed to fetch variable ... due to not being set`（决议详情 hover） | 决议 UI 会预演 `effect` 来生成 tooltip，且 **`hidden_effect` 内的 `trigger_event` 也会追进事件 `immediate`**。预演器不保证其中先 set global、后读取 global 的顺序，账簿阈值链因此一次产生数千条错误；2026-08-18 CK3 1.19 实测 | decision 的 `hidden_effect` 只设置 pending global；由注册的 1×1 GUI window 通过 scripted GUI 在真实点击后消费 pending 并 `trigger_event`。不要从 decision effect（包括 hidden_effect）直接打开含顺序依赖的事件 |
| `mother trigger [ Failed context switch ]` / `father trigger ...`（运行期刷屏） | 触发器里 `father = {}`/`mother = {}` 链对**不存在/未知**的亲属报运行期错误，且 `OR` 不短路（每分支都求值）——`every_dynasty_member` 循环里一行链 × 全宗族 = 错误风暴 | 后代统计改为从死者 `every_child` 逐层向下遍历（effect 的上下文切换对空链安静），5 代展开 + 临时 flag 去重 + 事后清 flag。见 xar_effects.txt 的 `xar_desc_node_l1..l5` |
| `player_heir` 在 `on_game_start_after_lobby` 里是空 | 继承人在开局钩子时点尚未指派 | 要在死后于继承人身上跑逻辑：从结算事件（root=继承人）里嵌套触发检查器 |
| 结算事件窗打开后时间永远不走 | 事件窗（至少 character_event 结算窗）**硬暂停**游戏（底栏 tooltip「因轮回终结事件暂停」）；开局也默认暂停、死亡弹继承窗强制暂停 | 依赖日 tick 的逻辑必须在该窗打开前完成。无 delay 的 `trigger_event` 不跨游戏日，但不能把它视为阻止原生继承窗先出现的原子屏障 |
| `on_death` 已打印父 effect 日志，但死亡 root 上的 hidden child event 永不进入 `immediate`；或 delayed heir event 被 trigger 静默拒绝 | CK3 1.19.0.6 可先显示继承窗并使死者失效；实测 scorer 后的父语句未执行，delayed control event 则显示 score/scopes 已提交但死者的 `xa_enabled` 已被清除 | 仿照原版 `death_management.0100`：在 dying root 有效时先保存 dead/carrier scope 并排入 living-heir `delayed = yes` event，再执行 scorer。delayed trigger 用预先建立的全局角色见证认证，不得重查死者 flag、AI 状态或继承关系；无继承人才保留同步链 |
| `days = 1095` 重开被报告为累计每轮多一天 | delay 从每次安排它的成交 option 当日计算，不从整局开局日计算；重开打开下一场到 runner 完成可见成交可能再跨一日 | 用同号 `reopen.elapsed - pair.elapsed = 1095` 验证逐笔 timer；绝对 elapsed 只作证据，不与 `n×1095` 比较。2026-08-20 emperor 长测实证 |
| 开局 GUI 桥偶尔迟迟不触发 | scripted GUI 桥（xar_meta）的求值 tick 会被模态窗（继承/结算）饿死 | 自测类链路：先轮询等桥交付（自重排的隐藏事件 days=1），再做不可逆动作（如自杀） |
| `Unrecognized loc key xar_..._slot_x`（CEventOptionDesc，**加载期**）；补同名 yml 后三个选项全显示 fallback | 事件选项 `name` 不能直接消费 custom-loc resolver；同名静态 yml key 不会被 resolver 覆盖，反而会遮蔽动态值 | 事件改用普通 wrapper key，yml 内容写 `[SCOPE.Custom('xar_..._slot_x')]`；resolver key 本身禁止出现在 yml。`tools/validate_loc.py` 同时校验 wrapper 精确内容和同名遮蔽（2026-08-18 简中实机 OCR 验证） |
| 事件切换后 OCR 读到上一事件并误点 | `debug_log` 在事件 `immediate` 执行时写出，早于新模态窗口完成像素替换；日志 marker 只能证明脚本已开始，不能证明 UI 已稳定 | marker 后继续 OCR 等待新事件标题出现，再读选项；截图前把鼠标移出选项区，避免 debug tooltip 被识别成选项行（2026-08-18 实测） |
| trait track hover 报 `VFSOpen Error: gfx/interface/icons/trait_level_tracks/<trait>.dds not found` | 原生 trait track 按 trait key 自动加载独立 track 图标，不复用 trait 定义里的 `icon =` | 补 `gfx/interface/icons/trait_level_tracks/<trait_key>.dds`，并纳入发布资源静态校验（2026-08-18 实测） |
| 事件 immediate 里 `has_game_rule` 表现存疑 | 未查明（该行无日志可判定真假） | 换用全局旗标：`has_global_variable`（任何上下文都可靠） |
| 同一 `immediate` 内把 scripted value 或计算结果分别复制为“修改前/修改后”变量，两个快照仍相等 | 同一 effect 链内的变量复制未形成可依赖的时间序列快照，具体求值时机未查明 | 改为断言一次正式计算后的固定不变量，或跨事件边界后再比较；不要在同一 `immediate` 内做 before/after 快照。2026-08-18 成长赛道 selftest 实测 |
| 同一事件 `immediate` 内先计算并写 global，再用 `save_scope_value_as` 复制该 global，报 `Value of wrong type ... none` | scripted effect 返回后也不构成写入可见边界；事件内后续表达式仍可能在写入提交前求值。2026-08-18 账簿链实测：score capture、阈值投影和显示快照各需要独立事件 | 把每个存在读后写依赖的阶段拆成连续 hidden event，最终可见事件只读取上一事件已经提交的 globals |
| 无继承人同步结算显示 0，或外部 GUI 的 `SuccessionEventWindow.GoToMenu` 点击无效 | 死亡计分仍在 `on_death` 父 effect 内未提交；且 `SuccessionEventWindow` action 只在原生窗口有完整输入上下文。2026-08-18 CK3 1.19.0.6 实测 | 使用 `on_death -> hidden compute -> hidden dispatch -> hidden snapshot` 前向事件链；把结算 widget 生成注入原生 `window_succession_event.gui`，按钮在原生窗口内调用 `GoToMenu` |
| 正数差值经过 `max = 0` 后总是变成 0 | CK3 数值块的 `max` 是上限、`min` 是下限；`max = 0` 会把所有正数压到 0 | 表达 `max(value, 0)` 要写 `min = 0`。2026-08-18 成长计分与账簿差值实机定位 |
| 原版 effect 报错的调用栈只因 `common/on_action/xar_*.txt` 路径而命中 XAR 错误门禁 | 用 `on_actions = {}` 扩展原版 hook 后，引擎会把原版 effect 的调用者位置归到扩展定义文件；2026-08-19 九年长测实测 EP3 `war_task_contracts_completion_effect` 的原版错误因此带上适配器路径，但没有进入 `xar_contract_*` effect | on_action 适配器使用不含 `xar` 的中性文件名，hook/effect 标识仍保留 `xar_*`；这样真实自定义 effect 错误仍会由脚本位置中的符号命中门禁，原版错误不会仅因调用者文件名误报 |
| 死亡中间节点后的在世后代不计分，或清理时报 `remove_character_flag effect [ scope is dead during effect execution ]` | `every_child`/`any_parent` 关系列表默认排除已故角色；加 `even_if_dead` 后，清理 effect 又会实际进入 dead scope，而角色 flag effect 不接受死者 | 后代展开、清理和 preview 的所有关系列表都加 `even_if_dead = yes`；计分与清 flag 分别包 `is_alive = yes`，关系遍历仍可穿过死者。2026-08-19 受控谱系 `xar_accept_h0lgmvyf` 实测 1–5 代、死亡中间节点、双路径去重和清理，0 `xar` errors。 |

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

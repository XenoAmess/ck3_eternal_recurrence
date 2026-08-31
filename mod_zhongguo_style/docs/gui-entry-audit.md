# 361 GUI 入口与按钮布局审计

日期：2026-08-29（Asia/Shanghai）

静态事实更新：2026-08-31（Asia/Shanghai）

目标版本：CK3 1.19.0.6

当前审计对象：`gui/zg361_scoreboard.gui`，SHA-256 `9550A4DA7DF1E4052A3D32E9A1A988AEF563AAD4D7D08C58A75D85E513DC2FC2`。

状态：当前精确字节仅为 `static-ready`。对 41 份保留的实机 runtime 副本逐一计算 SHA-256，命中当前 SHA 的副本为 **0**；下文旧 SHA 的实机结果仅作历史诊断证据，不能继承为当前字节的 L3 或整批 GREEN。

## 1. “考核榜”为什么会出现在奇怪的位置

旧投影把 `180×44` 的常驻按钮直接挂在全屏顶层窗口上：

```text
parentanchor = top|right
position = { -205 165 }
```

这个坐标既不属于原版顶部资源栏，也没有贴住右侧 `50` GUI 单位宽的主功能栏；它会悬在地图右上方。更重要的是，旧按钮的可见性只检查有没有榜单数据，不检查原版右侧窗口是否打开。

已有 2560×1440 实机证据确认了两个问题：

- `cell/04_gameplay_hud.png`：按钮脱离原版 HUD 控件组，独自悬在右上地图区。
- `cell/07_scoreboard_button.png`：原版“决议和大型工程”抽屉打开时，按钮仍盖在抽屉的标题/内容区域上，视觉上像是决议列表的一部分，也会争抢该区域鼠标输入。

证据根目录为：

```text
Z:\ck3_mod_rewrite_process_assets\zg361\runs\zga_20260829_061314_ea5f04ad
```

原版 CK3 1.19.0.6 的相关 HUD 契约是：

- outliner 按钮：`parentanchor = top|right`、`position = { -5 55 }`；
- 主功能栏：`parentanchor = top|right`、`position = { 0 90 }`、宽 `50`；
- 相邻原版控件会在 `IsRightWindowOpen`、暂停菜单、非默认 GUI 模式等状态下隐藏。

## 2. 最小布局修复

权威修改点是 `tools/gen_scoreboard_snapshot.py`，不能手改生成的 `gui/zg361_scoreboard.gui`。

新按钮保持完整的 `180×44` 多语言文本空间，但改为：

```text
parentanchor = top|right
position = { -60 90 }
```

它的右边缘离屏幕右侧 `60` GUI 单位，正好留出原版 `50` 单位主功能栏和 `10` 单位间隙；顶部与原版主功能栏的 `y = 90` 对齐。参考布局矩形为：

| 分辨率/投影 | 按钮矩形（left, right, top, bottom） | 结论 |
|---|---:|---|
| 1920×1080 GUI 参考空间 | `(1680, 1860, 90, 134)` | 完整可见，右侧留 60，顶部资源栏下方 |
| 本机 2560×1440，1.30 HUD 缩放 | `(2248, 2482, 117, 174)` | 完整可见；右侧留 78 px，扣除约 65 px 原生栏后仍有约 13 px 间隔 |

按钮容器现在同时要求：

- `Not(IsPauseMenuShown)`；
- `IsDefaultGUIMode`；
- `Not(IsGameViewOpen('struggle'))`；
- 玩家 scope 的 `hide_ui_main_tabs <= 0`；
- `Not(IsRightWindowOpen)`；
- `Not(IsGameViewOpen('outliner'))`；
- `Not(IsGameViewOpen('barbershop'))`。

以上共七项 HUD 显示门。`outliner` 必须单独排除，因为它本身不是一个可用 `IsRightWindowOpen` 判定的普通右侧窗口；`struggle` 与 `hide_ui_main_tabs` 则镜像原版主功能栏在特殊视图和教程隐藏主栏时的行为。没有直接把按钮注入 `hud.gui`：那会整体覆盖原版大文件，制造版本升级和其他 UI mod 的高冲突面；相邻锚定加原生显示门是当前最小可靠方案。

## 3. 全部 mod 自有 GUI 入口清单

| 入口/控件 | 数量 | 父容器与层 | 显示/输入结论 |
|---|---:|---|---|
| 考核榜常驻入口 | 1 个逻辑入口、3 个互斥 `button_standard` 变体 | 全屏 `middle` 顶层中的右上锚定容器 | 优先级依次为“所辖榜”→“本人榜”→“仅制度账本”；第三种只在前两类数据均不可用而制度账本可用时出现，并直接打开制度页。外层全屏仍 `alwaystransparent = yes`，不会吞地图点击 |
| 模态背景关闭按钮 | 1 | `zg361_scoreboard_modal`，100%×100% | 仅榜单打开时存在；`filter_mouse = all`，点击面板外关闭，刻意阻止点击穿透到地图/原版窗口 |
| 标题栏关闭按钮 | 1 | 视口 `90%×90%` 居中面板标题栏 | 清除打开变量并支持原生 `close_window`（Escape）；重复清除是幂等操作 |
| 页签按钮 | 7 | 面板内部横向栏 | 3 个外层页签为“所辖官员”“本人所属考核单元”“制度驾驶舱”，4 个案卷页签为 facts/peer/quota/audit；各自带 availability、`onclick` 和 `down` 状态 |
| 所辖官员行链接 | 最多 80 个人物链接 + 80 个案卷按钮 | 所辖页双轴 scrollbox | 每行以冻结的角色 scope 为 datacontext；人物链接先调用原生人物点击再关闭榜单；同级案卷按钮只选择该冻结槽，不嵌套进人物按钮 |
| 本人考核单元行链接 | 最多 80 个人物链接 + 80 个案卷按钮 | 本人页双轴 scrollbox | 与所辖行同构；只有玩家本人行显示可用案卷按钮，只显示实际冻结槽位，不存在透明占位按钮 |
| 案卷返回按钮 | 1 | 唯一详情 pane 顶部 | 清除唯一 detail buffer，返回当前外层榜单，不复制 `160×4` 套详情页 |
| 按需滚动条 | 7 个水平 surface；既有名单/案卷垂直 surface 显式化，制度账新增 1 个垂直 surface | 2 个名单页、4 个案卷内页、1 个制度账页 | 使用原版 `Scrollbar_Horizontal` / `Scrollbar_Vertical`；只在内容超过当前 viewport 时出现，滚动控件受面板 scissor/modal 限制，不执行任何产品动作 |
| 决议执行桥 | 0 个可交互按钮 | `1×1`、`tutorial` 层、左上角 | `alwaystransparent = yes`，只有 state/on_start，没有鼠标命中区域；位置不构成遮挡 |
| 361 政策卡桥 | 0 个可交互按钮 | `1×1`、`tutorial` 层、左上角 | 同上；两个 state 只负责把原生决议确认后的标记写回游戏脚本 |

按当前生成文件的显式节点计，产品 GUI 有 `332` 个直接按钮节点：164 个 `button_standard`（3 个互斥 HUD
入口、160 个案卷按钮、1 个案卷返回）、1 个 `button_normal` 背景、7 个 `button_tab` 和 160 个
`button_tertiary` 人物链接。标题栏通过 `header_pattern` 的 inherited `button_close` override 再提供 1 个产品关闭定义，
所以产品动作按钮按定义计为 `333`。本轮没有新增产品动作按钮；新增的是 7 个原版水平滚动 surface（模板每个含
track/slider/dec/inc 四个导航后代，共 28 个）和制度账新增的 1 个垂直 surface（4 个导航后代）。它们只移动被
scissor 的内容；最坏情况下制度账同屏出现 8 个新增导航后代。两个 bridge 仍然没有按钮。

四项基础决议、361 张政策卡、京察活动入口、互动按钮和事件选项都由 CK3 原生决议/活动/互动/事件窗口渲染；本 mod 没有给它们额外叠放坐标，因此不属于这次 additive GUI 位置故障。

## 4. 面板尺寸、层级与点击审计

- 面板现在是父级视口的 `90%×90%`，继续以 `parentanchor = center`、`widgetanchor = center` 居中。百分比尺寸经 UI scale
  投影后仍占物理视口 90%，所以每边保留 5%：三档分辨率中最小物理边距是 1366×768 的纵向 `38.4 px`，高于静态合同
  的 `32 px`。旧 `1220×820` 固定外框已经从生成投影移除。
- 百分比外框不再强迫内部 `1120` 单位宽表格压缩。名单、案卷与制度账共 7 个内容 surface 都显式使用
  `scrollbarpolicy_horizontal = as_needed`、`scrollbarpolicy_vertical = as_needed`、原版双轴 scrollbar 和
  `set_parent_size_to_minimum = yes`；名单设计宽度为 `1120`，案卷为 `720`，制度账为 `760`。最窄格子可通过滚动访问
  内容，scrollbox 自己始终被 expanding viewport 与面板 modal 约束。
- 最坏格子 1366×768@150% 的逻辑面板是 `819.6×460.8`。按 CK3 1.19.0.6 原版 `Window_Margins`、
  `header_pattern`、`button_tab`、`Font_Size_Small`、`portrait_head_small` 和 12 单位水平滚动条逐项计入，名单、制度账、
  案卷字段面的固定 chrome 预算分别是 `200`、`236`、`417`；最坏滚动 viewport 分别仍有 `260.8`、`224.8`、
  `43.8` 逻辑单位，依次高于 `250`、`210`、`37` 的合同下限。案卷最窄时至少保留一条字段行的高度，其余字段经纵向
  滚动到达。这个数值是确定性静态投影，不是 CK3 已渲染证明；真实 rect、
  scrollbar visible/focus 与点击阻塞仍须用当前 SHA 的 MCP named-widget 状态复验。
- 入口按钮自身的右上锚点不依赖面板尺寸：1920×1080 参考空间矩形为 `(1680, 1860, 90, 134)`；2560×1440、1.30 投影为 `(2248, 2482, 117, 174)`，与原版右侧 `50` GUI 单位主栏保留 `10` GUI 单位间隔。面板超界与入口按钮超界是两个独立断言。
- 顶层窗口保持 `alwaystransparent = yes`，关闭状态下只有真实可见按钮接收输入。
- 模态层打开时改为 `alwaystransparent = no`、`filter_mouse = all`，这是有意的全屏模态语义；居中面板本身也截获输入，面板内点击不会误触背景关闭按钮。
- managed/received/ledger-only 三个常驻按钮变体按优先级互斥，不会静态堆出多个可点击热区。
- 三个外层页签和四个案卷页签只改变既有 variable-system 状态，面板仍由同一模态层持有；标题 X、外层页签和详情返回
  都在滚动 surface 外，不会随内容横向或纵向滚动到 viewport 外。
- 160 个人物链接和 160 个同级案卷按钮由生成器统一产出，尺寸、点击链与 frozen-snapshot 数据上下文完全同构；静态测试
  逐槽确认 80+80 行及 sibling 关系。

### 4.1 全局 UI 状态转换风险（未实机判定）

打开状态与当前页签使用未按玩家 scope 分区的 `GetVariableSystem` 键：`zg361_scoreboard_open` 和 `zg361_scoreboard_tab`。当前 GUI 只在 backdrop、标题 X/Escape 与人物行点击等显式交互中清理 `open`，没有在 `GetPlayer` 失效、切换玩家、继承或 managed/received/ledger availability 改变时执行生命周期清理，也没有把页签回退到仍可用页面。

此外，七项 HUD 门只包住常驻入口容器；已经打开的 modal 自身只检查 `open + 任一 availability`，不会随 Pause、非默认模式、struggle、`hide_ui_main_tabs`、右窗、outliner 或 barbershop 自动关闭/隐藏。因此静态上存在四条可达风险，均须保留为待测，不能直接定性为已发生的产品 bug：

1. 榜单打开时切换玩家或完成继承，若新玩家具有任一 availability，旧的全局 `open` 可能让榜单在新玩家上下文中自动保持/重新出现；
2. 旧页签在新玩家不可用时，modal 仍可能因另一类 availability 成立而显示，但 managed/received/system 三个内容容器全部不满足，形成有框无内容的空面板；
3. 若 `open` 在不可见阶段残留，下一次入口的 `Toggle` 可能先把它清掉，而不是完成用户预期的首次打开。
4. 榜单已经打开后再进入暂停菜单或原版右侧/特殊视图，modal 可能继续存在并与新界面叠层；仅验证“关闭状态下入口会隐藏”不能覆盖此风险。

最低复验必须在同一次 CK3 启动中执行“打开榜单 → 切换到真实 received-only 玩家 → 再切换到真实 ledger-only 公爵及以上天朝制玩家”，逐跳记录是否自动弹窗、是否空页、当前页签和第一次点击结果；不能只用新开局或重启后清零的状态证明无风险。

## 5. 回归与下一轮实机验收

当前静态回归应锁定：

- 新锚点、按钮安全矩形、`90%×90%` 外框和 3×3 几何投影；
- 七项原版 HUD 显示门；
- 三个入口变体的互斥优先级，以及 ledger-only 入口默认写入 `system` 页签；
- 直接产品按钮 `332`、包含 inherited X 为 `333`；本轮新增产品动作按钮为 0；
- 7 个按需双轴 scroll surface、各自 design width、scissor/modal 归属与 scrollbar 模板计数；
- 生成投影不可手工漂移；
- 两处 `shortcut = close_window` 为无引号原版语法、3 个外层页签、4 个案卷页签和 80+80 行入口的静态结构继续成立。

这些断言只能证明生成器与当前投影没有静态漂移；尤其不能把无引号 shortcut、互斥表达式或固定尺寸计算写成 CK3 已实际执行。当前精确字节建议按以下最小矩阵合批：

| 批次 | 配置/角色状态 | 必须连续验证的观察点 | 当前结论 |
|---|---|---|---|
| F1 主功能批次 | 2560×1440、1.30；真实宋帝，managed + ledger | 安全区入口；右窗打开时消失及关闭后恢复；managed → system → managed；深滚动；1 条真实 managed 人物行；标题 X、背景、**只按一次且不回退背景点击的 Escape** 各自关闭并可重开 | 待当前 SHA L3 |
| F2 七门批次 | 延续 F1 | 关闭榜单时，Pause、非默认 GUI mode、struggle、`hide_ui_main_tabs`、右窗、outliner、barbershop 每项至少连续两帧入口消失，退出后连续两帧恢复；再在榜单已打开时各触发一次，记录 modal 是关闭、隐藏还是叠层，且退出后状态可恢复。不得用另一扇门仍开启来冒充目标门通过 | 待当前 SHA L3；打开态为全局转换风险 |
| F3 全局状态批次 | 榜单保持打开后切换到真实 received-only 受考角色 | 不自动弹出、不出现空面板；第一次入口点击即打开 received；标题、考核人、年度与 `3.25` 可见；实点 received 页签与 1 条真实 received 人物行 | 待当前 SHA L3；也是 4.1 风险复验 |
| F4 第三入口批次 | 真实天朝制公爵及以上；ledger 可用、managed/received 均不可用 | 只出现第三入口；第一次点击直接打开 system；配置/校验和与 14 类账本均可见；关闭、重开仍落在可用页，不出现空面板 | 待当前 SHA L3 |
| F5 层级与发布画面 | 延续 F1/F4，触发一个正常产品事件 | 产品事件位于榜单之上；关闭事件后原页签与滚动状态可继续；画面没有 fixture 决议、测试按钮或 `ZGA` 文本 | 待当前 SHA L3；测试入口不得进入宣传素材 |
| G1 低分辨率三档 | 1366×768，100%/125%/150% | 外框 rect、标题 X、外层页签、名单双轴 scrollbar、案卷四内页、制度账双轴 scrollbar、背景阻塞和入口安全区；每档均从 named widget 重新定位 | 静态 3/3 安全；待当前 SHA MCP/实机 |
| G2 标准分辨率三档 | 1920×1080，100%/125%/150% | 同 G1；150% 必须实证名单水平滚动出现且最右案卷按钮可达，不能因默认停在左端写 GREEN | 静态 3/3 安全；待当前 SHA MCP/实机 |
| G3 高分辨率三档 | 2560×1440，100%/125%/150% | 同 G1；按需水平条在内容可完整容纳时应隐藏，不能留下无意义热区；入口仍与右侧主栏保持 10 GUI 单位间隔 | 静态 3/3 安全；待当前 SHA MCP/实机 |

F1–F5 应尽量放进一次 2560×1440、1.30 启动；G1–G3 是完整 9 格合同，应优先由 MCP named-widget 批量切换并读取 rect/
visible/focus/modal/blocking。若游戏允许可靠热应用显示设置就在同一进程完成，否则按分辨率合并成至多三次几何启动。所有
点击必须从当前 named rect 定位，不得复用 2560×1440、1.30 的固定像素；OCR 仍只准在状态真值闭合后截最终素材。

### 5.1 旧字节候选运行历史（仅作诊断证据）

当时的新布局已经随当时的正式候选进入 CK3 合批验收。该候选实机证据证明右侧原生抽屉打开时入口会被正确抑制；完整“关闭抽屉 → 安全区重现 → 打开榜单 → 切页/关闭”链仍以首次全绿报告为准，不能用中途 RED 冒充，也不能外推到其后的 `DECB9824…` 候选，更不能外推到当前 `FE00D622…` 字节。

截至 `zga_20260829_133619_5fbed52`，该历史合批只承诺已经发生的常驻入口、右窗抑制、原生决议抽屉标题 X、所辖页和页签点击。榜单自身标题 X、模态背景与人物行的代表性点击链是在该 RED 之后才接入 runner，当时只能称 static-ready；必须以对应 artifact 中的 `08_gui_audit_*` 截图和报告字段为准。即使一条人物行通过，也只证明同一生成结构的代表样本，绝不称作 160 条逐项 L3。

第三次候选运行 `promo/captures/zga_20260829_124857_7af8fc88` 已窄范围实证第 1–2 步：`07_scoreboard_hidden_by_right_panel.png` 中原生决议抽屉完整打开，而“考核榜”没有叠在抽屉上。随后 runner 只按了一次 Escape；当时鼠标仍停在决议行并显示 tooltip，Escape 没有关掉抽屉，故等待按钮重现超时。失败图仍是原生抽屉打开状态，说明产品显示门继续正确隐藏按钮；这是关闭状态机的 harness RED，不是把按钮藏丢。该失败 attempt 与录屏均永久保留，但不能替代完整 GUI GREEN。

第四次候选运行 `promo/captures/zga_20260829_130808_b030ccda` 已再次通过玩法主链、361/361、项目诊断零错误和右窗抑制，但暴露了测试器标题栏坐标录入错误：固定 2560×1440 截图里的原生 X 可见像素质心约为 `(2461, 92)`，归一化约 `(0.961, 0.064)`；旧常量 `(0.769, 0.050)` 实际点在抽屉标题文字附近。抽屉按预期没有关闭，连续两帧门禁因此明确 RED。修复只校正 harness 坐标并加像素投影回归，不放宽 `IsRightWindowOpen` 产品门禁；报告与录屏永久保留，完整 GUI GREEN 仍待下一次合批。

第五次候选运行 `promo/captures/zga_20260829_132440_957d8cc` 实证校正后的原生 X 点击有效：保存了 `07_scoreboard_right_panel_closed_by_title_button.png`，随后“考核榜”在限定安全区中心约 `(2365,145)` 重现并可打开完整面板，所辖页 OCR 通过。切到制度驾驶舱后，正常排队的产品事件“野狗与小白兔”覆盖在模态榜单上，使驾驶舱字段 OCR 超时；这是随机事件遮挡的 harness RED，不是页签、层级或坐标故障。下一轮在点击页签后只处理被完整识别的原生事件，再验证下层驾驶舱；不得以关闭或跳过驾驶舱断言来求绿。

第六次候选运行 `promo/captures/zga_20260829_133619_5fbed52` 中，干净制度驾驶舱已经完整渲染，但旧恢复器把驾驶舱居中的说明误认成事件并点击非交互页脚，仍为 harness RED。现候选修复先短门确认干净驾驶舱，只有缺字段时才进入保守事件恢复，并把原生事件标题限制在左半标题区；同时接入上述三个代表性按钮实点。两项都尚无该修复后的 CK3 结果，不能提前升级为 live GREEN。

第七次候选运行 `promo/captures/zga_20260829_150020_78d3e9fb` 在关闭“你主持的考核：名册已定”后停在干净地图；玩法主链、361/361 与项目诊断零错误均已通过，但 `timeout_07_scoreboard_overlay_gate_decisions_tooltip.png` 和 `fatal_state.png` 显示共享测试器用固定 `(0.987, 0.367)` 打开原生决议抽屉时，在拥有更多原生入口的宋帝右栏中命中了“派系 F7”，真正的“决议 F8”已向下移动。这证明右栏几何会随玩家角色变化，不能再把开局 Robert 的坐标当成语义定位。CK3 1.19.0.6 原生 `decision_window` 快捷键固定为 `F8`，harness 现改为在确认标题缺失后按 `F8`，并在标题区连续两帧确认“决议”出现；产品 `IsRightWindowOpen` 门禁和考核榜坐标均未修改。该次 RED 在榜单实点前终止，因此标题 X、模态背景、人物行和受评页签仍维持 static-ready，等待修复后的完整 GREEN。

第八次候选运行 `runs/zga_20260829_151729_213db5a6` 又给出一条独立实证：即便原生 tooltip 声明 `F8`，通过当前桌面自动化向已聚焦 CK3 直接发送功能键也没有打开抽屉。失败发生在开局 Robert、fixture 初始化与录屏之前，干净全屏图没有任何产品窗口可被误判。harness 因而只把 F8 留作非致命快速路径；缺少标题时改为逐个悬停右侧原生栏候选点，在限定右侧 tooltip 区真正 OCR 到“决议”后点击该点，再用连续两帧标题确认。这是角色无关的语义扫描，不回退到某个角色的固定纵坐标；产品 GUI 仍未改动。

第九次候选运行 `promo/captures/zga_20260829_154406_1d3a6295` 已把动态原生入口、考核榜右窗抑制、安全区入口、制度驾驶舱、标题栏 X 和全屏模态背景全部升级为 L3：Robert 与宋帝的“决议/F8”分别在 y=544 和 y=606 被语义识别，原生抽屉关闭后“考核榜”在 `(2365,145)` 重现；标题 X `(1991,240)`、背景 `(128,720)` 均关闭榜单并能重新打开。代表性人物行则发现真实产品 blocker：点击吕居简姓名时只出现该文字的 tooltip，父级整行按钮不响应。CK3 GUI 的 `alwaystransparent` 只约束声明它的 widget，不能假设容器会让有 tooltip/按钮语义的全部后代自动穿透；原版整行人物按钮也会在姓名等叶节点重复声明。权威生成器现为每行 12 个可见叶节点设置 `alwaystransparent = yes`，portrait 使用 `blockoverride "portrait_button"`，因此修复覆盖 160 条同构入口，但在下一次 1 条真实人物代表点击 GREEN 前仍只称 static-ready。受评页签尚未抵达，继续维持 static-ready。

第十次候选运行 `promo/captures/zga_20260829_160055_a4d24cd4` 已证明人物行产品修复生效：代表性点击“岭西经略使，杨完” `(896,508)` 后榜单标题消失，原生人物侧栏打开，并在限定左侧区域连续识别同一人物名；结构化证据记录 `scoreboard_closed=true` 与 `native_character_view_open=true`。标题栏 X、模态背景、制度驾驶舱与动态原生右栏也再次通过。此轮 RED 发生在测试器清理阶段：CK3 的人物侧栏没有响应三次 Escape，导致后续受评页和京察尚未执行；失败图中原生人物 X 位于约 `(592,20)`。runner 现直接点击该原生标题栏控件，并要求人物名连续两帧消失后才继续。故代表性人物行已是 production-live primitive，完整 GUI 批次和受评页仍等待下一轮整批 GREEN；160 行只声明共享结构静态覆盖加 1 行实点，不冒充 160 行逐条点击。

第十一次候选运行 `runs/zga_20260829_161849_1d78a5b6` 再次用“淮南观察使，梁适”证明整行可点击并打开正确人物；但第一次原生 X 修复误把工具内缩预览坐标当作 2560×1440 原图坐标，点击 `(591,20)` 实际命中配偶 portrait。隔离配置明确 GUI scale 为 `1.3`；原始 PNG 的金色 X 像素簇中心在 `(740,26)`，与 610 GUI 单位侧栏经缩放后的几何关系吻合。harness 已校正到 `(0.2891,0.0181)`，下一轮仍须以“人物名连续消失两帧 → 安全区考核榜入口重现两帧 → 所辖页重开”闭合完整清理链；本次仍是 harness RED，不撤销两次独立的人物行产品实证。

## 6. 第十二次历史候选的 GUI 阻塞结论

`promo/captures/zga_20260829_163300_59bb983` 已在同一实机启动中闭合人物行清理链：代表行“青徐观察使，卢士宗”打开正确原版人物页，校正后的原版 X `(740,26)` 一次关闭，人物名连续消失，安全区入口重新出现，榜单随后成功重开。对应三帧 SHA-256 依次为 `2767427C559FA20CC715CBFFE3DB6D0D01423731D677D643E045C59BC1186448`、`024CE29313BB49CDE414CFEBE58F8E5AC6DB3B7D8CD6EB802FD61D81FC847566`、`D88D69FA24222FB0814FBD0F21FC652A82A66D2DD0F453E7C8A7026286AD9EE4`。

因此，该轮历史字节只证明所辖页、驾驶舱切换/返回、标题栏 X、模态背景和 1 条所辖人物行。本人榜入口、本人页签与本人榜人物行仍无该轮字节的 deliberate-click L3；驾驶舱也缺少“关闭榜单 → 重开 → 再进入”的独立闭环。后来八轮还反复证明 Escape 没有关掉榜单，所以不得继续用“三个页签和全部关闭路径均已有实机证据”的口径。下一轮仍会在同一次启动里批量重跑，不借用局部通过冒充整批 GREEN。

## 7. 2026-08-29 新一轮阻塞审计与修复

只读审计当时对照 GUI SHA-256 `B50D3122907AAF25A6E82BF1C60528095E85DBAA749526656F960C1813EA03AB` 与最新同字节实机投影，发现三个产品缺口：

1. 只有 361 制度账本、尚无 managed/received 榜单时，HUD 没有任何按钮变体，modal 也拒绝显示，制度驾驶舱被困死。
2. HUD 显示门没有镜像原版 `main_tabs` 的 `struggle` 与 `hide_ui_main_tabs`；中国教程真实设置后者时，原生栏可能隐藏而考核榜独自残留。
3. backdrop 和标题 X 都写成 `shortcut = "close_window"`；八轮实机中 Escape 均未关闭榜单，原版同类控件使用无引号 `shortcut = close_window`。

权威生成器随后作了最小修复：增加 ledger-only 第三个互斥入口并默认打开 `system` 页；modal 可由 managed、received 或 ledger 任一状态维持；显示门补齐 `struggle` 与 `hide_ui_main_tabs`；两处 shortcut 改为原版无引号形式。生成投影与九项静态测试曾通过。Escape 的根因虽然与原版语法差异高度吻合，但在当前精确字节完成 CK3 同批复验前仍只标 `static-ready`，不能提前写成 L3。

### 7.1 2026-08-30 前一候选的精确字节边界

- 该候选生成投影 SHA-256：`DECB98240A4FE328E2A5FB18606713C88760A13343D337312A62A7667C1BDB5C`；当时的权威生成器 `tools/gen_scoreboard_snapshot.py` SHA-256：`162EF4731DD011D0B409540670ED7C006D697B7A9173C95E9EFBCD223C054752`。
- 从 `Z:\ck3_mod_rewrite_process_assets\zg361` 扫描到 41 份保留的 `mod-content/zhongguo_361/gui/zg361_scoreboard.gui` runtime 副本；其 SHA 只有五种更旧值，命中 `DECB9824…` 的数量为 **0**。因此该候选字节的 GUI L3 次数为 **0**。
- `B50D3122… → DECB9824…` 的产品差异包括：新增 `struggle`/`hide_ui_main_tabs` 两门、第三个 ledger-only 入口、modal 的 ledger availability，以及两处 shortcut 从有引号改为无引号。它们恰好覆盖入口、可见性和关闭行为，不能用旧字节的 X/backdrop/managed 行结果推定当前字节仍通过。
- 该候选静态结构是三个入口变体、`167` 个直接按钮、包含 inherited 标题 X 共 `168`；这只是源码/生成投影事实，不是 168 个控件的逐项实点。
- 该候选仍须覆盖：三个入口变体、三个页签、managed/received 代表行、深滚动、ledger-only、精确 Escape、七项 HUD 门的关闭态与打开态、玩家切换/继承状态转换、正常产品事件叠层，以及 1920×1080 和低分辨率/高缩放几何。通过前不得写 GUI GREEN。

## 8. 2026-08-30 冻结案卷详情候选

本轮把榜单的角色行扩展为冻结案卷入口，并增加事实、互评、配额与审计四个面板内页；仍只保留原有
`zg361_scoreboard_toggle`、`zg361_scoreboard_window` 与同一 modal，不增加 HUD 按钮、顶层 window 或 scripted-widget 注册。
入口锚点继续是 `position = { -60 90 }`，七项 HUD 显示门与 modal 阻塞门也继续共用同一生成常量。

- 当前 GUI SHA-256：`FE00D6220CE071535E317D4D14A575F3502D4AE94F20169D0823C449A8319CC0`；生成器 SHA-256：`3DA5EAFA7CE9370470A666AA254D2B5E39AB309D821EF616344109EF8C510420`。
- managed selector 与本人 received selector 都要求冻结人物、case owner、cycle serial 与 case serial 完整；详情打开时再次比对同一组身份，拒绝旧槽或跨上司案卷。
- 详情页只读取发布时冻结字段；当前候选已加入自评 choice/score/gap、shadow response/delta、互评聚合、跨周期评价信用、配额前后档与审计 receipt。received 侧使用单独本人缓冲区，未公开的互评作者、原始评语和回避身份不写入该缓冲区，并有负例注入断言。
- backdrop、标题 X、Escape、外层页签、内层页签和新一次发布都会把详情状态退回安全初值，避免关闭重开后保留旧人物案卷。
- 静态验收为 scoreboard `18/18`、phase-2 wiring `12/12`、本地生成器 `--check` 与 `validate_local.py` GREEN。该精确字节已经提交为 `ae9a1e7`；官方 CI `33317524617` GREEN。它们只证明生成与绑定合同，不是 CK3 GUI 实机 GREEN。

当前精确字节的 GUI L3 次数仍为 **0**。正式批次必须优先通过 MCP named-widget 状态/动作/冻结案卷查询完成
入口矩形、七项 HUD 门的开关两态、modal 阻塞、四个详情页、managed/received ACL、关闭重开、玩家切换与
1366×768、1920×1080、2560×1440 几何审计。MCP 能力未接通前，OCR 只允许在状态真值闭合后截取最终素材，
不得承担导航或 GREEN 判定。

## 9. 2026-08-31 #013 披露 ACL 候选

提交 `6d084d3` 把 #013 的 A/B/C 披露策略接入本人榜案卷，同时修正了 B1 案号与结果案号被错误视为同一
cursor 的问题。合法正例固定为 B1 case `41`、result case `903`；两套案号分别冻结，A/B 的 policy ID
只绑定 B1 case，后续申诉等 mutable 更新只绑定 result tuple。

- 当前 GUI SHA-256 为 `179AE0792B7D508876440983B15E18E198041ADADB23BF0ABEEF4383822B8EC4`；生成器 SHA-256 为 `A8E8DB4FFD1FDB9466C42AB21487AD09B356716D34E88B200B120C1315D9C80E`。
- 本次没有新增 HUD 按钮、顶层 window、详情页签、关闭控件或 scripted-widget 注册；按钮数量、`position = { -60 90 }` 锚点和 `1220×820` 外框均未改变。GUI 差异只给 received 详情行增加字段可用性 `visible` 门：A 显示本人结果、理由、证据与申诉，B 只显示最终结果，C/旧存档维持旧本人视图；不可披露行直接不占布局。
- 静态门为 scoreboard `24/24`、生成器 `--check`、`validate_local.py` 与 phase-2 wiring `12/12` GREEN。它们证明 ACL 和生成投影，不证明真实分辨率、鼠标阻塞、modal、Escape 或案卷内容在 CK3 中已 GREEN。
- 新按钮阻塞审计的静态结论是“本提交新增按钮数为 0”；但原有三个入口变体、标题 X、四个详情页签、人物行、背景 modal 与 Escape 仍必须作为一个 MCP named-widget 批次复验。MCP 能力未实现前保持 `static-ready`，禁止用 OCR 首判或继承旧 SHA 的实点结果。

## 10. 2026-08-31 响应式外框与 3×3 阻塞候选

本轮只修改权威生成器、生成投影、同源静态合同和本文，没有手改 `GENERATED FILE`。当前 GUI SHA-256 为
`9550A4DA7DF1E4052A3D32E9A1A988AEF563AAD4D7D08C58A75D85E513DC2FC2`；生成器 SHA-256 为
`D1B626B63945ED81994B5890739B3493518267D4EC021E2A4A128FAB2FA352E8`。

旧 `1220×820` 固定面板替换为视口 `90%×90%`。名单的年度/人数/三档摘要、列头和全部 80 行现在处于同一个
双轴 scrollbox，因此横向移动时列头、人物行与最右案卷按钮保持同一内容坐标；案卷四页和制度账也各自有 bounded
双轴 surface。标题 X、3 个外层页签、案卷返回和页脚仍在各内容 surface 外，不能被内部滚动带走。

静态矩阵以 CK3 GUI scale 的逻辑视口建模；百分比外框投影回物理像素后仍为屏幕 90%。`Window_Margins` 的左右
`40+40` 单位纳入名单可用宽度。纵向不是用一个偏乐观的统一常数：名单、制度账、案卷字段面分别扣除
`200`、`236`、`417` 单位固定 chrome（均已包含 12 单位水平滚动条）：

| 分辨率 | UI scale | 逻辑面板 | 物理 panel rect（L,T,R,B） | 名单水平条合同 | 名单/制度账/案卷滚动高度 |
|---|---:|---:|---:|---|---:|
| 1366×768 | 100% | 1229.4×691.2 | 68.3, 38.4, 1297.7, 729.6 | as-needed（设计宽度可容纳） | 491.2 / 455.2 / 274.2 |
| 1366×768 | 125% | 983.5×553.0 | 68.3, 38.4, 1297.7, 729.6 | 必须出现 | 353.0 / 317.0 / 136.0 |
| 1366×768 | 150% | 819.6×460.8 | 68.3, 38.4, 1297.7, 729.6 | 必须出现 | 260.8 / 224.8 / 43.8 |
| 1920×1080 | 100% | 1728.0×972.0 | 96.0, 54.0, 1824.0, 1026.0 | as-needed（设计宽度可容纳） | 772.0 / 736.0 / 555.0 |
| 1920×1080 | 125% | 1382.4×777.6 | 96.0, 54.0, 1824.0, 1026.0 | as-needed（设计宽度可容纳） | 577.6 / 541.6 / 360.6 |
| 1920×1080 | 150% | 1152.0×648.0 | 96.0, 54.0, 1824.0, 1026.0 | 必须出现 | 448.0 / 412.0 / 231.0 |
| 2560×1440 | 100% | 2304.0×1296.0 | 128.0, 72.0, 2432.0, 1368.0 | as-needed（设计宽度可容纳） | 1096.0 / 1060.0 / 879.0 |
| 2560×1440 | 125% | 1843.2×1036.8 | 128.0, 72.0, 2432.0, 1368.0 | as-needed（设计宽度可容纳） | 836.8 / 800.8 / 619.8 |
| 2560×1440 | 150% | 1536.0×864.0 | 128.0, 72.0, 2432.0, 1368.0 | as-needed（设计宽度可容纳） | 664.0 / 628.0 / 447.0 |

九格均满足：panel 四边在全屏 modal 内、最小物理边距大于 `32 px`，三类 surface 分别不低于自身的
`250`/`210`/`37` 逻辑高度下限；`180×44` HUD 入口按当前 scale 投影后也完整留在屏内，并继续给原生 `50` 单位右栏加 `10`
单位间隔。modal 仍是 `100%×100%`、`alwaystransparent = no`、`filter_mouse = all`，背景关闭按钮也是
`100%×100%`；响应式改造没有开出点击穿透洞。

按钮增量审计：显式产品按钮数保持 `332`，含 inherited 标题 X 保持 `333`，所以新增产品动作按钮为 **0**。
新增交互仅为 7 个按需水平 scrollbar 的 28 个模板导航后代，以及制度账新垂直 scrollbar 的 4 个模板导航后代；
它们只滚动自己的 scissored surface，不能写游戏状态。任何时刻只有当前外层页/案卷内页可见；新增导航后代同屏最多
8 个（制度账双轴都溢出时）。

静态门更新为 scoreboard `27/27`、生成器 `--check`、生成 GUI 的 brace/BOM 与 `validate_local.py` GREEN。这里的“九格安全”
严格限定为生成语法和确定性几何合同；当前 SHA 尚未启动 CK3，更没有 MCP named-widget rect/visible/focus/modal/
blocking 证据。正式 GREEN 必须按 G1–G3 批量读取 9 格，并在三格“必须出现”中实证最右案卷按钮可达，在其余格子
实证无不必要水平热区；不得改用 OCR 首判。

## 11. 2026-09-01 named-widget action identity 候选

本轮没有新增任何可见按钮、顶层 window、modal、scrollbar 或业务动作；只给
既有三个外层页签与三个 list-page 容器补稳定 runtime name，以便 MCP 不靠坐标
执行并独立查询后置。当前 GUI SHA-256 为
`B10A83B96E70ADBC91777B9EC1E46C5CE672559931A679CCF8910FEAF2E24C62`，
生成器 SHA-256 为
`71FAF2886E0B319965C6419ED444E511242EC00515368B30033C1D08DC30CE89`。

新增 identity 恰为：

- `zg361_scoreboard_tab_managed`、`zg361_scoreboard_tab_received`、
  `zg361_scoreboard_tab_system`；
- `zg361_scoreboard_page_managed`、`zg361_scoreboard_page_received`、
  `zg361_scoreboard_page_system`。

这 6 个名字不改变 onclick、visible、down、尺寸、层级、阻塞、锚点或滚动合同，
按钮总数仍保持上一节的 `332/333`。只读 provider 的固定实例由 9 个扩为 15 个，
仍只冻结 exists、local/effective visibility 和 same-query instance/vtable。动作
contract 可据此规划 open、三切页、close、reopen，但当前 enabled 仍 typed
unavailable，生产 dispatch 未接线，所以动作 gate 继续 RED。

静态 fixture 只能证明名字唯一、provider-owned allowlist、stale instance/ACL/
visible/enabled 的 fail-closed，以及 ACK 与 later-query 分离。当前精确 GUI 字节仍
没有 CK3 paused artifact；不得继承旧 GUI SHA 的鼠标证据，也不得用 OCR 或固定
坐标补 action GREEN。完整合同和后续接线清单见
`361-scoreboard-mcp-action-cell.md`。

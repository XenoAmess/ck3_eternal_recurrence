# “自动升级建筑”四期：超直辖暂停策略需求与开发计划

状态：**implementation-complete；4.0.0 发布级九语、逻辑矩阵 R0032 与专属决议插图 R0033 均 GREEN，尚待 Workshop、fresh-cache 与 changelog 收口**

候选版本：`4.0.0`

产品目录：`mod_auto_upgrade_buildings/`

Steam Workshop item：`3800124956`

研究基线：CK3 `1.19.0.6 (Scribe)`、维护版 `3.0.0`

## 1. 需求结论

四期在玩家执行【启用自动建造】时增加一项“超直辖策略”，由玩家选择：

1. **超直辖就暂停自动修建**；
2. **超直辖了也要自动修建**。

需求在纯 CK3 数据 Mod 中可行，不需要 DLL、MCP 或桌面自动化参与运行时。策略必须是每名玩家自己的持久状态，并在每次 15 日扫描时读取该玩家的**当前**直辖状态；它不是启用瞬间的一次性判断。

“暂停”在本计划中严格定义为：本轮不扫描地产、不升级建筑、不扣除任何资源，但 `enable_auto_build` 与唯一全局 15 日循环仍然保留。玩家回到直辖上限以内后，下一次正常轮询自动恢复，无须重新执行决议。

总体可行性：**高**。建筑图谱、605 条升级边、资金策略和支付逻辑均无需重做；改动集中在启用决议、一个角色 flag、`auto_build.0004` 的整轮入口门禁、本地化、fixture 与验收 runner。

## 2. “超直辖”的冻结语义

四期直接复用原版【超出直辖领地上限】警报的判定：

```text
domain_limit_available < 0
```

边界如下：

| `domain_limit_available` | 原版语义 | 选择“超直辖暂停”后的行为 |
| ---: | --- | --- |
| `1` 或更高 | 仍有空余直辖容量 | 正常自动修建 |
| `0` | 恰好达到直辖上限 | 正常自动修建 |
| `-1` 或更低 | 已超出直辖上限 | 整轮暂停，零升级、零扣费 |

不得改用“严重超直辖”或建筑失效相关的 `domain_size_excluding_grace_period` / `building_disable_inefficient_value`。那是另一套更晚触发、带宽限语义的原版规则，不符合本需求中“刚超过一个也算超直辖”的普通含义。

政府类型、修正和临时状态对直辖上限的影响全部交给引擎现算；Mod 不自行重建 `domain_size` 与 `domain_limit` 算式。这样四期行为会与同版本原版警报保持一致。

## 3. 决议界面的技术约束与推荐交互

### 3.1 原版约束

CK3 1.19.0.6 的 `common/decisions/_decisions.info` 明确规定一个决议最多嵌入一个 custom widget。现有 3.0.0 已用掉该位置，通过 `decision_option_list_controller` 显示三种资金来源。因此，不能在同一决议里再并列加入第二个独立的原生二选一控件。

原版通用列表本身带 `470 × 166` 的滚动区，可以承载六个条目；控制器仍然只返回一个选中 scope。基于这一边界，首选方案是把两维策略做成一个 3×2 笛卡尔积列表：

| 资金来源 | 超直辖策略 |
| --- | --- |
| 只用国库 | 暂停 / 继续修建 |
| 只用个人金钱 | 暂停 / 继续修建 |
| 优先国库 | 暂停 / 继续修建 |

建议短标签采用“`资金来源｜超直辖行为`”，详细说明放在 tooltip 中，避免 450 像素按钮文字溢出。资金组顺序继续保持三期的“只用国库 → 只用个人 → 优先国库”；每组内先列“超直辖暂停”，再列“超直辖继续”。

默认项冻结为 **“优先国库｜超直辖继续”**，与 3.0.0 的现有行为完全一致。选择按钮文案由“选择资金来源”改为“选择资金与超直辖策略”。

### 3.2 一次 UI 可用性门禁

六项必然需要滚动，所以正式功能实机的第一项门禁是：六项均可见/可滚动到、标签不截断、选中态明确、默认项可辨认，且在任意实际桌面与截图尺寸下继续使用仓库既有的显式坐标换算脚本，不假定分辨率或图片比例。

如果这一次真实 UI 验证证明六项列表不可清楚使用，才切换到唯一后备方案：保留三期资金列表，在确认决议后立即弹出原生二选一事件，并且只在玩家完成该事件选择后结束启用流程。后备方案不开发自制双选择器 GUI；自制 GUI 会扩大兼容面，却没有当前必要性证据。

## 4. 存档与持久化方案

只增加一个角色 flag：

- `aub_pause_when_over_domain_limit`：存在时，超直辖暂停；
- flag 不存在：超直辖继续修建。

这个表示法有意让“无新 flag”对应 3.0.0 的原行为，因此：

- 已经启用自动建造的 3.0.0 旧存档无需迁移，升级四期后仍会在超直辖时继续修建；
- 新执行启用决议的玩家按六项选择设置或清除该 flag；
- 【禁用自动建造】同时清除该 flag 和三期的两个资金覆盖 flag；
- 玩家要更改任一策略时，仍沿用三期合同：先禁用，再重新启用并重新选择；四期不另增运行中设置决议；
- 若异常存档同时出现无法解释的选择状态，运行时仍以持久 flag 为唯一真相，不保留决议控制器的瞬时 scope。

旧存档“继续修建”是兼容默认；新决议的视觉默认也保持“优先国库｜超直辖继续”，两者不会产生隐式行为分叉。

## 5. 运行时设计

门禁放在 `auto_build.0004` 的角色级执行入口，位于 `save_scope_as = aub_payer` 和 `every_directly_owned_province` 之前。等价逻辑为：

```text
允许执行本轮 =
    没有 aub_pause_when_over_domain_limit
    OR domain_limit_available >= 0
```

只有“选择暂停”且当前值小于 0 时，才跳过整个现有 hidden effect。不得把判断分散到 605 条建筑边或每个省份内部，否则会重复求值、扩大生成 diff，并可能在同一轮中形成部分升级。

门禁保留以下合同：

- `auto_build.0005` 仍每 15 日为所有已启用真人玩家触发 `.0004`；暂停玩家不会导致全局循环停止；
- 多人局逐玩家独立判断，一个超直辖玩家暂停不影响其他玩家；
- 旧版本已经排队的 `.0004` 也会读取同一 flag，且无 flag 时维持旧行为；
- 暂停轮次不会保存付款 scope、遍历省份、调用 605 条边、升级建筑或扣除国库/个人金钱/威望/虔诚；
- 恢复到 `domain_limit_available >= 0` 后只在下一次既定轮询恢复，不额外补跑、不追偿、不一次升级多级；
- 继续保留二期的瞬时升级、成功后扣费、每链每轮最多一级，以及三期三种资金来源语义。

## 6. 开发工作包

### P0：决议六项与持久状态

- 将现有三个 `item` 扩为六个组合 `item.value`，保持一个原生 widget、一个 controller、一个默认项。
- 在决议 `effect` 中把瞬时选择一次性投影为两个资金 flag 加一个超直辖暂停 flag；所有六个组合必须映射唯一且完整。
- 更新确认按钮、选项名称、说明和启用结果 tooltip；日常实现阶段只创作/审阅简体中文和英文。
- 禁用决议清理 `aub_pause_when_over_domain_limit`。

### P1：整轮暂停门禁

- 在 `auto_build.0004` 入口加入一次角色级判断；不改 `.0005` 的 15 日调度和单实例 seed。
- 不改 `tools/gen_auto_upgrade_buildings.py`、165 条建筑链或 605 条生成升级边；若实现 diff 触及这些文件，必须先解释为何计划假设失效。
- fixture 增加可控的“恰好到上限 / 超出一个 / 恢复到上限”状态和轮询计数证据。

### P2：静态验证与构建

- 校验决议恰有六个唯一组合、覆盖 3×2 全集、顺序固定且只有“优先国库｜超直辖继续”为默认。
- 校验六个 choice scope 对三种持久 flag 的映射；启用前归一化、禁用时清理。
- 校验 `.0004` 的门禁只出现一次，并且位于省份遍历之前；`.0005` 仍会调度暂停玩家。
- 校验无暂停 flag 的旧存档路径等价于 3.0.0。
- 继续通过 165 链 / 605 边、4 个 Great Project 排除、三期支付矩阵、生成可重复性、本地化结构、release allowlist、manifest 与 deterministic ZIP 回归。
- 四期机制本身不新增运行时文件；随后按用户明确要求加入一张专属决议 DDS，因此正式 staging 从历史 15 个文件有依据地增加为 16 个。源 PNG、提示词和投影脚本不进入 staging。

### P3：一次抽样实机验收

不逐条实测 605 个建筑 key。图谱和支付系统由静态全量回归负责；实机只覆盖新状态机及必要的二、三期回归。

在同一 CK3 进程和一次性 `-userdir` 中抽样：

1. 打开启用决议，确认六项、滚动、标签、选中态和唯一默认项；实际点击至少一个“暂停”组合与一个“继续”组合。
2. 选择“暂停”，在 `domain_limit_available = 0` 时证明一次代表性建筑正常升级并按所选资金策略只扣一次。
3. 变为 `-1`，跨过至少一个 15 日轮询，证明建筑、国库、个人金钱及其他费用均不变，同时全局循环仍在。
4. 保持启用，把值恢复到 `0`；下一个既定轮询自动恢复，且只升级一级、只扣一次。
5. 选择“继续修建”，在 `-1` 时证明仍升级并按所选资金策略扣费。
6. 构造“已启用、无四期 flag”的旧存档状态，在 `-1` 时证明继续修建且不产生第二条循环。
7. 禁用后证明新 flag 被清理、已排队轮询零副作用；重新启用可以改选另一策略。
8. 四期新增状态机只抽样代表性普通槽；同一成熟 fixture 顺带复跑二期建筑与三期资金矩阵，不另起 CK3 轮次。
9. 项目相关 `error.log` / `debug.log` 诊断为零，源树、fixture、真实用户资料与 Steam 状态符合隔离合同。
10. R0032 后新增的专属决议插图只做一次聚焦实机复核：决议面板真实加载该图、没有紫块／缺图，人物和建筑主题在实际裁切中可辨；不重复已经由 R0032 证明的完整机制矩阵。

正式轮次使用该机器与本 Mod 在执行时由分配器给出的下一个递增编号，不在计划中预占历史 `R` 号。启动前必须取得 CK3 排他槽并证明 CK3 进程数为 0；本次计划编写不占用 CK3 或屏幕。

## 7. 明确非目标

- 不做按公国、地产、建筑类别、优先级或预算分别设置超直辖策略。
- 不做“仅停止新建但继续升级”之类的半暂停；本期只有整轮暂停或整轮继续。
- 不在超直辖时自动禁用功能、清除 `enable_auto_build`、弹提示事件或修改轮询频率。
- 不补跑暂停期间错过的升级，不保存欠账，不在恢复时加速。
- 不改直辖上限、超直辖惩罚、原版建筑启用规则或警报本身。
- 不新增个人优先/国库兜底、拆分付款、施工队列、原版进度条或取消退款。
- 不扩展二期建筑范围：住所系统、游牧/牧民地产、曼荼罗都城 Great Project 仍不在支持范围。
- 本需求分析不修改 Mod、不启动 CK3、不同步 Workshop 缓存、不切换 Steam 状态，也不发布。

## 8. 风险与控制点

| 风险 | 控制 |
| --- | --- |
| 把“超直辖”误写成严重超直辖 | 锁定原版警报同款 `domain_limit_available < 0`，验证 `0/-1` 边界 |
| 六项在原生滚动区内难以阅读 | 使用短标签与 tooltip，只做一次真实 UI 门禁；失败才转两阶段原生流程 |
| 旧存档升级后突然暂停 | 仅用“暂停”覆盖 flag；无 flag 永远等价于 3.0.0 的继续行为 |
| 暂停时把全局循环停掉，恢复后不再工作 | 门禁只放 `.0004` 执行体，`.0005` 继续 15 日调度 |
| 在一个扫描中部分地产升级、部分暂停 | 在任何 scope 保存和省份遍历前做一次角色级整轮判断 |
| 多人局由一名玩家的状态影响其他人 | flag 与 `domain_limit_available` 均在当前 `every_player` 角色作用域读取 |
| 为本期无必要地重生成 605 条边 | 计划冻结为不改生成器；静态 diff 门禁阻止范围漂移 |

## 9. 预计工作量与完成标准

截至 2026-09-14 的实现检查点：

- 决议已实现一个原生可滚动六选一列表，默认“优先国库＋超直辖继续”；启用和禁用均先规范化三类持久 flag。
- `auto_build.0004` 已在 payer scope 和地产遍历之前按 `domain_limit_available >= 0` 门禁整轮；`.0005` 的 15 日全局调度不读取暂停 flag。
- 一次性 fixture 已加入可叠加的直辖上限校准修正，冻结并断言 `0`、`-1`、暂停零副作用、恢复、继续和旧存档无 flag 行为。
- 实机 runner 的所有选项点击均来自当前截图 OCR 坐标；滚动只以实际可见选项为锚，不假定桌面、截图或面板尺寸。
- 9 语发布文案已补齐并完成键集、BOM、保护 token 与非英文占位检查。MiniMax-M3 只生成候选，最终文本已人工复核并修正可能暗示拆分付款的译法。
- 用户追加的 UI 缺陷已经闭环：六个原生 choice value 均补齐 `<value>_tooltip`；只在 `is_shown` 保留真人门禁，内部 AI／character flag 与 loop seed 全部移入 `hidden_effect`；确认页只显示当前所选组合的一段自然语言，不再强制换行。
- L0 已通过：静态验证（165 链）、snapshot、26 项翻译调用器测试、7 项 release builder 测试及 16 文件可重复构建。专属插图由权威 PNG 确定性投影为 `1100×440` DXT1 DDS，并受逐字节重建门禁保护；正式 manifest 与 ZIP 随最终发布 commit 重新冻结。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0031` 已证明六项 hover、无原始 key／AI／flag 泄露、自然确认文案和四期完整状态机 GREEN；之后被原版单按钮【已宣战】模态框暂停，按 RED attempt 永久保留于 `D:\workspace\ck3_auto_upgrade_runtime\phase4-live-r6-20260914`。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0032` 全量 GREEN：六项 hover、选择/确认、`0/-1/恢复`、暂停零副作用、继续策略、旧存档默认、三种资金、禁止拆分付款、禁用/重启，以及主建筑、普通、公国、特殊、混合资源和负向路径抽样全部通过；共保全 46 条 AUBT 记录（29 条 `TEST PASS`，所有必需 marker 各出现一次），项目诊断为 0，产品/fixture/源码未被游戏改写，受保护存储保持不变。证据入口为 `D:\workspace\ck3_auto_upgrade_runtime\phase4-live-r7-20260914\report.json`。
- R0032 的 Open Kaishek 层因该工具未登记 `auto-upgrade-buildings-1.19.0-source` fixture 而标为 `not-applicable / unknown-fixture`；同一报告中的 root parser 为 GREEN，真实 CK3 非调试实机为 GREEN。该工具覆盖缺口与产品结论分开记录。
- R0032 后用户选择了新的专属决议插图，因此 R0032 继续作为全部玩法和 UI 文案的权威 GREEN；新增美术只需一次不重复逻辑矩阵的聚焦加载验收。美术来源、提示词、哈希与投影合同见 [决议插图记录](auto-upgrade-buildings-art.md)。
- `desktop-3fevhd2-1c74096080--auto-upgrade-buildings--R0033` 已完成该聚焦验收：exact 16-file projection 在 CK3 `1.19.0.6` 的原生决议框中正确显示人物、图纸、施工现场与赛博噪声，没有紫块、缺图或拉伸；六项 hover 与确认文案顺带保持 GREEN，项目诊断为 0，产品／fixture／受保护存储未变化，一次性 userdir 已删除。报告入口为 `D:\workspace\ck3_auto_upgrade_runtime\phase4-art-live-20260914\report.json`，SHA-256 `0C0C380F8C953180EA63EB0D525369FB5CFD3C2E2C577869CB0C5BC2B7952663`；完整视觉审阅见 [决议插图记录](auto-upgrade-buildings-art.md)。

| 工作包 | 预计工时 |
| --- | ---: |
| 六项决议、flag 映射、中英文文案 | 0.75–1.25 小时 |
| `.0004` 门禁与 fixture | 0.5–1 小时 |
| 静态校验、runner 调整、正式构建回归 | 1–1.5 小时 |
| 一次抽样 CK3 实机与证据收口 | 1–1.5 小时 |
| **实现与验收合计** | **约 3.25–5.25 小时** |

若六项 UI 门禁失败并改为两阶段事件流程，增加约 0.75–1.25 小时。正式发布另计约 1–2 小时，用于发布级七语补齐、staging/tag、Workshop 上传、完整 Change Notes、公开逐字回读、fresh-cache 复核、永久 changelog、commit/push 与 Steam 离线恢复；只有用户明确要求发布时才进入该流程。

四期 implementation-complete 必须同时满足：六种组合可选、暂停/继续的 `0/-1/恢复` 状态机 GREEN、旧存档继续语义不变、15 日循环未中断、二三期抽样回归 GREEN、静态全量回归与正式构建 GREEN。release-complete 还必须完成 Workshop、fresh-cache、完整 Change Notes、永久 changelog 与 Git/tag 收口。

## 10. 依据

- 当前产品：`mod_auto_upgrade_buildings/common/decisions/build_decision.txt`、`mod_auto_upgrade_buildings/events/auto_build.txt`、`tools/validate_auto_upgrade_buildings_static.py`、`tools/run_auto_upgrade_buildings_acceptance.py`。
- 三期资金策略与 R0025 证据：[auto-upgrade-buildings-phase-3-plan.md](auto-upgrade-buildings-phase-3-plan.md)。
- 原版决议 schema：`C:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\decisions\_decisions.info`，SHA-256 `106977B58220107B66F537AADDA965F5A0602140DFB9BA7C79F3BA8BDD91CD9E`；第 145 行声明每个决议最多一个 custom widget。
- 原版超直辖警报：`C:\SteamLibrary\steamapps\common\Crusader Kings III\game\common\important_actions\00_realm_actions.txt`，SHA-256 `C1382FD5DFF09AB40BDB2BEE807D58DBF576877B87119F2F246DE9410CD2088D`；`action_above_domain_limit` 使用 `domain_limit_available < 0`。
- 原版通用选项列表：`C:\SteamLibrary\steamapps\common\Crusader Kings III\game\gui\decision_view_widgets\decision_view_widget_option_list_generic.gui`，SHA-256 `6C378FC5C4ACC9289F7947A994D85C89CDC9EEB8AE4EEAC2850D92598A960E53`；使用 `decision_option_list_controller` 和 `470 × 166` scrollbox。

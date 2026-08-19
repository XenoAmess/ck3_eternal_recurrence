# 付费自定义廷臣

## 状态

- 2026-08-19 已完成源码实现。
- 本文中的 CK3 行为依据来自 1.19 原版源码；受当前测试暂停要求影响，新增功能尚未执行静态检查或实机验收。未标注为实测结论。

## 为什么不用原生统治者设计器

原生入口 `TryStartRulerDesigning` 的已发现调用均位于准备大厅：

- `Crusader Kings III/game/gui/multiplayer_types.gui:1926`
- `Crusader Kings III/game/gui/multiplayer_types.gui:1975`
- `Crusader Kings III/game/gui/multiplayer_types.gui:2024`

可见性、可用性和 tooltip 同时依赖 `LobbyView.CanTryStartRulerDesigning`。没有发现受支持的运行期调用，可证明它能安全创建或覆盖当前游戏中的无地 NPC。因此本功能使用独立 scripted GUI，只开放有限且可定价的选择；姓名和外观交给 `create_character` 按文化、信仰生成。

## 玩家边界

- 入口决议必须同时满足 `has_character_flag = xa_enabled`、`is_ai = no`、`is_alive = yes`。
- 打开状态和所有选择均存放在玩家角色变量/旗标中，不使用 global variable，避免多人玩家互相覆盖配置。
- 决议只添加 `xar_cc_open_pending`；不可逆操作不放在会被 tooltip 预演的 decision effect 中。
- 1x1 决议桥按 `pending -> initialize -> open` 顺序打开窗口。
- 所有 scripted GUI 均复用 `xar_cc_ui_access_trigger`，AI 没有调用入口。

## 交易边界

取消、点击暗背景或关闭按钮只移除 `xar_cc_open`。确认链重新检查：

1. 窗口仍属于存活、签约的真人玩家。
2. 配置变量均在允许集合内，将领特质不超过 2 个，相反心性不并存。
3. 玩家仍有足够金币，且文化、信仰、所在地仍存在。

确认后先关闭窗口，令排队的双击失效；随后只创建一个角色。只有 `scope:xar_cc_created_courtier` 确实存在时才扣除一次 `xar_courtier_creator_cost`，再添加特质、招入廷臣并发送回执。

该收尾模式对应原版 `Crusader Kings III/game/common/scripted_effects/00_commander_effects.txt:473-500`：先检查创建 scope，再添加 25 年 `blocked_from_leaving`、必要时 `add_courtier`，最后发送 toast。

## 创建结果

- `location = root.location`
- `employer = root`
- `culture = root.culture`
- `faith = root.faith`
- `dynasty = none`
- `random_traits = no`
- 六项基础能力均为 6
- 年龄、性别、一个三级教育特质及可选特质由玩家配置

原版依据：

- `events/dlc/ep3/ep3_laamp_decision_events.txt:22389-22407`：`employer = root`、同文化、同信仰。
- `events/story_cycles/peasant_affair/story_cycle_peasant_affair_events.txt:24-38`：`create_character` 的 `age` 可读取变量。
- `events/bookmark_events.txt:464-485`：`gender_female_chance` 可使用条件式数值块。
- `events/religion_events/great_holy_war_events.txt:734-754`：动态变量可直接交给 `remove_short_term_gold`。

## 定价

基础价 90 金，包含 50 金塑造费和固定三级教育的 40 金。默认 30 岁配置为 120 金。

| 选择 | 调整 |
|---|---:|
| 18 / 30 / 45 岁 | +60 / +30 / +0 |
| 每项将领特质，最多 2 项 | +25 |
| 姣好 / 健硕 / 聪慧一级先天特质 | +40 / +60 / +80 |
| 勇敢 / 怯懦 | +40 / -10 |
| 冷静 / 暴怒 | +25 / +30 |
| 勤勉 / 懒惰 | +40 / -10 |

价格只由 `common/script_values/xar_courtier_creator_values.txt` 中的 `xar_courtier_creator_cost` 计算；确认按钮校验和实际扣款必须引用同一个 script value。

## 待验收

获得测试许可后至少验证：取消零副作用、金币不足、默认配置、最高价配置、将领上限、心性互斥、男性/女性、三档年龄、登陆与无地玩家招募、扣金恰好一次、保存后配置与打开状态恢复，以及九语言窗口截断。

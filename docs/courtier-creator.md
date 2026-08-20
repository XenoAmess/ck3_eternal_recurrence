# 付费自定义廷臣

## 状态

- 2026-08-20 v2 源码、L0 与 CK3 1.19.0.6 真实 UI 验收 GREEN。交付失败回滚审阅后的权威证据为 `xar_courtier_creator_postreview22_20260820`；它以创建角色同时不同于玩家的文化与信仰为硬断言，取代了只点击 heritage 标题、未真正证明动态文化的早期运行。
- 实机链覆盖原生决议、取消零副作用、119/120 金门槛、七页目录、数值步进、动态文化/信仰、同家族、关窗重开保留、默认 120 金与验收自定义配置 348 金的两次真实交付，以及 AI 运行期闸门；两次购买均校验创建角色本体，`xar error.log = 0`。
- 348 金只是验收向量，不是最高价格。

## 为什么不用原生统治者设计器

原生入口 `TryStartRulerDesigning` 的已发现调用均位于准备大厅：

- `Crusader Kings III/game/gui/multiplayer_types.gui:1926`
- `Crusader Kings III/game/gui/multiplayer_types.gui:1975`
- `Crusader Kings III/game/gui/multiplayer_types.gui:2024`

可见性、可用性和 tooltip 同时依赖 `LobbyView.CanTryStartRulerDesigning`。没有发现受支持的运行期调用，可证明它能安全创建或覆盖当前游戏中的无地 NPC。因此本功能使用独立 scripted GUI，复用原生统治者设计器的特质元数据、冲突关系和数值价格曲线；姓名和外观交给 `create_character` 按玩家选择的文化、信仰生成。

## 玩家边界

- 入口决议必须同时满足 `has_character_flag = xa_enabled`、`is_ai = no`、`is_alive = yes`。
- 打开状态、数值和所有待确认选择均存放在玩家角色变量/旗标中，避免多人玩家互相覆盖配置。全局列表只保存确定性的已载入文化及 heritage 目录，不保存任何玩家选择。
- 决议只添加 `xar_cc_open_pending`；不可逆操作不放在会被 tooltip 预演的 decision effect 中。
- 1x1 决议桥按 `pending -> initialize -> rebuild catalogs -> open` 顺序打开窗口。
- 所有 scripted GUI 均复用 `xar_cc_ui_access_trigger`，AI 没有调用入口。

## 交易边界

取消、点击暗背景或关闭按钮只移除 `xar_cc_open`。确认链重新检查：

1. 窗口仍属于存活、签约的真人玩家。
2. 年龄在 0–120、六项能力在 0–100，已选特质仍属于生成目录并满足原生年龄、性别和冲突规则。
3. 成人恰有一个教育特质、儿童没有教育特质；将领不超过 2 项、性格不超过 3 项。
4. 玩家仍有足够金币，已选文化/信仰仍属于已载入目录，同家族选择仍有有效家族。

确认后先关闭窗口，令排队的双击失效；随后只创建一个低身角色，并用 `employer` 与必要时的 `add_courtier` 尝试交付。只有角色确实成为玩家廷臣后才应用能力、特质、家族与离廷锁，扣除一次 `xar_courtier_creator_cost` 并发送回执；若交付后置条件失败，未配置的临时角色以 `death_vanished` 回滚，不扣金、不写入玩家家族，也不发送成功回执。

该收尾模式对应原版 `Crusader Kings III/game/common/scripted_effects/00_commander_effects.txt:473-500`：先检查创建 scope，再添加 25 年 `blocked_from_leaving`、必要时 `add_courtier`，最后发送 toast。

## 创建结果

- `employer = root`
- `culture` / `faith` 使用玩家选择的已载入条目
- 默认 `dynasty = none`；也可归入玩家当前宗族与家族
- `random_traits = no`
- 六项基础能力、年龄和性别由玩家配置
- 从五类生成目录应用全部已选且相容的特质

原版依据：

- `events/dlc/ep3/ep3_laamp_decision_events.txt:22389-22407`：`employer = root`、同文化、同信仰；指定 employer 时不再同时指定 location。
- `events/story_cycles/peasant_affair/story_cycle_peasant_affair_events.txt:24-38`：`create_character` 的 `age` 可读取变量。
- `events/bookmark_events.txt:464-485`：`gender_female_chance` 可使用条件式数值块。
- `events/religion_events/great_holy_war_events.txt:734-754`：动态变量可直接交给 `remove_short_term_gold`。

## 目录与定价

- 教育 25、将领 17、身体 38、性格 36、其他 108；唯一 trait 并集 224 项，冲突元数据 95 组。
- 年龄可在 0–120 间精确调整；六项基础能力可在 0–100 间用 `-10/-1/+1/+10` 调整。
- 价格为 50 金塑造费，加年龄调整、生成的原生 trait 价格和六项原生非线性绝对能力价格，再减去默认六项能力均为 6 的 88 金基线；最终四舍五入且不低于 0。
- 默认男性、30 岁、六项能力 6、`education_martial_3`、低身、玩家文化/信仰，价格 120 金。
- 验收自定义向量为女性、20 岁、外交/勇武 16、其余能力 6，并选择 `education_intrigue_1`、`logistician`、`military_engineer`、`beauty_bad_1`、`lustful`、`diplomat`、动态文化/信仰及同家族，价格 348 金。

价格只由 `common/script_values/xar_courtier_creator_values.txt` 中的 `xar_courtier_creator_cost` 计算；显示、确认校验和实际扣款引用同一个 script value。trait 目录与价格来自 `tools/courtier_traits_1_19_0_6.json`，由 `tools/gen_courtier_creator.py` 生成。

## 验收边界

自动验收已覆盖：取消零副作用、金币不足、默认配置、七页目录、年龄/能力步进、五类代表 trait、动态文化/信仰、同家族、登陆玩家招募、两次逐次精确扣金、关窗重开完整配置保留和 AI 拒绝。

仍需独立证明：无地玩家交付、跨进程存档读取配置，以及九语言最长字符串在支持 UI 缩放下无截断。关窗重开不等同于保存并重启进程。

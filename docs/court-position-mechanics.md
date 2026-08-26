# CK3 `牛来 / ox here` 机制记录

## 结论状态

本页记录 CK3 `1.19.0.6` 本地游戏文件研究及独立 mod `ox_here` 的实机结果。2026-08-27 已通过
`tools/run_ox_here_acceptance.py` 在隔离 userdir 中启动 exact-build CK3 完成全链验收；下文会分别标明原版静态依据与实机确认边界。

## 原版机制

### 勇士职位与月度薪资

- `common/court_positions/types/_court_positions.info` 将 `salary` 定义为宫廷职位的月度维护费用；`received_salary` 是职位持有者实际收到的薪资。
- `common/court_positions/types/00_court_positions.txt` 中的 `champion_court_position` 使用 `skill = prowess`，其 `salary` 同时覆盖 `gold` 与 `treasury`，两者都引用 `champion_total_salary_value`；`received_salary` 也引用该值。
- `common/script_values/00_court_position_values.txt` 中，`champion_total_salary_value` 的基础值是 `minor_court_position_salary`，并根据 Inner Circle、义务钩、薪资修正和无地冒险者状态继续调整。

### 任命与费用不是同一条链

- `common/scripted_effects/00_court_position_effects.txt` 的 `court_position_grant_effect` 在没有旧持有者时调用 `appoint_court_position`，有旧持有者时调用 `replace_court_position`，并额外显示薪资提示。
- 该 effect 本身没有发现直接扣除黄金、威望或虔诚的步骤。因此“任命时不扣即时资源”和“职位之后不产生月度薪资”必须分别处理。
- `temporary_court_position_cost_removal` 只被原版的职位替换事件等临时使用，并由 `minor_court_position_prestige_revoke_cost`、`medium_court_position_prestige_revoke_cost`、`major_court_position_prestige_revoke_cost` 读取。它解决的是撤销职位的威望花费，不能用来关闭月度职位薪资。

### 原版的定向免费职位范式

`master_of_horse_total_salary_value` 提供了一个可复用范式：通过 `scope:liege` 找到雇主，再用 `any_court_position_holder` 精确寻找拥有特定 character flag 的职位持有者；命中后将薪资乘以 0。这个范式比把所有职位或整个统治者的薪资都设为 0 更窄。

## 决议与角色逻辑中的静态观察

- 决议通过 `decision_group_type = ox_here` 放入独立分组；`is_shown`、`is_valid` 和 `is_valid_showing_failures_only` 都要求当前角色同时满足 `is_ruler = yes` 与 `is_married = yes`。
- 决议选项使用原版 `decision_view_widget_option_list_generic` 和 `decision_option_list_controller`。选项值保存在 `scope:ox_here_recruit`；effect 只在该值为 `yes` 时执行邀请逻辑，第二项没有 effect。
- `create_character` 使用 `template = ox_here_african_warrior` 和 `employer = root`。原版语法中 `employer` 负责决定新角色的雇主/宫廷归属；本 mod 还保留了一个 `add_courtier` fallback。创建时不要同时再指定 `location`，否则会触发原版的互斥参数错误。
- 角色模板指定男性、25–35 岁、40–60 基础勇武、`giant`、`fecund`，并关闭随机特质。巨人特质结算后，实机总勇武为 46–66。
- CK3 肖像遗传实际从创建文化读取 ethnicity，单在模板中填写自定义 ethnicity 不足以稳定得到金发。因此角色先以创建专用文化 `ox_here_blond_kanuri` 生成 DNA，再在 `after_creation` 立即切回原版 `culture:kanuri`。自定义 ethnicity 继承非洲模板，并把两份遗传发色样本都固定为 exact-build 发色表中的浅金点 `{ 0.25 0.2 0.25 0.2 }`；实机原始分辨率截图确认非洲外观和浅金头发/胡须同时成立。
- `set_knight_status = force` 与 `champion_court_position` 是两条独立链：前者强制成为骑士，后者只在 Royal Court 的勇士职位空缺且原生任命条件通过时执行。勋号骑士界面仍由原版系统负责；本 mod 没有找到直接创建勋号的通用脚本 effect。
- `every_consort` 会遍历统治者当前可用的配偶/侧室；当前 effect 进一步限制为在世且成年，因此不是只处理第一配偶。对每人先移除统治者与其既有的 soulmate、lover 关系，再由新 NPC 建立 lover 关系，并添加目标为该配偶的 `secret_lover` 秘密。
- 新 NPC 使用直接的 `start_scheme = { type = seduce target_character = ... }`，没有额外的性别、性取向或 `can_start_scheme` 门槛。实机夹具使用性取向不兼容目标，仍确认勾引阴谋成功建立。
- 本独立 mod 是主项目“AI 永远不得触发”规则的明确例外：AI 可以使用，但基础意愿为 0。骑士不足/低勇武骑士只给决议 `+1`、招募项 `+5`；主要战争方战争分数不高于 -50 才给决议 `+10`、招募项 `+25`，拒绝项始终为 100。
- 所有 AI 头衔层级的检查间隔均为 12 个月；每次 AI 执行后设置 `ox_here_ai_cooldown`，持续时间**恰好 1 年**。这是用户指定的最高上限，禁止将该冷却增加到 1 年以上。真人玩家不读取该冷却。

### 原生 option-list 的隐式 tooltip 合同

CK3 `1.19.0.6` 的 `game/gui/decision_view_widgets/decision_view_widget_option_list_generic.gui` 从
`DecisionViewWidgetOptionList.GetEntries` 物化每个行项，并在 `DecisionOptionItem` 上直接绑定
`tooltip = "[Entry.GetTooltip]"`。原版决议数据说明该 getter 的 loc 合同由 `item.value` 命名，与显式行名
`localization` 和详情文案 `current_description` 分开：

- `90_minor_decisions.txt` 的 `value = hire_physician_decision` 配套
  `hire_physician_decision_tooltip`；
- `dlc_decisions/bp3/00_bp3_other_decisions.txt` 的 `value = master_forest_terrain` 明明把行名和详情都指向
  `designated_terrain_forest_decision`，英文 loc 仍单独定义 `master_forest_terrain_tooltip`。

因此精确公式是：每个 `item { value = V }` 的行 tooltip 键为 **`V_tooltip`**。牛来的两个始终物化的
value 是 `ox_here_recruit` 和 `ox_here_decline`，所以每种发布语言都必须同时有
`ox_here_recruit_tooltip` 与 `ox_here_decline_tooltip`。已有的 `ox_here_decision_option_recruit_desc` /
`ox_here_decision_option_decline_desc` 只满足 `current_description`，不会被 `Entry.GetTooltip` 当作回退键。

2026-08-27 的英文发布缓存 loc-smoke Attempt4 给出了真实 UI 证据：
`C:\Users\xenoa\AppData\Local\Temp\oxls_workshop_3790635143_english_attempt4` 从 Steam item
`3790635143` 的已验证缓存启动 exact-build，招募行显示正确名称 `Mother...`，但 hover 浮层显示 raw
`ox_here_recruit_tooltip`。顶层 `report.json` 以此返回 RED，SHA-256 为
`e552553f6e2c11687566a28c81f8d87dcd6b659d1f73fd8b34a14002da3e3b1d`；截图
`cells/l_english/05_native_decision_selected.png` 的 SHA-256 为
`36334c0f08da05305d678185fd50d20c0cdc251d35a2caf475aa3728087bd59c`。该 Attempt4 **直接实读**了 recruit 键；当次鼠标没有
hover decline，故 decline 键的必需性是由同一原生逐行合同与两行均可见推出，不冒充当次实读。

## `牛来` 的实现

- 决议 effect 只有在统治者拥有 Royal Court、可以雇佣 `champion_court_position`、且当前没有该职位时，才会调用 `court_position_grant_effect`。
- 任命前，生成的 NPC 被设置 `ox_here_free_champion` character flag。
- `ox_here/common/script_values/ox_here_values.txt` 使用同名的 `champion_total_salary_value` 覆盖原版 script value；本仓库的数据库条目规则是同名条目由后加载者覆盖前者，因此该文件保留原版调整链，并在雇主的勇士职位持有人中发现 `ox_here_free_champion` 时将薪资乘以 0。实机验收已确认职位持有人正确且该职位薪资为 0。
- 因此该 NPC 仍然是原生 `champion_court_position`，不是另造一个伪职位；本次决议任命不产生即时资源扣除，并且该 NPC 实际担任勇士期间不产生月度职位薪资。
- 真人玩家的复杂创建 effect 不直接放在决议 tooltip 模拟路径，而是先设置 pending flag，再由不可见原生 GUI bridge 执行。这样查看决议时不会让不存在的创建后 scope 被 tooltip 求值器提前解析。AI 直接执行同一生产 effect，但跳过纯展示事件。
- `events/ox_here_events.txt` 的到庭事件会明确说明该 NPC 是响应玩家刚刚使用的“牛来”决议而来，已经来到宫廷并成为廷臣/骑士；获任勇士时还会说明职位零薪资。中文开场为用户指定的“我听到你刚刚说，牛来？”。

## 实机验收结果与边界

2026-08-27 最终 clean run 的隔离产物目录为
`C:\Users\xenoa\AppData\Local\Temp\oxa_20260827_035146_f80a6f08`，runner 返回 GREEN，保护存储前后不变，项目诊断日志为空。自动断言覆盖：

1. 拒绝项不产生副作用，招募项只交付一名角色。
2. 角色身份、最终勇武 46–66、廷臣、强制骑士与勇士职位全部成立。
3. 所有测试配偶/侧室的关系与 `secret_lover` 秘密成立。
4. 性取向不兼容时仍建立对统治者的勾引阴谋。
5. `champion_total_salary_value` 结果为 0。
6. 真人玩家的到庭事件可见，并保存了无头盔角色肖像截图。

验收没有把“AI 最终随机选择频率”冒充确定性证明；当前能确定的是原生脚本权重、12 个月检查周期、1 年硬冷却和 AI 生产 effect 均可加载。没有 Royal Court、职位已占用、后续手动撤职的原版边界仍由脚本条件和原版机制负责，本 mod 只承诺成功任命时的在职月薪为 0。

若 CK3 更新了 `champion_total_salary_value` 或 `champion_court_position` 的原版定义，必须重新对照上述文件，避免覆盖值遗漏新的原版薪资修正。

# CK3 `牛来 / ox here` 机制记录

## 结论状态

本页记录 CK3 `1.19.0.6` 本地游戏文件的静态研究结果，服务于独立 mod `牛来 / ox here`。本次没有启动 CK3，也没有进行实机验证；因此“静态确认”不等于“运行期已确认”。

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
- 角色模板静态指定男性、25–35 岁、`culture:kanuri`、`faith:west_african_bori_pagan`、40–60 勇武、`giant`、`fecund`，并关闭随机特质。`ox_here_african_blond` ethnicity 继承 `african` 模板并固定非洲发色表中的 Blonde 范围。
- `set_knight_status = force` 与 `champion_court_position` 是两条独立链：前者强制成为骑士，后者只在 Royal Court 的勇士职位空缺且原生任命条件通过时执行。勋号骑士界面仍由原版系统负责；本 mod 没有找到直接创建勋号的通用脚本 effect。
- `every_consort` 会遍历统治者当前可用的配偶/侧室；当前 effect 进一步限制为在世且成年，因此不是只处理第一配偶。对每人先移除统治者与其既有的 soulmate、lover 关系，再由新 NPC 建立 lover 关系，并添加目标为该配偶的 `secret_lover` 秘密。
- 新 NPC 使用直接的 `start_scheme = { type = seduce target_character = ... }`，没有额外的性别、性取向或 `can_start_scheme` 门槛。这符合需求，但该 scheme 在不同目标状态下是否被引擎接受仍需实机确认。
- AI 权重在决议和选项两层分别处理：基础值设为 0；骑士数量不足或存在勇武低于 `decent_skill_rating` 的骑士时提高权重；作为主要攻击方/防御方且战争分数不高于 -50 时进一步提高权重。具体运行期选择概率尚未实机确认。

## `牛来` 的实现

- 决议 effect 只有在统治者拥有 Royal Court、可以雇佣 `champion_court_position`、且当前没有该职位时，才会调用 `court_position_grant_effect`。
- 任命前，生成的 NPC 被设置 `ox_here_free_champion` character flag。
- `牛来/common/script_values/ox_here_values.txt` 使用同名的 `champion_total_salary_value` 覆盖原版 script value；本仓库的数据库条目规则是同名条目由后加载者覆盖前者，因此该文件保留原版调整链，并在雇主的勇士职位持有人中发现 `ox_here_free_champion` 时将薪资乘以 0。这个覆盖关系已做静态结构检查，尚未通过 CK3 启动后的实际加载日志确认。
- 因此该 NPC 仍然是原生 `champion_court_position`，不是另造一个伪职位；本次决议任命不产生即时资源扣除，并且该 NPC 实际担任勇士期间不产生月度职位薪资。

## 证据边界与待实机确认

当前只完成源码/原版数据静态检查。允许开始实机测试后，需要至少确认：

1. Royal Court 存在且勇士职位空缺时，决议执行后职位栏确实显示该 NPC 为勇士。
2. 勇士职位薪资 tooltip 显示免费，并在跨过月度 tick 后确认统治者资源没有职位薪资支出。
3. `received_salary` 不会产生意外的 NPC 收入或错误提示。
4. 没有 Royal Court、勇士职位已被占用时，不会错误任命或错误应用免费薪资逻辑。
5. 后续手动撤销该职位时，原版撤销威望费用仍按原版规则处理；本 mod 当前只承诺任命与在职月薪免费。

若 CK3 更新了 `champion_total_salary_value` 或 `champion_court_position` 的原版定义，必须重新对照上述文件，避免覆盖值遗漏新的原版薪资修正。

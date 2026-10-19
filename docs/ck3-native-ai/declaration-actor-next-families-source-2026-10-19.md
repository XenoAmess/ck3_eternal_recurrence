# 下一轮 declarable actor 闭包：额外 family 源研究

本包只交来源清单和审阅边界，不合入规则、不改 C++、当前四族规则 SHA、构建输入或 Native26 的 121 对象构建。执行 `machine_id: xenoamess-full-tower-eb9d2c1186`，来源是 `tools/ck3_live_run_id.py machine` 实读；主要封定观察时间 `2026-10-19T04:06:59.535968+00:00`。实际脚本根、全部文件 SHA、完整 token 闭包与当次容量读数见[研究 JSON](evidence/declaration-actor-next-families-source-2026-10-19.json)。无 Game/RPC、编译、注入或当前 Robert 状态读取。

沿用[已封四族模板](declaration-actor-candidate-performance-2026-10-19.md)的原生 caller 结论：完整查询的原 `allowed_for_character` 接收者是 actor-root，只有来源闭合、原生返回明确 no 时，才能把该 CB 的 defender 超集置空；yes / unknown 继续完整原路径。这里的额外清单尚未获得四族模板或运行时准入，不生成可用于环境开关的新 rules hash。

## 来源结果与下一轮优先次序

额外检查了 27 个 CB 根：18 个没有外部 named scope、参数替换、root/prev 或随机 token 的确定性 actor-derived 闭包；4 个只有 actor 派生的局部临时 scope，但超出现行模板；5 个存在 defender 或未特化上下文，暂不接收。JSON 保留每个根到全部递归 scripted-trigger 节点的关系、48 个节点的完整 token 文本和 23 份相关原版文件的全文 SHA，未省略 `is_house_head` 等容易误认成引擎原语的依赖。

| 额外根或 family | 完整依赖与确定性依据 | 条件与限制 |
| --- | --- | --- |
| `county_conquest_cb`、`duchy_conquest_cb`、`ducal_conquest_cb` | `can_use_conquest_cbs_trigger` → 当前政府 flag、rite parameter、culture parameter、Japan-feudal law；ducal 另查自身 perk。全为 actor 派生、布尔组合。 | **不能因封建就整族判 no。** county/duchy 有信仰、文化等 OR 出口；ducal 可因 perk 成为合法。 |
| `ireland_laudabiliter_conquest_cb` | `scope:attacker.house` 的存在与 house modifier；无递归 scripted trigger。 | actor.house 是已审 attacker 派生路径；当前是否有 modifier 未读。 |
| `clan_invasion_war` | 政府 flag、当前 house unity parameter、自身 cooldown 和变量集合；固定 if/else 分支。 | `government_is_clan` 为必要条件；来源确定、实际 flag 为 false 时可整族排除。 |
| `imperial_reconquest_cb`、`pax_romana_invasion_war` | `is_roman_emperor_excluding_byzantium_trigger` 实际检查 `h_roman_empire` / `h_eastern_roman_empire`；Pax 另查 administrative flag、自身 story 与 prestige。 | 不用 helper 名称猜成只检查一个头衔。Pax 有行政政府必要条件；普通帝国收复仍须真实 actor 结果。 |
| `nomadic_conquest_cb`、`nomadic_conquest_duchy_cb` | nomadic flag 与自身 realm-law flag；无递归依赖。 | nomadic flag 为必要条件，可优先安排下一轮资格。 |
| `mongol_invasion_war`、`mongol_realm_invasion_war` | `this` 与固定 `e_mongol_empire.holder` 比较、prestige；前者 → `has_mpo_dlc_trigger`，后者另查 `is_ai`。 | 固定全局头衔/DLC 也是同帧确定输入；不由演员名字推断结果。 |
| `fp1_varangian_adventurer_conquest` | 自身 culture 创新/时代、AI/traits、固定 `calc_true_if` 计数、game rule 与自身 realm county 地域谓词。无 scripted 依赖。 | `any_realm_county` 是 actor 辖境读，不是抽样；未出现 random/chance。不是仅凭封建可排除。 |
| `fp2_mediterranean_conquest_cb` | attacker/house modifier、是否 landed，以及对三个固定公国的 `completely_controls`。无 scripted 依赖。 | 固定 title operand 不引用当前 defender。自身控制范围可能变化，每查询重新判定。 |
| `japan_install_bloc_member_cb`、两种 `japan_soryo_conquest_county*` | `has_tgp_dlc_trigger`、`tgp_soryo_or_bushido_trigger`；landless 变体另 → `government_is_japanese_trigger`。闭包为 DLC、政府、culture tradition、landed/tier/house 存在。 | Soryo **或 Bushido culture** 是 OR，不能把所有非日本政府都直接排除；landless 变体有 landed=false 必要条件。 |
| `japan_demand_administrative_cb` | 当前/最高宗主 Japan-administrative flag；`tgp_is_ceremonial_liege_trigger` → `tgp_has_ceremonial_liege_title_trigger` → `tgp_realm_has_ceremonial_liege_trigger`。读取 actor.top_liege 的固定 title variable。 | actor 本人的 Japan-administrative flag 是必要条件；scripted title variable 不等于随机值或外部 defender。 |
| `mandala_raze_capital_structure_cb` | `has_tgp_dlc_trigger`、`has_mandala_capital_trigger` → actor capital province building flag。 | mandala flag 为必要条件；没有触碰当前建筑/宣战意图。 |

这里称“确定性”是指已审树只读取当次 actor 及其派生关系或当前全局/定义状态，使用固定逻辑、条件与存在/计数谓词，没有选择 defender 的输入或随机操作。它不是新 primitive whitelist 已经合入、Native ABI 已通过、实际 predicate 已求值或所有未来 mod 都相同的声明。每个新原语/路径仍须在下一轮 admission 中明确列入并验证。

## 四个局部 alias 闭包：不能漏依赖，也不能偷用现行模板

`tribal_subjugation_cb` → `pam_is_antipope_trigger`：先将当前 actor 保存为 `pam_antipope_holder_check`，再在自身 faith 的 religious-head challengers 中比较 holder。它的逻辑来源仍是 actor/faith，但包含 `save_temporary_scope_as` 和非 attacker 名字。

`invasion_war`、`japan_bloc_war_cb`、`mandala_plunder_cb` → scripted `is_house_head`（`00_dynasty_triggers.txt`）：`exists=this` 时先保存当前 actor 为 `house_check`，再读自身 house 的 house_head。`invasion_war` 还依赖 `ai_should_get_extreme_conqueror_bonuses`，实际只有 actor 的 conqueror variable 与 modifier。

这些依赖已完整写入 JSON，不能把 `is_house_head` 当未展开的 native primitive。当前四族审计明确拒绝 `save_` 与其他 named scope，故这四个 family **仍未准入**；下一轮须专门核临时 scope 的局部所有权、定义覆盖及 owned actor-context 行为。不能仅因族名或一个必要政府条件，就跳过现有 admission。

特别是 tribal 的 OR 还接受特定变量、宗教教义/宗教领袖/反教宗、house 扩展；invasion 也有 rite、flag、变量、conqueror、Mandala house 等出口。两者均不能由“Robert 是普通封建”推出完整 predicate 为 false。

## 暂不接收的 whole-trigger 路径

四种 `ep3_laamp_adventurer_*_invasion` 的 `allowed_for_character` 明确含 `scope:defender.highest_held_title_tier`。即使共同 actor trigger 能在普通封建时失败，现行整段 actor-root 接收者也不能对所有 actor 直接复用：它缺 defender 名字，可能误把原本合法的 defender 路径判 no。若未来做必要 actor 子式的专用优化，须另闭源/ABI，不能混入当前 whole-trigger 模式。

`mpo_nomad_invasion_cb` 的完整已取闭包含 `root`、`prev`、`$NOMAD$` / `$CHARACTER$` 参数和相邻 realm/关系/军力值。当前未完成参数、相对作用域与数值依赖的特化证明，保留宽路径。它的 nomadic 必要条件不能自动使整段复杂闭包获得资格。

索引时 `00_childhood_triggers.txt` 因顶层 `@... = 2` 常量不适配现有 parser；该文件不属于所列递归闭包。JSON 明确保留这一索引前沿，未宣称全 scripted-trigger 目录已准入。

## 普通封建的条件排除与历史成本

实际读取的 stock `feudal_government` flags 为 `government_is_feudal`、`government_is_settled`、`may_elevate_co_monarch`、`government_uses_crown_authority`、`government_uses_domain_limit`，文件 SHA 已记录。若当前原生 actor 确实仍使用这份定义，可由缺少必须的 clan / nomadic / administrative / Japan-administrative / mandala flag 说明上表若干 family 必然失败；这不是本包读回了当前 Robert 的政府，更不是替代未来原生 actor precheck 的名称黑名单。原 precheck 对实际对象返回 no 才可排除，yes / unknown 始终保留。

封定历史 profile 仍为 **`machine_id: unknown`，所属机器未核实**。只读原尾 65,536 B，offset `2221633`，SHA `9765060dea7f43eb9e141b0702383eeb6672a0ea44f3378f7fc9a3b7f8720770`；末完整行 SHA `88fca2fe1746dc583ba0b5663d1b2f90813a2822cb0856aa9c92153c9420de8b`。该行 actor82925/date53401728，不能冒充当前 Robert 或本机新计时。

按该历史行，额外18个 strict family 出现的 evaluator 调用合计 `420412`、instrumented evaluate `688904800 ns`。这只是被研究族在历史 profile 中占用的成本，**不是可节省时间**：当前 actor predicate 可能为 yes、未知，或该 family 在新查询根本未启用。新旧 profile 的 `available=0` 也不证明 actor gate 为 no。历史排序优先看 duchy conquest、clan/tribal/invasion、imperial 等，完整 top30 与每族原始行在 JSON；不据这些数值承诺当前硬件提速。

## 交付边界

只新增本文和研究 JSON，合计远小于 1 MiB 微池。提取使用现有四族工具的只读 tokenizer/parser；没有修改它、旧 source audit、rules hash 或任何构建入口。一次超长内联 Python 命令被 Windows 命令长度限制拒绝，未产生产品或构建修改；随后用本包短期脚本完成有界提取并精确删除该临时脚本。无测试/编译/运行时资格由本次源码研究产生。

下一轮应独立合批扩审新原语/局部 alias、全部新 CB 与 scripted-trigger 的实际加载来源，再做原 native no 与完整有序 tuple shadow 对照。当前 Native26 不因这份清单重编、热换或重新启动，候选数量与宣战意图没有改变。通用存储策略 `1.0.0` 继续适用，本包没有重型写入、删除旧证据或容量信用。
